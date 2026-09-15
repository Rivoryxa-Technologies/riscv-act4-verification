#!/usr/bin/env python3
"""Reproduce an upstream timer write/carry fix using unchanged historical RTL."""
import argparse, hashlib, json, platform, re, subprocess, sys, time, uuid
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from run import run_sim
ROOT=Path(__file__).resolve().parents[1]
URL='https://github.com/openhwgroup/cv32e40p-dv-review.git'
REVISIONS={'before':'1726d14796601884d54d9b0f699128800e2dcf55',
           'after':'001127416802a6f346aff3dde08e91d2b9f86958'}
FILES=('tb/core/mm_ram.sv','tb/core/dp_ram.sv','tb/core/tb_riscv/riscv_rvalid_stall.sv','tb/core/tb_riscv/riscv_gnt_stall.sv')
CASES={'smoke':None,'carry_without_write':None,'low_write_at_carry':'LOW_WRITE_CARRY_FAILED',
       'high_write_holds_low':'HIGH_WRITE_HOLD_FAILED','spurious_timer_irq':'SPURIOUS_TIMER_IRQ_FAILED'}
def sha(data): return hashlib.sha256(data).hexdigest()
def accepted(variant,case,rc,text,timed):
    markers=re.findall(r'\b[A-Z_]+_FAILED\b',text)
    expected=CASES[case] if variant=='before' else None
    if timed: return False
    if expected:
        return rc not in (0,127) and markers==[expected] and 'HISTORICAL_PASS' not in text
    return rc==0 and not markers and re.findall(r'^HISTORICAL_PASS case=(\w+)$',text,re.M)==[case]

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--source',type=Path,default=ROOT/'workspace/dv')
    ap.add_argument('--evidence',type=Path,default=ROOT/'evidence')
    a=ap.parse_args(); source=a.source.resolve()
    out=a.evidence.resolve()/('historical-'+uuid.uuid4().hex[:12]);out.mkdir(parents=True)
    if not source.exists():
        subprocess.run(['git','clone','--filter=blob:none',URL,str(source)],check=True,timeout=180)
    report={'schema_version':1,'upstream':URL,'revisions':REVISIONS,'cases':[], 'builds':[],
            'platform':platform.platform(),'python':platform.python_version(),
            'bench_sha256':sha((ROOT/'historical/mm_ram_timer_tb.sv').read_bytes()),
            'runner_sha256':sha(Path(__file__).read_bytes()),
            'verilator':subprocess.check_output(['verilator','--version'],text=True).strip()}
    for variant,revision in REVISIONS.items():
        work=out/variant; work.mkdir(); paths=[]; hashes={}
        for name in FILES:
            data=subprocess.check_output(['git','show',revision+':'+name],cwd=source,timeout=30)
            target=work/Path(name).name; target.write_bytes(data);paths.append(str(target));hashes[name]=sha(data)
        command=['verilator','--binary','--timing','-Wno-fatal','--top-module','mm_ram_timer_tb',
                 '--Mdir',str(work/'obj'),*paths,str(ROOT/'historical/mm_ram_timer_tb.sv')]
        start=time.monotonic();rc,text,timed=run_sim(command,work,180)
        (work/'compile.log').write_text(text)
        report['builds'].append({'variant':variant,'revision':revision,'source_sha256':hashes,
                                'command':command,'exit':rc,'timed_out':timed,'seconds':time.monotonic()-start})
        if rc or timed: break
        binary=work/'obj/Vmm_ram_timer_tb'
        report['builds'][-1]['simulator_sha256']=sha(binary.read_bytes())
        for case in CASES:
            command=[str(binary),'+CASE='+case];start=time.monotonic()
            rc,text,timed=run_sim(command,work,15);(work/(case+'.log')).write_text(text)
            ok=accepted(variant,case,rc,text,timed)
            report['cases'].append({'variant':variant,'case':case,'command':command,'exit':rc,'timed_out':timed,
                                    'seconds':time.monotonic()-start,'accepted':ok,
                                    'expected_failure':CASES[case] if variant=='before' else None})
            print(variant,case,'EXPECTED' if ok else 'UNEXPECTED',flush=True)
    pairs=[(c['variant'],c['case']) for c in report['cases']]
    report['ok']=len(pairs)==10 and set(pairs)=={(v,c) for v in REVISIONS for c in CASES} and all(c['accepted'] for c in report['cases'])
    (out/'summary.json').write_text(json.dumps(report,indent=2)+'\n'); print(out)
    return 0 if report['ok'] else 1
if __name__=='__main__':sys.exit(main())
