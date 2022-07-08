
from typing import Optional, Type

import pytest
from prompt_toolkit.document import Document
from prompt_toolkit.validation import ValidationError

import hexaforth_0_1


def test_snapshot():

    # Creating a new machine with empty initial stack
    snap = hexaforth_0_1.Snapshot(stack=b"abc",
                                     last_input=b"c.....",
                                     cursor_position=4)

    assert snap.stack == b"abc"
    assert snap.last_input == b"c....."
    assert snap.cursor_position == 4

    # attributes are read-only
    with pytest.raises(AttributeError):
        snap.stack = 42

    with pytest.raises(AttributeError):
        snap.last_input = 42

    with pytest.raises(AttributeError):
        snap.cursor_position = 42


def test_metamachine_dict():

    class CustomMachine(metaclass=hexaforth_0_1.MetaMachine):

        def __init__(self, initial_stack: Optional[bytes] = None):
            self.stack = bytearray() if initial_stack is None else bytearray(initial_stack)


    # instantiate a machine with its own stack
    machine1 = CustomMachine()
    machine2 = CustomMachine()

    # verify we have a dictionnary initialized properly, the same in machine1 and machine2
    assert machine1.dict == machine2.dict
    assert len(machine1.dict) == len(machine2.dict) == 4

    # it is not shared and each instance can mutate it
    topop = [k for k in machine1.dict.keys()]
    for k in topop:
        machine1.dict.pop(k)

    assert len(machine1.dict) == 0
    assert len(machine2.dict) == 4

    # but new machines will get a clean new dict
    machine3 = CustomMachine()
    assert machine3.dict == machine2.dict


def test_metamachine_repr():

    class CustomMachine(metaclass=hexaforth_0_1.MetaMachine):
        pass

    assert repr(CustomMachine) == "<class 'test_metamachine_repr.<locals>.CustomMachine' {.abc}>"


@pytest.mark.parametrize(
    "stack, ch_input, ch_output, next_result_or_except",
    [
        (b"", ord(b"a"), None, b"a"),
        (b"", ord(b"b"), None, b"b"),
        (b"", ord(b"."), None, IndexError),  # Error: this dot cannot be used !
        (b"c", ord(b"a"), None, b"ca"),
        (b"c", ord(b"b"), None, b"cb"),
        (b"c", ord(b"."), ord(b"c"), b""),  # dot is evaluated
    ],
)
def test_machine_dict(
    stack: bytes, ch_input: int, ch_output: int, next_result_or_except: bytes | Type[Exception]
):
    # global stack for using Machine.dict implementations
    test_stack = bytearray(stack)

    if isinstance(next_result_or_except, type):
        if not issubclass(next_result_or_except, Exception):
            raise NotImplementedError
        with pytest.raises(next_result_or_except):
            hexaforth_0_1.Machine.dict[ch_input](test_stack, ch_input)
    else:
        if ch_output is None:
            assert hexaforth_0_1.Machine.dict[ch_input](test_stack, ch_input) is None
        else:
            assert hexaforth_0_1.Machine.dict[ch_input](test_stack, ch_input) == ch_output
        # verify stack status after eval
        assert test_stack == bytearray(next_result_or_except)


@pytest.mark.parametrize(
    "b_input, b_expected, b_stack",
    [
        (b"abc", b"", b"abc"),
        (b".a", hexaforth_0_1.StackUnderflow, b""),
        (b"b.a", b"b", b"a"),
        (b"a.b.", b"ab", b""),
        (b"ab..", b"ba", b""),
        (b"ab.", b"b", b"a"),
        (b"...", hexaforth_0_1.StackUnderflow, b""),
    ],
)
def test_machine_call(b_input, b_expected, b_stack):

    # Creating a new machine with empty initial stack
    machine = hexaforth_0_1.Machine()

    if isinstance(b_expected, type):
        if not issubclass(b_expected, Exception):
            raise NotImplementedError
        with pytest.raises(b_expected):
            machine(b_input)
    else:
        assert machine(b_input) == b_expected
    assert machine.stack == b_stack


