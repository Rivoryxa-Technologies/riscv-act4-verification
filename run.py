#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Run the exact CV32E40P ACT4 ELF matrix and retain auditable evidence."""
import argparse, hashlib, json, os, platform, re, shutil, signal, subprocess, time
from pathlib import Path

ROOT=Path(__file__).resolve().parent
EXPECTED_NAMES=tuple(x for x in (ROOT/"expected-tests.txt").read_text().splitlines() if x)
EXPECTED=len(EXPECTED_NAMES)
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def tool_version(name):
    path=shutil.which(name)
    if not path: return {"path":None,"version":None}
    try:
        p=subprocess.run([path,"--version"],text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=10)
        version=p.stdout.splitlines()[0] if p.stdout else "unknown"
    except (OSError,subprocess.TimeoutExpired) as e: version=type(e).__name__
    return {"path":path,"version":version}
def case_pass(returncode,timed_out,markers):
    return returncode==0 and not timed_out and markers==["PASSED"]
def manifest_matches(names): return tuple(names)==EXPECTED_NAMES
def integration_diff_matches(diff,pins): return hashlib.sha256(diff).hexdigest()==pins["integration_diff_sha256"]
def regenerate_hex(objcopy,elf,hexfile,timeout):
    try:
        p=subprocess.run([objcopy,"-O","verilog",str(elf),str(hexfile)],text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=timeout)
    except (OSError,subprocess.TimeoutExpired) as e: raise RuntimeError(f"objcopy failed for {elf}: {e}") from e
    if p.returncode: raise RuntimeError(f"objcopy failed for {elf}: {p.stdout}")
def run_sim(cmd,cwd,timeout):
    try: proc=subprocess.Popen(cmd,cwd=cwd,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,start_new_session=True)
    except OSError as e: return 127,f"EXEC_ERROR: {e}\n",False
    try: text,_=proc.communicate(timeout=timeout); timed=False
    except subprocess.TimeoutExpired as exc:
        timed=True; os.killpg(proc.pid,signal.SIGKILL); remainder,_=proc.communicate()
        partial=exc.stdout or ""
        if isinstance(partial,bytes): partial=partial.decode(errors="replace")
        text=partial+(remainder or "")+"\nTIMEOUT\n"
    return proc.returncode,text,timed
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("workspace",type=Path); ap.add_argument("--timeout",type=float,default=120); ap.add_argument("--evidence-dir",type=Path,default=ROOT/"evidence"); ap.add_argument("--objcopy",default="riscv64-unknown-elf-objcopy"); a=ap.parse_args()
    if not (a.timeout>0 and a.timeout<float("inf")): ap.error("timeout must be positive and finite")
    ws=a.workspace.resolve(); sim=ws/"dv/sim/core/simulation_results/certification_rv32imc/verilator_executable"; elfroot=ws/"act4/work/cv32e40p-v2-rv32imc/elfs"
    pins=json.loads((ROOT/"pins.json").read_text()); paths={"riscv-arch-test":ws/"act4","cv32e40p-dv-review":ws/"dv","cv32e40p":ws/"core","core-v-verif":ws/"core-v-verif"}
    errors=[]; actual={}
    for name,path in paths.items():
        try: actual[name]=subprocess.check_output(["git","rev-parse","HEAD"],cwd=path,text=True,timeout=10).strip()
        except Exception as e: errors.append(f"cannot inspect {name}: {e}")
        if actual.get(name)!=pins[name]["commit"]: errors.append(f"pin mismatch: {name}")
        if name != "cv32e40p-dv-review" and actual.get(name)==pins[name]["commit"]:
            dirty=subprocess.run(["git","diff","--quiet","HEAD","--"],cwd=path).returncode
            if dirty: errors.append(f"tracked source modified: {name}")
    elfs=sorted(elfroot.rglob("*.elf")); names=tuple(str(x.relative_to(elfroot)) for x in elfs)
    if not manifest_matches(names): errors.append("ELF manifest mismatch (missing, extra, or renamed test)")
    if not sim.is_file(): errors.append(f"missing simulator: {sim}")
    objcopy=shutil.which(a.objcopy)
    if not objcopy: errors.append(f"missing objcopy: {a.objcopy}")
    try:
        diff=subprocess.check_output(["git","diff","--binary","HEAD","--"],cwd=ws/"dv")
        if not integration_diff_matches(diff,pins): errors.append("DUT integration diff mismatch")
    except Exception as e: errors.append(f"cannot verify integration diff: {e}")
    try:
        build=json.loads((ws/"build-provenance.json").read_text())
        if build.get("pins")!=actual or build.get("integration_diff_sha256")!=pins["integration_diff_sha256"] or build.get("simulator_sha256")!=sha(sim):
            errors.append("build provenance does not match sources or simulator")
    except Exception as e: errors.append(f"cannot verify build provenance: {e}")
    if errors: print("ERROR: "+"; ".join(errors)); return 2
    out=a.evidence_dir.resolve()/(time.strftime("run-%Y%m%dT%H%M%SZ",time.gmtime())+f"-{os.getpid()}"); (out/"logs").mkdir(parents=True)
    cases=[]
    for i,elf in enumerate(elfs,1):
        hexfile=elf.with_suffix(".hex")
        try: regenerate_hex(objcopy,elf,hexfile,a.timeout)
        except RuntimeError as e: print(e); return 1
        start=time.monotonic()
        returncode,text,timed=run_sim([str(sim),f"+elf_file={elf}"],out,a.timeout)
        rel=str(elf.relative_to(elfroot)); markers=re.findall(r"RVCP-SUMMARY: TEST (PASSED|FAILED)",text); ok=case_pass(returncode,timed,markers)
        log=out/"logs"/(rel.replace("/","__")+".log"); log.write_text(text)
        cases.append({"test":rel,"elf_sha256":sha(elf),"hex_sha256":sha(hexfile),"exit":returncode,"seconds":round(time.monotonic()-start,6),"timed_out":timed,"markers":markers,"pass":ok,"log":str(log.relative_to(out))})
        print(f"[{i:02d}/{EXPECTED}] {'PASS' if ok else 'FAIL'} {rel}")
    integration_files=[ws/"dv/tb/core/cv32e40p_dut_wrap.sv",ws/"dv/tb/core/tb_top.sv",ws/"dv/tb/core/mm_ram.sv"]
    summary={"schema_version":1,"scope":"CV32E40P v2 RV32IMC ACT4 integration matrix","expected_tests":EXPECTED,"pass":sum(x["pass"] for x in cases),"fail":sum(not x["pass"] for x in cases),"ok":all(x["pass"] for x in cases),"pins":actual,"build_provenance":build,"platform":platform.platform(),"python":platform.python_version(),"tools":{n:tool_version(n) for n in ("git","make","verilator","riscv64-unknown-elf-gcc","sail_riscv_sim")},"simulator_sha256":sha(sim),"integration_source_sha256":{str(p.relative_to(ws)):sha(p) for p in integration_files},"cases":cases}
    (out/"summary.json").write_text(json.dumps(summary,indent=2)+"\n"); print(out/"summary.json"); return 0 if summary["ok"] else 1
if __name__=="__main__": raise SystemExit(main())
