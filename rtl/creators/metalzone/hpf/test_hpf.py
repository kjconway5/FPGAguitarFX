import git
import os
import sys
import git

# I don't like this, but it's convenient.
_REPO_ROOT = git.Repo(search_parent_directories=True).working_tree_dir
assert os.path.exists(_REPO_ROOT), "REPO_ROOT path must exist"
sys.path.append(os.path.join(_REPO_ROOT, "util"))
from utilities import runner, lint, assert_resolvable
tbpath = os.path.dirname(os.path.realpath(__file__))

import pytest

import cocotb

from cocotb.clock import Clock
from cocotb.utils import get_sim_time
from cocotb.triggers import Timer, ClockCycles, RisingEdge

from pytest_utils.decorators import max_score, visibility, tags

timescale = "1ps/1ps"

tests = [
    "init_test",
    "zero_input",
    "step_response_positive_decay",
    "step_response_negative_decay",
    "valid_hold",
    "dc_rejection",
]


@pytest.mark.parametrize("test_name", tests)
@pytest.mark.parametrize("simulator", ["verilator", "icarus"])
@max_score(0)
def test_each(test_name, simulator):
    # This line must be first
    parameters = dict(locals())
    del parameters["test_name"]
    del parameters["simulator"]
    runner(simulator, timescale, tbpath, parameters, testname=test_name)


@pytest.mark.parametrize("simulator", ["verilator"])
@max_score(0.4)
def test_lint(simulator):
    # This line must be first
    parameters = dict(locals())
    del parameters["simulator"]
    lint(simulator, timescale, tbpath, parameters)


@pytest.mark.parametrize("simulator", ["verilator"])
@max_score(0.1)
def test_style(simulator):
    # This line must be first
    parameters = dict(locals())
    del parameters["simulator"]
    lint(
        simulator,
        timescale,
        tbpath,
        parameters,
        compile_args=["--lint-only", "-Wwarn-style", "-Wno-lint"],
    )


@pytest.mark.parametrize("simulator", ["verilator", "icarus"])
@max_score(1)
def test_all(simulator):
    # This line must be first
    parameters = dict(locals())
    del parameters["simulator"]
    runner(simulator, timescale, tbpath, parameters)


### Begin Tests ###

tests = [
    "init_test",
    "zero_input",
    "step_response_positive_decay",
    "step_response_negative_decay",
    "valid_hold",
    "dc_rejection",
]


WIDTH = 24
SHIFT = 6


def wrap_signed(val, width=WIDTH):
    mask = (1 << width) - 1
    val &= mask
    if val & (1 << (width - 1)):
        val -= (1 << width)
    return val


def hpf_model(prev_out, prev_in, line_in):
    """
    Python reference model for:
        diff     = line_in - prev_line_in
        sum      = prev_line_out + diff
        temp_out = sum - (sum >>> SHIFT)
    """
    diff = wrap_signed(line_in - prev_in)
    sum_val = wrap_signed(prev_out + diff)
    temp_out = wrap_signed(sum_val - (sum_val >> SHIFT))
    return temp_out


@cocotb.test()
async def init_test(dut):
    """Basic connectivity + reset behavior."""

    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())

    dut.reset.value = 1
    dut.valid.value = 0
    dut.line_in.value = 0

    await ClockCycles(dut.clk, 2)

    dut.reset.value = 0
    await RisingEdge(dut.clk)
    await Timer(1, units="ps")

    assert_resolvable(dut.line_out)

    got = dut.line_out.value.signed_integer
    assert got == 0, (
        f"init_test: expected line_out=0 after reset, got {got} "
        f"at {get_sim_time(units='ns')} ns"
    )


@cocotb.test()
async def zero_input(dut):
    """If input stays at 0, output should remain at 0."""

    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())

    dut.reset.value = 1
    dut.valid.value = 0
    dut.line_in.value = 0
    await ClockCycles(dut.clk, 2)

    dut.reset.value = 0
    dut.valid.value = 1

    for i in range(8):
        dut.line_in.value = 0
        await RisingEdge(dut.clk)
        await Timer(1, units="ps")

        got = dut.line_out.value.signed_integer
        assert got == 0, (
            f"zero_input[{i}]: expected 0, got {got} "
            f"at {get_sim_time(units='ns')} ns"
        )


