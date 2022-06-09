from __future__ import annotations
from typing import SupportsFloat, SupportsIndex

""" Implementing dual number with floats """


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
    def strategy(
        real=floats(allow_nan=True, allow_infinity=True),
        derivative=floats(allow_nan=True, allow_infinity=True),
    ):
        return builds(dual, real=real, derivative=derivative)

    def __init__(
        self,
        real: SupportsFloat | SupportsIndex | str | bytes | bytearray,
        derivative: SupportsFloat | SupportsIndex | str | bytes | bytearray = 1.0,
    ) -> None:

        # note nan and inf will have the same meaning as for float
        # in the real or derivative part of the dual number.
        # but we force the conversion early to trigger the usual error if any.
        object.__setattr__(self, "real", float(real))
        object.__setattr__(self, "derivative", float(derivative))

    def __eq__(self, other: object):
        # definitional
        if id(self) == id(other):
            return True

        if isinstance(other, dual):
            # identification
            return self.real == other.real and self.derivative == other.derivative
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

    def __mul__(self, other: dual):
        return dual(
            self.real * other.real,
            self.real * other.derivative + other.real * self.derivative,
        )


def isnan(d: dual) -> bool:
    return math.isnan(d.real) or math.isnan(d.derivative)


import unittest
from hypothesis import given
from hypothesis.strategies import floats
import math


class TestDualFloat(unittest.TestCase):
    @given(
        r=floats(),
        d=floats(),
    )
    def test_init(self, r: float, d: float):
        dn = dual(r, d)
        if math.isnan(dn.real):
            self.assertTrue(math.isnan(r))
        else:
            self.assertEqual(dn.real, r, f"{dn} has a real part of {dn.real}")

        if math.isnan(dn.derivative):
            self.assertTrue(math.isnan(d))
        else:
            self.assertEqual(
                dn.derivative, d, f"{dn} has a derivative part of {dn.derivative}"
            )

    @given(
        r=floats(),
        d=floats(),
    )
    def test_hash_and_setattr(self, r: float, d: float):
        dn = dual(r, d)
        # deterministic
        assert hash(dn) == hash(dn)
        # verify same dual number has same hash
        assert hash(dn) == hash(dual(r, d))

        # verify it is immutable so previously computed hash is always correct
        with self.assertRaises(AttributeError, msg="dual.real is immutable"):
            dn.real = 42
        with self.assertRaises(
            AttributeError, msg="dual.derivative is immutable"
        ):
            dn.derivative = 42
        with self.assertRaises(
            AttributeError, msg="dual has no attribute something"
        ):
            dn.something = 42

    @given(
        r=floats(),
        d=floats(),
    )
    def test_eq(self, r: float, d: float):
        d1 = dual(r, d)
        d2 = dual(r, d)

        # if one is nan, the other as well
        if isnan(d1) or isnan(d2):
            self.assertTrue(isnan(d1) and isnan(d2))
        else:
            self.assertEqual(d1, d2, f"{d1} != {d2}")
            # expected for a usual class instance but we can do better here...
            # TODO: cache instance since they are immutables ?
            self.assertFalse(d1 is d2, f"{d1} is {d2}")

    @given(
        r=floats(),
        d=floats(),
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

    @given(d1=dual.strategy(), d2=dual.strategy())
    def test_add(self, d1, d2):
        s = d1 + d2

        # CAREFUL: nan != nan
        if not math.isnan(s.real):
            self.assertEqual(s.real, d1.real + d2.real, f"real = {s.real}")
        else:
            self.assertTrue(math.isnan(d1.real +d2.real))

        if not math.isnan(s.derivative):
            self.assertEqual(s.derivative, d1.derivative + d2.derivative, f"derivative = {s.derivative}")
        else:
            self.assertTrue(math.isnan(d1.derivative + d2.derivative))

    @given(d1=dual.strategy(), d2=dual.strategy())
    def test_sub(self, d1, d2):
        s = d1 - d2

        # CAREFUL: nan != nan
        if not math.isnan(s.real):
            self.assertEqual(s.real, d1.real - d2.real, f"real = {s.real}")
        else:
            self.assertTrue(math.isnan(d1.real - d2.real))

        if not math.isnan(s.derivative):
            self.assertEqual(s.derivative, d1.derivative - d2.derivative, f"derivative = {s.derivative}")
        else:
            self.assertTrue(math.isnan(d1.derivative - d2.derivative))

    @given(d1=dual.strategy(), d2=dual.strategy())
    def test_mult(self, d1, d2):
        p = d1 * d2

        # CAREFUL: nan != nan
        if not math.isnan(p.real):
            self.assertEqual(p.real, d1.real * d2.real, f"real = {p.real}")
        else:
            self.assertTrue(math.isnan(d1.real * d2.real))

        if not math.isnan(p.derivative):
            self.assertEqual(p.derivative, d1.real * d2.derivative + d2.real * d1.derivative, f"derivative = {p.derivative}")
        else:
            self.assertTrue(math.isnan(d1.real * d2.derivative + d2.real * d1.derivative))

    @given(dual.strategy())
    def test_isnan(self, d):
        if isnan(d):
            self.assertTrue(math.isnan(d.real) or math.isnan(d.derivative))
        else:
            self.assertFalse(math.isnan(d.real) and math.isnan(d.derivative))


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
