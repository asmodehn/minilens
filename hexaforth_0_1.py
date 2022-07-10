""" A first iteration for a ASCII based Forth, limited to one character at a time.
We also want the interactive feedback to be character by character."""
from __future__ import annotations

import copy
import functools
from typing import Callable, ClassVar, Dict, List, Optional, Tuple

from prompt_toolkit import PromptSession
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import Completer, Completion, ThreadedCompleter
from prompt_toolkit.input import Input
from prompt_toolkit.lexers import PygmentsLexer
from prompt_toolkit.output import Output
from prompt_toolkit.styles import Style
from prompt_toolkit.validation import ValidationError, Validator
from pygments.lexer import RegexLexer
from pygments.token import Keyword, Name


class Snapshot:
    __slots__ = ('stack', 'last_input', 'cursor_position')

    def __init__(self, stack: bytes, last_input: bytes, cursor_position: int):
        object.__setattr__(self, 'stack', stack)
        object.__setattr__(self, 'last_input', last_input)
        object.__setattr__(self, 'cursor_position', cursor_position)

    def __setattr__(self, key, value):
        raise AttributeError(f"{key} is Read-Only")

    def __repr__(self):
        return f"{self.stack} > {self.last_input} @ {self.cursor_position}"

    def __hash__(self):
        return hash((self.stack, self.last_input, self.cursor_position))

    def __eq__(self, other):
        # return either intensional (from implementation) equality,
        # or extensional (semantic equality)
        return id(self) == id(other) or hash(self) == hash(other)


class StackUnderflow(Exception):
    """ Specific CStack underflow exception"""
    snap: Snapshot

    def __init__(self, snap: Snapshot, *args):
        self.snap = snap
        super().__init__(*args)

    def __str__(self):
        return f"StackUnderflow: {self.snap}"

    def __eq__(self, other):
        """ adding extensional equality via snapshot"""
        return id(self) == id(other) or self.snap == other.snap


class StackOverflow(Exception):
    """ Can happen on tiny machine, not ever likely in python"""
    pass


class UnknownToken(Exception):
    """ Specific CStack underflow exception"""
    snap: Snapshot

    def __init__(self, snap: Snapshot, *args):
        self.snap = snap
        super().__init__(*args)

    def __str__(self):
        return f"UnknownToken: {chr(self.snap.last_input[self.snap.cursor_position])} @ {self.snap.cursor_position}"


# TODO : package structure to hide sensitive things in a "lower" namespace (this should not be part of the metaclass)
# minimal inner immutable forth system
dict_prototype: Dict[int, Callable[[bytearray, int], int | None]] = {
    # ord(b"\n"): lambda s, c: eval(s, "all chars after c")  # TODO a way to handle \n via dict
    # TODO : maybe some way to represent implementation in a symbolic high level way ?? continuation ???
    ord(b"."): lambda s, _: s.pop(),  # popping (and outputting by return)
    ord(b"a"): lambda s, c: s.append(c),
    ord(b"b"): lambda s, c: s.append(c),
    ord(b"c"): lambda s, c: s.append(c),
}


def eval(dctn: Dict[int, Callable[[bytearray, int], int | None]], stck: bytearray, astr: bytes) -> bytes:
    """evaluates a line only. no \n present in astr or it will recurse /!\ TODO."""
    output = bytearray()
    # need to keep a copy of the stack as evidence in case of error
    stack_on_eval_start = bytes(stck)

    for i, b in enumerate(astr):  # extract from the queue (time sensitive -> FIFO)

        # Note the content of the queue should be in reverse order already (user input)
        # we don't drop "next" character, but the *previous* one in the stack.
        try:

            # find implementation in dctn, and run it
            if (out := dctn[b](stck, b)) is not None:
                output.append(out)

        except IndexError as ie:  # when stack underflows (or overflows ??)
            # raising an exception with a snapshot, where the eval can be replayed to trigger the same error
            raise StackUnderflow(Snapshot(stack=stack_on_eval_start, last_input=astr, cursor_position=i), *ie.args) from ie
        except KeyError as ke:  # when a token is not defined in dctn
            raise UnknownToken(Snapshot(stack=stack_on_eval_start, last_input=astr, cursor_position=i), *ke.args) from ke

    # Note: stack has been modified
    return bytes(output)


class MetaMachine(type):
    """
    This is a Forth MetaMachine.
    Useful for simple definition of a Forth Machine class/type.
    """

    dict: Dict[int, Callable[[bytearray, int], int | None]] = dict_prototype.copy()

    def __repr__(cls) -> str:
        return f"<class '{cls.__qualname__}' {{{''.join(chr(k) for k in cls.dict.keys())}}}>"


