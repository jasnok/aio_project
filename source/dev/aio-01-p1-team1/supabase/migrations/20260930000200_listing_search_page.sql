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
