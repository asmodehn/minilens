import io
import unittest

import forthvm


class WordTest(unittest.TestCase):

    @staticmethod
    def implementation(*param):
        return param

    def test_imm_word(self):

        w = forthvm.Primary("testword", WordTest.implementation, imm=True)

        assert w.name == "testword"
        assert w.code == WordTest.implementation
        assert w.imm

        assert isinstance(w, forthvm.Word)
        assert repr(w) == "testword"
        # assert w.get(0) == WordTest.implementation

    def test_noimm_word(self):
        w = forthvm.Primary("testword", WordTest.implementation, imm=False)

        assert w.name == "testword"
        assert w.code == WordTest.implementation
        assert not w.imm

        assert isinstance(w, forthvm.Word)
        assert repr(w) == "testword"
        # assert w.get(0) == WordTest.implementation

    def test_list_word(self):
        w = forthvm.Secondary("testword", [
                forthvm.Primary("this", lambda x: x),
                forthvm.Primary("is", lambda x:x),
                forthvm.Primary("a", lambda x:x),
                forthvm.Primary("secondary", lambda x:x),
                forthvm.Primary("word", lambda x:x)
            ], imm=False)

        assert w.name == "testword"
        assert w[0].name == "this"
        assert w[1].name == "is"
        assert w[2].name == "a"
        assert w[3].name == "secondary"
        assert w[4].name == "word"
        assert not w.imm

        assert isinstance(w, forthvm.Word)
        assert repr(w) == "testword"
        for i, sw in enumerate(w):
            # get grab one WORD only in the list
            assert w[i] == sw


class Word_DecoratorTest(unittest.TestCase):

    @staticmethod
    def implementation(*param):
        return param

    def test_word_code(self):
        w = forthvm.word_("testword", imm=True)(Word_DecoratorTest.implementation)

        assert w.name == "testword"
        assert w.code == Word_DecoratorTest.implementation
        assert w.imm

    def test_word_name(self):
        w = forthvm.word_("testword", imm=True)(Word_DecoratorTest.implementation)

        assert w.name == "testword"
        assert w.code == Word_DecoratorTest.implementation
        assert w.imm

    def test_word_noimm(self):
        w = forthvm.word_("testword")(Word_DecoratorTest.implementation)

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
        assert f.stack == ["c", "d"]
        forthvm.word.code(f)
        assert f.stack == ["c", "d", "e"]
        forthvm.word.code(f)
        assert f.stack == ["c", "d", "e", "f"]


class InnerTest(unittest.TestCase):

    def test_primary_loop(self):

        # check the order of the calls leveraging lexical scope (CAREFUL !)
        state = []

        W1 = forthvm.Primary("one", lambda: state.append(1))
        W2 = forthvm.Primary("two", lambda: state.append(2))
        W3 = forthvm.Primary("three", lambda: state.append(3))

        forthvm.inner(iter([W1, W2, W3]))

        assert state == [1,2,3]



if __name__ == "__main__":
    unittest.main(verbosity=2)