@pytest.mark.parametrize(
    "b_input, b_expected, snapshot",
    [
        (b".a", hexaforth_0_1.StackUnderflow, hexaforth_0_1.Snapshot(
            stack=b"", last_input=b".a", cursor_position=0)),
        (b"...", hexaforth_0_1.StackUnderflow, hexaforth_0_1.Snapshot(
            stack=b"", last_input=b"...", cursor_position=0)),
    ],
)
def test_machine_call_snapshot(b_input, b_expected, snapshot):

    # Creating a new machine with empty initial stack
    machine = hexaforth_0_1.Machine()

    if isinstance(b_expected, type):
        if not issubclass(b_expected, Exception):
            raise NotImplementedError
        with pytest.raises(b_expected) as ctxt:
            machine(b_input)

        assert ctxt.value.snap == snapshot

    else:
        assert machine(b_input) == b_expected


def test_machine_repr():

    assert repr(hexaforth_0_1.Machine) == "<class 'Machine' {.abc}>"

    m = hexaforth_0_1.Machine(b"")

    # running something
    assert b"a" == m(b"a.b")

    # asserting stack state is in repr
    assert repr(m) == "<{.abc} Machine stack: b'b'>"


def test_machine_copy():

    machine = hexaforth_0_1.Machine()

    mc = machine.copy()

    assert mc.stack == machine.stack

    # do an operation on stack
    machine(b"a")

    assert mc.stack != machine.stack

    # do the same operation on hte copy to recover stack equality
    mc(b"a")

    assert mc.stack == machine.stack






@pytest.mark.parametrize(
    "b_input, b_expected",
    [
        (b"", [b"a", b"b", b"c"]),  # because ` would trigger error
        (
            b"a",
            [b".", b"a", b"b", b"c"],
        ),  # because ` is more useful to compress the input, and we can always add more chars
        (b".", []),  # because ` already triggers error
        (b"a.", [b"a", b"b", b"c"]),  # because ` would trigger error
    ],
)
def test_live_char_expect(b_input, b_expected):

    if isinstance(b_expected, type):
        if not issubclass(b_expected, Exception):
            raise NotImplementedError
        with pytest.raises(b_expected):
            hexaforth_0_1.live_char_expect(b_input)
    else:
        assert hexaforth_0_1.live_char_expect(b_input) == b_expected


# We can now test the prompt session
from prompt_toolkit.input import create_pipe_input
from prompt_toolkit.output import DummyOutput


@pytest.mark.parametrize(
    "input, expected_completions, expected_validation",
    [
        ("a", [".", "a", "b", "c"], None),
        ("cba", [".", "a", "b", "c"], None),
        (".", [], ValidationError(message="CStackUnderflow: pop from empty bytearray")),
        ("cba...", ["a", "b", "c"], None),
        ("cba....", [], ValidationError(message="CStackUnderflow: pop from empty bytearray")),
    ],
)
def test_prompt_session(input, expected_completions, expected_validation):
    with create_pipe_input() as inp:

        yeast_session = hexaforth_0_1.session(
            input=inp,
            output=DummyOutput(),
        )

        # testing validation for this input
        if isinstance(expected_validation, Exception):
            with pytest.raises(type(expected_validation)) as raised:
                yeast_session.validator.validate(
                    Document(input, cursor_position=len(input))
                )
            assert raised.value.args == expected_validation.args
            assert list(yeast_session.completer.get_completions(
                    Document(input, cursor_position=len(input)), "unused_complete_event"
                )) == expected_completions

        elif expected_validation is None:
            assert yeast_session.validator.validate(
                Document(input, cursor_position=len(input))
            ) is None

            # testing completer for this input (including ordering !)
            assert expected_completions == [
                comp.text
                for comp in yeast_session.completer.get_completions(
                    Document(input, cursor_position=len(input)), "unused_complete_event"
                )
            ]

            # Only actually send text when valid (otherwise prompt never terminates)
            inp.send_text(input + "\n")  # forcing \n to get result
            result = yeast_session.prompt()

            assert result == input  # no direct modification of the input

        else:
            raise NotImplementedError


if __name__ == "__main__":
    pytest.main(["-sv", __file__])
