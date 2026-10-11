"""Import bundled draft workflows into a LOCAL Dify 1.17.1 installation.
Uses the version's console endpoints, not a supported stable public automation API.
Login password and cookies remain in memory. No model requests are made.
"""
import argparse,base64,getpass,http.cookiejar,json,sys,urllib.error,urllib.parse,urllib.request
from pathlib import Path
from demo_common import check_kit,checkpoint,digest,existing,save

BASE=Path(__file__).resolve().parent

def local_url(value):
    p=urllib.parse.urlsplit(value)
    if p.scheme not in ('http','https') or p.hostname not in ('localhost','127.0.0.1','::1') or p.username or p.password or p.path not in ('','/') or p.query or p.fragment:
        raise RuntimeError('Use a loopback URL only. For a remote host, establish an SSH tunnel first.')
    _=p.port
    return value.rstrip('/')

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):return None

class Client:
    def __init__(self, url):
        self.url=local_url(url);self.cookies=http.cookiejar.CookieJar()
        self.opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),urllib.request.HTTPCookieProcessor(self.cookies),NoRedirect())

    def request(self,path,payload=None):
        csrf=next((c.value for c in self.cookies if c.name in ('csrf_token','__Host-csrf_token')),None)
        headers={'Accept':'application/json','Origin':self.url,'Referer':self.url+'/'}
        if csrf:headers['X-CSRF-Token']=csrf
        data=None
        if payload is not None:
            data=json.dumps(payload).encode();headers['Content-Type']='application/json'
        req=urllib.request.Request(self.url+'/console/api'+path,data=data,headers=headers)
        try:
            with self.opener.open(req,timeout=60) as r:
                return json.loads(r.read(2*1024*1024))
        except urllib.error.HTTPError as e:
            # Never echo a server response that might contain account or token information.
            raise RuntimeError(f'Dify returned HTTP {e.code}; use the browser to check setup, version and permissions.') from None

    def login(self,email,password):
        result=self.request('/login',{'email':email,'password':base64.b64encode(password.encode()).decode(),'remember_me':False})
        if result.get('result')!='success':raise RuntimeError('Login did not succeed. Check local administrator setup.')
        if not any(c.name in ('csrf_token','__Host-csrf_token') for c in self.cookies):raise RuntimeError('CSRF cookie missing; refusing import.')

    def close(self):
        try:self.request('/logout',{})
        except Exception:pass
        self.cookies.clear()

def import_files(client, paths, state, state_path):
    for file in paths:
        sha=digest(file);old=existing(state,file.name,sha)
        if old:
            app=client.request('/apps/'+urllib.parse.quote(old['app_id'],safe=''))
            if app.get('id')!=old['app_id']:raise RuntimeError('Recorded app is absent or inaccessible; manual inspection required.')
            print('Already imported:',file.name,old['app_id']);continue
        # Record BEFORE a non-idempotent POST. A timeout must not cause an automatic duplicate.
        state['workflows'][file.name]={'sha256':sha,'state':'attempting'};save(state_path,state)
        result=client.request('/apps/imports',{'mode':'yaml-content','yaml_content':file.read_text(encoding='utf-8')})
        status=result.get('status');app_id=result.get('app_id')
        if status not in ('completed','completed-with-warnings') or not isinstance(app_id,str) or not app_id:
            raise RuntimeError('Import not confirmed complete (possibly pending version confirmation). Inspect Dify; no auto retry.')
        state['workflows'][file.name].update(state=status,app_id=app_id);save(state_path,state)
        print('Created draft app:',file.name,app_id,'status:',status)
    print('Import complete. Workflows have NOT been executed or published. Configure model credentials locally before AI testing.')

def main():
    p=argparse.ArgumentParser();p.add_argument('--url',default='http://localhost:8080');p.add_argument('--include-ai',action='store_true');p.add_argument('--dry-run',action='store_true');args=p.parse_args()
    url=local_url(args.url);paths=[BASE/'workflows/01-smoke.yml']
    if args.include_ai:paths.append(BASE/'workflows/02-deepseek.yml')
    if args.dry_run:
        print('Plan: log in locally, create new draft apps (no overwrite), no execution or publishing.')
        for file in paths:print(file.name,digest(file))
        return
    _,runtime=check_kit(BASE,'dify')
    with checkpoint(runtime,'dify:'+url) as (state,state_path):
        # Refuse uncertain previous attempts before asking for any account details.
        for file in paths:existing(state,file.name,digest(file))
        client=Client(url)
        try:
            if not sys.stdin.isatty():raise RuntimeError('Use an interactive terminal for hidden password entry; piped input is refused.')
            email=input('Local Dify administrator email: ').strip()
            password=getpass.getpass('Local Dify password (hidden, not saved): ')
            client.login(email,password);password=''
            import_files(client,paths,state,state_path)
        finally:client.close()

if __name__=='__main__':
    try:main()
    except (RuntimeError,OSError,ValueError,urllib.error.URLError) as e:
        print('FAILED:',str(e),file=sys.stderr);sys.exit(1)
