import unittest
from itertools import tee
from unittest import TestCase

from char import char


class CharTest(TestCase):

    def test_init(self):

        c = char(ord(b"a"), (2,3))
        assert c.yx == (2,3)
        assert c.ch == ord(b"a")

    def test_repr(self):  # TODO : property testing
        c = char(ord(b"a"), (2,3))
        assert repr(c) == "a @ (2, 3)", repr(c)

    def test_str(self):
        c = char(ord(b"a"),(2,3))
        assert str(c) == "a"

    def test_generate(self):
        input_seq = iter(b"abc\x04")
        pos_seq = iter([(1, 2), (1, 3), (1, 4)])
        cgen = char.generate(call_position=lambda: next(pos_seq),
                             call_input=lambda: next(input_seq),
                             until=[4]
                             )

        cgen, genout = tee(cgen)
        # using repr to validate the whole char with positions
        assert [repr(c) for c in cgen] == [
            "a @ (1, 2)",
            "b @ (1, 3)",
            "c @ (1, 4)",
            # Note limiter is not in generated values
        ], list(genout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
