# Lab 02 추가 계약 검사
# 최종 게시 후 실행: uv run --no-project python my-work/verify_cache.py
import json,urllib.request
from pathlib import Path
base='http://localhost:8800'
def req(url,body=None):
 data=None if body is None else json.dumps(body,ensure_ascii=False).encode()
 with urllib.request.urlopen(urllib.request.Request(url,data=data,headers={'Content-Type':'application/json'}),timeout=30) as r:return json.load(r)
req(base+'/cache-clear',{})
before=req(base+'/cache-stats')
body={'question':'VPN 접속이 자꾸 끊겨요. 어떻게 하나요?','no_cache':True}
result=req('http://localhost:5678/webhook/my-helpdesk',body)
after=req(base+'/cache-stats')
assert before==after,(before,after)
assert result['cached'] is False and result['llm_calls']==1,result
body=json.loads((Path(__file__).parent.parent/'requests/ticket-own.json').read_text())
result2=req('http://localhost:5678/webhook/my-helpdesk',body)
assert req(base+'/cache-stats')==after
assert result2['cached'] is False and result2['category']=='ticket'
report={'no_cache_before':before,'no_cache_after':after,'no_cache_result':result,'ticket_result':result2,'passed':True}
(Path(__file__).parent.parent/'runs/lab02-cache-contract.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print('PASS: no_cache and ticket skip both cache reads and writes')
