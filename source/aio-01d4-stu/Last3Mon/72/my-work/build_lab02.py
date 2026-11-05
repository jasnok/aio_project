import json,copy,sys,uuid
from pathlib import Path
p=Path(__file__).parent
stage=int(sys.argv[1])
w=json.loads((p.parent/'reference'/('lab02-example1-rules.json' if stage==1 else 'lab02-example2-cache.json')).read_text(encoding='utf-8'))
w['name']='72 IT helpdesk (my)'
n={x['name']:x for x in w['nodes']}
def code(name,js):
 if name not in n:
  node={'name':name,'type':'n8n-nodes-base.code','typeVersion':2,'position':[1800,650],'parameters':{}}
  w['nodes'].append(node); n[name]=node
 n[name]['parameters']={'jsCode':js}
def link(name,*targets):
 w['connections'][name]={'main':[[{'node':t,'type':'main','index':0}] if t else [] for t in targets]}
def gate(name,expr):
 node=copy.deepcopy(n['Known?']);node['name']=name;node['parameters']['conditions']['conditions']=[{'id':name,'leftValue':'={{ '+expr+' }}','rightValue':'','operator':{'type':'boolean','operation':'true','singleValue':True}}]
 w['nodes'].append(node);n[name]=node
# Preserve timing checkpoints for separate data operations.
code('After FAQ',"return [{json:{...$json,t:Date.now()}}];")
link('Search FAQ','After FAQ');link('After FAQ','Get ticket')
if stage>=2:
 code('Cache key',n['Cache key']['parameters']['jsCode'].replace('body.no_cache !== true',"body.no_cache !== true && !/T-?\\d{4}/i.test(String(body.question ?? ''))"))
 gate('Use cache?',"$json.use_cache === true")
 link('Cache key','Use cache?');link('Use cache?','Cache lookup','Search FAQ')
 n['Cache lookup']['parameters']['options']['timeout']=2000
# Keep existing contract and count only traversed LLM nodes.
code('Build result',r"""const ran = name => {try{return $(name).isExecuted;}catch{return false;}};
const get = name => $(name).first().json;
const body=get('Question webhook').body;
const category=ran('Parse category')?get('Parse category').category:get('Rule classify').category;
const answer=String(ran('Review check')?get('Review check').answer:get('Review').output??'').trim();
const t0=get('Start clock').t; const timings={};let last=t0;
for(const [label,node] of [['faq','After FAQ'],['ticket','After data'],['classify','After classify'],['answer','After answer'],['review','After review'],['check','Review check']]){
 if(!ran(node))continue; const mark=get(node).t;timings[label+'_ms']=mark-last;last=mark;
}
timings.data_ms=(timings.faq_ms??0)+(timings.ticket_ms??0);
timings.total_ms=Date.now()-t0;
const llm_calls=['Classify','Answer','Review'].filter(ran).length;
const steps=['rule','faq','ticket'];if(ran('Classify'))steps.push('classify');steps.push('answer',ran('Review check')?'check':'review');
const budget_ms=Number(body.budget_ms??3000);
return [{json:{route:'자동 답변',category,answer,sources:category==='faq'?(get('Search FAQ').results??[]).map(r=>r.id):[],llm_calls,cached:false,steps,timings,slowest_step:Object.entries(timings).filter(([k])=>!['total_ms','data_ms'].includes(k)).sort((a,b)=>b[1]-a[1])[0]?.[0].replace('_ms',''),llm_ms:(timings.classify_ms??0)+(timings.answer_ms??0)+(timings.review_ms??0),budget_ms,over_budget:timings.total_ms>budget_ms,...(ran('Review check')?{review_problems:get('Review check').review_problems}:{})}}];""")
if stage>=3:
 remove={'Review','Review model','After review'}
 w['nodes']=[x for x in w['nodes'] if x['name'] not in remove]
 for name in remove:w['connections'].pop(name,None)
 code('Review check',r"""let answer=String($json.output??'').trim();const review_problems=[];if(!answer)review_problems.push('empty');if(!/[가-힣]/.test(answer))review_problems.push('not_korean');if(answer.length>400){answer=answer.slice(0,400);review_problems.push('too_long');}return [{json:{answer,review_problems,t:Date.now()}}];""")
 link('After answer','Review check');link('Review check','Build result')
 n['Answer']['parameters']['options']['systemMessage']+=' Use polite 합니다체, at most 3 short sentences and 400 characters. Preserve ticket status verbatim, especially 처리 중. Keep the FAQ key actions. Do not invent a ticket for an unavailable or unauthorized record.'
if stage>=4:
 code('FAQ cache key',"const rule=$('Rule classify').first().json; const first=$('Search FAQ').first().json.results?.[0];return [{json:{...rule,faq_key:rule.category==='faq' && $('Cache key').first().json.use_cache && first ? 'faq-'+first.id : null}}];")
 gate('Use FAQ cache?',"$json.faq_key !== null")
 lookup=copy.deepcopy(n['Cache lookup']);lookup['name']='FAQ cache lookup';lookup['parameters']['url']="=http://data-api:8800/cache/{{ encodeURIComponent($('FAQ cache key').first().json.faq_key) }}";w['nodes'].append(lookup);n[lookup['name']]=lookup
 gate('FAQ cached?',"$json.value !== undefined")
 code('Back to rule',"return [{json:$('Rule classify').first().json}];")
 code('FAQ cached result',"const value=$json.value;return [{json:{...value,llm_calls:0,cached:true,cache_by:'faq',steps:['faq','ticket','rule','cache'],timings:{total_ms:Date.now()-$('Start clock').first().json.t}}}];")
 link('Rule classify','FAQ cache key');link('FAQ cache key','Use FAQ cache?');link('Use FAQ cache?','FAQ cache lookup','Back to rule');link('FAQ cache lookup','FAQ cached?');link('FAQ cached?','FAQ cached result','Back to rule');link('Back to rule','Known?');link('FAQ cached result','Send cached')
 store=copy.deepcopy(n['Store in cache']);store['name']='Store by FAQ';store['parameters']['url']="=http://data-api:8800/cache/{{ encodeURIComponent($('FAQ cache key').first().json.faq_key) }}";store['parameters']['jsonBody']="={{ JSON.stringify({ value: { route: $('Build result').first().json.route, category: 'faq', answer: $('Build result').first().json.answer, sources: $('Build result').first().json.sources }, ttl: 600 }) }}";w['nodes'].append(store)
 link('Store in cache','Store by FAQ');link('Store by FAQ','Result again')
 code('Cached result',n['Cached result']['parameters']['jsCode'].replace('cached: true','cached: true, cache_by: \'question\''))
 code('Build result',n['Build result']['parameters']['jsCode'].replace('cached:false','cached:false,cache_by:null'))
if stage>=2:
 code('Result again',"const result=$('Build result').first().json;result.timings.total_ms=Date.now()-$('Start clock').first().json.t;result.over_budget=result.timings.total_ms>result.budget_ms;return [{json:result}];")
for i,node in enumerate(w['nodes']):
 node['id']=str(uuid.uuid5(uuid.NAMESPACE_URL,'day72-helpdesk/'+node['name']))
 if node['name'] in ['After FAQ','Use cache?','Review check','FAQ cache key','Use FAQ cache?','FAQ cache lookup','FAQ cached?','Back to rule','FAQ cached result','Store by FAQ']:node['position']=[(i%8)*260,800+(i//8)*200]
(p/'helpdesk.json').write_text(json.dumps(w,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('built stage',stage)

