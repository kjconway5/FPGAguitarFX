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

    # Hold reset for a couple cycles
    await ClockCycles(dut.clk, 2)

    # Release reset
    dut.rst.value = 0
    await RisingEdge(dut.clk)
    await Timer(1, units="ps")

    # Now the output MUST be valid
    assert_resolvable(dut.out_signal)

@cocotb.test()
async def soft_clipping(dut):
    """Hard-clip path passes through when |in| < threshold (softclip=0)."""
    
    SOFT_LUT = [
        -8388607, 
        -8386611, -8384521, -8382330, -8380035, -8377630, -8375111, -8372472, -8369707, -8366810, -8363775, -8360596, 
        -8357265, -8353776, -8350121, -8346293, -8342282, -8338082, -8333682, -8329073, -8324245, -8319189, -8313894, 
        -8308348, -8302540, -8296458, -8290088, -8283418, -8276433, -8269120, -8261462, -8253445, -8245051, -8236263, 
        -8227063, -8217433, -8207352, -8196801, -8185758, -8174201, -8162106, -8149449, -8136206, -8122350, -8107854, 
        -8092690, -8076827, -8060236, -8042885, -8024740, -8005767, -7985930, -7965193, -7943516, -7920861, -7897186, 
        -7872448, -7846603, -7819605, -7791408, -7761963, -7731218, -7699124, -7665625, -7630669, -7594197, -7556152, 
        -7516474, -7475103, -7431977, -7387031, -7340201, -7291420, -7240620, -7187734, -7132692, -7075422, -7015855, 
        -6953919, -6889540, -6822648, -6753170, -6681033, -6606167, -6528499, -6447961, -6364483, -6277998, -6188441, 
        -6095749, -5999862, -5900722, -5798276, -5692473, -5583268, -5470621, -5354494, -5234859, -5111690, -4984971,
        -4854691, -4720847, -4583443, -4442493, -4298018, -4150050, -3998627, -3843801, -3685631, -3524187, -3359548, 
        -3191805, -3021059, -2847421, -2671013, -2491966, -2310421, -2126529, -1940450, -1752352, -1562414, -1370818, 
        -1177757, -983428, -788033, -591780, -394881, -197549,
        0, 
        197549, 394881, 591780, 788033, 983428, 1177757,
        1370818, 1562414, 1752352, 1940450, 2126529, 2310421, 2491966, 2671013, 2847421, 3021059, 3191805,
        3359548, 3524187, 3685631, 3843801, 3998627, 4150050, 4298018, 4442493, 4583443, 4720847, 4854691,
        4984971, 5111690, 5234859, 5354494, 5470621, 5583268, 5692473, 5798276, 5900722, 5999862, 6095749, 
        6188441, 6277998, 6364483, 6447961, 6528499, 6606167, 6681033, 6753170, 6822648, 6889540, 6953919,
        7015855, 7075422, 7132692, 7187734, 7240620, 7291420, 7340201, 7387031, 7431977, 7475103, 7516474, 
        7556152, 7594197, 7630669, 7665625, 7699124, 7731218, 7761963, 7791408, 7819605, 7846603, 7872448, 
        7897186, 7920861, 7943516, 7965193, 7985930, 8005767, 8024740, 8042885, 8060236, 8076827, 8092690,
        8107854, 8122350, 8136206, 8149449, 8162106, 8174201, 8185758, 8196801, 8207352, 8217433, 8227063, 
        8236263, 8245051, 8253445, 8261462, 8269120, 8276433, 8283418, 8290088, 8296458, 8302540, 8308348, 
        8313894, 8319189, 8324245, 8329073, 8333682, 8338082, 8342282, 8346293, 8350121, 8353776, 8357265, 
        8360596, 8363775, 8366810, 8369707, 8372472, 8375111, 8377630, 8380035, 8382330, 8384521, 8386611]
    
    assert len(SOFT_LUT) == 256


    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())

    # Reset
    dut.rst.value = 1
    dut.in_signal.value = 0
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
        # Interpret x as a signed 24-bit sample (two's complement wrap)
        x24 = x & 0xFFFFFF
        upper = (x24 >> 16) & 0xFF          # bits [23:16]
        addr = (upper + 128) & 0xFF
        exp = SOFT_LUT[addr]

        assert got == exp, (
            f"softclip_lut_test: in={x}, expected={exp}, got={got}, "
            f"t={get_sim_time(units='ns')} ns"
        )