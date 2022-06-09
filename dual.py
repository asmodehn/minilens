"""
Simple implementation of dual numbers.
First step to experiment on differentiable programming...
"""
from __future__ import annotations

import unittest
import copy
import numpy as np
from functools import singledispatch

from decimal import Decimal, getcontext


class Dual:
    """
    Dual numbers, implemented as a 2x2 matrix (linear algebra style)
    Internally uses Decimal numbers, since proper arithmetic should be addressed
    before we can consider extending it...
    """

    # Inner implementation details
    class Impl:
        # TODO : define types compatible with Decimal
        def __init__(self, real, seed = 1):
            self._i = np.array([[real, seed], [0, real]], dtype=Decimal)

        @property
        def real(self):
            return self._i[0][0]

        @property
        def derivative(self):
            return self._i[0][1]

        def __mul__(self, di: Dual.Impl):
            res = Dual.Impl(0)
            res._i = self._i.dot(di._i)
            return res

        def __add__(self, di: Dual.Impl):
            res = Dual.Impl(0)
            res._i = np.add(self._i, di._i)
            return res

        def __sub__(self, di: Dual.Impl):
            res = Dual.Impl(0)
            res._i = np.subtract(self._i, di._i)
            return res

    class Var:

        # TODO : define types for alebraic computation here
        def __init__(self, i: Dual.Impl):
            self._i = i

        @property
        def real(self):
            return self._i.real

        @property
        def derivative(self):
            return self._i.derivative

        def __add__(self, other: Dual.Var):
            o = other
            if isinstance(other, Dual.Const):
                o = Dual.Var(Dual.Impl(o.real))
            return Dual.Var(self._i + o._i)

        def __sub__(self, other: Dual.Var):
            o = other
            if isinstance(other, Dual.Const):
                o = Dual.Var(Dual.Impl(o.real))
            return Dual.Var(self._i - o._i)

        def __mul__(self, other: Dual.Var):
            o = other
            if isinstance(o, Dual.Const):
                o = Dual.Var(Dual.Impl(o.real))
            return Dual.Var(self._i * o._i)

        def __call__(self) -> Dual.Var:
            """
            Calling observe the value (leaf of computation tree)
            :return:
            """
            return self

        def __eq__(self, other):
            return self.real == other.real and self.derivative == other.derivative

    class Const:
        """
        A special class used for computation initialization purposes.
        Not actually implemented as a dual number, but matching properties.
        """
        def __init__(self, dc: Decimal = Decimal(0)):
            self.real = dc
            self.derivative = 0

        def __add__(self, other: Dual.Var):
            o = other
            if isinstance(o, Dual.Const):
                o = Dual.Var(Dual.Impl(o.real))
            return self() + o

        def __sub__(self, other: Dual.Var):
            o = other
            if isinstance(o, Dual.Const):
                o = Dual.Var(Dual.Impl(o.real))
            return self() - o

        def __mul__(self, other):
            o = other
            if isinstance(o, Dual.Const):
                o = Dual.Var(Dual.Impl(o.real))
            return self() * o

        def __call__(self):
            return Dual.Var(Dual.Impl(self.real))

    class Product:
        def __init__(self, d1, d2):
            if isinstance(d1, Dual.Const):
                d1 = Dual.Var(Dual.Impl(d1.real))

            if isinstance(d2, Dual.Const):
                d2 = Dual.Var(Dual.Impl(d2.real))

            self.d1 = d1
            self.d2 = d2

        @property
        def real(self):
            return self()._i.real

        @property
        def derivative(self):
            return self()._i.derivative

        def __call__(self) -> Dual.Var:
            """
            Doing the product
            => we cannot go back any longer
            :return:
            """

            prod = Dual.Var(self.d1()._i * self.d2()._i)
            return prod

        def __eq__(self, other):
            """ A notion of equality that depends on the computation tree"""
            return isinstance(other, Dual.Product) and self.d1 == other.d1 and self.d2 == other.d2

    class Sum:
        def __init__(self, d1, d2):
            if isinstance(d1, Dual.Const):
                d1 = Dual.Var(Dual.Impl(d1.real))

            if isinstance(d2, Dual.Const):
                d2 = Dual.Var(Dual.Impl(d2.real))

            self.d1 = d1
            self.d2=d2

        @property
        def real(self):
            return self()._i.real

        @property
        def derivative(self):
            return self()._i.derivative

        def __call__(self) -> Dual.Var:
            """
            Doing the sum
            => we cannot go back any longer
            """
            # TODO : maybe mutate should be handle on the outsie if desired instead...

            sum = Dual.Var(self.d1()._i + self.d2()._i)
            return sum

        def __eq__(self, other):
            """ A notion of equality that depends on the computation tree"""
            return isinstance(other, Dual.Sum) and self.d1 == other.d1 and self.d2 == other.d2


    class Sub:
        def __init__(self, d1, d2):
            if isinstance(d1, Dual.Const):
                d1 = Dual.Var(Dual.Impl(d1.real))

            if isinstance(d2, Dual.Const):
                d2 = Dual.Var(Dual.Impl(d2.real))

            self.d1 = d1
            self.d2=d2

        @property
        def real(self):
            return self()._i.real

        @property
        def derivative(self):
            return self()._i.derivative

        def __call__(self) -> Dual.Var:
            """
            Doing the sum
            => we cannot go back any longer
            """
            # TODO : maybe mutate should be handle on the outside if desired instead...

            sub = Dual.Var(self.d1()._i - self.d2()._i)
            return sub

        def __eq__(self, other):
            """ A notion of equality that depends on the computation tree"""
            return isinstance(other, Dual.Sub) and self.d1 == other.d1 and self.d2 == other.d2


    def __init__(self, i=0):
        """
        Create a Constant Dual Number.
        Upon operations it will change and evolve to become a full fledged variable number storing it s derivative...
        """
        self.value = Dual.Const(Decimal(i))

    @property
    def real(self):
        return self.value.real

    @property
    def derivative(self):
        return self.value.derivative

    def __eq__(self, other: Dual):
        """
        Whether two dual numbers are equals or not (computation path included)
        :param other:
        :return:
        """
        return self.value == other.value

    def __mul__(self, other: Dual):
        res = Dual()
        res.value = Dual.Product(self.value, other.value)
        return res

    def __add__(self, other):
        res = Dual()
        res.value = Dual.Sum(self.value, other.value)
        return res

    def __sub__(self, other):
        res = Dual()
        res.value = Dual.Sub(self.value, other.value)
        return res

