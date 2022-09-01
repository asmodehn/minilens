import contextlib
import curses
import functools

from line import line
from pipeline import Pipeline
from word import word
from char import char

EOT: int = 4  # ASCII: EOT


class Window:

    def __init__(self, scrolling=True):

        # computer user interface delegate to curses window
        self.stdscr = curses.initscr()
        self.scrolling = scrolling

    def __enter__(self):
        # these requires initscr() to be called before
        # no immediate echo
        curses.noecho()
        # cbreak mode to not buffer keys
        curses.cbreak()

        # Optional: allow scrolling on new line at end of main window
        self.stdscr.idlok(self.scrolling)
        self.stdscr.scrollok(self.scrolling)

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):

        # curses cleanup
        curses.nocbreak()
        curses.echo()

        # closing screen
        curses.endwin()

    def __call__(self, output: char | word | line, clrtobot=True):
        if isinstance(output, line):
            self.stdscr.move(*output.yx)
            if clrtobot:
                self.stdscr.clrtobot()
            self.stdscr.addstr(output.ln)
        elif isinstance(output, word):
            self.stdscr.move(*output.yx)
            if clrtobot:
                self.stdscr.clrtobot()
            self.stdscr.addstr(output.wd)
        elif isinstance(output, char):
            self.stdscr.move(*output.yx)
            if clrtobot:
                self.stdscr.clrtobot()
            self.stdscr.addch(output.ch)
        else:
            raise NotImplementedError

    # as a property, caching seems the implicit semantic for the user
    # to avoid recreating the iterator from scratch
    # Also linking the lifetime of the input stream to the window seems sensible...
    @property
    @functools.lru_cache
    def chario(self) -> Pipeline[char]:
        return Pipeline(char.generate(
            call_position=self.stdscr.getyx,
            call_input=self.stdscr.getch,
            until=[EOT]
        ))

    @property
    @functools.lru_cache
    def wordio(self) -> Pipeline[word]:
        return Pipeline(word.generate(
            chi=self.chario,
            separators=[
                32,  # EOW  via space
            ],
        ))

    # TODO : line as set of char ? or sentence as a set of words ??
    @property
    @functools.lru_cache
    def lineio(self) -> Pipeline[line]:
        return Pipeline(line.generate(
            chi=self.chario,
            separators=[
                10,  # EOL  via Enter/Return
            ]
        ))

    # TODO : only one "input" function as decorator, inspecting argument type hint
    #  to determine which iterator element to pass in the function


if __name__ == "__main__":

    # with Window() as win:
    #
    #     # declarative form for implicit process (functional - inside io iterator flow)
    #     @win.chario
    #     def process(c: char):
    #         c.ch += 1  # next char in encoding
    #         c.yx = (c.yx[0], c.yx[1] + 1)  # one char cell more on the right
    #         return c
    #
    #     # imperative form for explicit process, (effects - outside of io flow)
    #     for c in win.chario:
    #         win(c)

    # win is cleaned and reset when exiting the context
    # TODO : window cleanup is not working
    #  -> only one of both example can work as a time.
    #   => FIX IT

    with Window() as win:

        # COMMENT this to prevent char output while typing...
        @win.chario
        def char_process(c: char) -> char:
            # output as implicit #TODO : refine these...
            win(c)
            return c

        # declarative form for implicit process (functional - inside io iterator flow)
        @win.wordio
        def word_process(w: word) -> word:
            # currently just displaying the length.
            w.wd = f"{len(w.wd)} ".encode(
                "ascii"
            )  # reminder wd is bytes and we need to keep (or create!) separator
            win(w)  # simpler to address disply via window here instead of inside the WordInput class
            return w


        @win.lineio
        def line_process(l: line) -> line:
            # move cursor to beginning of word and clean
            # TODO: word processing upon ending when typing separator
            # currently just displaying the length.
            l.ln = f"{len(l.ln)} chars\n".encode(  # TODO : words for testing
                "ascii"
            )  # reminder wd is bytes and we need to keep separator
            win(l)
            return l

        # TODO : because of word or line using different iterators we have to choose our pipeline...
        #   how about combining them ???
        # imperative form for explicit process, (effects - outside of io flow)
        for l in win.lineio:
            win(l)

    # win is cleaned and reset when exiting the context
