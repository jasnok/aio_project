-- 개발용 샘플 데이터만 외래키의 반대 순서로 삭제합니다.
begin;

delete from public.comments where comment_id between '20260723092000001' and '20260723092000005';
delete from public.supports where support_id between '20260723093000001' and '20260723093000005';
delete from public.posts where post_id between '20260723091000001' and '20260723091000005';
delete from public.users where email like 'sample-user-%@example.com';

commit;
