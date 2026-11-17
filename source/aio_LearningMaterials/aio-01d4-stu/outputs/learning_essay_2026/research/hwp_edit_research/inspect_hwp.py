from pathlib import Path
import sys,struct,zlib,io,json
BASE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(BASE/'python_deps'))
import olefile
from hwp5.recordstream import read_records
src=Path(r'C:\Users\Playdata\Downloads\1. 2026년 서울시 평생교육이용권 수기 공모전 신청서 및 양식(이용자용).hwp')
ole=olefile.OleFileIO(src)
streams=[('/'.join(x),ole.get_size(x)) for x in ole.listdir()]
data=ole.openstream('BodyText/Section0').read()
data=zlib.decompress(data,-15)
recs=list(read_records(io.BytesIO(data)))
out=[]
for r in recs:
    rec={'i':r['seqno'],'tag':r['tagid'],'level':r['level'],'size':r['size']}
    if r['tagid']==66:
        p=r['payload']; rec['para']=dict(zip(['chars','ctrl','shape','style','split','ncharshape','nrange','nline','id'],struct.unpack('<IIHBBHHHI',p[:22])))
    if r['tagid']==67:
        rec['text']=r['payload'].decode('utf-16le',errors='replace')
    elif r['seqno']>400:
        rec['payload']=r['payload'].hex()
    out.append(rec)
dest=Path(__file__).parent
(dest/'records.json').write_text(json.dumps({'streams':streams,'records':out},ensure_ascii=False,indent=2),encoding='utf8')
print('stream',streams,'records',len(recs),'uncompressed',len(data))
for r in out[-110:]: print(json.dumps(r,ensure_ascii=False))