class Machine(metaclass=MetaMachine):
    """ Forth virtual machine as a class instance.
    The stack state needs to be kept between multiple evaluation calls.
    the machine is callable to trigger evaluation. the stack will be modified.
    a snapshot() method is provided to duplicate and freeze the state of the machine at that point in time.
    """

    dict: Dict[int, Callable[[bytearray, int], int | None]] = dict_prototype.copy()

    def __init__(self, initial_stack: Optional[bytes] = None, *,
        input: Optional[Input] = None,
        output: Optional[Output] = None
    ):
        self.stack = bytearray() if initial_stack is None else bytearray(initial_stack)
        self.input = input
        self.output = output

    @property
    def tokens(self) -> List[int]:
        return list(self.dict.keys())

    def __repr__(self):
        return f"<{{{''.join(chr(k) for k in self.tokens)}}} {self.__class__.__name__} stack: {bytes(self.stack)}>"

    def __copy__(self):
        """ forcing deepcopy. shallow copy doesn't make sense here"""
        return self.__deepcopy__()

    def __deepcopy__(self, memodict=None):
        if memodict is None:
            memodict = {}

        return Machine(copy.deepcopy(self.stack))

    def copy(self):
        """ en explicit copy() method like on mutable data structures """
        return copy.copy(self)

    def __call__(self, astr: bytes) -> bytes:
        """a live eval implementation. receiving one line at a time (as a sequence of bytes).
        If a newline character is present, the eval recurse into itself,
        to get into the correct state if exception occurs (bubble up all recursion levels)
        """

        # storing output
        output: List[bytes] = []

        for seq in astr.split(b"\n"):
            # implemented as loop. The other option is an eval recursion,
            # which is nasty in python, or non tail-call-optimized languages
            output.append(eval(self.dict, self.stack, seq))
            # note the stack is modified during the loop, as simply this passes the reference to it.

        # return the output after evaluating this line
        return b"\n".join(output)

    def snapshot(self, last_input: bytes, cursor_position: int):
        return Snapshot(
            stack=bytes(self.stack),  # will copy the bytearray in an immutable bytes
            last_input=last_input,
            cursor_position=cursor_position
        )

    @property
    def lexer(self) -> PygmentsLexer:
        machine = self

        class CustomLexer(RegexLexer):
            """A basic lexer for our dummy language"""

            name = "dummy"

            tokens = {
                "root": [
                    # use different colors for different instruction types
                    (r"[.]", Keyword),
                    (r"[a-c]", Name),
                ],
            }
        return PygmentsLexer(CustomLexer)

    @property
    def completer(self) -> Completer:
        machine = self

        """dynamic auto complete"""
        class CustomCompleter(Completer):
            def get_completions(self, document, complete_event):
                acceptable: List[Tuple[bytes, int]] = []

                # duplicate the Machine for each possible subsequent input
                for next_ch in machine.tokens:
                    m = machine.copy()

                    try:
                        next_bytes = bytes([next_ch])
                        r = m(bytes(document.text_before_cursor.encode("ascii")) + next_bytes)
                    except Exception as e:
                        pass  # ignore failures when guessing possible completions
                    else:
                        # storing acceptable inputs with some measure of priority
                        acceptable.append((next_bytes, len(r)))

                suggest = [a[0] for a in sorted(acceptable, key=lambda t: t[1], reverse=True)]

                for s in suggest:
                    yield Completion(s.decode("ascii"))

        completer = CustomCompleter()
        # just performance optimisation (?)
        # completer = ThreadedCompleter(CustomCompleter())
        return completer

    @property
    def validator(self) -> Validator:
        machine = self

        class CustomValidator(Validator):
            def validate(self, document):

                # duplicate the machine, as we dont want the validator to modify the current state
                m = machine.copy()

                whole_text = bytes(document.text.encode("ascii"))
                try:
                    m(whole_text)
                except Exception as e:

                    message = f"{type(e).__name__}: {e}"

                    # attempt to find index of the last valid sequence of char
                    b = 1
                    # TODO : BackMachine ?? anyway the cursor position doesnt seem to work at the moment..
                    # for b in range(1, len(whole_text)):
                    #     partial_text = whole_text[:-b]
                    #     try:
                    #         live_line_eval(partial_text)
                    #     except Exception as e:
                    #         continue  # text still invalid
                    #     else:
                    #         break  # found a valid text

                    raise ValidationError(
                        message=str(e),
                        # BUG : doesnt work ?
                        cursor_position=0,
                    )
        return CustomValidator()

    def prompt_session(self, **kwargs):

        style = Style.from_dict(
            {
            }
        )

        return PromptSession(
            message="> ",
            lexer=self.lexer,
            auto_suggest=AutoSuggestFromHistory(),
            enable_history_search=False,
            completer=self.completer,
            complete_while_typing=True,
            validator=self.validator,
            validate_while_typing=True,
            style=style,
            wrap_lines=False,
            input=self.input,
            output=self.output,
            **kwargs,
        )


# Known issue about completion on backspace : https://github.com/prompt-toolkit/python-prompt-toolkit/issues/491


def repl(machine: Machine):
    session = machine.prompt_session()

    while True:
        print(f"< {machine.stack.decode('ascii')}")
        try:
            text = session.prompt()
        except KeyboardInterrupt:
            continue  # Control-C pressed. Try again.
        except EOFError:
            break  # Control-D pressed.

        try:
            # modify machine stack
            out = machine(text.encode("ascii"))

            # printing output
            print(out)

        except IndexError as ie:
            # ideally validation is good enough that we never reach here...
            print("Error evaluating parameters. Reset!\n> ")
        except Exception as e:
            print(repr(e))

    print("GoodBye!")


if __name__ == "__main__":
    repl(Machine())
