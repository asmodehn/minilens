
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


@pytest.mark.parametrize("dict, init_stack, input, output, end_stack",[
    (hexaforth_0_1.dict_prototype, b"", b"abc", b"", b"abc"),
    (hexaforth_0_1.dict_prototype, b"", b".a", hexaforth_0_1.StackUnderflow, b""),
        (hexaforth_0_1.dict_prototype, b"", b"b.a", b"b", b"a"),
        (hexaforth_0_1.dict_prototype, b"", b"a.b.", b"ab", b""),
        (hexaforth_0_1.dict_prototype, b"", b"ab..", b"ba", b""),
        (hexaforth_0_1.dict_prototype, b"", b"ab.", b"b", b"a"),
        (hexaforth_0_1.dict_prototype, b"", b"...", hexaforth_0_1.StackUnderflow, b""),
    ])
def test_eval(dict, init_stack, input, output, end_stack):
    # prepare the stack
    stack = bytearray(init_stack)

    # check the output
    if isinstance(output, type) and issubclass(output, Exception):
        if output is not hexaforth_0_1.StackUnderflow:
            raise NotImplementedError
        with pytest.raises(output) as first_error:
            hexaforth_0_1.eval(dctn=dict, stck=stack, astr=input)

        retry_stack = bytearray(first_error.value.snap.stack)
        retry_input = first_error.value.snap.last_input
        # on error, a replay from snapshot data is enough to simulate again if needed

        with pytest.raises(output) as second_error:
            hexaforth_0_1.eval(dctn=dict, stck=retry_stack, astr=retry_input)

        assert second_error.value == first_error.value  # exact same error in the exact same way
        # except for the local traceback in this test which shows the exact same information
        # even if inside python it's 2 execution -> actual traceback entries are different
        assert all(str(stb) == str(ftb) for stb in second_error.traceback[1:] for ftb in first_error.traceback[1:])
    else:
        assert hexaforth_0_1.eval(dctn=dict, stck=stack, astr=input) == output

    # check the stack
    assert bytes(stack) == end_stack


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


# TODO : find a way to test pygment lexer...


@pytest.mark.parametrize(
    "input, expected_completions",
    [
        ("a", [".", "a", "b", "c"]),
        ("cba", [".", "a", "b", "c"]),
        (".", []),  # error means no completions (but error ignored in completer)
        ("cba...", ["a", "b", "c"]),
    ],
)
def test_machine_completer(input, expected_completions):

    m = hexaforth_0_1.Machine()

    # testing completer for this input (including ordering !)
    assert expected_completions == [
        comp.text
        for comp in m.completer.get_completions(
            Document(input, cursor_position=len(input)), "unused_complete_event"
        )
    ]


@pytest.mark.parametrize(
    "input, expected_validation",
    [
        ("a",  None),
        ("cba",  None),
        (".", ValidationError(message="StackUnderflow: b'' > b'.' @ 0")),
        ("cba...", None),
        ("cba....", ValidationError(message="StackUnderflow: b'' > b'cba....' @ 6")),
    ],
)
def test_machine_validator(input, expected_validation):

    m=hexaforth_0_1.Machine()

    if expected_validation is None:
        assert m.validator.validate(
            Document(input, cursor_position=len(input))
        ) is None
    else:
        with pytest.raises(type(expected_validation)) as raised:
            m.validator.validate(
                Document(input, cursor_position=len(input))
            )
        assert raised.value.args == expected_validation.args


# We can now test the prompt session
from prompt_toolkit.input import Input, create_pipe_input
from prompt_toolkit.output import DummyOutput, Output


@pytest.mark.parametrize(
    "input, expected_completions, expected_validation",
    [
        ("a", [".", "a", "b", "c"], None),
        ("cba", [".", "a", "b", "c"], None),
        (".", [], ValidationError(message="StackUnderflow: b'' > b'.' @ 0")),
        ("cba...", ["a", "b", "c"], None),
        ("cba....", [], ValidationError(message="StackUnderflow: b'' > b'cba....' @ 6")),
        ("cb\na", [".", "a", "b", "c"], None),  # validating that \n in bytes is supported in test
        ("cb\na....", [], ValidationError(message="StackUnderflow: b'cb' > b'a....' @ 4")),
    ],
)
def test_prompt_session(input, expected_completions, expected_validation):
    with create_pipe_input() as inp:

        m = hexaforth_0_1.Machine(
            input=inp,
            output=DummyOutput()
        )

        yeast_session = m.prompt_session()

        if expected_validation is None:
            assert yeast_session.validator.validate(
                Document(input, cursor_position=len(input))
            ) is None

            # split input into multiple prompt calls if needed, simulating user interactivity
            for snip in input.split("\n"):
                # Only actually send text when valid (otherwise prompt never terminates)
                inp.send_text(snip + "\n")  # forcing \n to get result
                result = yeast_session.prompt()

                assert result == snip  # no direct modification of the input by prompt(), only consumption of the last "\n"

        else:
            # verify validation is correct (no input possible). Note this also includes "interpreting" newlines.
            with pytest.raises(type(expected_validation)) as raised:
                yeast_session.validator.validate(
                    Document(input, cursor_position=len(input))
                )
            assert raised.value.args == expected_validation.args


if __name__ == "__main__":
    pytest.main(["-sv", __file__])
