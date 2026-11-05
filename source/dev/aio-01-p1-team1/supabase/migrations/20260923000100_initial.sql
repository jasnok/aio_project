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
