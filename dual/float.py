from __future__ import annotations
from typing import SupportsFloat, SupportsIndex

""" Implementing dual number as an extension to float numbers """


from hypothesis.strategies import floats, builds

class dual:
    """
    Dual number based on float data type
    """

    __slots__ = ("real", "derivative")

    # helping mypy
    real: float
    derivative: float

    @staticmethod
    def strategy(real = floats(allow_nan=False, allow_infinity=False),
                 derivative = floats(allow_nan=False, allow_infinity=False)):
        return builds(dual, real=real, derivative=derivative)

    @staticmethod
    def float_conversion(x: SupportsFloat | SupportsIndex | str | bytes | bytearray):
        f = float(x)  # force conversion first to trigger usual error if any

        # then raise if nan or inf as not supported
        if f in [float("nan"), float("inf")]:
            raise ArithmeticError(
                f"{f} not supported as real or derivative part of a dual"
            )

        return f

    def __init__(
        self,
        real: SupportsFloat | SupportsIndex | str | bytes | bytearray,
        derivative: SupportsFloat | SupportsIndex | str | bytes | bytearray = 1.0,
    ) -> None:

        object.__setattr__(self, "real", dual.float_conversion(real))
        object.__setattr__(self, "derivative", dual.float_conversion(derivative))

    def __eq__(self, other: object):
        # definitional
        if id(self) == id(other):
            return True

        if isinstance(other, dual):
            # identification
            return hash(self) == hash(other)
        else:
            RuntimeError(f"{other} is not a dual. Ambiguous comparison with {self}.")

    def __setattr__(self, name, value):
        """
        Overriding __setattr__ to make dual instance immutable.
        Since it is hashable, it should be immutable.
        Ref: https://hynek.me/articles/hashes-and-equality/
        """
        if name in self.__slots__:
            msg = f"{self.__class__}.{name}' is immutable"
        else:
            msg = f"{self.__class__}' has no attribute {name}"
        raise AttributeError(msg)

    def __hash__(self) -> int:
        # this will also define equality
        return hash((self.real, self.derivative))

    def __repr__(self):
        if self.derivative == 0.0:
            # special case : same as for a usual float
            return repr(self.real)
        real_repr = "" if self.real == 0.0 else f"{self.real} +"
        deriv_repr = " ε " if self.derivative == 1.0 else f" ε {self.derivative}"
        return "(" + real_repr + deriv_repr + ")"

    def __add__(self, other: dual):
        return dual(self.real + other.real, self.derivative + other.derivative)

    def __sub__(self, other: dual):
        return dual(self.real - other.real, self.derivative - other.derivative)


import unittest
from hypothesis import given
from hypothesis.strategies import floats


class TestDualFloat(unittest.TestCase):
    @given(
        r=floats(allow_nan=False, allow_infinity=False),
        d=floats(allow_nan=False, allow_infinity=False),
    )
    def test_init(self, r: float, d: float):
        dn = dual(r, d)
        self.assertEqual(dn.real, r, f"{dn} has a real part of {dn.real}")
        self.assertEqual(dn.derivative, d, f"{dn} has a derivative part of {dn.derivative}")

    @given(
        r=floats(allow_nan=False, allow_infinity=False),
        d=floats(allow_nan=False, allow_infinity=False),
    )
    def test_hash_and_setattr(self, r: float, d: float):
        dn = dual(r, d)
        # deterministic
        assert hash(dn) == hash(dn)
        # verify same dual number has same hash
        assert hash(dn) == hash(dual(r, d))

        # verify it is immutable so previously computed hash is always correct
        with self.assertRaises(AttributeError, msg="dual.real is immutable") as cm:
            dn.real = 42
        with self.assertRaises(AttributeError, msg="dual.derivative is immutable") as cm:
            dn.derivative = 42
        with self.assertRaises(AttributeError, msg="dual has no attribute something") as cm:
            dn.something = 42

    @given(
        r=floats(allow_nan=False, allow_infinity=False),
        d=floats(allow_nan=False, allow_infinity=False),
    )
    def test_eq(self, r: float, d: float):
        d1 = dual(r, d)
        d2 = dual(r, d)
        assert d1 == d2, f"{d1} != {d2}"
        # expected for a usual class instance but we can do better here...
        assert d1 is not d2, f"{d1} is not {d2}"

    @given(
        r=floats(allow_nan=False, allow_infinity=False),
        d=floats(allow_nan=False, allow_infinity=False),
    )
    def test_repr(self, r: float, d: float):
        dn = dual(r, d)
        if dn.derivative == 0.0:
            assert repr(dn) == repr(r), repr(dn)
        elif dn.derivative == 1.0 and dn.real == 0.0:
            assert repr(dn) == "( ε )", repr(dn)
        elif dn.derivative == 1.0:
            assert repr(dn) == f"({r} + ε )", repr(dn)
        elif dn.real == 0.0:
            assert repr(dn) == f"( ε {d})", repr(dn)
        else:
            assert repr(dn) == f"({r} + ε {d})", repr(dn)

    # @given(floats())
    # def test_mult(self, a: float, b: float):
    #     td = dual(42)
    #     tdb = dual(53)
    #     assert (td * tdb).real == 42*53
    #     assert (td * tdb).derivative == 42+53

    @given(d1=dual.strategy(), d2=dual.strategy())
    def test_add(self, d1, d2):
        s = d1 + d2
        assert s.real == d1.real + d2.real
        assert s.derivative == d1.derivative + d2.derivative

    @given(d1=dual.strategy(), d2=dual.strategy())
    def test_sub(self, d1, d2):
        s = d1 - d2
        assert s.real == d1.real - d2.real
        assert s.derivative == d1.derivative - d2.derivative


if __name__ == "__main__":
    import sys
    from mypy import api

    result = api.run([__file__])

    if result[0]:
        print("\nType checking report:\n")
        print(result[0])  # stdout

    if result[1]:
        print("\nError report:\n")
        print(result[1])  # stderr

    if result[2] == 0:
        # only launch unit testing if types are correct

        loader = unittest.TestLoader()
        suite = loader.loadTestsFromName(__name__)
        runner = unittest.TextTestRunner(verbosity=2)
        runner.run(suite)
