from __future__ import annotations
import contextlib
import itertools
import operator
from itertools import cycle, groupby, pairwise
from typing import Callable, Generator, Iterator, List

from char import char
from pipeline import Pipeline

"""

Word input as bytes iterator (possibly async ?)
Also as a Pipeline to modify itself with operators on iterables

"""


class word:

    __slots__ = ("yx", "wd")

    # Note:
    # - Char input, is a generator of (one) byte = int
    # - Word input is a generator of bytes
    # - line input is a generator of bytes (as lines), and is also a stream (following stream protocol).

    @classmethod
    def generate(
        cls, chi: Pipeline[char], separators: List[int]
    ) -> Generator[word, None, None]:
        # we want a new pipeline, without modifying the existing char_pipeline
        # Note : we want to tee the char pipeline to allow others (line pipeline f.i.) to consume it (?????)
        for k, gc in groupby(chi, key=lambda c: c.ch in separators):
            if not k:  # if this char is not a separator
                yield word(chi=gc, separators=separators)

    def __init__(self, chi: Iterator[char], separators: List[int]) -> None:
        # get the position of the beginning of the word
        first_char = next(chi)
        self.yx = first_char.yx
        # accumulate chars from iterator into a word (until a separator is encountered)
        self.wd = bytes([first_char.ch] + [ch.ch for ch in chi if ch.ch not in separators])

    def __repr__(self) -> str:
        return f"{self.wd.decode('ascii')} @ {self.yx}"

    def __str__(self) -> str:
        return self.wd.decode("ascii")

    @property
    def chars(self) -> Pipeline[char]:
        # building generators from existing data
        char_gen = iter(self.wd)
        # here we expect char to be only one cell to compute position... (as per definition ?)
        pos_gen = ((self.yx[0], self.yx[1] + i) for i, c in enumerate(self.wd))

        # passing next in generator as callable to get the next element
        return Pipeline(char.generate(pos_gen.__next__, char_gen.__next__, until=[]))


if __name__ == "__main__":
    import curses

    # computer user interface delegate to curses window
    stdscr = curses.initscr()

    # these requires initscr() to be called before
    # no immediate echo
    curses.noecho()
    # cbreak mode to not buffer keys
    curses.cbreak()

    # to allow scrolling on new line at end of main window
    stdscr.idlok(True)
    stdscr.scrollok(True)
    # TODO : this somehow breaks word replacing logic with position...
    #   but only when scrolling... TOFIX !

    charin = Pipeline(char.generate(
        call_position=stdscr.getyx,
        call_input=stdscr.getch,
        until=[
            4,  # EOT  via Ctrl-D
        ],
    ))

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

    wordin = Pipeline(word.generate(
        chi=charin,
        separators=[
            32,  # EOW  via space
            10,  # EOL  via Enter/Return
        ],
    ))

    @wordin
    def word_process(w: word) -> word:
        stdscr.move(*w.yx)
        stdscr.clrtobot()
        # currently just displaying the length.
        w.wd = f"{len(w.wd)} ".encode(
            "ascii"
        )  # reminder wd is bytes and we need to keep (or create!) separator
        stdscr.addstr(w.wd.decode("ascii"))
        return w

    # to loop through the iterator until the end
    print([w for w in wordin])

    # curses cleanup
    curses.nocbreak()
    curses.echo()

    # closing screen
    curses.endwin()
