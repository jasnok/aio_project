"""가상 공고 준비. 기본은 미리보기, --apply일 때만 연결된 Supabase에 저장합니다."""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import date, timedelta
import hashlib
import json
import os
from pathlib import Path
import struct
import sys
import zlib

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.core.settings import settings
from app.core.supabase_config import get_supabase
from app.schemas.listing_schema import ListingCreate

ROOT = Path(__file__).resolve().parents[2]
PREFIX = "https://example.invalid/portfolio-demo/v1/"
MARKER = "[포트폴리오 시연용 가상 공고]"
REGIONS = ("강남구", "마포구", "노원구", "송파구", "은평구")


def fixtures(reference: date) -> list[dict]:
    rows = []
    for i in range(15):
        start, end = ((7, 21), (-7, 7), (-21, -7))[i % 3]
        region = REGIONS[i % len(REGIONS)]
        item = dict(
            title=f"{MARKER} {region} 데모주택 {i+1:02d}",
            housing_name=f"가상 {region} 데모주택 {i+1:02d}",
            area_sqm=str(24 + i * 3), recruitment_count=5+i,
            location=region, detail_address=None,
            deposit=10000000+i*5000000, monthly_rent=100000+i*25000,
            application_start_date=str(reference+timedelta(days=start)),
            application_end_date=str(reference+timedelta(days=end)),
            description=f"{MARKER}\n실제 모집·신청 대상이 아닙니다. 실제 주소나 개인정보는 포함하지 않습니다.\n시연 기준일: {reference}\n검색·정렬·이미지 표시를 확인하는 연습 자료입니다.",
            source_url=f"{PREFIX}{i+1:03d}",
            image_url=None, image_urls=[],
        )
        ListingCreate.model_validate(item)
        rows.append(item)
    return rows


def diagram_png(variant: int) -> bytes:
    """외부 사진 없이 코드로 만드는 가상 평면도. 실제 건축 도면이 아닙니다."""
    width, height = 480, 300
    colors = ((89, 151, 180), (124, 168, 119), (196, 149, 90))
    color = colors[variant]
    raw = bytearray()
    for y in range(height):
        raw.append(0)
        for x in range(width):
            inside = 35 < x < 445 and 35 < y < 265
            wall = inside and (x < 42 or x > 438 or y < 42 or y > 258 or (235 < x < 243 and y < 210) or (145 < y < 153 and x > 240))
            pixel = (36, 52, 65) if wall else (color if inside else (245, 247, 250))
            raw.extend(pixel)
    def chunk(kind, data):
        return struct.pack('!I',len(data))+kind+data+struct.pack('!I',zlib.crc32(kind+data)&0xffffffff)
    return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('!2I5B',width,height,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(bytes(raw)))+chunk(b'IEND',b'')


@contextmanager
def project_lock(url: str):
    """같은 PC에서 같은 프로젝트에 대한 동시 실행 방지. 종료 시 OS가 잠금 해제."""
    folder = ROOT / '.runtime'
    folder.mkdir(exist_ok=True)
    path = folder / ('demo-'+hashlib.sha256(url.encode()).hexdigest()[:16]+'.lock')
    with path.open('a+b') as stream:
        stream.seek(0); stream.write(b'0'); stream.flush(); stream.seek(0)
        if os.name == 'nt':
            import msvcrt
            msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            yield
        finally:
            stream.seek(0)
            if os.name == 'nt':
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(stream, fcntl.LOCK_UN)


def owned_row(rows: list[dict]) -> dict | None:
    if len(rows) > 1:
        raise RuntimeError('시연 식별자가 중복됩니다. 자동 변경을 중단합니다.')
    if rows and not (rows[0]['title'].startswith(MARKER) and rows[0]['description'].startswith(MARKER)):
        raise RuntimeError('같은 주소의 기존 공고가 있어 자동 변경을 중단합니다.')
    return rows[0] if rows else None


def apply_seed(client, reference: date, refresh_dates: bool = False) -> dict:
    # 모든 충돌을 쓰기 전에 확인합니다. 중간 장애 후 재실행하면 기존 ID를 재사용합니다.
    planned = fixtures(reference)
    existing = {}
    for row in planned:
        found = client.table('listings').select('id,title,description').eq('source_url',row['source_url']).limit(2).execute().data
        existing[row['source_url']] = owned_row(found)
    bucket = client.storage.get_bucket('listing-images')
    if not bucket.public:
        raise RuntimeError('listing-images 저장소의 공개 설정을 확인하세요.')
    store = client.storage.from_('listing-images')
    listed = {item['name'] for item in store.list('portfolio-demo/v1')}
    images = []
    for variant in range(3):
        data = diagram_png(variant)
        name = hashlib.sha256(data).hexdigest()+'.png'
        path = 'portfolio-demo/v1/'+name
        if name not in listed:
            store.upload(path,data,{'content-type':'image/png'})
        else:
            if store.download(path) != data:
                raise RuntimeError('기존 시연 이미지 내용이 다릅니다. 덮어쓰지 않습니다.')
        images.append(store.get_public_url(path).rstrip('?'))
    created = 0
    ids = []
    for i,row in enumerate(planned):
        row.pop('image_urls')
        urls = images[:(0,1,3)[i%3]]
        row['image_url'] = urls[0] if urls else None
        old = existing[row['source_url']]
        if old:
            listing_id = old['id']
            # 날짜 갱신은 별도 옵션. 기본 재실행은 기존 공고 본문을 변경하지 않습니다.
            if refresh_dates:
                client.table('listings').update({k:row[k] for k in ('application_start_date','application_end_date','description')}).eq('id',listing_id).eq('source_url',row['source_url']).execute()
        else:
            listing_id = client.table('listings').insert(row).execute().data[0]['id']
            created += 1
        current = client.table('listing_images').select('sort_order,image_url').eq('listing_id',listing_id).execute().data
        positions = {x['sort_order']:x['image_url'] for x in current}
        for order,url in enumerate(urls):
            if order in positions and positions[order] != url:
                raise RuntimeError('시연 이미지가 수동 수정되었습니다. 덮어쓰지 않습니다.')
            if order not in positions:
                client.table('listing_images').insert({'listing_id':listing_id,'sort_order':order,'image_url':url}).execute()
        ids.append(listing_id)
    return {'created':created,'reused':15-created,'listing_ids':ids,'reference_date':str(reference),'image_objects':3,'expected_image_links':20}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--date',type=date.fromisoformat,default=date.today())
    parser.add_argument('--apply',action='store_true')
    parser.add_argument('--refresh-dates',action='store_true')
    args = parser.parse_args()
    if not args.apply:
        print(json.dumps({'mode':'preview','date':str(args.date),'listings':fixtures(args.date)},ensure_ascii=False,indent=2))
        return
    try:
        with project_lock(settings.http_url('SUPABASE_URL')):
            result=apply_seed(get_supabase(),args.date,args.refresh_dates)
        print(json.dumps(result,ensure_ascii=False))
    except Exception as error:
        print(f'시연 데이터 준비 실패 ({type(error).__name__}). 키는 출력하지 않습니다. DB 구조·저장소·중복 식별자·네트워크를 확인한 뒤 같은 명령을 재실행하세요.',file=sys.stderr)
        raise SystemExit(1) from None


if __name__ == '__main__':
    main()
