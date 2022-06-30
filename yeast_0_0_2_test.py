from typing import Type

import pytest
import yeast_0_0_2


@pytest.mark.parametrize("result, ch_input, next_result_or_except", [
    (b'', ord(b'a'), b'a'),
    (b'', ord(b'*'), b'*'),
    (b'', ord(b'`'), IndexError),  # Error: this tick cannot be used !
    (b'x', ord(b'a'), b'xa'),
    (b'x', ord(b'*'), b'x*'),
    (b'x', ord(b'`'), b''),  # backtick is used
    # backtick should *never* be in result (since it is supposed to have been applied).
    # but if it ever is, it is automatically and cleanly dropped, for safety:
    (b'`', ord(b'a'), b'a'),
    (b'`', ord(b'*'), b'*'),
    (b'`', ord(b'`'), b''),
])
def test_live_char_eval(result: bytes, ch_input: int, next_result_or_except: bytes | Type[Exception]):
    res_stack = bytearray(result)

    if isinstance(next_result_or_except, type):
        if not issubclass(next_result_or_except, Exception):
            raise NotImplementedError
        with pytest.raises(next_result_or_except):
            yeast_0_0_2.live_char_eval(ch_input, res_stack)
    else:
        yeast_0_0_2.live_char_eval(ch_input, res_stack)
        assert res_stack == bytearray(next_result_or_except)


@pytest.mark.parametrize("b_input, b_expected", [
    (b'abc', b'abc'),
    (b'`a', IndexError),
    (b'b`a', b'a'),
    (b'a`b`', b''),
    (b'ab``', b''),
    (b'ab`', b'a'),
    (b'```', IndexError),
])
def test_live_line_eval(b_input, b_expected):

    if isinstance(b_expected, type):
        if not issubclass(b_expected, Exception):
            raise NotImplementedError
        with pytest.raises(b_expected):
            yeast_0_0_2.live_line_eval(bytearray(b_input))
    else:
        assert yeast_0_0_2.live_line_eval(bytearray(b_input)) == bytearray(b_expected)


# TODO : figure out how to test the repl...

if __name__ == '__main__':
    pytest.main(['-sv', __file__])
