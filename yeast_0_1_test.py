import pytest

import yeast
import yeast_0_1


def test_I():
    # no return, verify as continuation
    assert yeast_0_1.I(ord('a')) == ord('a')


def test_K():
    # no return, verify as continuation
    assert callable(yeast_0_1.K(ord('a')))
    # second arg returns
    assert yeast_0_1.K(ord('a'))(ord('b')) == ord('a')


@pytest.mark.parametrize("inpt, outpt, cstack_size", [
    # passing unknown character through as noop
    (b'*', b'*', 0),
    # known characters will produce a continuation
    (b'i', None, 1),
    (b'k', None, 1),
])
def test_apply_curry_noparam(inpt, outpt, cstack_size):

    # CAREFUL: this is intentional global state...
    yeast_0_1.cstack.clear()

    # ensure clean state
    assert len(yeast_0_1.cstack) == 0

    if outpt is None:
        assert yeast_0_1.apply_curry(ord(inpt)) is None
    else:
        assert yeast_0_1.apply_curry(ord(inpt)) == ord(outpt)

    # remaining continuations on the stack
    assert len(yeast_0_1.cstack) == cstack_size


@pytest.mark.parametrize("inpt, outpt, cstack_size", [
    # noop example to validate test ordering
    (b'abc', b'abc', 0),

    # i remains, until another param appears
    (b'i', b'', 1),
    # i and * (anything) return *
    (b'i*', b'*', 0),

    # k is consumed to make a continuation
    (b'k', b'', 1),
    # * is consumed to make a continuation, and replace the previous one from 'k'
    (b'k*', b'', 1),

    # i on k is just k
    (b'ik', b'k', 0),

])
def test_apply_curry(inpt, outpt, cstack_size):

    # CAREFUL: this is intentional global state...
    yeast_0_1.cstack.clear()

    # ensure clean state
    assert len(yeast_0_1.cstack) == 0

    res = bytearray()

    # HERE we parse chars in normal order
    for i in inpt:
        if (r := yeast_0_1.apply_curry(i)) is not None:
            res.append(r)
            # and we get result in correct order !

    assert bytes(res) == outpt

    # remaining continuations on the stack
    assert len(yeast_0_1.cstack) == cstack_size


# CAREFUL, because of stack semantics, the char order is reversed !
@pytest.mark.parametrize("inpt, outpt, cstack_size", [
    # noop example to validate test ordering
    (b'cba', b'abc', 0),

    # i has an implementation, so it is consumed
    (b'i', b'', 1),
    # i and * (anything) return *
    (b'*i', b'*', 0),

    # k has an implementation, so it is consumed
    (b'k', b'', 1),
    # k and only one param produce only one continuation
    (b'*k', b'', 1),

    # i on k is just k
    (b'ki', b'k', 0),
    # ki and * (anything) returns i
    (b'*ik', b'i', 0),
    # k* and i (anything) returns *
    (b'i*k', b'*', 0),

    # TODO : W

])
def test_apply(inpt, outpt, cstack_size):

    # CAREFUL: this is intentional global state...
    yeast_0_1.cstack.clear()

    # ensure clean state
    assert len(yeast_0_1.cstack) == 0

    pstack = bytearray(inpt)

    # we passed arguments in reverse order, but we dont need to reverse the result,
    # when checking like this, all at once in order.
    assert bytes(yeast_0_1.apply(pstack)) == outpt

    # remaining continuations on the stack
    assert len(yeast_0_1.cstack) == cstack_size


if __name__ == '__main__':
    pytest.main(['-sv', __file__])
