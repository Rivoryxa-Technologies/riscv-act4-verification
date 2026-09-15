# Recorded clean proof — 2026-09-15

This directory contains raw logs from one clean Linux ARM64 reproduction. No
ELFs, HEX files, simulator binaries, or private source trees are included.

The source repositories and ACT4 build image are the immutable revisions in
`../../pins.json`. The executed stages were equivalent to `../../reproduce.sh`:

1. `generation.log`: pinned ACT4 image, `make clean`, then the pinned CV32E40P
   ACT4 configuration. It completed 470 build actions and produced the exact 94
   names in `../../expected-tests.txt` (`real 6m22.587s`; first-use Ruby/UDB
   installation is included).
2. `build.log`: `setup.py workspace --build` using Verilator 5.020. It rebuilt
   the RTL simulator and wrote `build-provenance.json` (`real 48.613s`).
3. `run.log` and `run-20260915T061653Z-5599/`: every ELF was converted to its
   consumed HEX and executed. The summary records 94 passes, zero failures,
   source/tool hashes, per-test hashes, and timings (`real 6.368s`).

The runner verified that the simulator hash matched `build-provenance.json`.
Individual simulation logs contain the unmodified DUT output and exact ACT4
result marker.
