-- 현재 애플리케이션을 새 Supabase 프로젝트에 설치하는 기준 스키마입니다.
-- 데이터 삭제/초기화 없이 테이블이 없을 때만 만듭니다.
-- 기존 테이블의 구조를 고치는 마이그레이션은 아닙니다.
-- Data API는 서버 service_role만 사용합니다. 사용자 로그인은 Supabase Auth가 담당합니다.
-- RLS는 직접 DB 접근을 보호하며, 백엔드 API의 사용자/관리자 권한 검사를 대신하지 않습니다.

BEGIN;

CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    nickname VARCHAR(50),
    phone VARCHAR(13),
    birth_date DATE,
    interests JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT ck_profiles_interests CHECK (jsonb_typeof(interests) = 'array')
);

CREATE TABLE IF NOT EXISTS public.admins (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.listings (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    housing_name VARCHAR(255) NOT NULL,
    area_sqm NUMERIC(10,2) NOT NULL,
    recruitment_count INTEGER NOT NULL,
    location VARCHAR(50) NOT NULL,
    detail_address VARCHAR(255),
    deposit BIGINT NOT NULL,
    monthly_rent BIGINT NOT NULL,
    application_start_date DATE NOT NULL,
    application_end_date DATE NOT NULL,
    description TEXT NOT NULL,
    image_url TEXT,
    source_url TEXT NOT NULL,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT ck_listings_area_sqm CHECK (area_sqm > 0),
    CONSTRAINT ck_listings_recruitment_count CHECK (recruitment_count > 0),
    CONSTRAINT ck_listings_deposit CHECK (deposit >= 0),
    CONSTRAINT ck_listings_monthly_rent CHECK (monthly_rent >= 0),
    CONSTRAINT ck_listings_application_period CHECK (application_end_date >= application_start_date),
    CONSTRAINT ck_listings_latitude CHECK (latitude IS NULL OR latitude BETWEEN -90 AND 90),
    CONSTRAINT ck_listings_longitude CHECK (longitude IS NULL OR longitude BETWEEN -180 AND 180)
);

CREATE TABLE IF NOT EXISTS public.favorites (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    listing_id BIGINT NOT NULL REFERENCES public.listings(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_favorites UNIQUE (user_id, listing_id)
);

CREATE TABLE IF NOT EXISTS public.listing_images (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    listing_id BIGINT NOT NULL REFERENCES public.listings(id) ON DELETE CASCADE,
    image_url TEXT NOT NULL,
    sort_order INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_listing_images_order UNIQUE (listing_id, sort_order),
    CONSTRAINT ck_listing_images_sort_order CHECK (sort_order >= 0)
);

CREATE TABLE IF NOT EXISTS public.logs (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    time TIMESTAMPTZ NOT NULL,
    level VARCHAR(10) NOT NULL CHECK (level IN ('warning', 'error')),
    screen VARCHAR(50) NOT NULL,
    message TEXT NOT NULL,
    latency_ms INTEGER NOT NULL CHECK (latency_ms >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.chat_summaries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    summary TEXT NOT NULL,
    message_count INTEGER NOT NULL CHECK (message_count >= 0),
    model TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_listings_location ON public.listings(location);
CREATE INDEX IF NOT EXISTS idx_listings_deposit ON public.listings(deposit);
CREATE INDEX IF NOT EXISTS idx_listings_monthly_rent ON public.listings(monthly_rent);
CREATE INDEX IF NOT EXISTS idx_listings_application_start_date ON public.listings(application_start_date DESC);
CREATE INDEX IF NOT EXISTS idx_listings_application_end_date ON public.listings(application_end_date);
CREATE INDEX IF NOT EXISTS idx_favorites_listing_id ON public.favorites(listing_id);
CREATE INDEX IF NOT EXISTS idx_favorites_user_id ON public.favorites(user_id);
CREATE INDEX IF NOT EXISTS idx_listing_images_listing_id ON public.listing_images(listing_id, sort_order);
CREATE INDEX IF NOT EXISTS idx_listing_images_image_url ON public.listing_images(image_url);
CREATE INDEX IF NOT EXISTS idx_logs_time ON public.logs(time DESC);
CREATE INDEX IF NOT EXISTS idx_logs_level ON public.logs(level);
CREATE INDEX IF NOT EXISTS idx_chat_summaries_user_created ON public.chat_summaries(user_id, created_at DESC);

CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER SET search_path = ''
AS $$
BEGIN
    INSERT INTO public.profiles (id, nickname, phone, birth_date, interests)
    VALUES (
        NEW.id,
        NEW.raw_user_meta_data->>'nickname',
        NEW.raw_user_meta_data->>'phone',
        NULLIF(NEW.raw_user_meta_data->>'birth_date', '')::date,
        CASE WHEN jsonb_typeof(NEW.raw_user_meta_data->'interests') = 'array'
             THEN NEW.raw_user_meta_data->'interests' ELSE '[]'::jsonb END
    ) ON CONFLICT (id) DO NOTHING;
    RETURN NEW;
END;
$$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
        WHERE tgrelid = 'auth.users'::regclass
          AND tgname = 'on_auth_user_created'
          AND NOT tgisinternal
    ) THEN
        CREATE TRIGGER on_auth_user_created
            AFTER INSERT ON auth.users
            FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();
    END IF;
END;
$$;

ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.admins ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.listings ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.favorites ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.listing_images ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.chat_summaries ENABLE ROW LEVEL SECURITY;

-- 이 앱의 DB 읽기/쓰기는 FastAPI를 통해 처리합니다.
-- 화면의 anon key로 프로필/관리자 비밀번호 등 테이블을 직접 읽지 못하게 합니다.
REVOKE ALL ON TABLE public.profiles, public.admins, public.listings,
    public.favorites, public.listing_images, public.logs, public.chat_summaries
    FROM PUBLIC, anon, authenticated;
GRANT ALL ON TABLE public.profiles, public.admins, public.listings,
    public.favorites, public.listing_images, public.logs, public.chat_summaries
    TO service_role;
REVOKE ALL ON SEQUENCE public.admins_id_seq, public.listings_id_seq,
    public.favorites_id_seq, public.listing_images_id_seq, public.logs_id_seq
    FROM PUBLIC, anon, authenticated;
GRANT USAGE, SELECT ON SEQUENCE public.admins_id_seq, public.listings_id_seq,
    public.favorites_id_seq, public.listing_images_id_seq, public.logs_id_seq
    TO service_role;
REVOKE ALL ON FUNCTION public.handle_new_user() FROM PUBLIC, anon, authenticated;

NOTIFY pgrst, 'reload schema';
COMMIT;

SELECT tablename, rowsecurity
FROM pg_tables
WHERE schemaname = 'public'
  AND tablename IN ('profiles', 'admins', 'listings', 'favorites', 'listing_images', 'logs', 'chat_summaries')
ORDER BY tablename;

-- 신규 프로젝트의 수동 bootstrap도 공고·사진 원자 저장 함수를 준비합니다.
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

-- Public read-only paging; one statement keeps the count and items consistent.
CREATE OR REPLACE FUNCTION public.search_listings_page(
    p_page integer DEFAULT 1, p_page_size integer DEFAULT 10,
    p_sort text DEFAULT 'end_date_asc', p_location text DEFAULT NULL,
    p_max_deposit bigint DEFAULT NULL, p_max_monthly_rent bigint DEFAULT NULL,
    p_today date DEFAULT CURRENT_DATE
) RETURNS jsonb LANGUAGE plpgsql STABLE SECURITY INVOKER SET search_path = public AS $$
DECLARE
    ordering text;
    size integer := LEAST(100, GREATEST(1, p_page_size));
    requested integer := GREATEST(1, p_page);
    result jsonb;
BEGIN
    IF p_sort = 'end_date_asc' THEN
        -- Match existing user listing order, including recent closed notices first.
        ordering := '(application_end_date < $6) ASC NULLS FIRST,
          CASE WHEN application_end_date >= $6 THEN application_end_date END ASC NULLS LAST,
          CASE WHEN application_end_date < $6 THEN application_end_date END DESC NULLS LAST,
          CASE WHEN application_end_date < $6 THEN created_at END ASC,
          CASE WHEN application_end_date >= $6 THEN created_at END DESC,
          CASE WHEN application_end_date < $6 THEN id END ASC, id DESC';
    ELSE
        ordering := CASE p_sort
          WHEN 'created_desc' THEN 'created_at DESC'
          WHEN 'area_desc' THEN 'area_sqm DESC' WHEN 'area_asc' THEN 'area_sqm ASC'
          WHEN 'recruitment_desc' THEN 'recruitment_count DESC' WHEN 'recruitment_asc' THEN 'recruitment_count ASC'
          WHEN 'deposit_desc' THEN 'deposit DESC' WHEN 'deposit_asc' THEN 'deposit ASC'
          WHEN 'rent_desc' THEN 'monthly_rent DESC' WHEN 'rent_asc' THEN 'monthly_rent ASC'
          ELSE NULL END;
        IF ordering IS NULL THEN RAISE EXCEPTION 'Unknown listing sort'; END IF;
        ordering := '(application_end_date < $6) ASC NULLS FIRST, ' || ordering || ' NULLS LAST, id DESC';
    END IF;
    EXECUTE format($query$
      WITH filtered AS MATERIALIZED (
        SELECT * FROM listings WHERE ($3 IS NULL OR location ILIKE '%%' || $3 || '%%')
          AND ($4 IS NULL OR deposit <= $4) AND ($5 IS NULL OR monthly_rent <= $5)
      ), meta AS (
        SELECT count(*) AS total_count,
          GREATEST(1, CEIL(count(*)::numeric / $2)::integer) AS total_pages FROM filtered
      ), bounds AS (
        SELECT *, LEAST($1, total_pages) AS page FROM meta
      ), selected AS (
        SELECT f.*, row_number() OVER (ORDER BY %s) AS position FROM filtered f
      ), items AS (
        SELECT to_jsonb(s) - 'position' || jsonb_build_object('listing_images',
          (SELECT COALESCE(jsonb_agg(jsonb_build_object('image_url', i.image_url,
            'sort_order', i.sort_order) ORDER BY i.sort_order), '[]'::jsonb)
           FROM listing_images i WHERE i.listing_id = s.id)) AS item, position
        FROM selected s, bounds b WHERE position > (b.page - 1) * $2 AND position <= b.page * $2
      )
      SELECT jsonb_build_object('page', b.page, 'page_size', $2,
        'total_count', b.total_count, 'total_pages', b.total_pages,
        'items', COALESCE((SELECT jsonb_agg(item ORDER BY position) FROM items), '[]'::jsonb))
      FROM bounds b
    $query$, ordering) INTO result USING requested, size, p_location, p_max_deposit, p_max_monthly_rent, p_today;
    RETURN result;
END;
$$;
REVOKE ALL ON FUNCTION public.search_listings_page(integer, integer, text, text, bigint, bigint, date) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.search_listings_page(integer, integer, text, text, bigint, bigint, date) TO service_role;
NOTIFY pgrst, 'reload schema';
