
# Yeast 

Adapted from Wikipedia:

>Yeasts are eukaryotic, single-celled microorganisms classified as members of the fungus kingdom. Eukaryotes are organisms whose cells have a KERNEL enclosed within a REPL.

>Yeasts are unicellular organisms that evolved from multicellular ancestors, with some species having the ability to develop multicellular characteristics by forming strings of connected budding cells known as pseudohyphae or false hyphae.

>Most yeasts reproduce asexually by COPY.

## Design

### Aims

- minimal programming language
- learnable programming language
- self-contained and reflective
- readable and interactive
- dynamically extensible
- permanent memory model

### Constraints

- Introspectable with usual computer tooling
- Possible to be used for literal programming
- following standards (ASCII adaptable to UTF-8).
- minimal in size but extensible during "runtime".
- self-contained and reflective, possibly homoiconic, with a permanent memory model.
- Minimal and Mathematically sound (functional)

### Inspirations

- Forth
- Unlambda
- J

## Technical Specs

Yeast aim to be a single binary file that can be run and be its own interpreter, like Forth systems.
It can be grown, at first, hosted in an existing programming language *interpreter*, as we want to emphasize the tight interaction and feedback loop with human users (no separate compilation step)
A compilation step can be added later on for minimization, but is only a system developer tool, not for the user to know about.

This implementation is currently in python, meaning it is an ASCII file, that is interpreted in python, and is self-contained, in that it contains it s own KERNEL (stack base vm), an INTERPRETER (eval) and a SHELL (REPL in tty)

### Basic Consideration

To have a self-contained vm, interpreter and repl in a single file, and somehow be able to represent itself, the programming language must:
- have different "code" and "string" datatypes
- a string can be represented by a pointer/reference to a part of memory
- have a simple way to represent list/array both for "code" and "string" base types
- be able to convert automatically and implicitly between both

### Tech Design

- ASCII char are character on 8 bits (7bit + 1 for UTF-8 extensiblity) and as an array form ASCII strings (null-terminated for compatibility with hex viewers)
- code is represented by an ASCII string in file ( == memory == state ), but interpreted as code, using the delimiter / (inverted lambda \), since it uses inverted unlambda strings as code.

#### Evolution constraints

Yeast will be grown from a python file.
The representation we take at this stage must match python representation to allow self manipulation.
Therefore:
- arrays are python lists
- code strings are bytearrays
- char strings are raw strings

To be readable by human (literal programming) there can be annotations included. 
These will have to be marked by '#' to be recognized as comments

#### Possible Variations

- curried & direct order (unlambda - only one return stack)
- curried & reverse order (partial apply via return stack)
- non-curried & reverse order

Implementation choices:

- function as python callable
- closure as data structure
- something else, somewhere in the middle...

#### Final goal

Arrays aim to be compatible with csv format for ASCII strings, therefore using the comma ',' as cell delimiter and \n for row delimiter.
For arrays in code however, we have two dimensions, as usual with the ' ' and the '\n' character, to form obvious matrices when viewed with usual tooling.

To be readable by human (literal programming) there can be annotations included. 
These will have to be marked in a way that suits the host language and existing tooling.

#### Origin - the STRUCTURE

There are few zones in the memory
- a stack
- immutable codeword list
- mutable codeword list
- vm implementation
- interpreter implementation
- repl implementation

These are reflected in the python file structure.

#### Life - the VM

A stack based VM, inspired from Forth systems.

#### Understandability - the INTERPRETER

It relies on the VM to execute code. But it has to parse code string into code chars

#### Interactivity - the REPL

Since we want interactivity to be a first class consideration, the "file" is not the main way to interract with Yeast. 
The terminal / tty becomes is the main interface, and each interaction should be immediately taken into account.
The interaction is keypress based (minus modifiers), instead of line-based as it is traditionally in REPLs.
We are closer to a game-like interactive design.




