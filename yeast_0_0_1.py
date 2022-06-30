import asyncio
from typing import Tuple

from prompt_toolkit.input import create_input
from prompt_toolkit.keys import Keys

"""
This is a starting point to determine the structure of our interactive unlambda repl.
There is just one transformation possible on a stream of characters : ` will drop the next character in the stream.
The repl interface is a usual line, with 'enter' key triggering the evaluation of a sequence of char, the usual way.
"""


def live_char_eval(ch: int, drop_count: int) -> Tuple[int | None, int]:
    # v0.0.1 : one char apply: drop next char on tick

    if ch == ord(b"`"):
        drop_count += 1
        return None, drop_count  # tick is consumed
    elif drop_count > 0:
        drop_count -= 1
        return None, drop_count  # this char is consumed
    else:
        return ch, drop_count  # return this char untouched


def live_line_eval(s: bytearray) -> bytearray:
    """a live eval implementation. receiving one line."""
    result = bytearray()

    # the drop count is local to the line (unused backticks will be discarded)
    # but it persists between multiple live_char_eval calls
    drop_count = 0

    for b in s:  # extract from the queue (time sensitive -> FIFO)
        r, d = live_char_eval(b, drop_count)
        drop_count = d
        if r is not None:
            result.append(r)  # (time sensitive -> FIFO)

    return result


def live_char_tty(key_press, pqueue: bytearray):
    """a live tty implementation. receiving keypresses one by one and returning outputs.
    TODO : we could pass a data representation of the tty, instead of using print and global sys.stdout"""

    if key_press.key == Keys.Enter:
        print()  # EOL -> eval everything
        result = live_line_eval(pqueue)
        pqueue = result
        # next line prompt filled with result
        print(f"> {pqueue.decode('ascii')}", end="")

    elif key_press.key == Keys.Backspace:
        print(
            "\b", end="\033[K"
        )  # we rely on ANSI escape code CSI K for terminal control.
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
