-- 개발용 샘플 데이터입니다. user → post → comment → support 순서로 입력합니다.
begin;

insert into public.users (user_id, email, password, name)
values
    ('20260723090000001', 'sample-user-01@example.com', 'pbkdf2_sha256$600000$4raNjbxK9dGMvwIVYYgTog==$P7zvKA+cTEGhZnk3h9Dzj4ev/TCM0CuBc5bZDn6sUfE=', '샘플회원01'),
    ('20260723090000002', 'sample-user-02@example.com', 'pbkdf2_sha256$600000$4raNjbxK9dGMvwIVYYgTog==$P7zvKA+cTEGhZnk3h9Dzj4ev/TCM0CuBc5bZDn6sUfE=', '샘플회원02'),
    ('20260723090000003', 'sample-user-03@example.com', 'pbkdf2_sha256$600000$4raNjbxK9dGMvwIVYYgTog==$P7zvKA+cTEGhZnk3h9Dzj4ev/TCM0CuBc5bZDn6sUfE=', '샘플회원03'),
    ('20260723090000004', 'sample-user-04@example.com', 'pbkdf2_sha256$600000$4raNjbxK9dGMvwIVYYgTog==$P7zvKA+cTEGhZnk3h9Dzj4ev/TCM0CuBc5bZDn6sUfE=', '샘플회원04'),
    ('20260723090000005', 'sample-user-05@example.com', 'pbkdf2_sha256$600000$4raNjbxK9dGMvwIVYYgTog==$P7zvKA+cTEGhZnk3h9Dzj4ev/TCM0CuBc5bZDn6sUfE=', '샘플회원05'),
    ('20260723090000006', 'sample-user-06@example.com', 'pbkdf2_sha256$600000$4raNjbxK9dGMvwIVYYgTog==$P7zvKA+cTEGhZnk3h9Dzj4ev/TCM0CuBc5bZDn6sUfE=', '샘플회원06'),
    ('20260723090000007', 'sample-user-07@example.com', 'pbkdf2_sha256$600000$4raNjbxK9dGMvwIVYYgTog==$P7zvKA+cTEGhZnk3h9Dzj4ev/TCM0CuBc5bZDn6sUfE=', '샘플회원07'),
    ('20260723090000008', 'sample-user-08@example.com', 'pbkdf2_sha256$600000$4raNjbxK9dGMvwIVYYgTog==$P7zvKA+cTEGhZnk3h9Dzj4ev/TCM0CuBc5bZDn6sUfE=', '샘플회원08'),
    ('20260723090000009', 'sample-user-09@example.com', 'pbkdf2_sha256$600000$4raNjbxK9dGMvwIVYYgTog==$P7zvKA+cTEGhZnk3h9Dzj4ev/TCM0CuBc5bZDn6sUfE=', '샘플회원09'),
    ('20260723090000010', 'sample-user-10@example.com', 'pbkdf2_sha256$600000$4raNjbxK9dGMvwIVYYgTog==$P7zvKA+cTEGhZnk3h9Dzj4ev/TCM0CuBc5bZDn6sUfE=', '샘플회원10')
on conflict do nothing;

insert into public.posts (post_id, user_id, title, content)
values
    ('20260723091000001', '20260723090000001', '첫 번째 샘플 게시글', '첫 번째 게시글 내용입니다.'),
    ('20260723091000002', '20260723090000002', '두 번째 샘플 게시글', '두 번째 게시글 내용입니다.'),
    ('20260723091000003', '20260723090000003', '세 번째 샘플 게시글', '세 번째 게시글 내용입니다.'),
    ('20260723091000004', '20260723090000004', '네 번째 샘플 게시글', '네 번째 게시글 내용입니다.'),
    ('20260723091000005', '20260723090000005', '다섯 번째 샘플 게시글', '다섯 번째 게시글 내용입니다.')
on conflict do nothing;

insert into public.comments (comment_id, post_id, user_id, content)
values
    ('20260723092000001', '20260723091000001', '20260723090000002', '첫 번째 게시글의 댓글입니다.'),
    ('20260723092000002', '20260723091000001', '20260723090000003', '첫 번째 게시글의 두 번째 댓글입니다.'),
    ('20260723092000003', '20260723091000002', '20260723090000001', '두 번째 게시글의 댓글입니다.'),
    ('20260723092000004', '20260723091000003', '20260723090000004', '세 번째 게시글의 댓글입니다.'),
    ('20260723092000005', '20260723091000004', '20260723090000005', '네 번째 게시글의 댓글입니다.')
on conflict do nothing;

insert into public.supports (support_id, user_id, title, content, status)
values
    ('20260723093000001', '20260723090000001', '로그인 문의', '로그인 기능에 대해 문의합니다.', 'pending'),
    ('20260723093000002', '20260723090000002', '게시글 문의', '게시글 수정 방법을 문의합니다.', 'answered'),
    ('20260723093000003', '20260723090000003', '회원 정보 문의', '회원 이름 변경을 문의합니다.', 'closed'),
    ('20260723093000004', '20260723090000004', '댓글 문의', '댓글 삭제 방법을 문의합니다.', 'pending'),
    ('20260723093000005', '20260723090000005', '서비스 문의', '서비스 이용 방법을 문의합니다.', 'answered')
on conflict do nothing;

commit;
