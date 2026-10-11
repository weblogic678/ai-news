import getpass,json,urllib.request,urllib.error
key=getpass.getpass('DeepSeek API Key (hidden): ')
if input('One API call may cost money. Type yes: ') != 'yes': raise SystemExit('Cancelled')
payload={'model':'deepseek-flash','messages':[{'role':'user','content':'请用一句话说明备份有什么用。'}],'stream':False}
req=urllib.request.Request('https://api.deepseek.com/chat/completions',data=json.dumps(payload).encode(),headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'})
try:
 with urllib.request.urlopen(req,timeout=120) as r: result=json.load(r)
 print(result['choices'][0]['message']['content'])
except urllib.error.HTTPError as e: print('HTTP',e.code,'Check key, balance, model, and limits; response body hidden.')
