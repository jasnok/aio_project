from pathlib import Path
import sys,struct,zlib,io,json,hashlib,math
HERE=Path(__file__).parent
BASE=HERE.parents[1]
sys.path.insert(0,str(HERE.parent/'python_deps'))
import olefile
from hwp5.recordstream import read_records, encode_record_header, Record
from hwp5.binmodel import Hwp5File
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

src=Path(r'C:\Users\Playdata\Downloads\1. 2026년 서울시 평생교육이용권 수기 공모전 신청서 및 양식(이용자용).hwp')
dest=BASE/'최종신청서_원고입력.hwp'
content=json.loads((BASE/'final_v2.json').read_text(encoding='utf8'))
title=content['title']; paras=content['paragraphs']
assert len(paras)==10
ole=olefile.OleFileIO(src)
old_streams={'/'.join(x):ole.openstream(x).read() for x in ole.listdir()}
records=list(read_records(io.BytesIO(zlib.decompress(old_streams['BodyText/Section0'],-15))))
assert records[305]['tagid']==66 and records[308]['tagid']==72 and records[309]['tagid']==66
pdfmetrics.registerFont(TTFont('HwpMalgun', r'C:\Windows\Fonts\malgun.ttf'))

def starts_for(text,width=47940,font='HwpMalgun',size=11):
    starts=[0]; w=0
    for i,ch in enumerate(text):
        cw=pdfmetrics.stringWidth(ch,font,size)*100
        if w+cw>width and i>starts[-1]:
            starts.append(i); w=0
        w+=cw
    return starts

def paragraph(text,template,charshape,parashape,y,last,body=True):
    text=text+'\r'; units=len(text.encode('utf-16le'))//2
    h=bytearray(template['payload'])
    struct.pack_into('<I',h,0,units|(0x80000000 if last else 0))
    struct.pack_into('<I',h,4,0)
    struct.pack_into('<H',h,8,parashape)
    h[10]=0;h[11]=0
    starts=starts_for(text[:-1]) if body else [0]
    struct.pack_into('<HHH',h,12,1,0,len(starts))
    struct.pack_into('<I',h,18,0)
    seg=[]
    for n,chpos in enumerate(starts):
        seg.append(struct.pack('<iiiiiiiiI',chpos,y+n*1760,1100,1100,935,660,0,47940,393216 if n==0 else 1441792))
    level=template['level']
    result=[Record(66,level,bytes(h)),Record(67,level+1,text.encode('utf-16le')),
            Record(68,level+1,struct.pack('<II',0,charshape)),Record(69,level+1,b''.join(seg))]
    return result,y+len(starts)*1760

# Preserve the title paragraph style (centered) and use the existing Malgun 11 pt
# black character style for readability. Only records inside the two target cells
# are replaced; every other original record is retained byte for byte.
title_recs,_=paragraph(title,records[305],24,20,0,True,False)
title_recs[-1]=records[307].copy()
institution_recs,_=paragraph('코드잇',records[265],14,20,0,True,False)
institution_recs[-1]=records[267].copy()
course_recs,_=paragraph('7개월 무제한 수강권',records[269],14,20,0,True,False)
course_recs[-1]=records[271].copy()
body_header=records[308].copy()
bh=bytearray(body_header['payload']);struct.pack_into('<H',bh,0,len(paras));body_header['payload']=bytes(bh)
body_recs=[]; y=0
for n,p in enumerate(paras):
    rs,y=paragraph(p,records[309],14,23,y,n==len(paras)-1)
    body_recs+=rs
new_records=(records[:265]+institution_recs+records[268:269]+course_recs+
             records[272:305]+title_recs+[body_header]+body_recs+records[313:])
raw=b''.join(encode_record_header(r)+r['payload'] for r in new_records)
compressor=zlib.compressobj(level=9,wbits=-15)
new_stream=compressor.compress(raw)+compressor.flush()
assert len(new_stream)>=4096

# Reallocate only this regular stream within the original compound file's free
# sectors. Sector count, all other streams, tree links and mini-streams stay intact.
data=bytearray(src.read_bytes());sector_size=ole.sectorsize
fat=list(ole.fat); entry_idx=ole._find('BodyText/Section0');entry=ole.direntries[entry_idx]
def chain(start):
    result=[];seen=set();s=start
    while s not in (0xfffffffe,0xffffffff):
        assert s not in seen and s<len(fat)
        seen.add(s);result.append(s);s=fat[s]
    return result
