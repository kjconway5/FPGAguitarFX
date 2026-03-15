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
    "step_response_positive",
    "step_response_negative",
    "valid_hold",
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
    "step_response_positive",
    "step_response_negative",
    "valid_hold",
]

WIDTH = 24

def wrap_signed(val, width=WIDTH):
    mask = (1 << width) - 1
    val &= mask
    if val & (1 << (width - 1)):
        val -= (1 << width)
    return val

def lpf_model(prev_out, line_in):
    diff = wrap_signed(line_in - prev_out)
    scaled = wrap_signed(diff >> 4)
    temp_out = wrap_signed(prev_out + scaled)
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

    for _ in range(8):
        dut.line_in.value = 0
        await RisingEdge(dut.clk)
        await Timer(1, units="ps")

        got = dut.line_out.value.signed_integer
        assert got == 0, (
            f"zero_input: expected 0, got {got} "
            f"at {get_sim_time(units='ns')} ns"
        )


@cocotb.test()
async def step_response_positive(dut):
    """Positive step response should follow the LPF recurrence."""

    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())

    dut.reset.value = 1
    dut.valid.value = 0
    dut.line_in.value = 0
    await ClockCycles(dut.clk, 2)

    dut.reset.value = 0
    dut.valid.value = 1

    x = 8000
    expected_prev = 0

    for i in range(10):
        dut.line_in.value = x

        expected = lpf_model(expected_prev, x)

        await RisingEdge(dut.clk)
        await Timer(1, units="ps")

        got = dut.line_out.value.signed_integer
        assert got == expected, (
            f"step_response_positive[{i}]: expected {expected}, got {got} "
            f"for input {x} at {get_sim_time(units='ns')} ns"
        )

        expected_prev = expected


@cocotb.test()
async def step_response_negative(dut):
    """Negative step response should follow the LPF recurrence."""

    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())

    dut.reset.value = 1
    dut.valid.value = 0
    dut.line_in.value = 0
    await ClockCycles(dut.clk, 2)

    dut.reset.value = 0
    dut.valid.value = 1

    x = -8000
    expected_prev = 0

    for i in range(10):
        dut.line_in.value = x

        expected = lpf_model(expected_prev, x)

        await RisingEdge(dut.clk)
        await Timer(1, units="ps")

        got = dut.line_out.value.signed_integer
        assert got == expected, (
            f"step_response_negative[{i}]: expected {expected}, got {got} "
            f"for input {x} at {get_sim_time(units='ns')} ns"
        )

        expected_prev = expected


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

    # Let output move for a few valid cycles
    model_prev = 0
    for _ in range(4):
        expected = lpf_model(model_prev, 8000)

        await RisingEdge(dut.clk)
        await Timer(1, units="ps")

        got = dut.line_out.value.signed_integer
        assert got == expected, (
            f"valid_hold setup: expected {expected}, got {got} "
            f"at {get_sim_time(units='ns')} ns"
        )
        model_prev = expected

    held_value = model_prev

    # Drop valid, change input wildly, output should not change
    dut.valid.value = 0
    for x in [0, -12000, 12000, -3000]:
        dut.line_in.value = x

        await RisingEdge(dut.clk)
        await Timer(1, units="ps")

        got = dut.line_out.value.signed_integer
        assert got == held_value, (
            f"valid_hold: expected held output {held_value}, got {got} "
            f"when valid=0 and line_in={x} at {get_sim_time(units='ns')} ns"
        )