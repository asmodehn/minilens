#!/usr/bin/env python
# -*- coding: ascii -*-

# typedefs for clarity in python
from __future__ import annotations
from typing import Callable, List, Tuple, TypeVar, Union

codeT = bytearray
wordT = bytes
charT = int  # type of one byte in python

# we implement combinator calculus via lambdas that return one tuple
cimplT = wordT
# the continuation must return the same type
pimplT = Union[
    None, Callable[..., cimplT]
]  # None being the noop continuation without args

# -*- implementation -*-

cstack: List[pimplT] = []  # to hold continuations

# We use only one parameter to fit with unlambda and not have to encode the arity of a function here.
# Similarly we implement curry/partial application via continuation (python closures) that we put on the cstack.
# all functions here have the same type to facilitate usage via consistency.
# Note: we rely on the fact that List.append returns None to have multiple statements in a lambda
impl: dict[charT, pimplT] = {
    ord(b"'"): lambda x: cstack.append(lambda y: x(y)) or b"",  # partial apply returning the (representation of the) continuation
    ord(b"i"): lambda x: bytes([x]),
    ord(b"k"): lambda x: cstack.append(lambda y: x) or b"",
    ord(b"s"): lambda x: cstack.append(lambda y: cstack.append(lambda z: bytes([y, z]) + x(z)) or b"") or b"",
}
# Note: the structure of lambdas here could also be implemented via data storing continuations
# or at runtime in the host language, or a mix of both


# -*- stacks -*- [bytearray, bytearray, ...]
pstack: codeT = bytearray()  # to hold parameters


# defining our own Yeast exception class for clarity
class YeastException(Exception):
    pass


def apply_next_param(cont: pimplT) -> Union[None, wordT]:
    try:
        # pick the next param
        p = pstack.pop()
    except IndexError as ie:
        # no param in stack, we're on hold, waiting for code to come in...
        # in eager sync python this means we return nothing and wait to be called again
        return None
    else:
        try:
            # apply the continuation to the param
            return cont(p)
        except Exception as e:
            raise YeastException(e)


def maybe_apply(code: wordT):
    """apply a function 'code' to a stack of 'params'
    This is the "complex function & multiple params" level
    """

    for ch in code:  # we are in an imperative host language, lets loop.
        try:
            # find the implementation
            i = impl[ch]
            if (r := apply_next_param(i)) is None:
                # put the code charT onto the pstack
                pstack.extend(wordT([ch]))
            else:
                # push result tuple onto the parameter stack
                pstack.extend(r)

        except KeyError as ke:  # not found in words dict
            # push the new token into the stack
            pstack.extend(wordT([ch]))

        # At each character parsed, we want to run as many continuations as possible
        for c in reversed(cstack):
            try:
                if (r := apply_next_param(c)) is None:
                    break  # no params any more
                else:
                    pstack.extend(r)
            except Exception as e:
                raise YeastException(e)

# Note : there is a duality here between param and conts...
# apply could probably be written in the other way...

# -- repl --


from prompt_toolkit import PromptSession


def main():
    session = PromptSession()

    while True:
        try:
            print("< " + pstack.decode('ascii'))
            # TODO: char by char for interactive behavior
            text = session.prompt("> ")
        except KeyboardInterrupt:
            continue
        except EOFError:
            break
        else:
            maybe_apply(text.encode('ascii'))

    print("GoodBye!")


if __name__ == "__main__":
    main()
