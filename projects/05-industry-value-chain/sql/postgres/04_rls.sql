-- Project 5 — Row Level Security: public read-only (Supabase web/REST needs this).
set search_path = industry, public;

alter table industry.dim_region enable row level security;
create policy "public read dim_region" on industry.dim_region for select using (true);
alter table industry.dim_vintage enable row level security;
create policy "public read dim_vintage" on industry.dim_vintage for select using (true);
alter table industry.dim_industry enable row level security;
create policy "public read dim_industry" on industry.dim_industry for select using (true);
alter table industry.map_industry_alias enable row level security;
create policy "public read map_industry_alias" on industry.map_industry_alias for select using (true);
alter table industry.fact_dividends_fcfe enable row level security;
create policy "public read fact_dividends_fcfe" on industry.fact_dividends_fcfe for select using (true);
alter table industry.fact_financing_flows enable row level security;
create policy "public read fact_financing_flows" on industry.fact_financing_flows for select using (true);
alter table industry.fact_growth_fundamental_eb enable row level security;
create policy "public read fact_growth_fundamental_eb" on industry.fact_growth_fundamental_eb for select using (true);
alter table industry.fact_industry_firmcount enable row level security;
create policy "public read fact_industry_firmcount" on industry.fact_industry_firmcount for select using (true);
alter table industry.fact_margins enable row level security;
create policy "public read fact_margins" on industry.fact_margins for select using (true);
alter table industry.fact_multiples_pe enable row level security;
create policy "public read fact_multiples_pe" on industry.fact_multiples_pe for select using (true);
alter table industry.fact_multiples_ps enable row level security;
create policy "public read fact_multiples_ps" on industry.fact_multiples_ps for select using (true);
alter table industry.fact_rnd enable row level security;
create policy "public read fact_rnd" on industry.fact_rnd for select using (true);

-- expose the schema to the Supabase API (Dashboard > Settings > API > Exposed schemas)
grant usage on schema industry to anon, authenticated;
grant select on all tables in schema industry to anon, authenticated;
