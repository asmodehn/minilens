import asyncio
import io
from typing import Type
from unittest import mock

import pytest
from prompt_toolkit.application import create_app_session
from prompt_toolkit.document import Document
from prompt_toolkit.input import create_input
from prompt_toolkit.key_binding import KeyPress
from prompt_toolkit.keys import Keys

import yeast_0_0_3


@pytest.mark.parametrize(
    "result, ch_input, next_result_or_except",
    [
        (b"", ord(b"a"), b"a"),
        (b"", ord(b"*"), b"*"),
        (b"", ord(b"`"), IndexError),  # Error: this tick cannot be used !
        (b"x", ord(b"a"), b"xa"),
        (b"x", ord(b"*"), b"x*"),
        (b"x", ord(b"`"), b""),  # backtick is used
        # backtick should *never* be in result (since it is supposed to have been applied).
        # but if it ever is, it is automatically and cleanly dropped, for safety:
        (b"`", ord(b"a"), b"a"),
        (b"`", ord(b"*"), b"*"),
        (b"`", ord(b"`"), b""),
    ],
)
def test_live_char_eval(
    result: bytes, ch_input: int, next_result_or_except: bytes | Type[Exception]
):
    res_stack = bytearray(result)

    if isinstance(next_result_or_except, type):
        if not issubclass(next_result_or_except, Exception):
            raise NotImplementedError
        with pytest.raises(next_result_or_except):
            yeast_0_0_3.live_char_eval(ch_input, res_stack)
    else:
        yeast_0_0_3.live_char_eval(ch_input, res_stack)
        assert res_stack == bytearray(next_result_or_except)


@pytest.mark.parametrize(
    "b_input, b_expected",
    [
        (b"abc", b"abc"),
        (b"`a", IndexError),
        (b"b`a", b"a"),
        (b"a`b`", b""),
        (b"ab``", b""),
        (b"ab`", b"a"),
        (b"```", IndexError),
    ],
)
def test_live_line_eval(b_input, b_expected):

    if isinstance(b_expected, type):
        if not issubclass(b_expected, Exception):
            raise NotImplementedError
        with pytest.raises(b_expected):
            yeast_0_0_3.live_line_eval(bytearray(b_input))
    else:
        assert yeast_0_0_3.live_line_eval(bytearray(b_input)) == bytearray(b_expected)


@pytest.mark.parametrize(
    "b_input, b_expected",
    [
        (b"", [b"a", b"b", b"c"]),  # because ` would trigger error
        (
            b"a",
            [b"`", b"a", b"b", b"c"],
        ),  # because ` is more useful to compress the input, and we can always add more chars
        (b"`", []),  # because ` already triggers error
        (b"a`", [b"a", b"b", b"c"]),  # because ` would trigger error
    ],
)
def test_live_char_expect(b_input, b_expected):

    if isinstance(b_expected, type):
        if not issubclass(b_expected, Exception):
            raise NotImplementedError
        with pytest.raises(b_expected):
            yeast_0_0_3.live_char_expect(b_input)
    else:
        assert yeast_0_0_3.live_char_expect(b_input) == b_expected


# We can now test the prompt session
from prompt_toolkit.input import create_pipe_input
from prompt_toolkit.output import DummyOutput


@pytest.mark.parametrize(
    "input, expected_completions, expected_last_eval_error",
    [
        ("a", ["`", "a", "b", "c"], None),
        ("cba", ["`", "a", "b", "c"], None),
        ("`", [], IndexError("pop from empty bytearray")),
        ("cba```", ["a", "b", "c"], None),
        ("cba````", [], IndexError("pop from empty bytearray")),
    ],
)
def test_prompt_session(input, expected_completions, expected_last_eval_error):
    with create_pipe_input() as inp:

        yeast_session = yeast_0_0_3.session(
            input=inp,
            output=DummyOutput(),
        )

        inp.send_text(input + "\n")  # forcing \n to get result

        result = yeast_session.prompt()

    assert result == input  # no direct modification of the input

    # testing completer for this input (including ordering !)
    assert expected_completions == [
            comp.text
            for comp in yeast_0_0_3.completer.get_completions(
                Document(input, cursor_position=len(input)), "unused_complete_event"
            )
        ]

    # testing last eval error for this input
    if expected_last_eval_error is None:
        assert yeast_0_0_3.last_eval_error is None
    else:
        assert yeast_0_0_3.last_eval_error == expected_last_eval_error


if __name__ == "__main__":
    pytest.main(["-sv", __file__])
