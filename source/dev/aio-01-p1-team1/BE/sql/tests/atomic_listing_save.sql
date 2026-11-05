-- 로컬 전용 회귀 검증. 모든 임시 자료와 CHECK는 마지막에 롤백합니다.
BEGIN;
ALTER TABLE public.listing_images ADD CONSTRAINT test_reject_image
    CHECK (image_url <> 'https://example.invalid/reject.png');
DO $$
DECLARE
    payload jsonb := '{"title":"[검증용 가상 공고] 원자 저장","housing_name":"검증주택","area_sqm":"26.5","recruitment_count":2,"location":"중구","deposit":1000,"monthly_rent":100,"application_start_date":"2026-10-01","application_end_date":"2026-10-31","description":"검증 후 롤백","source_url":"https://example.invalid/atomic-test"}';
    saved jsonb;
    test_listing_id bigint;
BEGIN
    saved := public.save_listing_atomic(payload, ARRAY['https://example.invalid/a.png', 'https://example.invalid/b.png']);
    test_listing_id := (saved->>'id')::bigint;
    BEGIN
        PERFORM public.save_listing_atomic(payload || '{"title":"실패한 수정"}',
            ARRAY['https://example.invalid/c.png', 'https://example.invalid/reject.png'], test_listing_id);
        RAISE EXCEPTION '삽입 실패가 발생하지 않았습니다';
    EXCEPTION WHEN check_violation THEN NULL;
    END;
    IF (SELECT title FROM public.listings WHERE id = test_listing_id) <> payload->>'title'
       OR (SELECT array_agg(image_url ORDER BY sort_order) FROM public.listing_images WHERE listing_id = test_listing_id)
          <> ARRAY['https://example.invalid/a.png', 'https://example.invalid/b.png'] THEN
        RAISE EXCEPTION '실패한 수정이 기존 공고 또는 사진을 바꿨습니다';
    END IF;
    PERFORM public.save_listing_atomic(payload, ARRAY['https://example.invalid/b.png'], test_listing_id);
    IF (SELECT image_url FROM public.listings WHERE id = test_listing_id) <> 'https://example.invalid/b.png'
       OR (SELECT count(*) FROM public.listing_images WHERE listing_id = test_listing_id) <> 1 THEN
        RAISE EXCEPTION '부분 삭제 후 대표 사진 또는 목록이 잘못되었습니다';
    END IF;
    BEGIN
        PERFORM public.save_listing_atomic(payload, ARRAY['https://example.invalid/reject.png']);
        RAISE EXCEPTION '생성 실패가 발생하지 않았습니다';
    EXCEPTION WHEN check_violation THEN NULL;
    END;
    IF (SELECT count(*) FROM public.listings WHERE source_url = payload->>'source_url') <> 1 THEN
        RAISE EXCEPTION '사진 저장 실패 후 불완전한 새 공고가 남았습니다';
    END IF;
    saved := public.remove_listing_primary_image_atomic(test_listing_id);
    IF saved->>'image_url' IS NOT NULL OR saved->>'title' <> payload->>'title'
       OR jsonb_array_length(saved->'listing_images') <> 0 THEN
        RAISE EXCEPTION '대표 사진 삭제 후 본문 또는 사진 연결이 잘못되었습니다';
    END IF;
    IF has_function_privilege('anon', 'public.save_listing_atomic(jsonb,text[],bigint)', 'EXECUTE')
       OR has_function_privilege('authenticated', 'public.save_listing_atomic(jsonb,text[],bigint)', 'EXECUTE') THEN
        RAISE EXCEPTION '일반 사용자가 저장 함수를 직접 실행할 수 있습니다';
    END IF;
    RAISE NOTICE 'PASS: 생성·부분 삭제·삽입 실패 롤백·함수 권한';
END;
$$;
ROLLBACK;

