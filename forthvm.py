#! /usr/bin/env python
# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2010. José Dinuncio
# All Rights Reserved.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License.
#
# Modifications by @asmodehn
##############################################################################
import sys
import inspect


def word_(name="", imm=False):
    """Word decorator for functions"""
    def wr(fn, name=name, imm=imm):
        if not name:
            name = fn.__name__
        word = Word(name, fn, imm)
        return word
    return wr


class Word:
    __slots__ = ("name", "code", "imm")

    """A Forth Word"""
    def __init__(self, name, code, imm=False):
        self.name = name
        self.code = code
        self.imm = imm

    def is_instruction(self):
        """True is self.code is executable"""
        return inspect.isroutine(self.code)

    def get(self, i):
        """Return the i-th word of this word"""
        ### Investigation ongoing
        if isinstance(self.code, str):
            print("GET on char witnessed !!! Is this actually intended ???")
        assert isinstance(self.code, list)  # the expected intent ??
        ### Investigation end
        return self.code[i]

    def __repr__(self):
        return f"{self.name}"
        # return f"Word({self.name}, {self.code}, {self.imm})"


class PC:
    __slots__ = ("word", "idx")

    """The Program Counter"""
    def __init__(self, word, idx=0):
        self.word = word
        self.idx = idx

    def next(self):
        """Returns the word pointed by the PC and increment it"""
        v = self.this()
        self.inc()
        return v

    def this(self):
        """Returns the word pointed by the PC"""
        return self.word.get(self.idx)

    def inc(self, x=1):
        """Increments the PC"""
        self.idx = self.idx + x

    def __repr__(self):
        return f"PC({self.word.name}, {self.idx})"


class Forth:
    """Forth Virtual Machine"""
    def __init__(self, run=True, words=None, debug=False, fin=sys.stdin, fout=sys.stdout):

        self.stack = []
        self.rstack = []
        self.dct = {}
        self.fin = fin
        self.fout = fout
        self.debug = debug
        self.debugger = None
        self.last_word = None

        self._init_words()
        if words is None:
            self._load_words([])
        else:
            self._load_words(words)
        if run:
            self._run()

    # Utility functions
    def _debug(self):
        if not self.debug:
            return

        if self.debugger:
            self.debugger(self)
            return

        print('word:    ', self.pc.word.name)
        print('rs - pc: ', self.rstack, self.pc)
        print('         ', self.pc.word.code)
        print('cur i:   ', self.pc.this())
        print('stack:   ', self.stack)
        print('interpret', self.dct.get('forth_interpret', False))
        print()

    def _str_to_bool(self, ws):
        'Returns a boolean given a string or RuntimeError'
        ws = ws.lower()
        if ws == 'true':
            return True
        elif ws == 'false':
            return False
        else:
            raise RuntimeError

    def _traduce(self, ws):
        'Return an int, float, bool, word or string given an string'
        for fn in [self.dct.__getitem__, int, float, self._str_to_bool, str]:
            try:
                r = fn(ws)
                return r
            except:
                pass

    def compile_word(self, name, def_, imm=False):
        '''
        Create and register a word.

        This is an utility function for test purposes.
        If a word is not in the dictionary is treated as a string.
        '''
        wns = def_.split()
        parts = []
        for wn in wns:
            part = self._traduce(wn)
            parts.append(part)
        word = Word(name, parts, imm)
        self._add_word(word)
        return word

   # Execution

    def _run(self, word=None):
        """Start running the virtual machine"""
        if not word:
            word = self.dct['init']

        if word.is_instruction():
            self._exec_instruction(word)
            return

        self.pc = PC(word)
        while True:
            word = self._next()
            if word == end:
                return
            self._exec(word)
            self._debug()

    def _exec(self, word):
        """Exec a word"""
        if word.is_instruction():
            self._exec_instruction(word)
        else:
            self._exec_word(word)

    def _exec_instruction(self, word):
        """Exec an instuction"""
        word.code(self)

    def _exec_word(self, word):
        """Exec a word"""
        self.rpush(self.pc)
        self.pc = PC(word)

    # PC

    def _inc_pc(self, i=1):
        """Increment the program counter"""
        self.pc.inc(i)

    def _next(self):
        """Get the word referenced by the pc"""
        return self.pc.next()

    # Stack

    def push(self, v):
        self.stack.append(v)

    def pop(self):
        return self.stack.pop()

    def rpush(self, v):
        self.rstack.append(v)

    def rpop(self):
        return self.rstack.pop()

    # Dictionary

    def _init_words(self):
        """Load the dictionary with the words defined in this module"""
        me = sys.modules[__name__]
        words = self._get_words(me)
        self._load_words(words)

    def _get_words(self, module):
        """Get the words defined in a module"""
        words = []
        for name in dir(module):
            word = getattr(module, name)
            if isinstance(word, Word):
                words.append(word)
        return words

    def _load_words(self, words):
        """Load the dictionary with words"""
        for word in words:
            self._add_word(word)

    def _add_word(self, word):
        """Add a word to the dictionary"""
        self.dct[word.name] = word
        self.last_word = word


