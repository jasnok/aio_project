BEGIN;
DO $$
DECLARE result jsonb; ids integer[]; expected integer[]; actual integer[] := '{}'; n integer;
BEGIN
    FOR n IN 1..25 LOOP
        INSERT INTO listings(title,housing_name,area_sqm,recruitment_count,location,deposit,monthly_rent,
            application_start_date,application_end_date,description,source_url)
        VALUES ('페이지 검증',n::text,n,n,'페이지검증용',n*100,n*10,'2026-01-01',
            DATE '2026-09-30' + CASE WHEN n<=8 THEN -n ELSE n END,'가상','https://example.invalid/page-test');
    END LOOP;
    FOR n IN 1..3 LOOP
        result := search_listings_page(n,10,'end_date_asc','페이지검증용',NULL,NULL,'2026-09-30');
        SELECT array_agg((item->>'housing_name')::integer ORDER BY position) INTO ids
            FROM jsonb_array_elements(result->'items') WITH ORDINALITY a(item,position);
        actual := actual || ids;
        IF (result->>'total_count')::integer <> 25 THEN RAISE EXCEPTION 'Incorrect total'; END IF;
    END LOOP;
    SELECT array_agg(x) INTO expected FROM (SELECT generate_series(9,25) x UNION ALL SELECT generate_series(1,8)) q;
    IF actual <> expected THEN RAISE EXCEPTION 'Incorrect global order: %', actual; END IF;
    result := search_listings_page(99,10,'area_desc','페이지검증용',500,NULL,'2026-09-30');
    IF (result->>'page')::integer <> 1 OR (result->>'total_count')::integer <> 5
       OR result->'items'->0->>'housing_name' <> '5' THEN RAISE EXCEPTION 'Filter or bounds failed'; END IF;
    result := search_listings_page(1,10,'end_date_asc','不存在',NULL,NULL,'2026-09-30');
    IF result->'items' <> '[]'::jsonb OR (result->>'total_count')::integer <> 0 THEN RAISE EXCEPTION 'Empty failed'; END IF;
    RAISE NOTICE 'PASS: filters, closed order, paging without duplicates, bounds and empty results';
END;
$$;
ROLLBACK;