old_chain=chain(entry.isectStart)
need=math.ceil(len(new_stream)/sector_size)
free=[i for i,x in enumerate(fat) if x==0xffffffff and i not in old_chain]
chosen=(old_chain+free)[:need]
assert len(chosen)==need
for s in old_chain:fat[s]=0xffffffff
for i,s in enumerate(chosen):
    fat[s]=chosen[i+1] if i+1<len(chosen) else 0xfffffffe
    chunk=new_stream[i*sector_size:(i+1)*sector_size].ljust(sector_size,b'\0')
    data[(s+1)*sector_size:(s+2)*sector_size]=chunk
fat_sector_ids=[x for x in struct.unpack_from('<109I',data,76) if x!=0xffffffff][:ole.num_fat_sectors]
assert len(fat_sector_ids)==ole.num_fat_sectors
for i,s in enumerate(fat_sector_ids):
    original=list(struct.unpack_from('<'+str(sector_size//4)+'I',data,(s+1)*sector_size))
    for j in range(sector_size//4):
        idx=i*(sector_size//4)+j
        if idx<len(fat):original[j]=fat[idx]
    struct.pack_into('<'+str(sector_size//4)+'I',data,(s+1)*sector_size,*original)
dir_chain=chain(ole.first_dir_sector)
entry_off=entry_idx*128
entry_pos=(dir_chain[entry_off//sector_size]+1)*sector_size+entry_off%sector_size
struct.pack_into('<I',data,entry_pos+116,chosen[0]);struct.pack_into('<Q',data,entry_pos+120,len(new_stream))
dest.write_bytes(data)

out=olefile.OleFileIO(dest)
new_streams={'/'.join(x):out.openstream(x).read() for x in out.listdir()}
assert old_streams.keys()==new_streams.keys()
assert [x for x in old_streams if old_streams[x]!=new_streams[x]]==['BodyText/Section0']
assert zlib.decompress(new_streams['BodyText/Section0'],-15)==raw
model=Hwp5File(str(dest))
parsed=list(model.bodytext['Section0'].models())
texts=[]
for m in parsed:
    if m['tagid']==67:
        texts.append(''.join(x[1] for x in m['content']['chunks'] if isinstance(x[1],str)))
assert title in texts
assert all(p in texts for p in paras)
assert '코드잇' in texts and '7개월 무제한 수강권' in texts
validation={
    'source':str(src),'output':str(dest),'output_size':len(data),
    'changed_streams':['BodyText/Section0'], 'original_stream_size':len(old_streams['BodyText/Section0']),
    'new_stream_size':len(new_stream),'paragraph_count':len(paras),
    'title_exact_match':True,'body_exact_match':True,'models_parse_success':True,
    'body_font':'맑은 고딕','body_pt':11,'body_character_shape_id':14,
    'body_paragraph_shape_id':23,'body_line_spacing':160,
    'title_style':'original centered paragraph and original HY견고딕 12pt character style',
    'known_fields_filled':{'사용기관명':'코드잇','강좌명':'7개월 무제한 수강권'},
    'cached_body_line_count':sum(len(starts_for(p)) for p in paras),
    'untouched_stream_hashes':{k:hashlib.sha256(v).hexdigest() for k,v in old_streams.items() if k!='BodyText/Section0'},
}
(HERE/'fill_validation.json').write_text(json.dumps(validation,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(validation,ensure_ascii=False,indent=2))

# An ODT conversion is supplied only as an independent read/render aid. The HWP
# output above remains the native form artifact.
from contextlib import closing
from hwp5.xmlmodel import Hwp5File as XMLHwp5File
from hwp5.hwp5odt import ODTTransform,open_odtpkg
odtpath=HERE/'filled_form.odt'
with closing(XMLHwp5File(str(dest))) as hwpfile:
    with open_odtpkg(str(odtpath)) as odtpkg:
        ODTTransform().transform_hwp5_to_package(hwpfile,odtpkg)
print('ODT_RENDER_AID',str(odtpath))
