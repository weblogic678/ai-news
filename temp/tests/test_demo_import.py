"""Failure and duplication guards using simulated services, not deployment tests."""
import importlib.util,json,sys,tempfile,unittest,subprocess
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2];SOURCE=ROOT/'temp/source-kits'
sys.path.insert(0,str(SOURCE/'dify-1.17.1/linux-x86'))
import demo_common as common

def module(tool):
 p=SOURCE/tool/'linux-x86/import-demo.py';s=importlib.util.spec_from_file_location(tool.replace('-','_'),p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
D=module('dify-1.17.1');N=module('n8n-2.42.6')
class Guards(unittest.TestCase):
 def test_loopback_only(self):
  for url in ('https://example.com','http://localhost@evil.com','http://localhost/path','http://localhost/?token=x'):
   with self.assertRaises(RuntimeError):D.local_url(url)
 def test_uncertain_dify_never_reposts(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)/'demo.yml';p.write_text('demo');state={'workflows':{}}
   class Client:
    def request(self,*args):raise TimeoutError('fixture timeout')
   with self.assertRaises(TimeoutError):D.import_files(Client(),[p],state,Path(t)/'state.json')
   with self.assertRaises(RuntimeError):D.import_files(Client(),[p],state,Path(t)/'state.json')
   self.assertEqual(state['workflows'][p.name]['state'],'attempting')
 def test_completed_dify_reads_without_recreation(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)/'demo.yml';p.write_text('demo');calls=[]
   class Client:
    def request(self,path,payload=None):
     calls.append((path,payload));return {'status':'completed','app_id':'fixture'} if payload else {'id':'fixture'}
   state={'workflows':{}};D.import_files(Client(),[p],state,Path(t)/'state.json');D.import_files(Client(),[p],state,Path(t)/'state.json')
   self.assertEqual(sum(payload is not None for _,payload in calls),1)
 def test_checkpoint_excludes_concurrent_import(self):
  with tempfile.TemporaryDirectory() as t:
   with common.checkpoint(Path(t),'fixture'):
    with self.assertRaises(RuntimeError):
     with common.checkpoint(Path(t),'fixture'):pass
   self.assertFalse((Path(t)/'.demo-import.lock').exists())
 def test_n8n_missing_export_restarts_and_retains_uncertainty(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)/'demo.json';p.write_text(json.dumps({'name':'fixture','nodes':[],'connections':{}}));calls=[];payload=[]
   def compose(meta,runtime,args,stdin=None):calls.append(args);return 'n8n\n'
   def job(meta,runtime,entry,args,stdin=None):
    if stdin:payload.extend(json.loads(stdin))
    return '[]' if entry=='cat' else ''
   state={'workflows':{}}
   with patch.object(N,'compose',compose),patch.object(N,'job',job):
    with self.assertRaises(RuntimeError):N.import_files({'project':'fixture'},Path(t),[p],state,Path(t)/'state.json')
   self.assertIn(['up','-d','--pull','never','n8n'],calls);self.assertFalse(payload[0]['active']);self.assertEqual(len(payload[0]['id']),16)
   self.assertEqual(state['workflows'][p.name]['state'],'attempting')
 def test_timeout_removes_only_owned_helper(self):
  with patch.object(N,'compose',side_effect=subprocess.TimeoutExpired('fixture',180)),patch.object(N.subprocess,'run') as run:
   with self.assertRaises(subprocess.TimeoutExpired):N.job({},Path('.'),'node',[])
   args=run.call_args.args[0];self.assertEqual(args[:3],['docker','rm','-f']);self.assertTrue(args[3].startswith('ai-news-demo-helper-'));self.assertEqual(len(args),4)
class SessionChecks(unittest.TestCase):
 def test_dify_session_csrf_and_logout(self):
  import base64,threading
  from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
  seen=[]
  class Handler(BaseHTTPRequestHandler):
   def log_message(self,*args):pass
   def do_POST(self):
    payload=json.loads(self.rfile.read(int(self.headers.get('Content-Length','0'))));seen.append((self.path,payload,self.headers.get('X-CSRF-Token')))
    self.send_response(200)
    if self.path.endswith('/login'):self.send_header('Set-Cookie','csrf_token=fixture; Path=/')
    self.end_headers();self.wfile.write(b'{"result":"success"}')
  server=ThreadingHTTPServer(('127.0.0.1',0),Handler);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
  try:
   client=D.Client('http://127.0.0.1:'+str(server.server_port));client.login('fixture@example.invalid','fixture-password');client.request('/apps/imports',{'mode':'yaml-content'});client.close()
   self.assertEqual(base64.b64decode(seen[0][1]['password']).decode(),'fixture-password');self.assertEqual(seen[1][2],'fixture');self.assertEqual(list(client.cookies),[])
  finally:server.shutdown();server.server_close();thread.join()
 def test_n8n_repeat_verifies_without_second_import(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)/'demo.json';p.write_text(json.dumps({'name':'fixture','nodes':[],'connections':{}}));records={};imports=[];export_id=['']
   def compose(*args,**kwargs):return 'n8n\n'
   def job(meta,runtime,entry,args,stdin=None):
    if stdin:
     for x in json.loads(stdin):records[x['id']]=x
    if args[0]=='import:workflow':imports.append(args)
    if args[0]=='export:workflow':export_id[0]=next(x[5:] for x in args if x.startswith('--id='))
    return json.dumps([records[export_id[0]]]) if entry=='cat' else ''
   state={'workflows':{}}
   with patch.object(N,'compose',compose),patch.object(N,'job',job):
    N.import_files({'project':'fixture'},Path(t),[p],state,Path(t)/'state.json');N.import_files({'project':'fixture'},Path(t),[p],state,Path(t)/'state.json')
   self.assertEqual(len(imports),1);self.assertEqual(state['workflows'][p.name]['state'],'completed')
if __name__=='__main__':unittest.main()
