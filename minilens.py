import contextlib

from dual.float import dual


# actual polynome as data
bbox = (1.0, 2.0, 3.0)


def polynome(x: dual):
    return x * x * bbox[2] + x * bbox[1] + bbox[0]


# model of a polynome as data
model = (0.0, 0.0, 0.0)


def simulation(x: float):
    return model[0] + model[1] * x + model[2] * x * x


@contextlib.contextmanager
def minilens(x: float):

    # the main (data) component of the lens
    dx = dual(x, 1.0)

    actual = polynome(dx)

    print(f"x: {dx}")

    yield actual

    # TODO : some learning ?
    # Ref : Newton iterative method https://pythonnumericalmethods.berkeley.edu/notebooks/chapter17.05-Newtons-Polynomial-Interpolation.html


# @contextlib.contextmanager
# def world():
#
#     yield polynome


if __name__ == "__main__":

    print(f"polynome coefficients: {bbox}")

    with minilens(42) as value:
        print(f"computed value of polynome p(42): {value}")

    with minilens(51) as value:
        print(f"computed value of polynome p(51): {value}")

    with minilens(33) as value:
        print(f"computed value of polynome p(33): {value}")

    # print(f"found coefficient: {model}")
