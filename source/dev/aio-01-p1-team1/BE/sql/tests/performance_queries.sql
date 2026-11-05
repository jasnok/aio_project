-- 로컬 전용. 모든 검증 데이터와 수정은 마지막에 롤백합니다.
BEGIN;
DO $$
DECLARE ids bigint[]; page1 jsonb; page2 jsonb; user1 uuid := gen_random_uuid(); user2 uuid := gen_random_uuid();
BEGIN
  WITH inserted AS (
    INSERT INTO public.listings(title,housing_name,area_sqm,recruitment_count,location,deposit,monthly_rent,
      application_start_date,application_end_date,description,source_url)
    SELECT '[SQL성능검증] 공고 ' || n, 'SQL성능검증 주택', 20, 1, '강남구', 1000, 100,
      current_date,current_date+7,'가상 SQL 검증 공고','https://example.invalid/sql-perf/' || n
    FROM generate_series(1,45) n RETURNING id
  ) SELECT array_agg(id ORDER BY id) INTO ids FROM inserted;
  page1 := public.search_location_candidates('SQL성능검증',1,20);
  page2 := public.search_location_candidates('SQL성능검증',2,20);
  ASSERT (page1->>'total_count')::int = 45, '검색 개수';
  ASSERT (page1->>'total_pages')::int = 3, '후보 페이지 개수';
  ASSERT jsonb_array_length(page1->'items') = 20, '후보 분량';
  ASSERT NOT EXISTS (SELECT 1 FROM jsonb_array_elements(page1->'items') a
    JOIN jsonb_array_elements(page2->'items') b ON a->>'id'=b->>'id'), '페이지 중복';
  ASSERT (public.search_location_candidates('SQL성능검증',999,20)->>'page')::int = 3, '범위 보정';
  ASSERT (public.search_location_candidates('   ',1,20)->>'total_count')::int = 0, '빈 검색';
  UPDATE public.listings SET title='[SQL성능검증] ＡＢＣ 행복 주택 100%_특수' WHERE id=ids[1];
  ASSERT (public.search_location_candidates('abc행복',1,20)->>'total_count')::int = 1, '전각·공백·대소문자';
  ASSERT (public.search_location_candidates('100%_특수',1,20)->>'total_count')::int = 1, '와일드카드 문자 이스케이프';
  INSERT INTO auth.users(id) VALUES(user1),(user2);
  INSERT INTO public.favorites(user_id,listing_id) VALUES(user1,ids[1]),(user2,ids[1]),(user1,ids[2]);
  ASSERT (SELECT favorite_count FROM public.favorite_ranking_counts() WHERE listing_id=ids[1])=2, '순위 전체 집계';
  ASSERT NOT has_function_privilege('anon','public.search_location_candidates(text,integer,integer)','execute'), 'anon RPC 차단';
  ASSERT NOT has_function_privilege('authenticated','public.favorite_ranking_counts()','execute'), '관리자 집계 RPC 차단';
END;
$$;
ROLLBACK;
