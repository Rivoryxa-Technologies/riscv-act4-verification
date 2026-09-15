# CV32E40P ACT4 integration example

This repository reproduces an actual RTL run of the RISC-V ACT4 tests on the
OpenHW CV32E40P v2 RV32IMC configuration. It pins the ACT4 framework, DUT RTL,
testbench, and shared verification sources, then requires exactly 94 generated
self-checking ELFs and an exact `RVCP-SUMMARY: TEST PASSED` marker from every
RTL simulation.

ACTs are architectural certification tests, not a substitute for processor
verification. This result covers only the named configuration and pinned
source revisions. It is an integration result, not an endorsement or claim of
general RISC-V compliance or certification.

## Reproduce

Prerequisites are Git, Python 3.10+, Make, `uv`, Ruby/Bundler, a compatible
RISC-V GCC toolchain, Sail RISC-V 0.13.1, Verilator, and a C++ compiler. The
upstream ACT4 README documents these dependencies. `setup.py` invokes no package
installer and does not use unpinned source branches.

```sh
python3 setup.py ./workspace --generate --build
python3 run.py ./workspace
```

Both commands work from any current directory. Generation produces expected
results with the pinned Sail/UDB configuration; simulation executes those ELFs
on the pinned CV32E40P RTL. The runner exits 2 for setup or pin/count errors, 1
for any failed, missing, ambiguous, or timed-out result, and 0 only for 94/94.
Each run retains unique logs, ELF hashes, source commits, integration-source and
simulator hashes, available tool versions, wall times, and `summary.json` under
`evidence/`.

The corrected `mm_ram` at the pinned `cv32e40p-dv-review` revision implements
the ACT platform interrupt-generator address `0x15000024`. The setup script also
applies the narrow testbench wiring required to expose `debug_req` and the core
configuration parameter; it fails closed if upstream context differs.

## Licensing and provenance

This wrapper code is MIT licensed. It does not vendor upstream source or ACT
artifacts. Exact repositories, commits, and SPDX license families are recorded
in `pins.json`; the cloned projects retain their own copyright and license
files. Generated ELFs derive from the pinned ACT4 tests and Sail expectations.

## Limits

The current matrix is CV32E40P v2 RV32IMC only. It does not cover floating point,
other privilege configurations, other cores, formal verification, performance,
security, CDC, or physical implementation. Tool availability and clean build
time make this unsuitable as a lightweight hosted CI job; the checked workflow
validates the wrapper itself and documents how to run the full local proof.
