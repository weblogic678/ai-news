"""Read-only local reachability evidence. Does not execute workflows or call models."""
import datetime,json,platform,subprocess,sys,urllib.request,urllib.parse
from pathlib import Path
from demo_common import check_kit,save
BASE=Path(__file__).resolve().parent
class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):return None

def rows(text):
    try:
        value=json.loads(text)
        return value if isinstance(value,list) else [value]
    except ValueError:return [json.loads(line) for line in text.splitlines() if line.strip()]

def inspect(meta,runtime,run=subprocess.run,opener=None):
    # Keep errors generic: Docker diagnostics can contain paths or deployment details.
    report={'checked_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'tool':meta['tool'],'bundle_version':meta['version'],'platform':platform.system(),'scope':'Local Docker/HTTP reachability only; workflow execution, backup restoration, model calls and listing approval NOT verified','checks':{},'services':[],'runtime_reachability_passed':False,'listing_allowed':False}
    try:
        r=run(['docker','info','--format','{{.ServerVersion}}'],capture_output=True,text=True,check=True,timeout=20)
        report['checks']['docker_daemon']=True
    except (OSError,subprocess.SubprocessError):
        report['checks']['docker_daemon']=False;return report
    try:
        expected=run(['docker','compose','--project-name',meta['project'],'config','--services'],cwd=runtime,capture_output=True,text=True,check=True,timeout=30).stdout.splitlines()
        r=run(['docker','compose','--project-name',meta['project'],'ps','--all','--format','json'],cwd=runtime,capture_output=True,text=True,check=True,timeout=30)
        for item in rows(r.stdout):
            report['services'].append({key:item.get(key) for key in ('Service','State','Health','ExitCode','Image')})
        def ready(x):
            if meta['tool']=='dify' and x['Service']=='init_permissions':return x['State']=='exited' and x['ExitCode']==0
            return x['State']=='running' and x['Health'] in ('',None,'healthy')
        report['checks']['containers_running']=bool(expected) and set(expected)=={x['Service'] for x in report['services']} and all(ready(x) for x in report['services'])
    except (OSError,ValueError,subprocess.SubprocessError):report['checks']['containers_running']=False
    url=meta['url'];u=urllib.parse.urlsplit(url)
    if u.scheme not in ('http','https') or u.hostname not in ('localhost','127.0.0.1','::1') or u.username or u.password or u.path not in ('','/') or u.query or u.fragment:
        raise RuntimeError('Manifest URL must be a plain loopback URL.')
    opener=opener or urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect())
    try:
        with opener.open(urllib.request.Request(url,headers={'Accept':'text/html'}),timeout=15) as response:
            report['checks']['local_http_200']=response.status==200
            response.read(1024) # No response content, cookies or credentials stored in report.
    except (OSError,ValueError):report['checks']['local_http_200']=False
    report['runtime_reachability_passed']=all(report['checks'].values())
    return report

def main():
    meta=json.loads((BASE/'manifest.json').read_text());meta,runtime=check_kit(BASE,meta['tool'])
    report=inspect(meta,runtime);dest=runtime/'local-verification.json';save(dest,report)
    print(json.dumps(report,ensure_ascii=False,indent=2));print('Report:',dest)
    return 0 if report['runtime_reachability_passed'] else 1
if __name__=='__main__':
    try:sys.exit(main())
    except (RuntimeError,OSError,ValueError):print('FAILED: install this kit first and check its local manifest/runtime.',file=sys.stderr);sys.exit(1)