# Instructions

# Stack instructions
@word_()
def dup(forth):
    v = forth.stack[-1]
    forth.push(v)

@word_()
def drop(forth):
    forth.pop()

@word_()
def swap(forth):
    b = forth.pop()
    a = forth.pop()
    forth.push(b)
    forth.push(a)

@word_()
def over(forth):
    v = forth.stack[-2]
    forth.push(v)

@word_()
def rot(forth):
    c = forth.pop()
    b = forth.pop()
    a = forth.pop()
    forth.push(b)
    forth.push(c)
    forth.push(a)

@word_('rot-')
def rot(forth):
    c = forth.pop()
    b = forth.pop()
    a = forth.pop()
    forth.push(b)
    forth.push(c)
    forth.push(a)

@word_()
def depth(forth):
    d = len(forth.stack)
    forth.push(d)

@word_()
def pick(forth):
    i = forth.pop()
    v = forth.stack[-1 - i]
    forth.push(v)

# Arithmetic
@word_('+')
def add(forth):
    b = forth.pop()
    a = forth.pop()
    forth.push(a + b)

@word_('-')
def sub(forth):
    b = forth.pop()
    a = forth.pop()
    forth.push(a - b)

@word_('*')
def mul(forth):
    b = forth.pop()
    a = forth.pop()
    forth.push(a * b)

@word_('/')
def x(forth):
    b = forth.pop()
    a = forth.pop()
    forth.push(a / b)

@word_('/mod')
def divmod(forth):
    b = forth.pop()
    a = forth.pop()
    forth.push(a / b)
    forth.push(a % b)

# Bit Operation
@word_('&')
def b_and(forth):
    b = forth.pop()
    a = forth.pop()
    forth.push(a & b)

@word_('|')
def b_or(forth):
    b = forth.pop()
    a = forth.pop()
    forth.push(a | b)

@word_('^')
def b_xor(forth):
    b = forth.pop()
    a = forth.pop()
    forth.push(a ^ b)

@word_('~')
def neg(forth):
    a = forth.pop()
    forth.push(~a)


@word_('<<')
def shl(forth):
    b = forth.pop()
    a = forth.pop()
    forth.push(a << b)

@word_('>>')
def shr(forth):
    b = forth.pop()
    a = forth.pop()
    forth.push(a >> b)

# Logic
@word_('and')
def and_(forth):
    b = forth.pop()
    a = forth.pop()
    v = a and b
    forth.push(v)

@word_('or')
def or_(forth):
    b = forth.pop()
    a = forth.pop()
    v = a or b
    forth.push(v)

@word_('not')
def not_(forth):
    a = forth.pop()
    v = not a
    forth.push(v)

# Comparison

@word_('<=')
def le(forth):
    b = forth.pop()
    a = forth.pop()
    v = a <= b
    forth.push(v)

@word_('<')
def lt(forth):
    b = forth.pop()
    a = forth.pop()
    v = a < b
    forth.push(v)

@word_('>=')
def ge(forth):
    b = forth.pop()
    a = forth.pop()
    v = a >= b
    forth.push(v)

@word_('>')
def gt(forth):
    b = forth.pop()
    a = forth.pop()
    v = a > b
    forth.push(v)

@word_('=')
def eq(forth):
    b = forth.pop()
    a = forth.pop()
    v = a == b
    forth.push(v)

@word_('<>')
def ne(forth):
    b = forth.pop()
    a = forth.pop()
    v = (a != b)
    forth.push(v)

# Branch

