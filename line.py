from __future__ import annotations

from char import CharInput, char
from pipeline import Pipeline

"""

Sentences input as list of bytes iterator (possibly async ?)
# TODO : stream protocol(like reading file, line by line)
Also as a Pipeline to modify itself with operators on iterables

 TODO : difference between sentence and line ?? 
       - what about wordwrap ?? 
       - period to end commands (cf. Joy) ??
       - Maybe two different iterators on top of word iterator ?

"""
from itertools import groupby
from typing import Callable, Generator, Iterator, List

from word import WordInput, word


class line:

    __slots__ = ("stdscr", "yx", "ln")

    @classmethod
    def generate(
        cls, stdscr, wdi: Iterator[char], separators: List[int]
    ) -> Generator[line, None, None]:
        # we want a new pipeline, without modifying the existing char_pipeline
        for k, gc in groupby(wdi, key=lambda c: c.ch in separators):
            if not k:  # if this word is not a separator
                yield line(stdscr=stdscr, chi=gc, separators=separators)

    def __init__(self, stdscr, chi: Iterator[char], separators: List[int]) -> None:
        self.stdscr = stdscr
        # initialize word on iterator to get the position of the beginning of the word
        first_char_pos = self.stdscr.getyx()
        # IMPORTANT: remove the size of the first char !!!
        self.yx = first_char_pos[0], first_char_pos[1] - 1
        # accumulate chars from iterator into a word (omitting separators)
        self.ln = bytes(ch.ch for ch in chi if ch.ch not in separators)

    def __repr__(self) -> str:
        return f"{self.ln.decode('ascii')} @ {self.yx}"

    def __str__(self) -> str:
        return self.ln.decode("ascii")

    @property
    def chars(self) -> Generator[char]:
        # building generators from existing data
        char_gen = iter(self.ln)
        # here we expect char to be only one cell to compute position... (as per definition ?)
        pos_gen = ((self.yx[0], self.yx[1] + i) for i, c in enumerate(self.ln))

        # passing next in generator as callable to get the next element
        return char.generate(pos_gen.__next__, char_gen.__next__, until=[])

    @property
    def words(self) -> Generator[word]:
        return word.generate(stdscr=self.stdscr,
                             chi=self.chars,
                             separators=[32])


class LineInput(Pipeline):

    # Note:
    # - Char input, is a generator of (one) byte = int
    # - Word input is a generator of bytes
    # - line input is a generator of bytes (as lines), and is also a stream (following stream protocol).

    def __init__(self, stdscr, char_pipeline: Pipeline[char], until: List[int]):
        self.until = until
        self.windex = 0
        self.stdscr = stdscr

        line_pipeline = line.generate(
            stdscr=stdscr, wdi=char_pipeline, separators=until
        )
        super(LineInput, self).__init__(line_pipeline)

    def __call__(self, fun: Callable[[line], line]):
        # applying the function to this iterator
        # effectively making this a decorator (?)

        def fun_wrapper(l: line) -> line:

            # move cursor to beginning of word and clean
            self.stdscr.move(*l.yx)
            self.stdscr.clrtoeol()

            processed = fun(l)

            # replace with processed
            self.stdscr.addstr(str(processed))

            return processed

        self.map(fun_wrapper)


if __name__ == "__main__":
    import curses

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

    wordin = WordInput(
        stdscr=stdscr,
        char_pipeline=charin,
        until=[
            32,  # EOW  via space
            # 10,  # EOL  via Enter/Return ???
        ],
    )

    @wordin
    def word_process(w: word) -> word:
        # TODO: word processing upon ending when typing separator
        # currently just displaying the length.
        w.wd = f"{len(w.wd)} ".encode(
            "ascii"
        )  # reminder wd is bytes and we need to keep separator
        return w


    linein = LineInput(
        stdscr=stdscr,
        char_pipeline=charin,
        until=[
            10,  # EOL  via Enter/Return ???
        ]
    )


    @linein
    def line_process(l: line) -> line:
        # TODO: word processing upon ending when typing separator
        # currently just displaying the length.
        l.ln = f"{len(list(l.words))} words".encode(
            "ascii"
        )  # reminder wd is bytes and we need to keep separator
        return l


    # to loop through the iterator until the end
    print([l for l in linein])

    # curses cleanup
    curses.nocbreak()
    curses.echo()

    # closing screen
    curses.endwin()
