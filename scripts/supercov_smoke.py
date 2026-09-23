#!/usr/bin/env python3
"""Run before/after/failing Node tests through the optional evidence adapter."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from supercov_evidence import collect


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--supercov', required=True);p.add_argument('--out',required=True);a=p.parse_args()
    root=Path(a.out).resolve();root.mkdir(parents=True,exist_ok=False)
    (root/'src').mkdir();(root/'test').mkdir()
    (root/'.gitignore').write_text('.supercov/\n.artifacts/\n')
    (root/'package.json').write_text('{"name":"factory-smoke","private":true,"type":"module"}\n')
    (root/'src/price.js').write_text("export function price(qty) { if (qty < 0) throw new Error('negative'); return qty >= 10 ? qty * 8 : qty * 10; }\n")
    test=root/'test/price.test.js'
    test.write_text("import {test} from 'node:test';\nimport assert from 'node:assert/strict';\nimport {price} from '../src/price.js';\ntest('regular price', () => assert.equal(price(2), 20));\n")
    def git(*args):subprocess.run(['git','-C',str(root),*args],check=True,capture_output=True)
    git('init','-q');git('add','.');git('-c','user.name=Fixture','-c','user.email=f@example.invalid','commit','-qm','smoke fixture')
    results={}
    for stage in ('before','after','failed'):
        if stage=='after':
            test.write_text(test.read_text()+"test('discount', () => assert.equal(price(10), 80));\ntest('negative', () => assert.throws(() => price(-1), /negative/));\n")
        if stage=='failed':
            test.write_text(test.read_text()+"test('deliberate failure', () => assert.equal(price(2), 999));\n")
        results[stage]=collect(root,str(Path(a.supercov).absolute()),root/'.artifacts'/stage,['node','--test'],120)
    assert results['before']['coverage']['branches']['percentage']==50
    assert results['after']['coverage']['branches']['percentage']==100
    assert results['failed']['test_status']=='failed'
    assert results['failed']['coverage']['branches']['percentage']==100
    summary={k:{'branches':v['coverage']['branches'],'test_status':v['test_status'],'run_id':v['run_id']} for k,v in results.items()}
    (root/'.artifacts/acceptance.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary))

if __name__=='__main__':main()
