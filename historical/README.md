# A timer write that creates a spurious interrupt

This is an independent reproduction of an **upstream historical verification-platform defect**, not a new Rivoryxa discovery or a CV32E40P core defect. The original fix was authored upstream by `karabambus` and merged in [OpenHW PR #16](https://github.com/openhwgroup/cv32e40p-dv-review/pull/16).

The actual `mm_ram` module implements memory, virtual peripherals, the interrupt generator, and a 64-bit machine timer used by the core testbench. Its timer increments every clock. Software can write either 32-bit half through the data bus. The upstream correction defines a timer write as suppressing that cycle's increment, including any carry into the other half.

Before [0011274](https://github.com/openhwgroup/cv32e40p-dv-review/commit/001127416802a6f346aff3dde08e91d2b9f86958), a low-half write at `0xffffffff` also incremented the untouched high half. With the compare value at `0x00000001_00000000`, replacing the low half with `0x20` could spuriously assert the timer interrupt. A high-half write also incorrectly incremented the untouched low half. Ordinary low writes away from rollover and normal free-running carry both pass on that old revision.

## Reproduce

Requirements: Python 3, Git, Verilator with `--binary` and `--timing`, make, and a C++ compiler. This focused reproduction does not require Docker, ACT generation, or a RISC-V compiler.

```sh
python3 -m unittest discover -s tests -v
python3 historical/run.py
```

The runner fetches the upstream repository if `workspace/dv` is absent. It extracts each of four unchanged RTL sources directly from the exact historical commits using `git show`. It does not rewrite the RTL or change an existing checkout. Each variant compiles the real `mm_ram`, dual-port RAM, and grant/response stall modules with the same testbench and simulator options.

| Scenario | Before, `1726d147` | After, `00112741` |
| --- | --- | --- |
| Ordinary low write and increment | Pass | Pass |
| Free-running low-to-high carry | Pass | Pass |
| Low write on the carry boundary | `LOW_WRITE_CARRY_FAILED` | Pass |
| High write preserves low half | `HIGH_WRITE_HOLD_FAILED` | Pass |
| Carry-boundary write must not assert MTIP | `SPURIOUS_TIMER_IRQ_FAILED` | Pass |

All setup uses public bus writes. No timer state is forced or backdoor-initialized. The monitor observes internal timer state for localization and checks the public interrupt output for the resulting functional symptom. Each required diagnostic is checked exactly; timeout, compilation failure, or unrelated failure cannot satisfy an expected failing case. Source hashes, commands, tool version, timings, compile logs, simulator logs, and the complete ten-outcome matrix are saved to a new evidence directory.

## Why this is useful, and its limits

The failure depends on the relationship between a split-register write, counter carry, and level-sensitive interrupt generation. A normal timer smoke test misses it. The test is short because it sets up that boundary deliberately; its value comes from the interaction it isolates, not the number of RTL lines.

This is a directed module-level simulation of verification-platform RTL. It is not an ACT test executed on the CPU, a discovered processor defect, a formal proof, a complete peripheral test, or a production client result. It reproduces only the timer-write part of the upstream commit, not the separate platform-register read correction. RAM data paths, random stalls, byte-write semantics, and debug generation are not covered here. The separate 94-test ACT4 integration remains unchanged.

The upstream files retain their original copyright and Solderpad/Apache licence notices when fetched. Rivoryxa's contribution here is the new focused regression, failure classification, and recorded independent reproduction.
