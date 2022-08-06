import curses
import unittest
from cui import Word, chars


def test_chars_gen():
    test_value = b"testing"

    # generate test input
    def test_input():
        yield from test_value

    gen = test_input()

    # iterative input function
    def input_iter():
        return next(gen)

    gen_word_input = chars(input_iter, limiters=[ord(b" ")])
    for i, c in enumerate(gen_word_input):
        assert c == test_value[i]


def test_chars_gen_limiter():
    test_value = b"testing multiple word"

    # generate test input
    def test_input():
        yield from test_value

    gen = test_input()

    # iterative input function
    def input_iter():
        return next(gen)

    gen_word_input = chars(input_iter, limiters=[ord(b" ")])
    for i, c in enumerate(gen_word_input):
        assert c == test_value[i]

    # assert only one word has been acknowledged
    #  and limiter is outputted
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

        def input_gen():
            yield from b"testing something\n"

        mock_input = input_gen()

        w(input=mock_input)

        # Note: no word delimiter in word buffer
        assert w.buffer == bytearray(b"testing")

        w2 = Word(limiters=[ord(b"\n")])
        # next word from same generator
        w2(input=mock_input)

        # Note: other delimiter in word buffer for possible input for external process
        assert w.buffer == bytearray(b"testing\n")


if __name__ == "__main__":
    unittest.main()




