from __future__ import annotations
import contextlib
from itertools import repeat
from typing import Callable, Generator, Iterator, List, Tuple

import curses
from pipeline import Pipeline

"""

Character input as int [0..254] iterator (possibly async ?)
Also as a Pipeline to modify itself with operators on iterables

"""


class char:

    __slots__ = ("yx", "ch")

    @classmethod
    def generate(
        cls,
        call_position: Callable[[], Tuple[int, int]],
        call_input: Callable[[], int],
        until: List[int]
    ) -> Generator[char, None, None]:
        while (ch := call_input()) not in until:
            yield char(ch, call_position())

    def __init__(self, ch: int, yx: Tuple[int, int]) -> None:
        self.yx = yx
        self.ch = ch

    def __repr__(self) -> str:
        return f'{self} @ {self.yx}'

    def __str__(self) -> str:
        return bytes([self.ch]).decode('ascii')


# Note:
# - Char input, is a generator of (one) byte = int
# - Word input is a generator of bytes
# - line input is a generator of bytes (as lines), and is also a stream (following stream protocol).


class CharInput(Pipeline):

    # TODO : add methods to manipulate output on screen, usable on generator pipeline/stream
    #        -> CharIO

    def __init__(self, call_position:  Callable[[], Tuple[int, int]], call_input: Callable[[], int], until: List[int]):
        iter_input = char.generate(call_position, call_input, until)
        super(CharInput, self).__init__(iter_input)

    def __call__(self, fun: Callable[[char], char]):
        # applying the function to this iterator
        # effectively making this a decorator (?)
        self.map(fun)
        # TODO : better mapper here (follow mapper in word implementation)


if __name__ == "__main__":

    # computer user interface delegate to curses window
    stdscr = curses.initscr()

    # these requires initscr() to be called before
    # no immediate echo
    curses.noecho()
    # cbreak mode to not buffer keys
    curses.cbreak()

    charin = CharInput(
        call_position=stdscr.getyx,
        call_input=stdscr.getch,
        until=[
            4,  # EOT  via Ctrl-D
            10,  # EOL  via Enter/Return
        ],
    )

    @charin
    def char_process(ch: char) -> char:
        # TODO: unicode / complex char / multipress input ???
        if ch.ch in [
            ord(b"\b"),
            127,
            curses.KEY_BACKSPACE,
        ]:  # various possible ascii codes for a delete backspace
            stdscr.delch(ch.yx[0], ch.yx[1] - 1)
        else:
            stdscr.addch(ch.ch)
        return ch

    # to loop through the iterator until the end
    print([c for c in charin])
    # Note : no time to see the print in output since curses erases the screen on exit

    # curses cleanup
    curses.nocbreak()
    curses.echo()

    # closing screen
    curses.endwin()
