const cast = [
 {id:'jiwoo',name:'지우',age:28,mbti:'ENFP',job:'브랜드 디자이너',tag:'햇살 같은 분위기 메이커',bg:'#d9b7a5',shirt:'#e9dfd1',skin:'#e3b69e',hair:'#5b4036'},
 {id:'minjun',name:'민지',age:30,mbti:'INTJ',job:'건축가',tag:'차분하고 깊은 관찰자',bg:'#a9b4ad',shirt:'#d6d2c8',skin:'#d6a58b',hair:'#34342f'},
 {id:'seoyeon',name:'서연',age:27,mbti:'ISFJ',job:'플로리스트',tag:'다정함을 건네는 사람',bg:'#d3c3a7',shirt:'#f2e9dd',skin:'#e8bda4',hair:'#483932'},
 {id:'dohyun',name:'도연',age:29,mbti:'ENTP',job:'콘텐츠 기획자',tag:'호기심 많은 이야기꾼',bg:'#b8b6a8',shirt:'#d2d9d2',skin:'#d3a78f',hair:'#3f3935'},
 {id:'yuna',name:'유나',age:26,mbti:'INFP',job:'일러스트레이터',tag:'작은 순간을 사랑하는',bg:'#cdb1a8',shirt:'#ecdbd1',skin:'#e2b49c',hair:'#4a3833'},
 {id:'hajun',name:'하린',age:31,mbti:'ESFJ',job:'셰프',tag:'모두를 편하게 만드는',bg:'#c6b7a5',shirt:'#e3ddd1',skin:'#d5a68c',hair:'#393632'}
];
const grid=document.querySelector('#cast-grid');
grid.innerHTML=cast.map((p,i)=>`<article class="cast-card"><div class="portrait photo" style="--position-x:${(i%3)*50}%;--position-y:${Math.floor(i/3)*100}%" role="img" aria-label="${p.name}의 가상 모델 이미지"><span class="number">0${i+1} / CAST</span><span class="spark">✳</span></div><div class="cast-info"><div class="cast-name">${p.name} <span class="mbti">${p.mbti}</span></div><p>${p.age}세 · ${p.job}</p><p>${p.tag}</p></div></article>`).join('');
const game=document.querySelector('#game');
// 각 인물의 선호와 말투는 이 작품을 위한 가상의 설정입니다.
const profiles={
 jiwoo:{taste:'spark',intro:'“처음 만난 사람과도 금방 친해지는 편이에요. 우리 오늘 재미있는 추억 만들어요!”',message:'“문자 고마워요! 내일은 더 많이 웃을 수 있으면 좋겠어요.”',invite:'“정말요? 우리만의 작은 모험이 시작되는 거네요!”',replies:{spark:'“좋아요! 계획에 없던 순간이 제일 오래 기억에 남더라고요.”',depth:'“천천히 서로의 이야기를 듣는 것도 좋겠어요. 생각보다 편안하네요.”',care:'“그런 작은 배려에 마음이 따뜻해져요. 고마워요.”'}},
 minjun:{taste:'depth',intro:'“시끄러운 자리보다는 한 사람과 오래 이야기하는 시간이 좋아요.”',message:'“오늘 나눈 대화가 생각났어요. 문자 보내줘서 고마워요.”',invite:'“좋아요. 이번엔 우리 이야기를 조금 더 해볼까요?”',replies:{spark:'“낯설지만, 당신과 함께라면 새로운 경험도 괜찮겠어요.”',depth:'“서두르지 않고 서로를 알아갈 수 있어서 좋아요.”',care:'“세심하게 생각해 줬네요. 그 마음이 전해졌어요.”'}},
 seoyeon:{taste:'care',intro:'“사소한 취향을 기억해 주는 사람에게 마음이 가요.”',message:'“덕분에 첫날의 긴장이 풀렸어요. 좋은 밤 보내요.”',invite:'“함께라면 어디든 편안할 것 같아요. 기대돼요.”',replies:{spark:'“조금 두근거리지만 새로운 곳도 함께라면 좋을 것 같아요.”',depth:'“그런 이야기를 해줘서 고마워요. 저도 솔직해지고 싶어요.”',care:'“제 마음을 살펴줘서 고마워요. 저도 당신을 더 챙기고 싶어요.”'}},
 dohyun:{taste:'spark',intro:'“정답 없는 질문을 좋아해요. 예측 못 한 대답이면 더 좋고요!”',message:'“오, 나를 골랐네요? 내일은 더 재미있는 질문을 준비해 둘게요.”',invite:'“좋아요! 지루할 틈 없는 하루를 만들어 봐요.”',replies:{spark:'“역시! 우리 둘이 만나면 이야기가 어디로 튈지 모르겠네요.”',depth:'“그렇게 생각할 수도 있군요. 당신의 다른 생각도 궁금해요.”',care:'“장난만 치는 줄 알았는데, 이렇게 다정하면 반칙이죠.”'}},
 yuna:{taste:'depth',intro:'“좋아하는 장면이나 노래를 나누다 보면 그 사람의 마음이 보이는 것 같아요.”',message:'“오늘의 장면 하나를 고르라면 이 문자일 것 같아요.”',invite:'“좋아요. 조용히 우리만의 시간을 보내고 싶었어요.”',replies:{spark:'“새로운 풍경을 함께 보면 어떤 기분일지 궁금해요.”',depth:'“그 마음을 들려줘서 고마워요. 저도 조금씩 이야기해 볼게요.”',care:'“그렇게 말해주니 마음이 놓여요. 참 따뜻한 사람이네요.”'}},
 hajun:{taste:'care',intro:'“함께 밥을 먹고 서로를 챙기는 평범한 시간이 제일 소중해요.”',message:'“잘 들어갔어요? 오늘 당신 덕분에 즐거웠어요.”',invite:'“기쁘네요! 당신이 좋아하는 것부터 찾아볼까요?”',replies:{spark:'“좋아요, 즐거운 추억을 함께 만들어 봐요!”',depth:'“당신의 이야기를 들으니 한 걸음 가까워진 기분이에요.”',care:'“마음이 참 다정하네요. 저도 당신을 잘 챙겨주고 싶어요.”'}}
};
const dateReactions={
 jiwoo:['“우리 취향이 통했네요! 오늘 있었던 일, 오래 기억할 것 같아요.”','“이런 시간도 새롭네요. 당신의 취향을 알게 돼서 좋아요.”'],
 minjun:['“조용히 함께한 시간이 편안했어요. 조금 더 이야기하고 싶네요.”','“제가 평소 고르지 않을 선택이라 더 기억에 남을 것 같아요.”'],
 seoyeon:['“서로를 생각하며 보낸 시간이 참 좋았어요. 당신 덕분이에요.”','“오늘 저를 초대해 줘서 고마워요. 새로운 모습도 보게 됐어요.”'],
 dohyun:['“이렇게 웃은 게 얼마 만인지! 다음엔 제가 깜짝 계획을 세울게요.”','“예상 밖이었어요. 그래서 오히려 당신이 더 궁금해졌는데요?”'],
 yuna:['“천천히 흘러가는 이 시간이 좋아요. 나중에 그림으로 남기고 싶어요.”','“당신과 함께라서 평소와 다른 하루도 즐거웠어요.”'],
 hajun:['“이렇게 서로 챙기면서 보내니까 정말 편하고 좋네요.”','“덕분에 즐거웠어요. 다음에는 제가 좋아하는 곳도 보여주고 싶어요.”']
};
const deepReactions={
 jiwoo:['“맞아요. 조금 겁나도 같이 해보면 더 재미있을 거예요.”','“그런 생각을 하는군요. 서로 다르더라도 함께 알아가면 좋겠어요.”'],
 minjun:['“저도 그래요. 차이를 이해하려면 충분한 대화가 필요하니까요.”','“그런 시선은 미처 생각 못 했어요. 당신을 더 알고 싶네요.”'],
 seoyeon:['“상대의 속도를 기다려 주는 게 저에게도 정말 중요해요.”','“이야기해 줘서 고마워요. 다르더라도 서로 배려하면 좋겠어요.”'],
 dohyun:['“생각이 달라서 오히려 더 재미있는 일이 생길 수도 있죠!”','“그 대답은 예상 못 했어요. 당신의 이유가 더 궁금해지네요.”'],
 yuna:['“저도 천천히 진심을 나눌 수 있는 관계가 좋아요.”','“다른 생각을 듣는 것도 좋네요. 그렇게 느끼는 이유가 궁금해요.”'],
 hajun:['“상대를 편안하게 해주고 싶은 마음, 저도 정말 공감해요.”','“솔직하게 말해줘서 고마워요. 서로 맞춰 갈 수 있으면 좋겠어요.”']
};
const freshState=()=>({stage:'welcome',first:null,date:null,final:null,scores:Object.fromEntries(cast.map(p=>[p.id,0])),feedback:null,chats:Object.fromEntries(cast.map(p=>[p.id,[]]))});
let state=freshState();
const person=id=>cast.find(p=>p.id===id);
const mark=(id,points)=>{state.scores[id]+=points;};
const label=(episode,title,number)=>`<div class="game-label"><span>EPISODE ${episode} · ${title}</span><span class="game-progress">${String(number).padStart(2,'0')} / 08</span></div>`;
const peopleButtons=(action)=>`<div class="choices">${cast.map(p=>`<button class="choice" data-action="${action}" data-id="${p.id}">${p.name} <span class="mbti">${p.mbti}</span><small>${p.tag}</small></button>`).join('')}</div>`;
const answerButtons=(action,items)=>`<div class="choices" style="grid-template-columns:1fr">${items.map(item=>`<button class="choice" data-action="${action}" data-id="${item.type}">${item.text} <span style="float:right;color:#e5a396">↗</span></button>`).join('')}</div>`;
const talkOptions=[{type:'spark',text:'“낯선 곳을 함께 탐험하는 하루요.”'},{type:'depth',text:'“오래도록 진솔하게 이야기하는 하루요.”'},{type:'care',text:'“서로 좋아하는 음식을 나누는 하루요.”'}];
const dateOptions=[{type:'spark',text:'지도 없이 골목을 걷는 즉흥 데이트'},{type:'depth',text:'조용한 북카페에서 서로의 이야기 듣기'},{type:'care',text:'시장에서 장을 보고 함께 저녁 만들기'}];
const deepOptions=[{type:'spark',text:'“불확실해도 함께 새로운 걸 해보고 싶어요.”'},{type:'depth',text:'“다른 마음도 솔직하게 나누면서 천천히 알아가요.”'},{type:'care',text:'“상대가 편안한 속도를 먼저 살펴볼 것 같아요.”'}];
const chatPanel=p=>`<details class="chat-panel"><summary>${p.name}와 직접 이야기하기 <span>↗</span></summary><div class="chat-body"><p class="chat-hint">궁금한 것을 자유롭게 물어보세요. 대화를 마친 뒤 아래 선택지로 이야기를 이어갈 수 있어요.</p><div class="chat-messages" role="log" aria-label="${p.name}와의 대화" aria-live="polite"></div><form class="chat-form"><label class="chat-label" for="chat-input">메시지</label><div class="chat-compose"><input id="chat-input" name="message" type="text" maxlength="600" autocomplete="off" placeholder="메시지를 입력해 주세요" required><button class="chat-send" type="submit">보내기</button></div></form><p class="chat-status" role="status" aria-live="polite"></p></div></details>`;
function setupChat(p){
 const panel=game.querySelector('.chat-panel');
 if(!panel)return;
 const form=panel.querySelector('.chat-form'), input=form.elements.message, send=form.querySelector('button'), log=panel.querySelector('.chat-messages'), status=panel.querySelector('.chat-status');
 const activeState=state, stage=state.stage;
 function drawMessages(){
  log.replaceChildren();
  for(const item of activeState.chats[p.id]){
   const row=document.createElement('div');row.className=`chat-message ${item.role==='user'?'mine':'theirs'}`;
   const name=document.createElement('span');name.className='chat-speaker';name.textContent=item.role==='user'?'나':p.name;
   const bubble=document.createElement('p');bubble.textContent=item.content;row.append(name,bubble);log.append(row);
  }
  log.scrollTop=log.scrollHeight;
 }
 drawMessages();
 form.addEventListener('submit',async event=>{
  event.preventDefault();const content=input.value.trim();if(!content||send.disabled)return;
  const history=activeState.chats[p.id], message={role:'user',content};
  history.push(message);drawMessages();input.value='';input.disabled=true;send.disabled=true;status.textContent=`${p.name}가 답장을 생각하고 있어요…`;
  try{
   const response=await fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({characterId:p.id,messages:history.slice(-20),stage})});
   if(!response.ok)throw new Error('chat unavailable');
   const data=await response.json();if(typeof data.reply!=='string'||!data.reply.trim())throw new Error('empty response');
   history.push({role:'assistant',content:data.reply.trim()});
   if(state!==activeState||!panel.isConnected)return;
   drawMessages();status.textContent='';
  }catch(error){
   const index=history.indexOf(message);if(index!==-1)history.splice(index,1);
   if(state!==activeState||!panel.isConnected)return;
   drawMessages();input.value=content;status.textContent='대화 서버에 연결할 수 없어요. 다시 시도하거나 아래 선택지로 계속 진행해 주세요.';
  }finally{
   if(state===activeState&&panel.isConnected){input.disabled=false;send.disabled=false;input.focus();}
  }
 });
}
function feedback(title,body,next,number){state.feedback={title,body,next,number};}
function render(){
 if(state.feedback){let f=state.feedback;game.innerHTML=`${label('STORY','A MOMENT TO REMEMBER',f.number)}<h3>${f.title}</h3><p class="desc" style="font-size:14px;color:#665c55;line-height:1.9">${f.body}</p><button class="game-button" data-action="continue">다음 이야기 &nbsp; ↗</button>`;return;}
 if(state.stage==='welcome'){game.innerHTML=`${label('01','THE FIRST MEETING',1)}<h3>첫 만남, 첫 번째 설렘</h3><p class="desc">낯선 공간, 여섯 개의 서로 다른 마음.<br>대화와 데이트를 거쳐 당신만의 이야기를 완성해 보세요.</p><div style="font:italic 28px 'Playfair Display';color:#dca194;margin:27px 0">Every heart has a story.</div><button class="game-button" data-action="start">나는 솔로 입주하기 &nbsp; ↗</button>`;return;}
 if(state.stage==='first'){game.innerHTML=`${label('01','FIRST IMPRESSION',1)}<h3>첫인상이 가장 궁금한 사람은?</h3><p class="desc">문이 열리고 여섯 명의 입주자가 모였습니다.<br>가장 먼저 알아가고 싶은 한 사람을 골라주세요.</p>${peopleButtons('first')}`;return;}
 if(state.stage==='talk'){const p=person(state.first);game.innerHTML=`${label('01','A LITTLE CLOSER',2)}<h3>${p.name}와 첫 대화</h3><p class="desc">${profiles[p.id].intro}<br><br>“우리에게 하루가 주어진다면 어떤 시간을 보내고 싶어요?”</p>${chatPanel(p)}${answerButtons('talk',talkOptions)}`;setupChat(p);return;}
 if(state.stage==='message'){game.innerHTML=`${label('02','FIRST NIGHT',3)}<h3>첫날 밤, 마음을 담은 문자</h3><p class="desc">하루의 끝, 단 한 사람에게 문자를 보낼 수 있습니다.<br>첫인상과 달라도 괜찮아요. 누구에게 보내고 싶나요?</p>${peopleButtons('message')}`;return;}
 if(state.stage==='date'){game.innerHTML=`${label('03','DATE INVITATION',4)}<h3>함께 데이트하고 싶은 사람은?</h3><p class="desc">다음 날 아침, 둘만의 데이트 기회가 찾아왔어요.<br>지금 더 알아가고 싶은 사람을 초대해 보세요.</p>${peopleButtons('date')}`;return;}
 if(state.stage==='plan'){const p=person(state.date);game.innerHTML=`${label('03','OUR DATE',5)}<h3>${p.name}와 어떤 하루를 보낼까요?</h3><p class="desc">두 사람만의 시간이 시작됩니다.<br>어떤 데이트를 제안하고 싶나요?</p>${answerButtons('plan',dateOptions)}`;return;}
 if(state.stage==='deep'){const p=person(state.date);game.innerHTML=`${label('04','HEART TO HEART',6)}<h3>조금 더 가까워지는 대화</h3><p class="desc">해가 지고, ${p.name}가 조심스레 묻습니다.<br><br>“서로 다른 점을 발견하면 당신은 어떻게 하고 싶어요?”</p>${chatPanel(p)}${answerButtons('deep',deepOptions)}`;setupChat(p);return;}
 if(state.stage==='lastMessage'){game.innerHTML=`${label('05','ONE LAST MESSAGE',7)}<h3>마지막 밤의 문자</h3><p class="desc">최종 선택을 앞둔 밤, 마음을 전할 마지막 기회예요.<br>누구에게 오늘의 마음을 보내고 싶나요?</p>${peopleButtons('lastMessage')}`;return;}
 if(state.stage==='final'){game.innerHTML=`${label('06','THE FINAL CHOICE',8)}<h3>마지막으로, 마음이 향하는 사람은?</h3><p class="desc">함께 보낸 시간을 떠올려 보세요.<br>관계의 깊이에 따라 상대의 선택도 달라집니다.</p>${peopleButtons('final')}`;return;}
 const p=person(state.final), score=state.scores[p.id], matched=score>=6;
 const result=matched?`${p.name}도 당신과 함께 보낸 시간을 특별하게 기억하고 있었어요. 서로의 마음이 닿아 새로운 커플이 탄생했습니다!`:score>=2?`${p.name}는 당신에게 호감을 느꼈지만, 아직은 조금 더 알아갈 시간이 필요하다고 생각했어요. 두 사람의 이야기는 열린 결말로 남았습니다.`:`${p.name}는 아직 당신의 마음을 충분히 알지 못했어요. 이번 선택은 이어지지 않았지만, 새로운 만남의 가능성은 남아 있습니다.`;
 game.innerHTML=`<div class="game-label"><span>THE END · YOUR STORY</span><span class="game-progress">♥</span></div><div class="result-heart">♥</div><h3>${matched?'서로의 마음이 닿았어요!':score>=2?'조금 더 알아가는 사이':'엇갈린 마음'}</h3><p class="desc">당신의 최종 선택은 <span class="result-highlight">${p.name} · ${p.mbti}</span><br>${result}</p><button class="game-button" data-action="restart">다시 플레이하기 &nbsp; ↗</button><a class="game-button secondary" href="#cast">입주자 다시 보기</a>`;
}
game.addEventListener('click',e=>{
 const btn=e.target.closest('button[data-action]');if(!btn)return;
 const {action,id}=btn.dataset;
 if(action==='start')state.stage='first';
 if(action==='continue'){state.stage=state.feedback.next;state.feedback=null;}
 if(action==='first'){state.first=id;mark(id,1);feedback(`${person(id).name}에게 다가갑니다`,profiles[id].intro,'talk',1);}
 if(action==='talk'){const p=state.first;mark(p,profiles[p].taste===id?2:0);feedback(`${person(p).name}의 대답`,profiles[p].replies[id],'message',2);}
 if(action==='message'){mark(id,1);feedback(`${person(id).name}에게 문자를 보냈어요`,profiles[id].message,'date',3);}
 if(action==='date'){state.date=id;mark(id,2);feedback(`${person(id).name}의 대답`,profiles[id].invite,'plan',4);}
 if(action==='plan'){const p=state.date;mark(p,profiles[p].taste===id?2:0);feedback(`${person(p).name}와의 데이트`,dateReactions[p][profiles[p].taste===id?0:1],'deep',5);}
 if(action==='deep'){const p=state.date;mark(p,profiles[p].taste===id?2:0);feedback(`${person(p).name}의 마음`,deepReactions[p][profiles[p].taste===id?0:1],'lastMessage',6);}
 if(action==='lastMessage'){mark(id,1);feedback(`${person(id).name}에게 마음을 전했어요`,profiles[id].message,'final',7);}
 if(action==='final'){state.final=id;state.stage='result';}
 if(action==='restart')state=freshState();
 render();game.scrollIntoView({behavior:'smooth',block:'start'});
});
render();
