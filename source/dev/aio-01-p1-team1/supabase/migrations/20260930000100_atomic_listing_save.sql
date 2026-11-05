-- 공고 본문과 사진 참조를 한 트랜잭션에서 변경합니다.
CREATE OR REPLACE FUNCTION public.save_listing_atomic(
    p_listing jsonb,
    p_image_urls text[],
    p_id bigint DEFAULT NULL
) RETURNS jsonb
LANGUAGE plpgsql
SET search_path = public
AS $$
DECLARE
    saved public.listings%ROWTYPE;
    item record;
    image_rows jsonb;
BEGIN
    IF p_listing IS NULL OR p_image_urls IS NULL THEN
        RAISE EXCEPTION '공고와 사진 목록은 필수입니다';
    END IF;
    IF EXISTS (SELECT 1 FROM unnest(p_image_urls) AS url WHERE url IS NULL OR btrim(url) = '') THEN
        RAISE EXCEPTION '빈 사진 URL은 저장할 수 없습니다';
    END IF;

    IF p_id IS NULL THEN
        INSERT INTO public.listings (
            title, housing_name, area_sqm, recruitment_count, location,
            detail_address, deposit, monthly_rent, application_start_date,
            application_end_date, description, image_url, source_url
        ) VALUES (
            p_listing->>'title', p_listing->>'housing_name',
            (p_listing->>'area_sqm')::numeric, (p_listing->>'recruitment_count')::integer,
            p_listing->>'location', p_listing->>'detail_address',
            (p_listing->>'deposit')::bigint, (p_listing->>'monthly_rent')::bigint,
            (p_listing->>'application_start_date')::date,
            (p_listing->>'application_end_date')::date, p_listing->>'description',
            p_image_urls[1], p_listing->>'source_url'
        ) RETURNING * INTO saved;
    ELSE
        UPDATE public.listings SET
            title = p_listing->>'title', housing_name = p_listing->>'housing_name',
            area_sqm = (p_listing->>'area_sqm')::numeric,
            recruitment_count = (p_listing->>'recruitment_count')::integer,
            location = p_listing->>'location', detail_address = p_listing->>'detail_address',
            deposit = (p_listing->>'deposit')::bigint,
            monthly_rent = (p_listing->>'monthly_rent')::bigint,
            application_start_date = (p_listing->>'application_start_date')::date,
            application_end_date = (p_listing->>'application_end_date')::date,
            description = p_listing->>'description', image_url = p_image_urls[1],
            source_url = p_listing->>'source_url'
        WHERE id = p_id RETURNING * INTO saved;
        IF NOT FOUND THEN
            RETURN NULL;
        END IF;
        DELETE FROM public.listing_images WHERE listing_id = p_id;
    END IF;

    FOR item IN SELECT url, ordinal FROM unnest(p_image_urls) WITH ORDINALITY AS t(url, ordinal)
    LOOP
        INSERT INTO public.listing_images (listing_id, image_url, sort_order)
        VALUES (saved.id, item.url, item.ordinal - 1);
    END LOOP;

    SELECT coalesce(jsonb_agg(jsonb_build_object('image_url', image_url, 'sort_order', sort_order)
                              ORDER BY sort_order), '[]'::jsonb)
    INTO image_rows FROM public.listing_images WHERE listing_id = saved.id;
    RETURN to_jsonb(saved) || jsonb_build_object('listing_images', image_rows);
END;
$$;

REVOKE ALL ON FUNCTION public.save_listing_atomic(jsonb, text[], bigint) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.save_listing_atomic(jsonb, text[], bigint) TO service_role;
NOTIFY pgrst, 'reload schema';

-- 대표 사진 삭제는 제목·금액을 다시 저장하지 않고 사진 칼럼만 변경합니다.
CREATE OR REPLACE FUNCTION public.remove_listing_primary_image_atomic(p_id bigint)
RETURNS jsonb LANGUAGE plpgsql SET search_path = public AS $$
DECLARE
    saved public.listings%ROWTYPE;
    image_rows jsonb;
BEGIN
    SELECT * INTO saved FROM public.listings WHERE id = p_id FOR UPDATE;
    IF NOT FOUND THEN RETURN NULL; END IF;
    DELETE FROM public.listing_images WHERE listing_id = p_id AND image_url = saved.image_url;
    UPDATE public.listings SET image_url = (
        SELECT image_url FROM public.listing_images WHERE listing_id = p_id ORDER BY sort_order LIMIT 1
    ) WHERE id = p_id RETURNING * INTO saved;
    SELECT coalesce(jsonb_agg(jsonb_build_object('image_url', image_url, 'sort_order', sort_order)
                             ORDER BY sort_order), '[]'::jsonb)
    INTO image_rows FROM public.listing_images WHERE listing_id = p_id;
    RETURN to_jsonb(saved) || jsonb_build_object('listing_images', image_rows);
END;
$$;
REVOKE ALL ON FUNCTION public.remove_listing_primary_image_atomic(bigint) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.remove_listing_primary_image_atomic(bigint) TO service_role;
NOTIFY pgrst, 'reload schema';
