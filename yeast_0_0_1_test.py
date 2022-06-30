import pytest
import yeast_0_0_1


@pytest.mark.parametrize(
    "drop_count, ch_input, ch_expected, drop_count_expected",
    [
        (0, ord(b"a"), ord(b"a"), 0),
        (0, ord(b"*"), ord(b"*"), 0),
        (0, ord(b"`"), None, 1),  # this tick is consumed !
        (1, ord(b"a"), None, 0),
        (1, ord(b"*"), None, 0),
        (1, ord(b"`"), None, 2),  # backtick is consumed (and should NOT drop itself)
    ],
)
def test_live_char_eval(drop_count, ch_input, ch_expected, drop_count_expected):

    assert yeast_0_0_1.live_char_eval(ch_input, drop_count) == (
        ch_expected,
        drop_count_expected,
    )


@pytest.mark.parametrize(
    "b_input, b_expected",
    [
        (b"abc", b"abc"),
        (b"`a", b""),
        (b"b`a", b"b"),
        (b"`a`b", b""),
        (b"``ab", b""),
        (b"`ab", b"b"),
        (b"```", b""),
    ],
)
def test_live_line_eval(b_input, b_expected):
    assert yeast_0_0_1.live_line_eval(bytearray(b_input)) == bytearray(b_expected)


# TODO : figure out how to test the repl...

if __name__ == "__main__":
    pytest.main(["-sv", __file__])
