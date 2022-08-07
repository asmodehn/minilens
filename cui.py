from __future__ import annotations
import contextlib
import curses
from typing import Any, Callable, ClassVar, Generator, List, MutableSequence, Optional

"""
Structuring screen as an interface for simpler manipulation from code
Here we attempt to follow the structure of human produced texts where suitable and feasible...
"""


def chars(input: Callable[[], int], until: List[int]):
    try:
        while (ch := input()) not in until:
            yield ch
        yield ch  # last yield to return limiter and terminate generator
    except StopIteration as si:
        return  # return if (potentially) underlying generator terminates


# TODO : same but lazy ? iterator ?
# def word_transform(w: List[Char]) -> List[Char]:
#     return [Char(c) for c in str(len(w))]


@contextlib.contextmanager
def word_area(stdscr):
        r, c = stdscr.getyx()
        # self.normalizer = normalizer
        yield

        # move to the beginning of the word
        stdscr.move(r, c)

        # erase until the end of line (input limit)
        stdscr.clrtoeol()

        # screen is now clean again for next word


class Word:

    EOW: ClassVar[int] = ord(b" ")

    def __init__(self, limiters, content: bytes | bytearray = b"") -> None:
        self.buffer: bytearray = bytearray(content)
        # Note: a higher level limiter implies this limiter
        self.limiters = limiters + [self.EOW]

    def __eq__(self, other: Word | str | bytes):
        if isinstance(other, Word):
            return self.buffer == other.buffer
        # otherwise, we use self conversions to check for equality in other's type
        elif isinstance(other, str):
            return str(self) == str
        elif isinstance(other, bytes):
            return bytes(self.buffer) == other
        else:
            raise NotImplementedError

    def __iter__(self) -> Generator[int, None, None]:
        """ input word and copy into screen.
        implicit iterator, where the cursor is always on the next (upcoming) input
        """

        yield from self.buffer

    # TODO : async
    def __call__(self, input: Callable[[], int]) -> Word:
        """ async generator for input : one char at a time, asynchronously."""

        while len(self.buffer) == 0:  # preventing empty (meaningless) word
            for ch in chars(input, until=self.limiters):
                if ch == self.EOW:
                    break  # end of word input
                # last char is not appended to buffer
                # unless it is not Word limiter
                self.buffer.append(ch)

        return self

    def __str__(self) -> str:
        return self.buffer.decode("ascii")

#
# @contextlib.contextmanager
# def line_area(stdscr):
#     r, c = stdscr.getyx()
#     # self.normalizer = normalizer
#     yield
#
#     # move to the beginning of the word
#     stdscr.move(r, c)
#
#     # erase until the end of line (input limit)
#     stdscr.clrtoeol()
#
#     # screen is now clean again for next word
#
#
# class Line:
#
#     EOL: ClassVar[int] = 10  # ASCII: Line Feed
#
#     def __init__(self, limiters: List[int]):
#         self.buffer: List[Word] = []
#         # Note: a higher level limiter implies this limiter
#         self.limiters = limiters + [self.EOL]
#
#     async def __call__(self, stdscr) -> Word | Char:
#         ch = Line.EOL
#         while ch == Line.EOL:
#             w = self.word()
#             async for ch in w(stdscr):  # waiting for word input
#                 # specific behavior from line with char input.
#                 if ch in self.limiters:
#                     break  # end of line (or more)
#             yield w  # yield last word
#
#         # we reach this code when ch is in self.limiter but ch != Line.EOL
#         yield ch  # yield last character to forward delimiter
#
#     def __iter__(self):
#         """ word input iterator"""
#
#         # iterate through existing buffer
#         yield from self.buffer
#
#         with line_area(self.stdscr):
#             # dummy initial value
#             ch = ord(r'a')  # holding last character after a word
#
#             # iterate on words until we terminate the line (or more)
#             while ch not in self.limiters:
#
#                 # iterate and expect next word input for this line
#                 w = self.word()
#                 for ch in w:
#                     # char input process from line perspective
#                     pass  # noop
#                 # loop finishes with ch == EOW
#
#                 yield w
#
#         # End of line (or more) -> not our concern any longer
#
#     def word(self):
#         return Word(stdscr=self.stdscr, limiters=self.limiters)


