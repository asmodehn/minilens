import asyncio
from typing import Callable, List

from prompt_toolkit.input import create_input
from prompt_toolkit.keys import Keys


# simple curried functional implementation, one input one return
def I(x: int) -> int:
    return x


# curried implementation, since we want the ability to apply char by char
def K(x: int) -> Callable[[int], int]:
    def pK(y: int) -> int:
        return x
    return pK


impl = {
    ord(b'i'): I,
    ord(b'k'): K
}


# defining our own Yeast exception class for clarity
class YeastException(RuntimeError):
    pass


Closure = Callable[[int], int] \
          | Callable[[int, int], int] \
          | Callable[[int, int, int], int]


cstack: List[Closure] = []


def apply_curry(ch: int) -> int | None:
    """ apply the top continuation to the current char.
    Result is returned as a char.
    None is returned when the char was processed without producing a result (pushing a continuation onto the cstack) """
    try:
        cont = cstack.pop()

        # CAREFUL, this may also return a closure in this implementation
        r = cont(ch)

        if callable(r):
            # context accumulated in the closure itself (not as a new element in the stack)
            cstack.append(r)  # append the new closure
        else:
            return r

    except IndexError as ie:
        # no continuation exist
        try:

            # jit  find implementation for this char
            i = impl[ch]

            # append the continuation to the cstack
            cstack.append(i)

            # IMPORTANT: let the caller manage the pstack !

        except KeyError as ke:
            # no implementation exists: just use this character as is.
            return ch

    return None


def apply(pstack: bytearray) -> bytearray:
    """ reduce a list of symbols.
    return the result as a list of symbols.
    Careful: the stack of continuation might have been modified"""

    # prepare stack for result
    rstack = bytearray()

    try:
        # find next character
        while ch := pstack.pop():
            res = apply_curry(ch)

            if res is not None:
                # complete application result
                rstack.append(res)

            else:
                # CAREFUL: cstack has been modified here
                pass

    except IndexError as ie:
        # consumed all params
        pass

    return rstack


pstack = bytearray()


async def main() -> None:
    done = asyncio.Event()
    input = create_input()

    def keys_ready():
        for key_press in input.read_keys():
            print("> ", end="")

            # print(key_press)

            if key_press.key == Keys.ControlC:
                print("GoodBye!")
                done.set()
            if key_press.key == Keys.Enter:
                apply(pstack)
            # otherwise, if there is only one ascii character
            elif len(ascii_input := key_press.data.encode("ascii")) == 1:
                pstack.append(ord(ascii_input))
                print(ascii_input)
            else:
                raise NotImplementedError(key_press)

    with input.raw_mode():
        with input.attach(keys_ready):
            await done.wait()


if __name__ == "__main__":
    asyncio.run(main())
