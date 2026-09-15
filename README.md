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

Host prerequisites are Git, Python 3.10+, Make, Docker, Verilator, a C++
compiler, and `riscv64-unknown-elf-objcopy`. The upstream ACT4 README documents
the generation dependencies. The pinned Linux ARM64 ACT4 build image supplies
GCC 16.1.0, Sail 0.13.1, `uv`, and Ruby/Bundler. `setup.py` invokes no package
installer and does not use unpinned source branches.

```sh
git clone https://github.com/Rivoryxa-Technologies/riscv-act4-verification.git
./riscv-act4-verification/reproduce.sh
```

Both commands work from any current directory. Generation produces expected
results with the pinned Sail/UDB configuration; simulation executes those ELFs
on the pinned CV32E40P RTL. The runner exits 2 for setup or pin/count errors, 1
for any failed, missing, ambiguous, or timed-out result, and 0 only for 94/94.
`setup.py --build` records source pins, the complete allowed integration diff,
the Verilator version, and simulator hash in `build-provenance.json`; the runner
rejects a missing or mismatched record. Each run regenerates the Verilog HEX actually consumed by the testbench from
its paired ELF. It retains unique logs, ELF and HEX hashes, source commits, integration-source and
simulator hashes, available tool versions, wall times, and `summary.json` under
`evidence/`.

The corrected `mm_ram` at the pinned `cv32e40p-dv-review` revision implements
the ACT platform interrupt-generator address `0x15000024`. The setup script also
applies the narrow testbench wiring required to expose `debug_req` and the core
configuration parameter; it fails closed if upstream context differs.

## Licensing and provenance

This wrapper code is MIT licensed. It does not vendor upstream source or ACT
artifacts. Exact repositories, commits, and upstream license-file paths are recorded
in `pins.json`; the cloned projects retain their own copyright and license
files. Generated ELFs derive from the pinned ACT4 tests and Sail expectations.

## Limits

The current matrix is CV32E40P v2 RV32IMC only. It does not cover floating point,
other privilege configurations, other cores, formal verification, performance,
security, CDC, or physical implementation. The GitHub Actions full-proof job
runs clean generation, RTL build, all 94 simulations, and uploads evidence.
