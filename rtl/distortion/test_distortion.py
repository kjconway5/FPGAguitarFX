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
         'soft_clipping',
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
         'soft_clipping',
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
    dut.softclip.value = 0

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
    dut.softclip.value = 0
    dut.in_signal.value = 0
    dut.threshold.value = 0
    await ClockCycles(dut.clk, 2)
    dut.rst.value = 0
    await ClockCycles(dut.clk, 1)

    # Apply stimulus
    thr = 5000
    dut.threshold.value = thr
    dut.softclip.value = 0

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
    dut.softclip.value = 0
    dut.in_signal.value = 0
    dut.threshold.value = 0
    await ClockCycles(dut.clk, 2)
    dut.rst.value = 0
    await ClockCycles(dut.clk, 1)

    # Apply stimulus
    thr = 5000
    dut.threshold.value = thr
    dut.softclip.value = 0

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
        
@cocotb.test()
async def soft_clipping(dut):
    """Hard-clip path passes through when |in| < threshold (softclip=0)."""
    
    SOFT_LUT = [
    -32767, -32759, -32751, -32742, -32734, -32724, -32714, -32704,
    -32693, -32682, -32670, -32658, -32645, -32631, -32617, -32602,
    -32586, -32570, -32552, -32534, -32516, -32496, -32475, -32453,
    -32431, -32407, -32382, -32356, -32329, -32300, -32270, -32239,
    -32206, -32172, -32136, -32098, -32059, -32018, -31975, -31930,
    -31882, -31833, -31781, -31727, -31670, -31611, -31549, -31484,
    -31417, -31346, -31272, -31194, -31113, -31028, -30940, -30847,
    -30751, -30650, -30544, -30434, -30319, -30199, -30074, -29943,
    -29806, -29664, -29515, -29360, -29199, -29030, -28855, -28672,
    -28481, -28283, -28076, -27861, -27638, -27405, -27163, -26911,
    -26650, -26379, -26097, -25805, -25501, -25187, -24861, -24523,
    -24173, -23811, -23436, -23049, -22649, -22236, -21809, -21369,
    -20915, -20448, -19967, -19472, -18963, -18440, -17904, -17353,
    -16789, -16211, -15619, -15014, -14397, -13766, -13123, -12468,
    -11801, -11122, -10433, -9734, -9025, -8306, -7580, -6845,
    -6103, -5355, -4600, -3841, -3078, -2312, -1542, -772,
    0, 772, 1542, 2312, 3078, 3841, 4600, 5355,
    6103, 6845, 7580, 8306, 9025, 9734, 10433, 11122,
    11801, 12468, 13123, 13766, 14397, 15014, 15619, 16211,
    16789, 17353, 17904, 18440, 18963, 19472, 19967, 20448,
    20915, 21369, 21809, 22236, 22649, 23049, 23436, 23811,
    24173, 24523, 24861, 25187, 25501, 25805, 26097, 26379,
    26650, 26911, 27163, 27405, 27638, 27861, 28076, 28283,
    28481, 28672, 28855, 29030, 29199, 29360, 29515, 29664,
    29806, 29943, 30074, 30199, 30319, 30434, 30544, 30650,
    30751, 30847, 30940, 31028, 31113, 31194, 31272, 31346,
    31417, 31484, 31549, 31611, 31670, 31727, 31781, 31833,
    31882, 31930, 31975, 32018, 32059, 32098, 32136, 32172,
    32206, 32239, 32270, 32300, 32329, 32356, 32382, 32407,
    32431, 32453, 32475, 32496, 32516, 32534, 32552, 32570,
    32586, 32602, 32617, 32631, 32645, 32658, 32670, 32682,
    32693, 32704, 32714, 32724, 32734, 32742, 32751, 32759 ]
    
    assert len(SOFT_LUT) == 256


    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())

    # Reset
    dut.rst.value = 1
    dut.in_signal.value = 0
    dut.threshold.value = 0
    dut.softclip.value = 1   # enable softclip path
    await ClockCycles(dut.clk, 2)
    dut.rst.value = 0
    await ClockCycles(dut.clk, 1)

    # Pick values that change the upper byte so we hit lots of LUT addresses
    vectors = [
        0, 1, -1,
        127, -128,
        255, 256, -256, -257,
        0x0100, 0x01FF,   # upper = 0x01
        0x7FFF, -0x8000,  # extremes
        -1000, 1000,
        12345, -12345,
    ]

    for x in vectors:
        dut.in_signal.value = x

        await RisingEdge(dut.clk)
        await Timer(1, units="ps")

        got = dut.out_signal.value.signed_integer
        x16 = x & 0xFFFF
        upper = (x16 >> 8) & 0xFF
        addr = (upper + 128) & 0xFF
        exp = SOFT_LUT[addr]

        assert got == exp, (
            f"softclip_lut_test: in={x}, expected={exp}, got={got}, "
            f"t={get_sim_time(units='ns')} ns"
        )