import asyncio
import io
from typing import Type

import pytest
from prompt_toolkit.input import create_input
from prompt_toolkit.key_binding import KeyPress
from prompt_toolkit.keys import Keys

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



@pytest.mark.parametrize("b_input, b_expected", [
    (b'', [b'a', b'b', b'c']),  # because ` would trigger error
    (b'a', [b'`', b'a', b'b', b'c']),  # because ` is more useful to compress the input, and we can always add more chars
    (b'`', []),  # because ` already triggers error
    (b'a`', [b'a', b'b', b'c'])  # because ` would trigger error
])
def test_live_char_expect(b_input, b_expected):

    if isinstance(b_expected, type):
        if not issubclass(b_expected, Exception):
            raise NotImplementedError
        with pytest.raises(b_expected):
            yeast_0_0_2.live_char_expect(bytearray(b_input))
    else:
        assert yeast_0_0_2.live_char_expect(bytearray(b_input)) == b_expected


# yeast 0.0.2 makes it possible to test interactive output !

@pytest.mark.parametrize("key_press, pqueue, pqueue_expected, out_expected", [
    (KeyPress(key='a', data='a'), bytearray(b''), bytearray(b'a'), "a"),
    (KeyPress(key='b', data='b'), bytearray(b''), bytearray(b'b'), "b"),
    (KeyPress(key='c', data='c'), bytearray(b''), bytearray(b'c'), "c"),
    (KeyPress(key='`', data='`'), bytearray(b''), bytearray(b'`'), "`"),
    (KeyPress(key=Keys.Enter), bytearray(b'`'), bytearray(b''), "\nError evaluating parameters. Reset!\n> "),
    (KeyPress(key='a', data='a'), bytearray(b'*'), bytearray(b'*a'), 'a'),
    (KeyPress(key='b', data='b'), bytearray(b'*'), bytearray(b'*b'), 'b'),
    (KeyPress(key='c', data='c'), bytearray(b'*'), bytearray(b'*c'), 'c'),
    (KeyPress(key='`', data='`'), bytearray(b'*'), bytearray(b'*`'), '`'),
    (KeyPress(key=Keys.Enter), bytearray(b'*`'), bytearray(b''), '\n> '),  # new line eval and prints next line
    (KeyPress(key=Keys.Enter), bytearray(b'a'), bytearray(b'a'), '\n> a'),  # new line eval and prints next line with pqueue on it
    # KeyPress Backspace TODO
])
def test_live_char_tty(key_press, pqueue, pqueue_expected, out_expected):

    outbuf = io.StringIO()
    yeast_0_0_2.live_char_tty(key_press, pqueue, outbuf)

    # pqueue input has been modified
    assert pqueue == pqueue_expected
    assert outbuf.getvalue() == out_expected


if __name__ == '__main__':
    pytest.main(['-sv', __file__])
