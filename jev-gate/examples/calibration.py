#!/usr/bin/env python3
"""Prepare matched, synthetic change-risk cases. Labels stay outside requests."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import service
import catalog

CASES = [
 ('assertion_removed', 'test_weakened', True, 'assert.equal(total(2), 20);', 'total(2);'),
 ('assertion_retained', 'test_weakened', False, 'assert.equal(total(2), 20);', 'assert.equal(total(2), 20);\nassert.equal(total(0), 0);'),
 ('query_interpolated', 'injection_introduced', True, 'db.execute("SELECT * FROM users WHERE name = ?", [req.query.name]);', 'db.execute("SELECT * FROM users WHERE name = " + req.query.name);'),
 ('query_parameterized', 'injection_introduced', False, 'db.execute("SELECT * FROM users WHERE name = ?", [req.query.name]);', 'db.execute("SELECT id FROM users WHERE name = ?", [req.query.name]);'),
 ('password_literal', 'credential_embedded', True, 'authenticateWithPassword(process.env.DB_PASSWORD);', 'authenticateWithPassword("pw");'),
 ('password_environment', 'credential_embedded', False, 'authenticateWithPassword(process.env.DB_PASSWORD);', 'authenticateWithPassword(process.env.DATABASE_PASSWORD);'),
]


def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('--out',required=True);a=p.parse_args()
    root=Path(a.out).resolve(); root.mkdir(parents=True,exist_ok=False)
    repo=root/'fixture';repo.mkdir()
    def git(*args):subprocess.run(['git','-C',str(repo),*args],check=True,capture_output=True)
    git('init','-q')
    (repo/'provenance.txt').write_text('Synthetic nonfunctional examples for development only. No real credentials.\n')
    for index, (_,_,_,before,after) in enumerate(CASES):
        (repo/f'{index}-before.txt').write_text(before+'\n');(repo/f'{index}-after.txt').write_text(after+'\n')
    git('add','.');git('-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit','-qm','synthetic cases')
    rev=service.revision(repo)
    def src(path,role):
        data=(repo/path).read_bytes()
        return {'path':path,'sha256':service.digest(data),'start':1,'end':len(data.splitlines()),'role':role,'kind':'primary'}
    labels=[]
    for index,(name,question,label,_,_) in enumerate(CASES):
        manifest={'schema_version':1,'stage':'change-risk','revision':rev,'expected_units':['change'],
                  'required_checks':['fixture_provenance'],
                  'checks':[{'id':'fixture_provenance','status':'passed','revision':rev,'evidence':src('provenance.txt','result')}],
                  'units':[{'id':'change','subject':'Assess the supplied code change.','complete':True,'risk':'standard',
                            'sources':[src(f'{index}-before.txt','before'),src(f'{index}-after.txt','after')]}]}
        plan=service.pack(repo,manifest)
        for suffix,value in [('manifest',manifest),('plan',plan)]:
            (root/f'{index}-{suffix}.json').write_text(json.dumps(value,indent=2)+'\n')
        labels.append({'index':index,'name':name,'question':question,'adverse':label,'split':'development',
                       'plan_sha256':service.digest(service.canonical(plan))})
    (root/'oracle-labels.json').write_text(json.dumps({'synthetic':True,'catalog_version':catalog.VERSION,'cases':labels},indent=2)+'\n')
    print(json.dumps({'cases':len(labels),'live_calls':0,'directory':str(root)}))

if __name__=='__main__':main()