# Final usecase : to keep focus...




# Internal inspection:

# proc = random_local_computation()

# while we need to
#   r = pick random number  # MonteCarlo
#   d = Dual(r)
#   proc(d)
#   # d contains the derivative of proc for d
#   # linear regression will give us hte polynome, provided that we know the degree...




# External inspection :
# proc = random external process()  # we cannot compute with duals directly
#  # but we can use them for our modelisation...

# while (not done)
#   di = Dual(i)
#   dxo = sim(di)  # compute expectation (random / Montecarlo, etc.)
#   o = proc(i)  # sample (In,Out)  # store as statistics -> can be used to infer probability of occurence in some conditions...
#   do = Dual(o)
#   error = min_square_error(xo, o)  # or other error function
#   use duals to find derivative and determine next sample (dichotomy on proper side) to minimize error at the limit.
#
# TODO :how to deal with oversampling with linear regression ?





class TestDualImpl(unittest.TestCase):

    def test_init(self):
        td = Dual.Impl(42)
        assert td.real == 42
        assert td.derivative == 1  # false as a "derivative" semantic but the actual value we expect for the seed

    def test_mult(self):
        td = Dual.Impl(42)
        tdb = Dual.Impl(53)
        assert (td * tdb).real == 42*53
        assert (td * tdb).derivative == 42+53

    def test_add(self):
        td = Dual.Impl(42)
        tdb = Dual.Impl(53)
        assert (td + tdb).real == 42+53
        assert (td+tdb).derivative == 2

    def test_sub(self):
        td = Dual.Impl(42)
        tdb = Dual.Impl(53)
        assert (td - tdb).real == 42-53
        assert (td-tdb).derivative == 0

# TODO : Review Var (essentialyl the same as Impl ?)
# TODO : Review Const based on usage...

class TestDualSum(unittest.TestCase):

    def test_init(self):
        td = Dual.Impl(42)
        tdb = Dual.Impl(53)
        s = Dual.Sum(Dual.Var(td), Dual.Var(tdb))
        assert s.real == 42+53
        assert s.derivative == 2

    def test_eq(self):
        td = Dual.Impl(42)
        tdb = Dual.Impl(53)
        s = Dual.Sum(Dual.Var(td), Dual.Var(tdb))
        sb = Dual.Sum(Dual.Var(td), Dual.Var(tdb))
        assert s == sb
        assert s != Dual.Var(Dual.Impl(42+53, seed = 2))

    def test_call(self):
        td = Dual.Impl(42)
        tdb = Dual.Impl(53)
        s = Dual.Sum(Dual.Var(td), Dual.Var(tdb))
        r = s()
        assert r == Dual.Var(Dual.Impl(42+53, seed=2))


class TestDualProduct(unittest.TestCase):

    def test_init(self):
        td = Dual.Impl(42)
        tdb = Dual.Impl(53)
        s = Dual.Product(Dual.Var(td), Dual.Var(tdb))
        assert s.real == 42*53
        assert s.derivative == 42+53

    def test_eq(self):
        td = Dual.Impl(42)
        tdb = Dual.Impl(53)
        s = Dual.Product(Dual.Var(td), Dual.Var(tdb))
        sb = Dual.Product(Dual.Var(td), Dual.Var(tdb))
        assert s == sb
        assert s != Dual.Var(Dual.Impl(42*53, seed=42+53))

    def test_call(self):
        td = Dual.Impl(42)
        tdb = Dual.Impl(53)
        p = Dual.Product(Dual.Var(td), Dual.Var(tdb))
        r = p()
        assert r == Dual.Var(Dual.Impl(42*53, seed=42+53))


class TestDual(unittest.TestCase):

    def test_init(self):
        d = Dual(42)
        assert d.real == 42
        assert d.derivative == 0

    def test_add_dual(self):

        d1 = Dual(2)
        d2 = Dual(3)

        d3 = d1 + d2

        assert d3.real == 5
        assert d3.derivative == 2

    def test_mul_dual(self):
        d1 = Dual(2)
        d2 = Dual(3)

        d3 = d1 * d2

        assert d3.real == 6
        assert d3.derivative == 5


if __name__ == '__main__':
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromName(__name__)
    runner = unittest.TextTestRunner()
    result = runner.run(suite)
