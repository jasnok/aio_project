BEGIN;
CREATE EXTENSION IF NOT EXISTS pg_trgm WITH SCHEMA extensions;

-- 한국어·전각 문자·대소문자·공백을 통일합니다. LIKE 특수문자는 검색에서 이스케이프합니다.
CREATE OR REPLACE FUNCTION public.location_search_key(value text)
RETURNS text LANGUAGE sql IMMUTABLE PARALLEL SAFE
SET search_path = public, pg_catalog
AS $$ SELECT lower(regexp_replace(normalize(coalesce(value, ''), NFKC), '[[:space:]]+', '', 'g')); $$;

CREATE INDEX IF NOT EXISTS ix_listings_location_search ON public.listings USING gin
  (public.location_search_key(title || ' ' || housing_name || ' ' || location || ' ' || coalesce(detail_address, '')) extensions.gin_trgm_ops);
CREATE INDEX IF NOT EXISTS ix_favorites_listing_id ON public.favorites(listing_id);

CREATE OR REPLACE FUNCTION public.search_location_candidates(p_query text, p_page integer DEFAULT 1, p_page_size integer DEFAULT 20)
RETURNS jsonb LANGUAGE sql STABLE SECURITY INVOKER
SET search_path = public, pg_catalog
AS $$
WITH options AS (
 SELECT greatest(1, least(coalesce(p_page_size, 20), 50)) AS size,
   replace(replace(replace(public.location_search_key(p_query), E'\\', E'\\\\'), '%', E'\\%'), '_', E'\\_') AS term
), filtered AS MATERIALIZED (
 SELECT l.* FROM public.listings l, options o WHERE o.term <> '' AND
 public.location_search_key(l.title || ' ' || l.housing_name || ' ' || l.location || ' ' || coalesce(l.detail_address, '')) LIKE '%' || o.term || '%' ESCAPE E'\\'
), totals AS (
 SELECT count(*) AS count, greatest(1, ceil(count(*)::numeric / (SELECT size FROM options))::integer) AS pages FROM filtered
), bounds AS (
 SELECT least(greatest(coalesce(p_page, 1), 1), t.pages) AS page, t.*, o.size FROM totals t CROSS JOIN options o
), selected AS (
 SELECT * FROM filtered ORDER BY id DESC LIMIT (SELECT size FROM bounds) OFFSET (SELECT (page - 1) * size FROM bounds)
)
SELECT jsonb_build_object('items', coalesce((SELECT jsonb_agg(to_jsonb(s) ORDER BY s.id DESC) FROM selected s), '[]'::jsonb),
 'page', b.page, 'page_size', b.size, 'total_count', b.count, 'total_pages', b.pages) FROM bounds b;
$$;

CREATE OR REPLACE FUNCTION public.favorite_ranking_counts()
RETURNS TABLE(listing_id bigint, title varchar, favorite_count bigint)
LANGUAGE sql STABLE SECURITY INVOKER SET search_path = public, pg_catalog
AS $$ SELECT f.listing_id, l.title, count(*) FROM public.favorites f
 JOIN public.listings l ON l.id = f.listing_id GROUP BY f.listing_id, l.title
 ORDER BY count(*) DESC, f.listing_id ASC; $$;

REVOKE ALL ON FUNCTION public.search_location_candidates(text, integer, integer), public.favorite_ranking_counts() FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.search_location_candidates(text, integer, integer), public.favorite_ranking_counts() TO service_role;
NOTIFY pgrst, 'reload schema';
COMMIT;
