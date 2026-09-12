"""Integration checks for safe output handling and actual resumed day equivalence."""
import json
import subprocess
import sys
import numpy as np
import model as m

def main():
    result={}
    frozen={str(p):m.digest(p) for p in (m.BASE/'smoke').glob('*.json')}
    run=subprocess.run([sys.executable,'-X','utf8','run.py','--days','1','--output','smoke'],cwd=m.BASE,capture_output=True,text=True,encoding='utf-8')
    result['nonempty_rejected']=run.returncode!=0 and 'output not empty' in run.stderr
    result['rejection_preserves_files']=all(m.digest(m.Path(p))==h for p,h in frozen.items())
    # Deliberately incompatible signature in an isolated test fixture.
    fixture=m.BASE/'tests/bad_signature'; fixture.mkdir(parents=True,exist_ok=True)
    (fixture/'signature.json').write_text('{}',encoding='utf-8')
    run=subprocess.run([sys.executable,'-X','utf8','run.py','--resume','--output','tests/bad_signature'],cwd=m.BASE,capture_output=True,text=True,encoding='utf-8')
    result['incompatible_signature_rejected']=run.returncode!=0 and 'signature mismatch' in run.stderr
    same=True
    for d in [31,32]:
        with np.load(m.BASE/'smoke/days'/f'{d:03d}.npz') as resumed,np.load(m.BASE/'results/days'/f'{d:03d}.npz') as straight:
            same &= set(resumed.files)==set(straight.files)
            for key in resumed.files:
                if key!='metadata': same &= np.array_equal(resumed[key],straight[key])
    result['actual_resume_matches_uninterrupted']=bool(same)
    payload=dict(passed=sum(result.values()),total=len(result),checks=result)
    (m.BASE/'tests/recovery_checks.json').write_text(json.dumps(payload,indent=2),encoding='utf-8')
    print(payload)
    assert all(result.values())

if __name__=='__main__': main()
