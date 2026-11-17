begin;

create table if not exists public.supports (
    support_id text primary key,
    user_id text not null,
    title text not null,
    content text not null,
    status text not null default 'pending',
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint supports_support_id_format_check check (support_id ~ '^[0-9]{17}$'),
    constraint supports_user_id_fk foreign key (user_id)
        references public.users (user_id) on update cascade on delete restrict,
    constraint supports_title_length_check check (char_length(btrim(title)) between 1 and 200),
    constraint supports_content_not_empty_check check (char_length(btrim(content)) >= 1),
    constraint supports_status_check check (status in ('pending', 'answered', 'closed'))
);

create index if not exists supports_user_id_idx on public.supports (user_id);
create index if not exists supports_status_idx on public.supports (status);

drop trigger if exists supports_set_updated_at on public.supports;
create trigger supports_set_updated_at
before update on public.supports
for each row execute function public.set_updated_at();

commit;
