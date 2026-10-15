create extension if not exists pgcrypto;

create table if not exists public.projects (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null,
  name text not null,
  slug text not null,
  created_at timestamptz not null default now(),
  unique (owner_id, slug)
);

create table if not exists public.eval_datasets (
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null references public.projects(id) on delete cascade,
  name text not null,
  version integer not null default 1,
  created_at timestamptz not null default now()
);

create table if not exists public.eval_runs (
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null references public.projects(id) on delete cascade,
  dataset_id uuid references public.eval_datasets(id) on delete set null,
  branch text,
  commit_sha text,
  status text not null check (status in ('queued','running','passed','failed','error')),
  task_success numeric(6,5),
  groundedness numeric(6,5),
  average_score numeric(6,5),
  average_latency_ms numeric(12,2),
  total_cost_usd numeric(14,6),
  started_at timestamptz not null default now(),
  completed_at timestamptz
);

create table if not exists public.eval_case_results (
  id uuid primary key default gen_random_uuid(),
  run_id uuid not null references public.eval_runs(id) on delete cascade,
  external_case_id text not null,
  correctness numeric(6,5) not null,
  groundedness numeric(6,5) not null,
  required_terms numeric(6,5) not null,
  score numeric(6,5) not null,
  passed boolean not null,
  reason text,
  unique (run_id, external_case_id)
);

create table if not exists public.trace_spans (
  id uuid primary key default gen_random_uuid(),
  run_id uuid not null references public.eval_runs(id) on delete cascade,
  parent_span_id uuid references public.trace_spans(id) on delete cascade,
  span_type text not null check (span_type in ('agent','model','tool','handoff','guardrail')),
  name text not null,
  started_at timestamptz not null,
  ended_at timestamptz,
  latency_ms integer,
  input jsonb,
  output jsonb,
  metadata jsonb not null default '{}'::jsonb
);

create index if not exists eval_runs_project_started_idx
  on public.eval_runs(project_id, started_at desc);

create index if not exists trace_spans_run_started_idx
  on public.trace_spans(run_id, started_at);

alter table public.projects enable row level security;
alter table public.eval_datasets enable row level security;
alter table public.eval_runs enable row level security;
alter table public.eval_case_results enable row level security;
alter table public.trace_spans enable row level security;

create policy "project owners can manage projects"
  on public.projects for all
  using (owner_id = auth.uid())
  with check (owner_id = auth.uid());

create policy "project owners can read datasets"
  on public.eval_datasets for select
  using (exists (
    select 1 from public.projects p
    where p.id = project_id and p.owner_id = auth.uid()
  ));

create policy "project owners can read runs"
  on public.eval_runs for select
  using (exists (
    select 1 from public.projects p
    where p.id = project_id and p.owner_id = auth.uid()
  ));

create policy "project owners can read case results"
  on public.eval_case_results for select
  using (exists (
    select 1 from public.eval_runs r
    join public.projects p on p.id = r.project_id
    where r.id = run_id and p.owner_id = auth.uid()
  ));

create policy "project owners can read traces"
  on public.trace_spans for select
  using (exists (
    select 1 from public.eval_runs r
    join public.projects p on p.id = r.project_id
    where r.id = run_id and p.owner_id = auth.uid()
  ));
