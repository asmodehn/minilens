import asyncio
from typing import List, Tuple

from prompt_toolkit.input import create_input
from prompt_toolkit.keys import Keys

"""
This is a second step to determine the structure of our interactive unlambda repl.
There is just one transformation possible on a stream of characters : ` will drop the next character in the stream.
The repl interface is a usual line, with 'enter' key triggering the evaluation of a sequence of char, the usual way.

The interface is now reverse (stack-based concatenative).
The main impact is that, the parameters already being present when inputting the next command, 
can be used by the system to adjust the set of possible inputs (structured editing style).

Concretely : one cannot drop more characters than present on the input line
=> prevents ambiguous behavior:
 - ` on previous line will remove first character of next line ?
 - or previous state has been cancelled after one line ?
 
Note : in this version we keep working char by char, and the whole state is visible on the input line.
  => the previous line being finished means hte state is clean (not like in Forth)
"""


def live_char_eval(ch: int, result: bytearray) -> None:
    # v0.0.2: one char apply: drop *previous* char on tick

    if ch == ord(b'`'):
        # if tick in input, tick is consumed, previous char is dropped
        result.pop()
    else:
        if len(result) >0 and result[-1] == ord(b'`'):
            # otherwise if tick in result, it is consumed (for safety, should not happen)
            result.pop()

        # and char is added anyway
        result.append(ch)  # return this char untouched (for now)


def live_line_eval(s: bytearray) -> bytearray:
    """ a live eval implementation. receiving one line at a time.

     """
    # global result holding computation state for the whole input line
    result = bytearray()

    for b in s:  # extract from the queue (time sensitive -> FIFO)

        # Note the content of the queue should be in reverse order already (user input)
        # we don't drop "next" character anymore, but the *previous* one in the result stack
        # => passing the result stack around is simpler than maintaining a counter.
        live_char_eval(b, result)
        # result has been modified

    return result


def live_char_expect(s: bytearray) -> List[int]:
    """
    smart editing that given a list of possible inputs and the current input line state,
    will evaluate immediately and propose only non-problematic inputs.
    sorted in order of more options later first, to more restrictive one (because life metaphysics)
    """
    possible_inputs = [b'a', b'b', b'c', b'`']
    raise NotImplementedError()


def live_char_tty(key_press, pqueue: bytearray):
    """ a live tty implementation. receiving keypresses one by one and returning outputs.
    TODO : we could pass a data representation of the tty, instead of using print and global sys.stdout"""

    if key_press.key == Keys.Enter:
        print()  # EOL -> eval everything
        result = live_line_eval(pqueue)
        pqueue = result
        # next line prompt filled with result
        print(f"> {pqueue.decode('ascii')}", end="")

    elif key_press.key == Keys.Backspace:
        print("\b", end="\033[K")  # we rely on ANSI escape code CSI K for terminal control.
        # Ref: https://en.wikipedia.org/wiki/ANSI_escape_code
        pqueue.pop()  # remove previous character

    elif len(ascii_input := key_press.data.encode("ascii")) == 1:
        pqueue.append(ord(ascii_input))  # as a queue !
        # printing in repl line after pushing to the stack
        print(ascii_input.decode("ascii"), end="")

    else:
        raise NotImplementedError(key_press)


async def repl() -> None:
    done = asyncio.Event()
    input = create_input()

    line = bytearray()  # unconsumed characters in-order
    # TODO : maybe we can use input buffer instead here ?

    def keys_ready():
        for key_press in input.read_keys():
            # print(key_press)

            if key_press.key == Keys.ControlC:
                print("GoodBye!")
                done.set()
            else:
                live_char_tty(key_press, line)

    with input.raw_mode():
        # first line prompt
        print("> ", end="")
        with input.attach(keys_ready):
            await done.wait()


if __name__ == "__main__":
    asyncio.run(repl())
