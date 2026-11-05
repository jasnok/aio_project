from pathlib import Path
import json

p = Path(__file__).parent
title, body = (p/'최종원고.txt').read_text(encoding='utf-8').strip().split('\n\n', 1)
paras = body.splitlines()
paras[2] = paras[2].replace('AI 기술은 빠르게 변하고 있었고, 취업을 준비하는 동안에도 계속 배워야 할 내용이 생길 것 같았습니다.', '빠르게 변하는 AI 분야에서 일하려면 교육이 끝난 뒤에도 꾸준히 공부해야 한다고 느꼈습니다.')
paras[4] = paras[4].replace('앞으로 무엇을 공부해야 할지 생각할 기준이 생겼습니다.', 'AI 개발자를 목표로 공부를 이어갈 방향이 조금씩 분명해졌습니다.')
paras[7] = paras[7].replace('제게 이 차이는 큽니다. ', '')
paras[8] = paras[8].replace('아직 AI 개발자로 재취업한 것은 아닙니다. 지금은 필요한 기술을 배우며 취업을 준비하는 과정에 있습니다.', '지금은 AI 개발자로 취업하기 위해 필요한 기술을 배우며 준비하고 있습니다.')
paras = paras[:4] + [paras[7]] + paras[4:7] + paras[8:]
out = title + '\n\n' + '\n'.join(paras)
(p/'final_v2.txt').write_text(out, encoding='utf-8', newline='\n')
data = {'title': title, 'paragraphs': paras, 'body_chars_spaces_no_newlines':sum(map(len,paras)), 'title_body_chars_spaces_no_newlines':len(title)+sum(map(len,paras)), 'entire_file_chars_with_LF':len(out)}
(p/'final_v2.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
assert data['entire_file_chars_with_LF'] < 3000
print(json.dumps({k:v for k,v in data.items() if k not in ('paragraphs','title')}, ensure_ascii=True))
