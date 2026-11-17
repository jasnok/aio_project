import json,re
from pathlib import Path
p=Path(__file__).parent; runs=p.parent/'runs'
perf=p/'PERF.md'
s=perf.read_text(encoding='utf-8-sig')
def bench(name):
 t=(runs/name).read_text();return re.search(r'p50 (.*?) · p95 (.*?) · max (.*?) · failures (.*)',t).groups()
b0=bench('lab02-baseline-bench.txt');b1=bench('lab02-stage1-bench.txt');bc=bench('lab02-cache-bench.txt');bn=bench('lab02-nocache-bench.txt');b3=bench('lab02-stage3-bench.txt')
rows=[('기준','3',b0,'lab01 4/4','없음'),('규칙 먼저','2',b1,'lab02 앞 네 케이스 통과','규칙 적용 범위 밖은 분류 필요'),('캐시 (같은 질문 두 번째)','0',bc,'lab02 9/9, lab01 4/4','최대 600초 오래된 FAQ 답'),('검토 → 검사 (과제 1)','1',b3,'lab02 9/9, lab01 4/4; challenge 보고서 참조','뜻·근거를 재검토하는 LLM 제거')]
for label,calls,b,test,loss in rows:
 pat=r'\| '+re.escape(label)+r' \|.*'
 repl=f'| {label} | {calls} | {b[0]} | {b[1]} | {test} | {loss} |'
 s=re.sub(pat,lambda m:repl,s)
s=re.sub(r'\| 캐시 씀 \|.*',lambda m:f'| 캐시 씀 | 2.33s | {bc[0]} | {bc[2]} | hits 4 · misses 1 |',s)
s=re.sub(r'\| 캐시 안 씀 \|.*',lambda m:f'| 캐시 안 씀 | '+re.search(r'#1 .*? ([0-9.]+s) ',(runs/'lab02-nocache-bench.txt').read_text()).group(1)+f' | {bn[0]} | {bn[2]} | 변화 없음 (4 · 1 유지) |',s)
s=s.replace('- 적중률 10% · 30%일 때 평균 어림:','- 적중률 10% · 30%일 때 평균 어림: 캐시 0.12초·미사용 2.29초 기준 2.073초 / 1.639초. 동일 질문 5회 조회 적중률은 4/5=80%. no_cache 요청은 조회하지 않으므로 통계에 포함되지 않음.')
perf.write_text(s,encoding='utf-8')
