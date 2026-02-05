import git
import os
import sys
import git

# I don't like this, but it's convenient.
_REPO_ROOT = git.Repo(search_parent_directories=True).working_tree_dir
assert (os.path.exists(_REPO_ROOT)), "REPO_ROOT path must exist"
sys.path.append(os.path.join(_REPO_ROOT, "util"))
from utilities import runner, lint, assert_resolvable
tbpath = os.path.dirname(os.path.realpath(__file__))

import pytest

import cocotb

from cocotb.clock import Clock
from cocotb.regression import TestFactory
from cocotb.utils import get_sim_time
from cocotb.triggers import Timer, ClockCycles, RisingEdge, FallingEdge, with_timeout
from cocotb.types import LogicArray, Range

from cocotb_test.simulator import run

from cocotbext.axi import AxiLiteBus, AxiLiteMaster, AxiStreamSink, AxiStreamMonitor, AxiStreamBus

from pytest_utils.decorators import max_score, visibility, tags
   
timescale = "1ps/1ps"

tests =['init_test',
         'no_clipping',
         'hard_clipping',
         ]


@pytest.mark.parametrize("test_name", tests)
@pytest.mark.parametrize("simulator", ["verilator", "icarus"])
@max_score(0)
def test_each(test_name, simulator):
    # This line must be first
    parameters = dict(locals())
    del parameters['test_name']
    del parameters['simulator']
    runner(simulator, timescale, tbpath, parameters, testname=test_name)

@pytest.mark.parametrize("simulator", ["verilator"])
@max_score(.4)
def test_lint(simulator):
    # This line must be first
    parameters = dict(locals())
    del parameters['simulator']
    lint(simulator, timescale, tbpath, parameters)

@pytest.mark.parametrize("simulator", ["verilator"])
@max_score(.1)
def test_style(simulator):
    # This line must be first
    parameters = dict(locals())
    del parameters['simulator']
    lint(simulator, timescale, tbpath, parameters, compile_args=["--lint-only", "-Wwarn-style", "-Wno-lint"])

@pytest.mark.parametrize("simulator", ["verilator", "icarus"])
@max_score(1)
def test_all(simulator):
    # This line must be first
    parameters = dict(locals())
    del parameters['simulator']
    runner(simulator, timescale, tbpath, parameters)

### Begin Tests ###

tests = ['init_test',
         'no_clipping',
         'hard_clipping',
         ]

@cocotb.test()
async def init_test(dut):
    """Basic connectivity + reset behavior."""

    # Start clock
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())

    # Apply reset
    dut.rst.value = 1
    dut.in_signal.value = 0
    dut.threshold.value = 0

    # Hold reset for a couple cycles
    await ClockCycles(dut.clk, 2)

    # Release reset
    dut.rst.value = 0
    await RisingEdge(dut.clk)
    await Timer(1, units="ps")

    # Now the output MUST be valid
    assert_resolvable(dut.out_signal)


@cocotb.test()
async def no_clipping(dut):
    """Hard-clip path passes through when |in| < threshold (softclip=0)."""

    # Start a clock
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())

    # Reset
    dut.rst.value = 1
    dut.in_signal.value = 0
    dut.threshold.value = 0
    await ClockCycles(dut.clk, 2)
    dut.rst.value = 0
    await ClockCycles(dut.clk, 1)

    # Apply stimulus
    thr = 5000
    dut.threshold.value = thr

    for x in [0, 123, -123, 999, -999, 4000, -4000]:
        dut.in_signal.value = x

        # Wait for the registered output to update
        await RisingEdge(dut.clk)
        await Timer(1, units="ps")

        got = dut.out_signal.value.signed_integer
        assert got == x, (
            f"no_clipping: expected {x}, got {got} (thr={thr}) "
            f"at {get_sim_time(units='ns')} ns"
        )
        
@cocotb.test()
async def hard_clipping(dut):
    """Hard-clip path passes through when |in| < threshold (softclip=0)."""

    # Start a clock
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())

    # Reset
    dut.rst.value = 1
    dut.in_signal.value = 0
    dut.threshold.value = 0
    await ClockCycles(dut.clk, 2)
    dut.rst.value = 0
    await ClockCycles(dut.clk, 1)

    # Apply stimulus
    thr = 5000
    dut.threshold.value = thr

    for x in [0, 123, -123, 5001, -5001, 6000, -6000]:
        dut.in_signal.value = x
       
        if x > thr:
            expected = thr
        elif x < -thr:
            expected = -thr
        else:
            expected = x
       
        # Wait for the registered output to update
        await RisingEdge(dut.clk)
        await Timer(1, units="ps")

        got = dut.out_signal.value.signed_integer
        assert got == expected, (
            f"hard_clipping: expected {expected}, got {got} (thr={thr}) "
            f"at {get_sim_time(units='ns')} ns"
        )
        