@word_()
def branch(forth):
    v = forth._next()
    forth._inc_pc(v)

@word_('0branch')
def zbranch(forth):
    c = forth.pop()
    v = forth._next()
    if not c:
        forth._inc_pc(v)

# Variable manipulation

@word_('!')
def store(forth):
    k = forth.pop()
    v = forth.pop()
    forth.dct[k] = v

@word_('@')
def fetch(forth):
    k = forth.pop()
    v = forth.dct[k]
    forth.push(v)

# return stack

@word_('>r')
def tor(forth):
    a = forth.pop()
    forth.rpush(a)

@word_('r>')
def fromr(forth):
    a = forth.rpop()
    forth.push(a)

@word_()
def rdrop(forth):
    return forth.rpop()

@word_()
def exit(forth):
    pc = forth.rpop()
    forth.pc = pc

# I/O

@word_()
def key(forth):
    '''Read a char from fin'''
    c = forth.fin.read(1)
    #c = ord(c)
    forth.push(c)

@word_()
def word(forth):
    '''Read a word from fin'''
    spaces = ' \t\n\f'

    while True:
        c = forth.fin.read(1)
        if (not c) or (c not in spaces):
            break
    w = c
    while True:
        c = forth.fin.read(1)
        if (not c) or (c in spaces):
            break
        w = w + c
    forth.push(w)

@word_()
def emit(forth):
    '''Write a char to fout'''
    c = forth.pop()
    if type(c) == int:
        c = chr(c)
    forth.fout.write(c)
    if c == '\n':
        forth.fout.flush()

# Interpreter

@word_()
def lit(forth):
    a = forth._next()
    forth.push(a)

@word_('`', imm=True)
def tick(forth):
    # Uses a trick reported by jonesforth from buzzard92
    # this tick only works in compiled code
    a = forth._next()
    forth.push(a)

@word_(',', imm=True)
def comma(forth):
    v = forth.pop()
    word = forth.last_word
    code = word.code
    code.append(v)

@word_('[', imm=True)
def lbrac(forth):
    forth.dct['forth_interpret'] = True

@word_(']', imm=True)
def rbrac(forth):
    forth.dct['forth_interpret'] = False

@word_()
def forth_interpret(forth):
    v = forth.dct['forth_interpret']
    forth.push(v)

@word_()
def is_immediate(forth):
    word = forth.pop()
    v = word.imm
    forth.push(v)

@word_()
def word_from_name(forth):
    name = forth.pop()
    v = forth._traduce(name)
    i = isinstance(v, Word)
    forth.push(v)
    forth.push(i)

@word_()
def create(forth):
    name = forth.pop()
    word = Word(name, [])
    forth._add_word(word)

@word_()
def immediate(forth):
    word = forth.last_word
    word.imm = True

@word_()
def exec_(forth):
    word = forth.pop()
    forth._exec(word)


end = Word('end', None)
bye = Word('bye', [end])
colon = Word(':', [word, create, rbrac, exit], imm=True)
semicolon = Word(';', [lit, exit, comma, lbrac, exit], imm=True)

interpret = Word('interpret',
                 [
                     lbrac,
                     # ini
                     word,                          # 0
                     dup, zbranch, 26,              # 1  --> exit
                     word_from_name,                # 4
                     zbranch, 12,                   # 5  --> lit
                     # is_word
                     dup, is_immediate,             # 7
                     forth_interpret,               # 9
                     or_, zbranch, 3,               # 10 --> wd_compile
                     # wd_interpret
                     exec_, branch, -16,            # 13 --> ini
                     # wd_compile
                     comma, branch, -19,            # 16 --> ini
                     # lit
                     forth_interpret,               # 19
                     zbranch, 2,                    # 20 --> lit_complie
                     # lit interpret
                     branch, -24,                   # 22 --> ini
                     # lit compile
                     tick, lit, comma, comma,       # 24
                     branch, -30,                   # 28 --> ini
                     # exit
                     drop, exit                     # 30
                 ])

init = Word('init', [interpret, exit])

if __name__ == '__main__':
    import io

    # inbuf = io.StringIO()
    #
    # def lexer(fin=sys.stdin):
    #     """ simple lexer to get one word at a time"""
    #     for l in fin.readline():
    #         yield from l.split()

    forth = Forth(debug=True)
