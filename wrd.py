from __future__ import annotations
import contextlib
import operator
from itertools import cycle, groupby, pairwise
from typing import Callable, Generator, Iterator, List

from chr import CharInput, char
from ppl import Pipeline


class word:

    __slots__ = ("yx", 'wd')

    @classmethod
    def generate(cls, stdscr, chi: Iterator[char], separators: List[int]) -> Generator[word, None, None]:
        for k, gc in groupby(chi, key=lambda c: c.ch in separators):
            if not k:  # if this char is not a separator
                yield word(stdscr=stdscr, chi=gc, separators=separators)

    def __init__(self, stdscr, chi: Iterator[char], separators: List[int]) -> None:
        # initialize word on iterator to get the position of the beginning of the word
        first_char_pos = stdscr.getyx()
        # IMPORTANT: remove the size of the first character !!!
        self.yx = first_char_pos[0], first_char_pos[1] -1
        # accumulate chars from iterator into a word (omitting separators)
        self.wd = bytes(ch.ch for ch in chi if ch.ch not in separators)

    def __repr__(self) -> str:
        return self.wd.decode("ascii")


class WordInput(Pipeline):

    # TODO : add methods to manipulate output on screen, usable on generator pipeline/stream
    #        -> WordIO

    # Note:
    # - Char input, is a generator of (one) byte = int
    # - Word input is a generator of bytes
    # - line input is a generator of bytes (as lines), and is also a stream (following stream protocol).

    def count(self, last, current):
        if current in self.until and last != current:
            self.windex = self.windex + 1
        return self.windex

    def __init__(self, char_pipeline: Pipeline[char], until: List[int]):
        self.until = until
        self.windex = 0

        # we want a new pipeline, without modifying the existing char_pipeline
        # word_pipeline = (list(ch) if ch not in self.until else []
        #                  for k, ch in groupby(
        #                     pairwise(char_pipeline),
        #                     key=lambda pchr: self.count(*pchr)
        #                 ))
        word_pipeline = word.generate(stdscr=stdscr, chi=char_pipeline, separators=until)
        super(WordInput, self).__init__(word_pipeline)

    def __call__(self, fun: Callable[[word], word]):
        # applying the function to this iterator
        # effectively making this a decorator (?)

        def fun_wrapper(w: word) -> word:

            # move cursor to beginning of word and clean
            stdscr.move(*w.yx)
            stdscr.clrtoeol()

            processed = fun(w)

            # replace with processed
            stdscr.addstr(processed.wd.decode("ascii"))

            return processed

        self.map(fun_wrapper)


@contextlib.contextmanager
def area(stdscr, finalize: Callable[[bytes], bytes]):
    y, x = stdscr.getyx()
    yield y, x
    # move to the beginning of the word
    stdscr.move(y, x)
    # erase until the end of line (input limit)
    stdscr.clrtoeol()
    # screen is now clean again for further output



if __name__ == "__main__":
    import curses

    # computer user interface delegate to curses window
    stdscr = curses.initscr()

    # these requires initscr() to be called before
    # no immediate echo
    curses.noecho()
    # cbreak mode to not buffer keys
    curses.cbreak()

    charin = CharInput.from_callable(stdscr=stdscr,call_input=stdscr.getch, until=[
        4,  # EOT  via Ctrl-D
        10,  # EOL  via Enter/Return
    ])

    @charin
    def char_process(ch: char) -> char:
        # TODO: unicode / complex char / multipress input ???
        if ch.ch in [ord(b"\b"), 127, curses.KEY_BACKSPACE]:  # various possible ascii codes for a delete backspace
            stdscr.delch(ch.yx[0], ch.yx[1] - 1)
        else:
            stdscr.addch(ch.ch)
        return ch


    wordin = WordInput(char_pipeline=charin, until=[
        32,  # EOW  via space
        10,  # EOL  via Enter/Return
    ])

    @wordin
    def word_process(w: word) -> word:
        # TODO: word processing upon ending when typing separator
        # currently just displaying the length.
        w.wd = f"{len(w.wd)} ".encode("ascii")  # reminder wd is bytes and we need to keep separator
        return w

    #
    # with WordArea(stdscr) as area:
    #     # This part seems necessary, as we want to output all chars while typing a word
    #     with CharArea(stdscr) as char_area:
    #         charin(char_area)
    #
    #     wordin(area)

    # to loop through the iterator until the end
    print([w for w in wordin])

    # curses cleanup
    curses.nocbreak()
    curses.echo()

    # closing screen
    curses.endwin()
