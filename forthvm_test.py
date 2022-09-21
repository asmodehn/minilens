import io
import unittest

import forthvm
from forthvm import Word, word_


class WordTest(unittest.TestCase):

    @staticmethod
    def implementation(*param):
        return param

    def test_imm_word(self):

        w = Word("testword", WordTest.implementation, imm=True)

        assert w.name == "testword"
        assert w.code == WordTest.implementation
        assert w.imm

        assert w.is_instruction()
        assert repr(w) == "testword"
        # assert w.get(0) == WordTest.implementation

    def test_noimm_word(self):
        w = Word("testword", WordTest.implementation, imm=False)

        assert w.name == "testword"
        assert w.code == WordTest.implementation
        assert not w.imm

        assert w.is_instruction()
        assert repr(w) == "testword"
        # assert w.get(0) == WordTest.implementation

    @unittest.expectedFailure
    def test_string_word(self):
        w = Word("testword", "this is a composed word", imm=False)

        assert w.name == "testword"
        assert w.code == "this is a composed word"
        assert not w.imm

        assert not w.is_instruction()
        assert repr(w) == "testword"
        for i, c in enumerate(w.code):
            # get grab one CHAR only in a string
            assert w.get(i) == c
            # TODO is there any actual use for this case ???

    def test_list_word(self):
        w = Word("testword", ["this", "is", "a", "composed", "word"], imm=False)

        assert w.name == "testword"
        assert w.code == ["this", "is", "a", "composed", "word"]
        assert not w.imm

        assert not w.is_instruction()
        assert repr(w) == "testword"
        for i, sw in enumerate(w.code):
            # get grab one WORD only in the list
            assert w.get(i) == sw


class Word_DecoratorTest(unittest.TestCase):

    @staticmethod
    def implementation(*param):
        return param

    def test_word_code(self):
        w = word_("testword", imm=True)(Word_DecoratorTest.implementation)

        assert w.name == "testword"
        assert w.code == Word_DecoratorTest.implementation
        assert w.imm

    def test_word_name(self):
        w = word_("testword", imm=True)(Word_DecoratorTest.implementation)

        assert w.name == "testword"
        assert w.code == Word_DecoratorTest.implementation
        assert w.imm

    def test_word_noimm(self):
        w = word_("testword")(Word_DecoratorTest.implementation)

        assert w.name == "testword"
        assert w.code == Word_DecoratorTest.implementation
        assert not w.imm


class Word_wordTest(unittest.TestCase):

    @staticmethod
    def forth_mock(fin=""):

        class ForthMock:
            def __init__(self, fin):
                self.fin = io.StringIO(fin)
                self.stack = []

            def push(self, el):
                self.stack.append(el)

        return ForthMock(fin=fin)

    def test_empty_str_word(self):
        f = self.forth_mock(fin="")
        forthvm.word.code(f)
        assert f.stack == [""]  # TODO : fix it ???

    def test_onechar_str_word(self):
        f = self.forth_mock(fin="c")
        forthvm.word.code(f)
        assert f.stack == ["c"]

    def test_leadingspace_str_word(self):
        f = self.forth_mock(fin=" c")
        forthvm.word.code(f)
        assert f.stack == ["c"]

    def test_multi_onechar_str_word(self):
        f = self.forth_mock(fin="c d")
        forthvm.word.code(f)
        assert f.stack == ["c"]
        forthvm.word.code(f)
        assert f.stack == ["c","d"]

    def test_multi_space_str_word(self):
        f =self.forth_mock(fin="c d\te\nf\fg")
        forthvm.word.code(f)
        assert f.stack == ["c"]
        forthvm.word.code(f)
        assert f.stack == ["c","d"]
        forthvm.word.code(f)
        assert f.stack == ["c","d","e"]
        forthvm.word.code(f)
        assert f.stack == ["c","d","e","f"]


if __name__ == "__main__":
    unittest.main(verbosity=2)
