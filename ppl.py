from __future__ import annotations

import inspect
from itertools import count, cycle, filterfalse, product, repeat, starmap, tee
from typing import Callable, Generator, Generic, Iterable, Iterator, List, Optional, Tuple, TypeVar

"""
A module implementing iterator pipelines as a mutable object
"""

T = TypeVar('T')


class Pipeline(Generic[T]):
    """ pipeline functionality for generators.
     A cleaner (?) wrapper over itertools
     """

    gen: Iterator[T] | Iterator[Tuple[T, T]]

    def __init__(self, source: Iterator[T] | Iterator[Tuple[T, T]]) -> None:
        self.gen = source

    def __iter__(self):
        """ iterable as much as the underlying iterator """
        return self

    def __next__(self) -> T:
        """ delegate next to underlying iterator"""
        return next(self.gen)

    @classmethod
    def repeat_data(cls, data: T, times: Optional[int] = None) -> Pipeline:
        return Pipeline(source=repeat(data, times))

    @classmethod
    def cycle_iterable(cls, iterable: Iterable[T]) -> Pipeline:
        return Pipeline(source=cycle(iterable))

    # Note : Count requires some cartesian structure on the type (+ and *)
    # TODO
    # @classmethod
    # def count(cls, start: T, step: Callable[[T], T]):
    #     PPL(source=count(start, step))

    def __str__(self) -> str:
        return str(self.gen)
        # TODO : more useful output ??
        # return f"{inspect.getgeneratorstate(self.gen)}: {inspect.getgeneratorlocals(self.gen)} | {inspect.getmembers(self.gen)}"

    def __repr__(self):
        return repr(self.gen)

    def __eq__(self, other: object) -> bool:
        """ equality of generators via bisimulation """

        if isinstance(other, Pipeline):
            # equality in PPL
            return all(s == o for s, o in zip(iter(self.gen), iter(other.gen)))
        else:
            raise NotImplementedError

    def filter(self, pred) -> None:
        self.gen = filter(pred, self.gen)

    def zip(self, other: Iterator[T]) -> None:
        """ zip another iterator onto this one.
        If you want a brand new PPL, you might want to use the product instead.
        """
        self.gen = zip(self.gen, other)

    # itertools

    def filterfalse(self, pred) -> None:
        self.gen = filterfalse(pred, self.gen)

    def map(self, fun: Callable[[T], T]) -> None:
        args = ((e, ) for e in self.gen)  # make a tuple
        self.gen = starmap(fun, args)  # TODO : generic starmap wrapper in pipeline ??

    def __mul__(self, other: Pipeline) -> Pipeline:
        return Pipeline(source=product(self.gen, other.gen))

    def tee(self, n: int = 2) -> List[Pipeline]:
        # original iterator should not be used -> replaced with one of tee result
        self.gen, *new_ones = tee(self.gen, n)
        return [Pipeline(source=n) for n in new_ones]

    def print(self):
        def printer(started_gen):
            e = next(started_gen)
            print(e)
            yield e
        self.gen = printer(self.gen)


if __name__ == "__main__":

    acc = 0

    def count_print(x: int, n: int = 9):
        """side effect with refl()"""
        global acc
        acc += 1
        # forcibly exit after n prints
        if acc > n:
            exit(0)
        return x

    ppl = Pipeline.cycle_iterable([33, 42, 51])
    ppl.filterfalse(lambda x: x < 35 or x > 45)
    # l = [v for v in ppl.tee()]
    # print(l)
    ppl.print()  # print in pipeline
    ppl.map(count_print)

    # actually run and print entire value list
    print(list(v for v in ppl))


