"""테이블의 앱 필수 칼럼·관계와 시연 자료를 읽기 전용으로 확인합니다."""
from collections import Counter
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.core.supabase_config import get_supabase
from app.services.listing_service import to_listing, LISTING_SELECT
from scripts.seed_demo import PREFIX

FIELDS = {
    'profiles':'id,nickname,phone,birth_date,interests,created_at',
    'admins':'id,username,password,created_at',
    'listings':'id,title,housing_name,area_sqm,recruitment_count,location,detail_address,deposit,monthly_rent,application_start_date,application_end_date,description,image_url,source_url,latitude,longitude,created_at',
    'favorites':'id,user_id,listing_id,created_at',
    'listing_images':'id,listing_id,image_url,sort_order,created_at',
    'logs':'id,time,level,screen,message,latency_ms,created_at',
    'chat_summaries':'id,user_id,title,summary,message_count,model,created_at',
}


def check():
    client=get_supabase()
    for table,fields in FIELDS.items():
        client.table(table).select(fields).limit(0).execute()
    client.table('favorites').select('id,listing:listings(id)').limit(0).execute()
    rows=client.table('listings').select(LISTING_SELECT).like('source_url',PREFIX+'%').order('id').execute().data
    for row in rows: to_listing(row)
    keys=Counter(row['source_url'] for row in rows)
    if any(n!=1 for n in keys.values()): raise RuntimeError('duplicate demo identifier')
    bucket=client.storage.get_bucket('listing-images')
    if not bucket.public: raise RuntimeError('public image bucket required')
    result={'table_columns':'7 passed','relationships':'passed','demo_listings':len(rows),
            'image_counts':dict(sorted(Counter(len(row['listing_images']) for row in rows).items())),
            'listing_ids':[row['id'] for row in rows],
            'scope':'Read-only column presence, response validation and relationship checks; no complete SQL type/index/RLS audit.'}
    print(json.dumps(result,ensure_ascii=False))


if __name__=='__main__':
    try: check()
    except Exception as error:
        print(f'Database check failed ({type(error).__name__}); no credentials printed.',file=sys.stderr)
        raise SystemExit(1) from None
