import unittest

from ppl import Pipeline


class TestPPL(unittest.TestCase):

    def test_iterable(self):
        val_list = [1, 2, 3, 4, 5]
        ppl = Pipeline(iter(val_list))

        for v in val_list:
            assert v == next(ppl)

        ppl_bis = Pipeline(iter(val_list))
        try:
            c = 0
            while True:  # infinite loop. exception in generator will break out of it.
                assert next(ppl_bis) == val_list[c]
                c += 1
        except StopIteration:
            pass  # generator terminated

    def test_not_callable(self):
        val_list = [1, 2, 3, 4, 5]
        ppl = Pipeline(iter(val_list))

        with self.assertRaises(TypeError) as raised:
            ppl()
        assert raised.exception.args[0] == "'PPL' object is not callable"

    def test_as_context_manager(self):
        val_list = [1, 2, 3, 4, 5]
        ppl = Pipeline(iter(val_list))

        with ppl as ppl_ctx:
            # zip with val_list
            ppl_ctx.zip(val_list)
            # check for equality one to one
            ppl_ctx.starmap(lambda a, b: a == b)

        # for all elements
        assert all(ppl_ctx)


if __name__ == "__main__":
    unittest.main()