#
# class Lines:
#
#     EOL: ClassVar[int] = 10  # ASCII: Line Feed
#
#     def __init__(self, stdscr, limiters: List[int]):
#         self.stdscr = stdscr
#         # Note: a higher level limiter implies this limiter
#         self.limiters = limiters + [self.EOL]
#
#     def __call__(self, line: bytes) -> None:
#         self.stdscr.addstr(line.decode("ascii"))
#
#     def __iter__(self):
#         """infinite line input iterator"""
#         return self
#
#     def __next__(self):
#         """ grab next line from input as bytes.
#         iterator on words will stop when a line limiter is detected
#         """
#         self.line_buffer = bytearray()
#         with line_area(self.stdscr):
#
#             count = 0  # custom process TODO
#             for w in self.words:
#                 w.append(Words.EOW)
#                 self.line_buffer.extend(w)
#                 # cutoms process TODO
#                 count += 1
#                 self.stdscr.addstr(str(count) + chr(Words.EOW))
#
#             return self.line_buffer
#
#         # line area is cleaned, up to caller to fill it up again.
#
#     def __exit__(self, exc_type, exc_val, exc_tb):
#         pass
#         # TODO : evaluation
#
#     @property
#     def words(self):
#         return Words(stdscr=self.stdscr, limiters=self.limiters)


class CursesUI:

    EOT: ClassVar[int] = 4  # ASCII: EOT

    def __init__(self):
        self.stdscr = None
        self.limiters = [self.EOT]

    def __enter__(self):
        # computer user interface delegate to curses window
        self.stdscr = curses.initscr()

        # these requires initscr() to be called before
        # no immediate echo
        curses.noecho()
        # cbreak mode to not buffer keys
        curses.cbreak()

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # curses cleanup
        curses.nocbreak()
        curses.echo()

        # closing screen
        curses.endwin()

    # @property
    # def lines(self):
    #     return Lines(stdscr=self.stdscr, limiters=self.limiters)

    @property
    def word(self):
        return Word(limiters=self.limiters)




    # semantics: transfer interface <-> compute
    # def __call__(self) -> None:


        # s = bytearray()


        # loop on input to grab the word in temporary memory (word_scr)
        # also does validation char by char
        # word(self.stdscr)

        # exiting the WordScr context normalizes the word





            # if control character, we compute in TUI, else send to memory

            # if c == 32:  # ASCII: space
            #     # trigger normalization
            #     out = self.word_compute()
            #     assert len(out) == 0  # never any output in normalization
            #
            #
            #
            # elif c == 10:  # ASCII: Line Feed
            #     # # trigger evaluation
            #     # out = self.compute() + c
            #     #
            #     # # move to the beginning of the line
            #     # self.stdscr.move(line_begin, 0)
            #     #
            #     # # erase the previous line
            #     # self.stdscr.clrtoeol()
            #     #
            #     # # replace it with the new stack content
            #     # # Note: this is an iterated addch...
            #     # self.stdscr.addstr(self.memory.storage.decode("ascii"))  # print the current stack
            #     # # => ignored keys will have no immediate output
            #     # # => this is a (dangerous, impractical) char by char input, requiring a step by step reduction.
            #     #
            #     # line_begin, word_begin = self.stdscr.getyx()
            #     pass  # TODO
            #
            # else:  # otherwise append to memory and keep looping
            #     self.word_compute.memory.append(c)
            #     self.stdscr.addch(c)


if __name__ == "__main__":

    # basic word + line counter as a usage example
    memory = bytearray()

    wcount = 0



    with CursesUI() as cui:

        def input_refl():  # immediately output inputted char
            ch = cui.stdscr.getch()
            cui.stdscr.addch(ch)
            return ch

        while True:
            w = cui.word(input_refl)
            # print("\n" + str(w))
        # do global stuff