@cocotb.test()
async def step_response_positive_decay(dut):
    """Positive step should create a transient that decays toward zero."""

    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())

    dut.reset.value = 1
    dut.valid.value = 0
    dut.line_in.value = 0
    await ClockCycles(dut.clk, 2)

    dut.reset.value = 0
    dut.valid.value = 1

    x = 8000
    expected_prev_out = 0
    expected_prev_in = 0

    for i in range(10):
        dut.line_in.value = x

        expected = hpf_model(expected_prev_out, expected_prev_in, x)

        await RisingEdge(dut.clk)
        await Timer(1, units="ps")

        got = dut.line_out.value.signed_integer
        assert got == expected, (
            f"step_response_positive_decay[{i}]: expected {expected}, got {got} "
            f"for input {x} at {get_sim_time(units='ns')} ns"
        )

        expected_prev_out = expected
        expected_prev_in = x


@cocotb.test()
async def step_response_negative_decay(dut):
    """Negative step should create a transient that decays toward zero."""

    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())

    dut.reset.value = 1
    dut.valid.value = 0
    dut.line_in.value = 0
    await ClockCycles(dut.clk, 2)

    dut.reset.value = 0
    dut.valid.value = 1

    x = -8000
    expected_prev_out = 0
    expected_prev_in = 0

    for i in range(10):
        dut.line_in.value = x

        expected = hpf_model(expected_prev_out, expected_prev_in, x)

        await RisingEdge(dut.clk)
        await Timer(1, units="ps")

        got = dut.line_out.value.signed_integer
        assert got == expected, (
            f"step_response_negative_decay[{i}]: expected {expected}, got {got} "
            f"for input {x} at {get_sim_time(units='ns')} ns"
        )

        expected_prev_out = expected
        expected_prev_in = x


@cocotb.test()
async def valid_hold(dut):
    """When valid=0, output/state should hold constant."""

    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())

    dut.reset.value = 1
    dut.valid.value = 0
    dut.line_in.value = 0
    await ClockCycles(dut.clk, 2)

    dut.reset.value = 0
    dut.valid.value = 1
    dut.line_in.value = 8000

    model_prev_out = 0
    model_prev_in = 0

    for i in range(4):
        expected = hpf_model(model_prev_out, model_prev_in, 8000)

        await RisingEdge(dut.clk)
        await Timer(1, units="ps")

        got = dut.line_out.value.signed_integer
        assert got == expected, (
            f"valid_hold setup[{i}]: expected {expected}, got {got} "
            f"at {get_sim_time(units='ns')} ns"
        )

        model_prev_out = expected
        model_prev_in = 8000

    held_value = model_prev_out

    dut.valid.value = 0
    for i, x in enumerate([0, -12000, 12000, -3000]):
        dut.line_in.value = x

        await RisingEdge(dut.clk)
        await Timer(1, units="ps")

        got = dut.line_out.value.signed_integer
        assert got == held_value, (
            f"valid_hold[{i}]: expected held output {held_value}, got {got} "
            f"when valid=0 and line_in={x} at {get_sim_time(units='ns')} ns"
        )


@cocotb.test()
async def dc_rejection(dut):
    """Constant input should decay toward zero through the HPF."""

    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())

    dut.reset.value = 1
    dut.valid.value = 0
    dut.line_in.value = 0
    await ClockCycles(dut.clk, 2)

    dut.reset.value = 0
    dut.valid.value = 1

    x = 8000
    prev_mag = None

    for i in range(20):
        dut.line_in.value = x

        await RisingEdge(dut.clk)
        await Timer(1, units="ps")

        got = dut.line_out.value.signed_integer
        mag = abs(got)

        if prev_mag is not None:
            assert mag <= prev_mag, (
                f"dc_rejection[{i}]: expected decay toward zero, "
                f"but magnitude grew from {prev_mag} to {mag} "
                f"at {get_sim_time(units='ns')} ns"
            )

        prev_mag = mag