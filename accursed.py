import contextlib
import curses

EOT: int = 4  # ASCII: EOT


@contextlib.contextmanager
def window():

    # computer user interface delegate to curses window
    stdscr = curses.initscr()

    # these requires initscr() to be called before
    # no immediate echo
    curses.noecho()
    # cbreak mode to not buffer keys
    curses.cbreak()

    yield stdscr

    # curses cleanup
    curses.nocbreak()
    curses.echo()

    # closing screen
    curses.endwin()


if __name__ == "__main__":

    with window() as stdscr:

        # Optional: allow scrolling on new line at end of main window
        stdscr.idlok(True)
        stdscr.scrollok(True)

        while (ch := stdscr.getch()) not in [EOT]:
            stdscr.addch(ch)

