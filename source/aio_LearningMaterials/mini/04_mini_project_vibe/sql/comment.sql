begin;

create table if not exists public.comments (
    comment_id text primary key,
    post_id text not null,
    user_id text not null,
    content text not null,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint comments_comment_id_format_check check (comment_id ~ '^[0-9]{17}$'),
    constraint comments_post_id_fk foreign key (post_id)
        references public.posts (post_id) on update cascade on delete cascade,
    constraint comments_user_id_fk foreign key (user_id)
        references public.users (user_id) on update cascade on delete restrict,
    constraint comments_content_not_empty_check check (char_length(btrim(content)) >= 1)
);

create index if not exists comments_post_id_idx on public.comments (post_id);
create index if not exists comments_user_id_idx on public.comments (user_id);

drop trigger if exists comments_set_updated_at on public.comments;
create trigger comments_set_updated_at
before update on public.comments
for each row execute function public.set_updated_at();

commit;
