from itertools import repeat
from typing import Callable, Iterator, List

import curses
from ppl import Pipeline

"""

Character input as int [0..254] iterator (possibly async ?)
Also as a Pipeline to modify itself with operators on iterables

"""

class CharInput(Pipeline):

    # TODO : add methods to manipulate output on screen, usable on generator pipeline/stream
    #        -> CharIO

    # Note:
    # - Char input, is a generator of (one) byte = int
    # - Word input is a generator of bytes
    # - line input is a generator of bytes (as lines), and is also a stream (following stream protocol).

    @classmethod
    def from_callable(cls, call_input: Callable[[], int], until: List[int]):
        def gen():
            while (ch := call_input()) not in until:
                yield ch

        # starting generator immediately (consumption is blocking)
        # TODO : maybe delay based on CharArea available and initialized ??
        return CharInput(gen(), until=until)

    def __init__(self, iter_input: Iterator[int], until: List[int]):
        self.until = until
        super(CharInput, self).__init__(iter_input)


class CharArea:  # TODO  :extract a common Area concept, that works for words and lines

    def __init__(self, stdscr):
        self.stdscr = stdscr

    def __enter__(self):
        self.r, self.c = self.stdscr.getyx()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # move to the beginning of the word
        self.stdscr.move(self.r, self.c)

        # erase until the end of line (input limit)
        self.stdscr.clrtoeol()

        # screen is now clean again for further output

    def __call__(self, ch: int) -> int:
        """ char input behavior in the area """
        # TODO: unicode / complex char / multipress input ???
        r, c = self.stdscr.getyx()  # local coord for this call / this char
        if ch in [ord(b"\b"), 127, curses.KEY_BACKSPACE]:  # various possible ascii codes for a delete backspace
            self.stdscr.delch(r, c - 1)
        else:
            self.stdscr.addch(ch)
        return ch


if __name__ == "__main__":

    # computer user interface delegate to curses window
    stdscr = curses.initscr()

    # these requires initscr() to be called before
    # no immediate echo
    curses.noecho()
    # cbreak mode to not buffer keys
    curses.cbreak()


    charin = CharInput.from_callable(call_input=stdscr.getch, until=[
        4,  # EOT  via Ctrl-D
        10,  # EOL  via Enter/Return
    ])

    with CharArea() as area:
        charin.map(area)

    # to loop through the iterator until the end
    print([c for c in charin])


    # curses cleanup
    curses.nocbreak()
    curses.echo()

    # closing screen
    curses.endwin()
