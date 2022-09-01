import contextlib
import curses
import functools
from word import WordInput, word
from char import CharInput, char

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

    def __call__(self, output: int | str | char | word, clrtobot=True):
        if isinstance(output, word):
            self.stdscr.move(*output.yx)
            if clrtobot:
                self.stdscr.clrtobot()
            self.stdscr.addstr(output.wd)
        elif isinstance(output, char):
            self.stdscr.move(*output.yx)
            if clrtobot:
                self.stdscr.clrtobot()
            self.stdscr.addch(output.ch)
        # these seem to break semantics, as they depend on external state (cursor position)
        # elif isinstance(output, str):
        #     self.stdscr.addstr(output)
        # elif isinstance(output, int):
        #     self.stdscr.addch(output)
        else:
            raise NotImplementedError

    # as a property, caching seems the implicit semantic for the user
    # to avoid recreating the iterator from scratch
    # Also linking the lifetime of the input stream to the window seems sensible...
    @property
    @functools.lru_cache
    def chario(self) -> CharInput:
        return CharInput(self.stdscr.getyx, self.stdscr.getch, until=[EOT])

    @property
    @functools.lru_cache
    def wordio(self) -> WordInput:
        return WordInput(
            stdscr=self.stdscr,
            char_pipeline=self.chario,
            until=[
                32,  # EOW  via space
                10,  # EOL  via Enter/Return
            ],
        )

    # TODO : only one "input" function as decorator, inspecting argument type hint
    #  to determine which iterator element to pass in the function

    # TODO : line ? sentence as a set of words ??


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

    with Window() as wordwin:

        # COMMENT this to prevent char output while typing...
        @wordwin.chario
        def char_process(c: char) -> char:
            # output as implicit #TODO : refine these...
            wordwin(c)
            return c

        # declarative form for implicit process (functional - inside io iterator flow)
        @wordwin.wordio
        def word_process(w: word) -> word:
            # currently just displaying the length.
            w.wd = f"{len(w.wd)} ".encode(
                "ascii"
            )  # reminder wd is bytes and we need to keep (or create!) separator
            wordwin(w)  # simpler to address disply via window here instead of inside the WordInput class
            return w


        # imperative form for explicit process, (effects - outside of io flow)
        for w in wordwin.wordio:
            wordwin(w)

    # win is cleaned and reset when exiting the context
