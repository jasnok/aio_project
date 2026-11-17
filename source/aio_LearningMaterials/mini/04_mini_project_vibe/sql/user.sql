begin;

create table if not exists public.users (
    user_id text primary key,
    email text not null,
    password text not null,
    name text not null,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint users_user_id_format_check check (user_id ~ '^[0-9]{17}$'),
    constraint users_email_length_check check (char_length(email) between 3 and 254),
    constraint users_email_lowercase_check check (email = lower(email)),
    constraint users_email_format_check check (email ~ '^[^[:space:]@]+@[^[:space:]@]+\.[^[:space:]@]+$'),
    constraint users_password_not_empty_check check (char_length(password) > 0),
    constraint users_name_length_check check (char_length(btrim(name)) between 1 and 100)
);

create unique index if not exists users_email_unique_idx on public.users (lower(email));

create or replace function public.set_updated_at()
returns trigger
language plpgsql
security invoker
set search_path = public
as $$
begin
    new.updated_at = now();
    return new;
end;
$$;

drop trigger if exists users_set_updated_at on public.users;
create trigger users_set_updated_at
before update on public.users
for each row execute function public.set_updated_at();

commit;
