begin;

create table if not exists public.posts (
    post_id text primary key,
    user_id text not null,
    title text not null,
    content text not null,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint posts_post_id_format_check check (post_id ~ '^[0-9]{17}$'),
    constraint posts_user_id_fk foreign key (user_id)
        references public.users (user_id) on update cascade on delete restrict,
    constraint posts_title_length_check check (char_length(btrim(title)) between 1 and 200),
    constraint posts_content_not_empty_check check (char_length(btrim(content)) >= 1)
);

create index if not exists posts_user_id_idx on public.posts (user_id);
create index if not exists posts_created_at_idx on public.posts (created_at desc);

drop trigger if exists posts_set_updated_at on public.posts;
create trigger posts_set_updated_at
before update on public.posts
for each row execute function public.set_updated_at();

commit;
