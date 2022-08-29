import curses
import unittest
from typing import Callable, Generator

from cui import Word, chars


# generate test input
def generator_from_bytes(input: bytes) -> Generator[int, None, None]:
    yield from input


def callable_from_bytes(input: bytes) -> Callable[[], int]:
    gen = generator_from_bytes(input)

    def it() -> int:
        nonlocal gen
        return next(gen)

    return it

# TODO : automatically test curses with interactive input


def test_chars_gen_initial():
    # no char usecase
    test_value = b""
    it = callable_from_bytes(input=test_value)

    gen_word_input = chars(it, until=[ord(b" ")])
    for c in gen_word_input:
        # we never enter this loop, otherwise it is a failure
        assert False

    # one char usecase
    test_value = b"a"
    it = callable_from_bytes(input=test_value)

    gen_word_input = chars(it, until=[ord(b" ")])
    for c in gen_word_input:
        # we enter this loop once for the limiter char
        assert c == ord(b"a")

    # one special char usecase
    test_value = b" "
    it = callable_from_bytes(input=test_value)

    gen_word_input = chars(it, until=[ord(b" ")])
    for c in gen_word_input:
        # we enter this loop once for the limiter char
        assert c == ord(b" ")


def test_chars_gen():
    test_value = b"testing"
    it = callable_from_bytes(test_value)

    # Note: terminating the generator if underlying input terminates is implicit
    gen_word_input = chars(it, until=[ord(b" ")])
    for i, c in enumerate(gen_word_input):
        assert c == test_value[i]


def test_chars_gen_until():
    test_value = b"testing multiple words"
    it = callable_from_bytes(test_value)

    gen_word_input = chars(it, until=[ord(b" ")])
    for i, c in enumerate(gen_word_input):
        assert c == test_value[i]

    # assert only one word has been acknowledged
    #  and limiter is in output
    assert i == 7
    assert c == ord(b" ")


class WordTest(unittest.TestCase):

    def test_01_eow(self):
        assert Word.EOW == ord(b" ")

    def test_02_init(self):
        w = Word(limiters=[ord(b"\n")])
        assert w.limiters == [ord(b"\n"), w.EOW]

    def test_03_eq(self):
        w1 = Word(limiters=[ord(b"\n")], content=b"testing")
        w2 = Word(limiters=[ord(b"\n")], content=b"testing")

        assert w1 == w2

    def test_04_iter(self):
        w = Word(limiters=[ord(b"\n")], content=b"testing")
        acc = bytearray()
        for c in w:
            acc.append(c)
        assert acc == w.buffer
        wbis = Word(limiters=[ord(b"\n")], content=acc)

        assert w == wbis

    def test_05_call(self):
        w = Word(limiters=[ord(b"\n")])

        test_value = b"testing something\n"
        it = callable_from_bytes(test_value)

        w(input=it)

        # Note: no word delimiter in word buffer
        assert w.buffer == bytearray(b"testing")

        w2 = Word(limiters=[ord(b"\n")])
        # next word from same generator
        w2(input=it)

        # Note: other delimiter in word buffer for possible input for external process
        assert w2.buffer == bytearray(b"something\n")

    def test_06_call_double_eow(self):
        w = Word(limiters=[ord(b"\n")])

        test_value = b"testing  another\n"
        it = callable_from_bytes(test_value)

        w(input=it)

        # Note: no word delimiter in word buffer
        assert w.buffer == bytearray(b"testing")

        w2 = Word(limiters=[ord(b"\n")])
        # next word from same generator
        w2(input=it)

        # Note: other delimiter in word buffer for possible input for external process
        assert w2.buffer == bytearray(b"another\n")

    def test_07_str(self):
        w = Word(limiters=[ord(b"\n")])

        test_value = b"testing output\n"
        it = callable_from_bytes(test_value)

        w(input=it)

        # Note: no word delimiter in output
        assert str(w) == "testing"

        w2 = Word(limiters=[ord(b"\n")])
        # next word from same generator
        w2(input=it)

        # Note: other delimiter in word buffer for possible input for external process
        assert str(w2) == "output\n"

    def test_08_len(self):
        w = Word(limiters=[ord(b"\n")])

        test_value = b"testing output\n"
        it = callable_from_bytes(test_value)

        w(input=it)

        # Note: no word delimiter in output
        assert str(w) == "testing"

        w2 = Word(limiters=[ord(b"\n")])
        # next word from same generator
        w2(input=it)

        # Note: other delimiter in word buffer for possible input for external process
        assert str(w2) == "output\n"

# class LineTest(unittest.TestCase):
#     # TODO


if __name__ == "__main__":
    unittest.main()
