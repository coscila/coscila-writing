#!/usr/bin/env python3
"""Execute all writing environments in an offline Bubblewrap sandbox.

Uses the deployment's declared read-only roots and base Python, with one
synthetic writable chat. It does not use credentials or existing chat data.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import tempfile

INNER = r'''
import json, os, subprocess
from pathlib import Path
home = Path(os.environ['OCSL_WRITING_HOME'])
state = Path(os.environ['OCSL_WRITING_STATE'])
workspace = Path.cwd()
launcher = str(home / 'bin/ocsl-writing')
checks = []
for root in [home, state / 'environment-templates', Path(os.environ['OCSL_WRITING_PYTHON']).parent.parent]:
    target = root / '.ocsl-writing-readonly-probe'
    try:
        with target.open('x') as handle:
            handle.write('unexpected writable mount')
    except OSError as error:
        assert error.errno == 30, (str(root), str(error))
    else:
        target.unlink()
        raise AssertionError('expected read-only mount: ' + str(root))
assert not (state / 'integration').exists(), 'operator migration state was exposed'
assert not Path('/local/phflot/miniconda3').exists(), 'host Python unexpectedly exposed'
for name, imports in [
    ('writing-core', 'import yaml,jsonschema,requests'),
    ('writing-documents', 'import docx,pypdf,fitz,pptx,PIL,bibtexparser,mammoth,pdfplumber,pypdfium2,openai,latex2mathml,playwright'),
    ('writing-figures', "import matplotlib; matplotlib.use('Agg'); import seaborn,numpy,pandas,scipy,plotly,PIL,skimage,fitz"),
    ('writing-mcp', 'import yaml,jsonschema,httpx,mcp,requests,toml,lxml,pybliometrics'),
]:
    result = subprocess.run([launcher, 'env', 'ensure', '--workspace', str(workspace), '--environment', name], capture_output=True, text=True, timeout=600)
    assert result.returncode == 0, result.stderr[-2000:]
    descriptor = json.loads(result.stdout)
    run = subprocess.run([launcher, 'env', 'run', '--workspace', str(workspace), '--environment', name, '--', 'python', '-c', imports], capture_output=True, text=True, timeout=180)
    assert run.returncode == 0, run.stderr[-2000:]
    verify = subprocess.run([launcher, 'env', 'verify', '--workspace', str(workspace), '--environment', name], capture_output=True, text=True, timeout=180)
    assert verify.returncode == 0, verify.stderr[-2000:]
    checks.append({'environment':name,'offlineEnsure':True,'imports':True,'verified':True})
(workspace / 'writing-output.txt').write_text('synthetic chat output')
print(json.dumps({'ok':True,'network':'unshared','sourceReadOnly':True,'templatesReadOnly':True,'basePythonReadOnly':True,'hostPythonHidden':True,'operatorIntegrationHidden':True,'chatWritable':True,'environments':checks}))
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--home', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--state', type=Path, default=Path('/local/science_lab_workspace/writing-state'))
    parser.add_argument('--python', type=Path, default=Path('/local/science_lab_workspace/conda-install/bin/python3'))
    parser.add_argument('--sandbox-config', type=Path, default=Path('/local/science_lab_workspace/runtime/sandbox.json'))
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    config = json.loads(args.sandbox_config.read_text())
    mounted = [args.home, args.state / 'environment-templates', args.python.parent.parent]
    assert all(str(p) in config['roRoots'] for p in mounted), 'required writing runtime root absent from staged sandbox'
    assert all(key in config['childEnvAllowlist'] for key in ['OCSL_WRITING_HOME','OCSL_WRITING_STATE','OCSL_WRITING_PYTHON'])
    with tempfile.TemporaryDirectory(prefix='ocsl-writing-sandbox-') as folder:
        chat = Path(folder) / 'chat'
        chat.mkdir()
        (chat / 'probe.py').write_text(INNER)
        command = ['bwrap', '--die-with-parent', '--new-session', '--unshare-all', '--clearenv']
        for source in ['/usr','/bin','/lib','/lib64','/etc']:
            if Path(source).exists():
                command += ['--ro-bind', source, source]
        command += ['--proc','/proc','--dev','/dev','--tmpfs','/tmp']
        for path in mounted:
            command += ['--ro-bind', str(path), str(path)]
        command += ['--bind',str(chat),str(chat),'--chdir',str(chat)]
        environment = {'HOME':str(chat),'PATH':str(args.python.parent)+':/usr/bin:/bin','LANG':'C.UTF-8',
                       'OCSL_WRITING_HOME':str(args.home),'OCSL_WRITING_STATE':str(args.state),
                       'OCSL_WRITING_PYTHON':str(args.python),'OCSL_WRITING_SANDBOX':'1',
                       'LAB_WORKSPACE_ROOT':str(chat),'PYTHONDONTWRITEBYTECODE':'1','PYTHONNOUSERSITE':'1'}
        for key,value in environment.items():
            command += ['--setenv',key,value]
        command += [str(args.python),str(chat/'probe.py')]
        result = subprocess.run(command,capture_output=True,text=True,timeout=1200)
        if result.returncode:
            receipt = {'ok':False,'error':result.stderr[-3500:]}
        else:
            receipt = json.loads(result.stdout)
        receipt['scope'] = 'Actual Bubblewrap execution with declared writing read-only roots and synthetic chat; separate provider-profile check covers discovery.'
        args.output.write_text(json.dumps(receipt,indent=2)+'\n')
        print(json.dumps(receipt))
        return 0 if receipt['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
