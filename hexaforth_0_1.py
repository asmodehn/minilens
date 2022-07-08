""" A first iteration for a ASCII based Forth, limited to one character at a time.
We also want the interactive feedback to be character by character."""
from __future__ import annotations

import copy
import functools
from typing import Callable, ClassVar, Dict, List, Optional, Tuple

from prompt_toolkit import PromptSession
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import Completer, Completion, ThreadedCompleter
from prompt_toolkit.lexers import PygmentsLexer
from prompt_toolkit.styles import Style
from prompt_toolkit.validation import ValidationError, Validator
from pygments.lexer import RegexLexer
from pygments.token import Keyword, Name


class StackUnderflow(Exception):
    """ Specific CStack underflow exception"""

    def __init__(self, snap: Snapshot, *args):
        self.snap = snap
        super().__init__(*args)

    def __str__(self):
        return f"StackUnderflow: {self.snap}"


class StackOverflow(Exception):
    """ Can happen on tiny machine, not ever likely in python"""
    pass


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


class MetaMachine(type):
    """
    This is a Forth MetaMachine.
    Useful for simple definition of a Forth Machine.
    It is the immutable part of our Forth System.
    """

    # minimal inner forth system
    dict: ClassVar[Dict[int, Callable[[bytearray, int], int | None]]] = {
        # TODO : maybe some way to represent implementation in a symbolic high level way ??
        ord(b"."): lambda s, _: s.pop(),
        ord(b"a"): lambda s, c: s.append(c),
        ord(b"b"): lambda s, c: s.append(c),
        ord(b"c"): lambda s, c: s.append(c),
    }

    def __call__(cls, initial_stack: Optional[bytes] = None):
        inst = super(MetaMachine, cls).__call__(initial_stack)
        # copying the initial forth dict onto the machine instance
        inst.dict = cls.dict.copy()
        # this guarantees that even if a machine screws up its class-wide dictionary,
        # we can always recreate an instance with a clean dictionary.
        return inst

    def __repr__(cls) -> str:
        return f"<class '{cls.__qualname__}' {{{''.join(chr(k) for k in cls.dict.keys())}}}>"


class Machine(metaclass=MetaMachine):
    """ Forth virtual machine as a class instance.
    The stack state needs to be kept between multiple evaluation calls.
    the machine is callable to trigger evaluation. the stack will be modified.
    a snapshot() method is provided to duplicate and freeze the state of the machine at that point in time.
    """

    def __init__(self, initial_stack: Optional[bytes] = None):
        self.stack = bytearray() if initial_stack is None else bytearray(initial_stack)

    def __repr__(self):
        return f"<{{{''.join(chr(k) for k in self.dict.keys())}}} {self.__class__.__name__} stack: {bytes(self.stack)}>"

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

    def __call__(self, s: bytes) -> bytes:
        """a live eval implementation. receiving one line at a time (as a sequence of bytes)."""

        self.__class__()

        # storing output
        output = bytearray()

        for i, b in enumerate(s):  # extract from the queue (time sensitive -> FIFO)

            # Note the content of the queue should be in reverse order already (user input)
            # we don't drop "next" character, but the *previous* one in the stack.
            try:

                # find implementation in dict, and run it
                if (out := self.dict[b](self.stack, b)) is not None:
                    output.append(out)

            except IndexError as ie:
                raise StackUnderflow(self.snapshot(last_input=s, cursor_position=i), *ie.args) from ie

            # Note: stack has been modified

        # return the output after evaluating this line
        return bytes(output)

    def snapshot(self, last_input: bytes, cursor_position: int):
        return Snapshot(
            stack=bytes(self.stack),  # will copy the bytearray in an immutable bytes
            last_input=last_input,
            cursor_position = cursor_position
        )

    @property
    def tokens(self) -> int:
        return self.dict.keys()



# The Machine
machine = Machine()


@functools.lru_cache
def live_char_expect(s: bytes) -> List[bytes]:
    """
    smart editing that given a list of possible inputs and the current input line state,
    will evaluate immediately and propose only non-problematic inputs.
    sorted in order of more options later first, to more restrictive one (because life metaphysics)

    This is a pure function -> should be cached, because the same sequence of bytes might be passed many times
    """
    possible_inputs = [b"a", b"b", b"c", b"."]
    acceptable_inputs = []
    forbidden_inputs = []

    for p in possible_inputs:
        # generate a new, distinct machine from the current one.
        # we do not want to affect the state of the current machine.
        # TODO
        t = bytearray(s)
        t.append(ord(p))

        try:
            r = live_line_eval(bytes(t))
        except Exception as e:
            forbidden_inputs.append(p)
        else:
            # storing acceptable inputs with some measure of priority
            acceptable_inputs.append((p, len(r)))

    return [a[0] for a in sorted(acceptable_inputs, key=lambda t: t[1])]


# global pstack as a global state, since prompt doesn't allow to prefill text via a parameter
# Note: The pstack is kept between lines, but reset for each session...
pstack = bytearray()


class CustomLexer(RegexLexer):
    """A basic lexer for our dummy language"""

    name = "dummy"

    tokens = {
        "root": [
            # use different colors for different instruction types
            (r"[.]+", Keyword),
            (r"[a-z]+", Name),
        ],
    }


# dynamic auto complete
class CustomCompleter(Completer):
    def get_completions(self, document, complete_event):
        acceptable = []

        # duplicate the Machine for each possible subsequent input
        for next_ch in machine.tokens:
            m = machine.copy()

            try:
                r = m(bytes(document.text_before_cursor.encode("ascii")) + bytes(next_ch))
            except Exception as e:
                pass  # ignore failures when guessing possible completions
            else:
                # storing acceptable inputs with some measure of priority
                acceptable.append((next_ch, len(r)))

        suggest = [a[0] for a in sorted(acceptable, key=lambda t: t[1])]

        for s in suggest:
            yield Completion(s.decode("ascii"))


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
            # TODO : BackMachine ?? anyway the cursor possition doesnt seem to work at teh moment..
            # for b in range(1, len(whole_text)):
            #     partial_text = whole_text[:-b]
            #     try:
            #         live_line_eval(partial_text)
            #     except Exception as e:
            #         continue  # text still invalid
            #     else:
            #         break  # found a valid text

            raise ValidationError(
                message=message,
                # BUG : doesnt work ?
                cursor_position=0,
            )


def session(**kwargs):

    lexer = PygmentsLexer(CustomLexer)

    # completer = CustomCompleter()
    # just performance optimisation
    completer = ThreadedCompleter(CustomCompleter())

    validator = CustomValidator()

    style = Style.from_dict(
        {
        }
    )

    return PromptSession(
        message="> " + pstack.decode("ascii"),
        lexer=lexer,
        auto_suggest=AutoSuggestFromHistory(),
        enable_history_search=False,
        completer=completer,
        complete_while_typing=True,
        validator=validator,
        validate_while_typing=True,
        style=style,
        wrap_lines=False,
        **kwargs,
    )


# Known issue about completion on backspace : https://github.com/prompt-toolkit/python-prompt-toolkit/issues/491


def repl(session: PromptSession):

    while True:
        print(f"< {machine.stack.decode('ascii')}")
        try:
            text = session.prompt()
        except KeyboardInterrupt:
            continue  # Control-C pressed. Try again.
        except EOFError:
            break  # Control-D pressed.

        try:
            # modify pstack
            out = machine(text.encode("ascii"))

            # printing output
            print(out)

        except IndexError as ie:
            print("Error evaluating parameters. Reset!\n> ")
        except Exception as e:
            print(repr(e))

    print("GoodBye!")


if __name__ == "__main__":
    repl(session())
