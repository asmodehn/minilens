import asyncio
import functools
import sys
from types import MethodType
from typing import List, Optional, Tuple

from prompt_toolkit import PromptSession
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import Completer, Completion, ThreadedCompleter
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.input import Input, create_input
from prompt_toolkit.keys import Keys
from prompt_toolkit.lexers import PygmentsLexer
from prompt_toolkit.output import Output
from prompt_toolkit.styles import Style
from prompt_toolkit.validation import ValidationError, Validator
from pygments.lexer import RegexLexer
from pygments.token import Keyword, Name

"""
This is a third step to determine the structure of our interactive unlambda repl.
There is just one transformation possible on a stream of characters : ` will drop the next character in the stream.
The repl interface is a usual line, with 'enter' key triggering the evaluation of a sequence of char, the usual way.

The interface is reverse (stack-based concatenative).
The main impact is that, the parameters already being present when inputting the next command, 
can be used by the system to adjust the set of possible inputs (structured editing style).

Concretely : one cannot drop more characters than present on the input line
=> prevents ambiguous behavior:
 - ` on previous line will remove first character of next line ?
 - or previous state has been cancelled after one line ?
 
In this version we take the approach of working with a line of input.
We also add syntax coloring and dynamic autocomplete along with basic validation,
as these are the most interesting interactive features possible on a char-based input, within a line-based context.
This way we are following what seem to be the usual user interface in a terminal...

To keep code complexity low, we will start relying on prompt_toolkit structure, for the user interface side at least.
 
Note : in this version we keep whole state visible on the input line.
  => the previous line being finished means the state is clean (not like in Forth Systems)
"""


def live_char_eval(ch: int, result: bytearray) -> None:
    # v0.0.2: one char apply: drop *previous* char on tick

    if ch == ord(b"`"):
        # if tick in input, tick is consumed, previous char is dropped
        result.pop()
    else:
        if len(result) > 0 and result[-1] == ord(b"`"):
            # otherwise if tick in result, it is consumed (for safety, should not happen)
            result.pop()

        # and char is added anyway
        result.append(ch)  # return this char untouched (for now)


def live_line_eval(s: bytes) -> bytearray:
    """a live eval implementation. receiving one line at a time (as a sequence of bytes)"""

    # global result holding computation state for the whole input line
    result = bytearray()

    try:
        for b in s:  # extract from the queue (time sensitive -> FIFO)

            # Note the content of the queue should be in reverse order already (user input)
            # we don't drop "next" character anymore, but the *previous* one in the result stack
            # => passing the result stack around is simpler than maintaining a counter.
            live_char_eval(b, result)
            # result has been modified

    except Exception as e:
        # just reraise
        raise e

    return result


@functools.lru_cache
def live_char_expect(s: bytes) -> List[bytes]:
    """
    smart editing that given a list of possible inputs and the current input line state,
    will evaluate immediately and propose only non-problematic inputs.
    sorted in order of more options later first, to more restrictive one (because life metaphysics)

    This is a pure function -> should be cached, because the same sequence of bytes might be passed many times
    """
    possible_inputs = [b"a", b"b", b"c", b"`"]
    acceptable_inputs = []
    forbidden_inputs = []

    for p in possible_inputs:
        t = bytearray(s)
        t.append(ord(p))

        try:
            r = live_line_eval(bytes(t))
        except Exception as e:
            forbidden_inputs.append(p)
        else:
            # storing acceptable inputs with a measure of priority
            acceptable_inputs.append((p, len(r)))

    return [a[0] for a in sorted(acceptable_inputs, key=lambda t: t[1])]


# global pstack as a global state, since prompt doesn't allow to prefill text via a parameter
pstack = bytearray()


class CustomLexer(RegexLexer):
    """A basic lexer for our dummy language"""

    name = "dummy"

    tokens = {
        "root": [
            # use different colors for different instruction types
            (r"[`]+", Keyword),
            (r"[a-z]+", Name),
        ],
    }


lexer = PygmentsLexer(CustomLexer)


# dynamic auto complete
class CustomCompleter(Completer):
    def get_completions(self, document, complete_event):
        # CAREFUL : don't forget prefix to input !
        suggest = live_char_expect(
            bytes(pstack) + bytes(document.text_before_cursor.encode("ascii"))
        )

        for s in suggest:
            yield Completion(s.decode("ascii"))


# completer = CustomCompleter()
# just performance optimisation
completer = ThreadedCompleter(CustomCompleter())


style = Style.from_dict(
    {
        "rprompt": "bg:#ff0000 #ffffff",
    }
)


class CustomValidator(Validator):
    def validate(self, document):
        whole_text = bytes(pstack) + bytes(document.text.encode("ascii"))
        try:
            live_line_eval(whole_text)
        except Exception as e:

            message = f"{type(e).__name__}: {e}"

            b = 1
            for b in range(1, len(whole_text)):
                partial_text = whole_text[:-b]
                try:
                    live_line_eval(partial_text)
                except Exception as e:
                    continue  # text still invalid
                else:
                    break  # found a valid text

            raise ValidationError(
                message=message,
                # BUG : doesnt work ?
                cursor_position=0,
            )


validator = CustomValidator()


def session(**kwargs):
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
        **kwargs,
    )


# Known issue about completion on backspace : https://github.com/prompt-toolkit/python-prompt-toolkit/issues/491


def repl(session: PromptSession):

    while True:

        try:
            text = pstack.decode("ascii") + session.prompt()
        except KeyboardInterrupt:
            continue  # Control-C pressed. Try again.
        except EOFError:
            break  # Control-D pressed.

        try:
            # modify pstack in place
            pstack[:] = live_line_eval(text.encode("ascii"))
        except IndexError as ie:
            print("Error evaluating parameters. Reset!\n> ")
            pstack.clear()  # clear parameter queue on error
        except Exception as e:
            print(repr(e))

    print("GoodBye!")


if __name__ == "__main__":
    repl(session())
