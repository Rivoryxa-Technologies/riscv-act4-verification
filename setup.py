#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Clone pinned upstreams and wire an isolated CV32E40P ACT4 workspace."""
import argparse, json, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PINS = json.loads((ROOT / "pins.json").read_text())

def run(*cmd, cwd=None):
    print("+", " ".join(map(str, cmd)))
    subprocess.run(list(map(str, cmd)), cwd=cwd, check=True)

def main():
    p = argparse.ArgumentParser()
    p.add_argument("workspace", type=Path)
    p.add_argument("--generate", action="store_true", help="generate the 94 ACT4 ELFs")
    p.add_argument("--build", action="store_true", help="build the Verilator RTL simulator")
    a = p.parse_args(); ws = a.workspace.resolve()
    ws.mkdir(parents=True, exist_ok=True)
    names = {"riscv-arch-test":"act4", "cv32e40p-dv-review":"dv", "cv32e40p":"core", "core-v-verif":"core-v-verif"}
    for key, dest in names.items():
        path = ws / dest; pin = PINS[key]
        if not path.exists(): run("git", "clone", "--filter=blob:none", pin["url"], path)
        run("git", "fetch", "origin", pin["commit"], cwd=path)
        run("git", "checkout", "--detach", pin["commit"], cwd=path)
        if subprocess.run(["git","diff","--quiet"], cwd=path).returncode: raise SystemExit(f"dirty checkout: {path}")
    dv = ws / "dv"
    for link, target in ((dv/"core-v-cores/cv32e40p", ws/"core"), (dv/"vendor_lib/openhwgroup_core-v-verif", ws/"core-v-verif"), (dv/"vendor_lib/riscv-arch-test/act4", ws/"act4")):
        link.parent.mkdir(parents=True, exist_ok=True)
        if not link.exists(): link.symlink_to(target)
    # Small integration needed by this testbench revision: expose debug_req and
    # the non-PULP core parameter. Checked replacements fail closed on drift.
    replacements = {
      dv/"tb/core/cv32e40p_dut_wrap.sv": [
        ("parameter FPU_EN            = 0)", "parameter FPU_EN            = 0,\n      parameter COREV_PULP        = 0)"),
        ("output logic [4:0]                   irq_id_o\n", "output logic [4:0]                   irq_id_o,\n    input logic debug_req_i\n"),
        (".PULP_XPULP      (0)", ".PULP_XPULP      (COREV_PULP)"), (".COREV_PULP      (0)", ".COREV_PULP      (COREV_PULP)"),
        (".debug_req_i         (1'b0)", ".debug_req_i         (debug_req_i)")],
      dv/"tb/core/tb_top.sv": [
        ("parameter FPU_EN            = 0\n", "parameter FPU_EN            = 0,\n      parameter COREV_PULP        = 0\n"),
        ("logic                   core_rst_n;", "logic                   core_rst_n;\n    logic                   debug_req;"),
        (".FPU_EN            (FPU_EN))", ".FPU_EN            (FPU_EN),\n        .COREV_PULP        (COREV_PULP))"),
        (".irq_id_o       (irq_id));", ".irq_id_o       (irq_id),\n       .debug_req_i    (debug_req));"),
        (".debug_req_o    (),", ".debug_req_o    (debug_req),")]
    }
    for path, edits in replacements.items():
        text = path.read_text()
        for old, new in edits:
            if new in text: continue
            if old not in text: raise SystemExit(f"integration context changed: {path}: {old!r}")
            text = text.replace(old, new)
        path.write_text(text)
    if a.generate:
        run("make", "CONFIG_FILES=config/cores/cve4/cv32e40p-v2-rv32imc/test_config.yaml", cwd=ws/"act4")
    if a.build: run("make", "verilate", "CV_CORE_CONFIG=rv32imc", "TEST=certification_rv32imc", cwd=dv/"sim/core")
    print(ws)
if __name__ == "__main__": main()
