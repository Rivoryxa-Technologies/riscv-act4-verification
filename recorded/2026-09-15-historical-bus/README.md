# Historical timer bus reproduction

A fresh local clone of harness revision `13172ba` fetched upstream independently and ran `python3 historical/run.py` on 15 September 2026. The complete fourteen-outcome matrix passed: two ordinary cases pass before and after; five targeted cases fail with their required diagnostics before and pass after. Two targeted cases read both timer halves through the public response bus against a model driven only by bus writes and clock cycles. The others localize timer state and demonstrate the spurious interrupt.

The runner verified commit ancestry, the exact changed-file set, and the pinned upstream diff hash. The summary records commit metadata, source/harness/simulator/log hashes, commands, versions, and timings. All recorded log hashes were independently checked against the summary. Compiler and simulation logs and the upstream patch are retained here. This public bundle omits generated RTL and simulator binaries; a newly executed run retains them in its unique evidence directory.

The upstream fix was authored by karabambus, not Rivoryxa. This is an independent regression on verification-platform RTL, not a discovered core defect or an ACT test running on a CPU. See `../../historical/README.md` for cause and scope. Absolute paths identify the temporary checkout used for this run; the runner works from other directories.
