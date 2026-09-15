#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Run the exact CV32E40P ACT4 ELF matrix and retain auditable evidence."""
import argparse, hashlib, json, os, platform, re, shutil, signal, subprocess, time
from pathlib import Path

ROOT=Path(__file__).resolve().parent; EXPECTED=94
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def tool_version(name):
    path=shutil.which(name)
    if not path: return {"path":None,"version":None}
    try:
        p=subprocess.run([path,"--version"],text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=10)
        version=p.stdout.splitlines()[0] if p.stdout else "unknown"
    except (OSError,subprocess.TimeoutExpired) as e: version=type(e).__name__
    return {"path":path,"version":version}
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("workspace",type=Path); ap.add_argument("--timeout",type=float,default=120); ap.add_argument("--evidence-dir",type=Path,default=ROOT/"evidence"); a=ap.parse_args()
    if not (a.timeout>0 and a.timeout<float("inf")): ap.error("timeout must be positive and finite")
    ws=a.workspace.resolve(); sim=ws/"dv/sim/core/simulation_results/certification_rv32imc/verilator_executable"; elfroot=ws/"act4/work/cv32e40p-v2-rv32imc/elfs"
    pins=json.loads((ROOT/"pins.json").read_text()); paths={"riscv-arch-test":ws/"act4","cv32e40p-dv-review":ws/"dv","cv32e40p":ws/"core","core-v-verif":ws/"core-v-verif"}
    errors=[]; actual={}
    for name,path in paths.items():
        try: actual[name]=subprocess.check_output(["git","rev-parse","HEAD"],cwd=path,text=True,timeout=10).strip()
        except Exception as e: errors.append(f"cannot inspect {name}: {e}")
        if actual.get(name)!=pins[name]["commit"]: errors.append(f"pin mismatch: {name}")
    elfs=sorted(elfroot.rglob("*.elf"));
    if len(elfs)!=EXPECTED: errors.append(f"expected {EXPECTED} ELFs, found {len(elfs)}")
    if not sim.is_file(): errors.append(f"missing simulator: {sim}")
    if errors: print("ERROR: "+"; ".join(errors)); return 2
    out=a.evidence_dir.resolve()/(time.strftime("run-%Y%m%dT%H%M%SZ",time.gmtime())+f"-{os.getpid()}"); (out/"logs").mkdir(parents=True)
    cases=[]
    for i,elf in enumerate(elfs,1):
        start=time.monotonic(); timed=False
        proc=subprocess.Popen([str(sim),f"+elf_file={elf}"],cwd=out,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,start_new_session=True)
        try: text,_=proc.communicate(timeout=a.timeout)
        except subprocess.TimeoutExpired:
            timed=True; os.killpg(proc.pid,signal.SIGKILL); text,_=proc.communicate(); text += "\nTIMEOUT\n"
        rel=str(elf.relative_to(elfroot)); markers=re.findall(r"RVCP-SUMMARY: TEST (PASSED|FAILED)",text); ok=proc.returncode==0 and not timed and markers==["PASSED"]
        log=out/"logs"/(rel.replace("/","__")+".log"); log.write_text(text)
        cases.append({"test":rel,"sha256":sha(elf),"exit":proc.returncode,"seconds":round(time.monotonic()-start,6),"timed_out":timed,"markers":markers,"pass":ok,"log":str(log.relative_to(out))})
        print(f"[{i:02d}/{EXPECTED}] {'PASS' if ok else 'FAIL'} {rel}")
    integration_files=[ws/"dv/tb/core/cv32e40p_dut_wrap.sv",ws/"dv/tb/core/tb_top.sv",ws/"dv/tb/core/mm_ram.sv"]
    summary={"schema_version":1,"scope":"CV32E40P v2 RV32IMC ACT4 integration matrix","expected_tests":EXPECTED,"pass":sum(x["pass"] for x in cases),"fail":sum(not x["pass"] for x in cases),"ok":all(x["pass"] for x in cases),"pins":actual,"platform":platform.platform(),"python":platform.python_version(),"tools":{n:tool_version(n) for n in ("git","make","verilator","riscv64-unknown-elf-gcc","sail_riscv_sim")},"simulator_sha256":sha(sim),"integration_source_sha256":{str(p.relative_to(ws)):sha(p) for p in integration_files},"cases":cases}
    (out/"summary.json").write_text(json.dumps(summary,indent=2)+"\n"); print(out/"summary.json"); return 0 if summary["ok"] else 1
if __name__=="__main__": raise SystemExit(main())
