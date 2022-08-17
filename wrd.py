from itertools import groupby
from typing import Callable, Iterator, List

from chr import CharArea, CharInput
from ppl import Pipeline


class WordInput(Pipeline):

    # TODO : add methods to manipulate output on screen, usable on generator pipeline/stream
    #        -> WordIO

    # Note:
    # - Char input, is a generator of (one) byte = int
    # - Word input is a generator of bytes
    # - line input is a generator of bytes (as lines), and is also a stream (following stream protocol).

    def __init__(self, char_pipeline: Pipeline[int], until: List[int]):
        self.until = until

        # we want a new pipeline, without modifying the existing char_pipeline
        word_pipeline = (list(ch) for k, ch in groupby(
            char_pipeline,
            key=lambda x: until.index(x) if x in until else -1)
        )

        super(WordInput, self).__init__(word_pipeline)


class WordArea:  # TODO  :extract a common Area concept, that works for words and lines

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

    def __call__(self, w: bytes) -> bytes:
        """ word input behavior in the area """
        # TODO: word processing upon ending when typing separator
        # currently just displaying the length.
        self.stdscr.addstr(str(len(w)))
        return str(len(w)).encode("ascii")


if __name__ == "__main__":
    import curses

    # computer user interface delegate to curses window
    stdscr = curses.initscr()

    # these requires initscr() to be called before
    # no immediate echo
    curses.noecho()
    # cbreak mode to not buffer keys
    curses.cbreak()

    charin = CharInput.from_callable(call_input=stdscr.getch, until=[
        4,  # EOT  via Ctrl-D
    ])
    wordin = WordInput(char_pipeline=charin, until=[
        32,  # EOW  via space
        10,  # EOL  via Enter/Return
    ])

    with WordArea(stdscr) as area:
        # This part seems necessary, as we want to output all chars while typing a word
        with CharArea(stdscr) as char_area:
            charin.map(char_area)

        wordin.map(area)

    # to loop through the iterator until the end
    print([w for w in wordin])

    # curses cleanup
    curses.nocbreak()
    curses.echo()

    # closing screen
    curses.endwin()
