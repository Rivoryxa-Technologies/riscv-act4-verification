# Independent historical timer reproduction

A fresh local clone of harness revision `c06192f` fetched upstream independently and ran `python3 historical/run.py` on 15 September 2026. The complete ten-outcome matrix passed: two ordinary cases pass before and after; three targeted cases fail with their required diagnostics before and pass after. The summary records exact historical source hashes, harness hashes, simulator hashes, commands, versions, and timings. Compiler and simulation logs are retained here. Generated sources and binaries remain in the run directory and are reproduced by the command.

The upstream fix was authored upstream, not by Rivoryxa. This is an independent regression on verification-platform RTL, not a discovered core defect or a full ACT run. See `../../historical/README.md` for cause and scope. Absolute paths in logs identify the recorded temporary checkout; the documented runner is location independent.
