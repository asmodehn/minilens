# HexaForth

Step by Step implementation of a minimal Forth system, in various ways, mostly for educational purposes.

One of the targets is to leverage HexaForth as a base for experiments on minimal programming systems...

# Bootstrap and Initial Constraints

Given our target of simplicity, quick feedback during implementation, the following seems the most suitable choices at the moment:

- Python as a bootstrap language. Well-known and full feature allowing shortcuts and ignoring implementation details not relevant for beginners.
- Incremental forth word set, to provide learning steps.
- Interpreted to not have a separate "compilation" stage.
- REPL as the tool for development, favoring interactive development.
- Mathematically correct by default (avoid implicit casting, separate different types, etc.), to make good habits from the beginning.
- functional semantics whenever possible (should be always true ? cf. lambda calculus, combinators, etc.)
- ASCII based, potentially extensible to UTF-8
- stay away from types as much as possible, even for the base formal system.
- should remain usable imperatively (stack operational semantics) and useable & useful without theoretical background.


# Potential targets
- minimal forth-core virtual machine (immutable) with extra definitions added on top (mutable).
- bytecode implicit compilation of file, so it is readable with an hexadecimal viewer.
- functional forth equivalence/clarity whenever possible.
- respect the forth standard as much as possible.
- usable as a theorem prover (RLE encoded church numerals as a base for arithmetic should provide good enough forth similarities ?)
- Assembly | Intermediate Representation as a target language (LLVM-IR) to leverage llvm tooling for production systems.
- Some "mathematically sound" behavior of the interpreter with respect to the environment (terminal, source file, vm state, stdin, stdout, etc.).
- interpreter and REPL written in the HexaForth language.


# Implementation

## Step1 the REPL

```python
from prompt_toolkit import PromptSession

def eval_line():
    raise NotImplementedError

def main():
    session = PromptSession()

    while True:
        try:
            text = session.prompt('> ')
        except KeyboardInterrupt:
            continue
        except EOFError:
            break
        else:
            eval_line(text)

    print('GoodBye!')


if __name__ == '__main__':
    main()

```

Then we need to implement the line and token eval function, relying on a stack on a dict of words.
```py

stack = []
words = {}

def eval_token(token: str):
    # execute the word if in dictionary
    try:
        words[token]()
        return True
    except KeyError as ke:  # not found in words dict
        # interpret as number otherwise const
        try:
            parsed = int(token)
        except Exception as e:
            # not a  number, complain
            print(str(e) + ' ?')
            return False
        else:
            # push the new token into the stack
            stack.append(parsed)
            return True


def eval_line(code: str):
    tokens = code.split(" ")
    for token in tokens:
        if not eval_token(token):
            break
```

We can then add the three first words, to implement some calculation on integers

- '+': addition of integers
- '.': write to stdout


```py
stack = []
words = {'+': lambda: stack.append(stack.pop() + stack.pop()),
         '.': lambda: print(f"{stack.pop()} ")
         }
```


With this we have a very basic integer arithmetic for + via a stack-based VM.

/!\ This is a good point to take a break and test things. /!\


## Step2 the Primitives

We can then add primitive forth words to implement the minimum necessary.
For this we can rely on sector forth primitives: 

| Primitive | Stack effects | Description                                   |
| --------- | ------------- | --------------------------------------------- |
| `@`       | ( addr -- x ) | Fetch memory contents at addr                 |
| `!`       | ( x addr -- ) | Store x at addr                               |
| `sp@`     | ( -- sp )     | Get pointer to top of data stack              |
| `rp@`     | ( -- rp )     | Get pointer to top of return stack            |
| `0=`      | ( x -- flag ) | -1 if top of stack is 0, 0 otherwise          |
| `+`       | ( x y -- z )  | Sum the two numbers at the top of the stack   |
| `nand`    | ( x y -- z )  | NAND the two numbers at the top of the stack  |
| `exit`    | ( r:addr -- ) | Pop return stack and resume execution at addr |
| `key`     | ( -- x )      | Read key stroke as ASCII character            |
| `emit`    | ( x -- )      | Print low byte of x as an ASCII character     |

We can also refer to the equivalent in [Minimal Forth](http://www.euroforth.org/ef15/papers/knaggs.pdf) as reference.

As well as the research literature for lambda calculus correspondance and combinator choices:
The [BCKW System](https://en.wikipedia.org/wiki/B,_C,_K,_W_system) has a straight forward operational stack semantics with denotational lambda semantics.
Using this, we can express anykind of supercombinator, and therefore any kind of lambda term.
However it is important to not that there may not be a normal form, the lambda calculus being turing complete, reduction might not terminate...

Some care needs to be taken to be able to represent the current state of the computer as an ASCII text file (for dump and diagnostics):
- stack must be representable
- word map needs to be representable

We need to stay inside some operational limits as well...
... TBD ...  

### Possible extensions
- add '(' and ')' given they are used very often in combinator logic, and will be useful for a lambda calculus
- add \' (as unlambda does) to get smaller size tree structure than with \( and \) 
- add X combinator as an even smaller primitive, allowing rudimentary visual representation
- add Y combinator to express non-terminating reductions ? others ?
- add some other [Combinator Birds](https://www.angelfire.com/tx4/cus/combinator/birds.html) ?

## Step 3 Arity
When we have a super combinator, we also need its arity to be able to verify if the intended usage is correct
To match with lambda representation, we can use "\" for this followed by a digit for clarity.

## Step 4 Arithmetic
TODO : (Peano or simpler ? only + and/or only * for decidability ?)


/!\ This is a good place to test various things /!\

## The repl as a maker app
Functional properties of the REPL ?
Running Tests ?
Writing docs ?
Dumping status on error ?
Event log ? csv ?
Graphic (terminal) API ?

## Step 4 IBCS base

When transforming lambda expression to supercombinator, the IBCS base give us a very straight forward algorithm
see [Combinatory Logic in Programming](https://web.archive.org/web/20070128222953/http://www.wolfengagen.mephi.ru/papers/Wolfengagen_CLP-2003(En).pdf)


## Lambda calculus


## TODO: Proofs and more...