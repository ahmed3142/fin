-- Project 5 — Industry Value-Chain :: Postgres schema (Supabase-ready)
-- Generated from the DuckDB warehouse. Run this first.

create schema if not exists industry;
set search_path = industry, public;

create table if not exists industry.dim_region (
  region_id bigint,
  region_code text,
  region_name text,
  primary key (region_id)
);

create table if not exists industry.dim_vintage (
  vintage_id bigint,
  vintage_year bigint,
  data_asof_date text,
  ttm_through text,
  asc842_lease_break boolean,
  tcja174_rnd_break boolean,
  primary key (vintage_id)
);
comment on table industry.dim_vintage is 'Annual Damodaran refresh. asc842_lease_break / tcja174_rnd_break flag methodology breaks (2019 leases, 2022 R&D) that make adjusted columns non-comparable across vintages.';

create table if not exists industry.dim_industry (
  industry_id bigint,
  industry_name text,
  sector_group text,
  is_financial boolean,
  is_total_market_rollup boolean,
  region_id bigint,
  primary key (industry_id)
);
comment on table industry.dim_industry is 'Conformed industry dimension (Damodaran ~94-industry US taxonomy). is_financial flags banks/insurers whose margins are non-comparable.';

create table if not exists industry.map_industry_alias (
  industry_name_raw text,
  canonical_name text,
  industry_id bigint,
  match_method text,
  confidence double precision,
  primary key (industry_name_raw)
);
comment on table industry.map_industry_alias is 'Entity-resolution crosswalk for the dirty free-text join key (e.g. the real ''Heathcare'' misspelling).';

create table if not exists industry.fact_dividends_fcfe (
  industry_id bigint,
  num_firms bigint,
  dividends double precision,
  payout double precision,
  dividends_plus_buybacks double precision,
  cash_return_pct_net_income double precision,
  fcfe double precision,
  net_cash_returned_pct_fcfe double precision,
  vintage_id bigint,
  region_id bigint,
  primary key (industry_id, vintage_id, region_id)
);

create table if not exists industry.fact_financing_flows (
  industry_id bigint,
  num_firms bigint,
  dividends double precision,
  buybacks double precision,
  equity_issuance double precision,
  net_equity_change_usd double precision,
  net_equity_change_pct_book_equity double precision,
  debt_repaid double precision,
  debt_raised double precision,
  net_debt_change_usd double precision,
  net_debt_change_pct_total_debt double precision,
  change_in_lease_debt double precision,
  vintage_id bigint,
  region_id bigint,
  primary key (industry_id, vintage_id, region_id)
);
comment on table industry.fact_financing_flows is 'Financing flows by industry. NOTE net_equity_change_usd = equity_issuance - buybacks (dividends NOT subtracted), verified against the data despite the source file''s own note.';

create table if not exists industry.fact_growth_fundamental_eb (
  industry_id bigint,
  num_firms bigint,
  roc double precision,
  reinvestment_rate double precision,
  expected_growth_ebit double precision,
  vintage_id bigint,
  region_id bigint,
  primary key (industry_id, vintage_id, region_id)
);

create table if not exists industry.fact_industry_firmcount (
  industry_id bigint,
  num_firms bigint,
  dataset_code text,
  vintage_id bigint,
  region_id bigint,
  primary key (industry_id, vintage_id, region_id, dataset_code)
);

create table if not exists industry.fact_margins (
  industry_id bigint,
  num_firms bigint,
  gross_margin double precision,
  net_margin double precision,
  pretax_operating_margin double precision,
  pretax_lease_rnd_adj_operating_margin double precision,
  ebitda_sales double precision,
  ebitdarnd_sales double precision,
  rnd_sales double precision,
  sga_sales double precision,
  sbc_sales double precision,
  vintage_id bigint,
  region_id bigint,
  primary key (industry_id, vintage_id, region_id)
);
comment on table industry.fact_margins is 'Operating & net margins. pretax_lease_rnd_adj_operating_margin is Damodaran''s own adjusted figure (uses his capitalized-R&D estimate).';

create table if not exists industry.fact_multiples_pe (
  industry_id bigint,
  num_firms bigint,
  current_pe double precision,
  trailing_pe double precision,
  forward_pe double precision,
  expected_growth double precision,
  peg double precision,
  vintage_id bigint,
  region_id bigint,
  primary key (industry_id, vintage_id, region_id)
);

create table if not exists industry.fact_multiples_ps (
  industry_id bigint,
  num_firms bigint,
  price_sales double precision,
  ev_sales double precision,
  net_margin double precision,
  pretax_operating_margin double precision,
  vintage_id bigint,
  region_id bigint,
  primary key (industry_id, vintage_id, region_id)
);

create table if not exists industry.fact_rnd (
  industry_id bigint,
  num_firms bigint,
  rnd_capitalized_usd_m double precision,
  cap_rnd_pct_invested_capital double precision,
  rnd_ltm_usd_m double precision,
  current_rnd_pct_revenue double precision,
  rnd_cagr_5y double precision,
  vintage_id bigint,
  region_id bigint,
  primary key (industry_id, vintage_id, region_id)
);
comment on table industry.fact_rnd is 'R&D. rnd_capitalized_usd_m and cap_rnd_pct_invested_capital are Damodaran ESTIMATES (assumed amortizable life), not reported GAAP.';

-- foreign keys
alter table industry.map_industry_alias add constraint map_industry_alias_industry_fk foreign key (industry_id) references industry.dim_industry(industry_id);
alter table industry.fact_dividends_fcfe add constraint fact_dividends_fcfe_industry_fk foreign key (industry_id) references industry.dim_industry(industry_id);
alter table industry.fact_dividends_fcfe add constraint fact_dividends_fcfe_vintage_fk foreign key (vintage_id) references industry.dim_vintage(vintage_id);
alter table industry.fact_dividends_fcfe add constraint fact_dividends_fcfe_region_fk foreign key (region_id) references industry.dim_region(region_id);
alter table industry.fact_financing_flows add constraint fact_financing_flows_industry_fk foreign key (industry_id) references industry.dim_industry(industry_id);
alter table industry.fact_financing_flows add constraint fact_financing_flows_vintage_fk foreign key (vintage_id) references industry.dim_vintage(vintage_id);
alter table industry.fact_financing_flows add constraint fact_financing_flows_region_fk foreign key (region_id) references industry.dim_region(region_id);
alter table industry.fact_growth_fundamental_eb add constraint fact_growth_fundamental_eb_industry_fk foreign key (industry_id) references industry.dim_industry(industry_id);
alter table industry.fact_growth_fundamental_eb add constraint fact_growth_fundamental_eb_vintage_fk foreign key (vintage_id) references industry.dim_vintage(vintage_id);
alter table industry.fact_growth_fundamental_eb add constraint fact_growth_fundamental_eb_region_fk foreign key (region_id) references industry.dim_region(region_id);
alter table industry.fact_industry_firmcount add constraint fact_industry_firmcount_industry_fk foreign key (industry_id) references industry.dim_industry(industry_id);
alter table industry.fact_industry_firmcount add constraint fact_industry_firmcount_vintage_fk foreign key (vintage_id) references industry.dim_vintage(vintage_id);
alter table industry.fact_industry_firmcount add constraint fact_industry_firmcount_region_fk foreign key (region_id) references industry.dim_region(region_id);
alter table industry.fact_margins add constraint fact_margins_industry_fk foreign key (industry_id) references industry.dim_industry(industry_id);
alter table industry.fact_margins add constraint fact_margins_vintage_fk foreign key (vintage_id) references industry.dim_vintage(vintage_id);
alter table industry.fact_margins add constraint fact_margins_region_fk foreign key (region_id) references industry.dim_region(region_id);
alter table industry.fact_multiples_pe add constraint fact_multiples_pe_industry_fk foreign key (industry_id) references industry.dim_industry(industry_id);
alter table industry.fact_multiples_pe add constraint fact_multiples_pe_vintage_fk foreign key (vintage_id) references industry.dim_vintage(vintage_id);
alter table industry.fact_multiples_pe add constraint fact_multiples_pe_region_fk foreign key (region_id) references industry.dim_region(region_id);
alter table industry.fact_multiples_ps add constraint fact_multiples_ps_industry_fk foreign key (industry_id) references industry.dim_industry(industry_id);
alter table industry.fact_multiples_ps add constraint fact_multiples_ps_vintage_fk foreign key (vintage_id) references industry.dim_vintage(vintage_id);
alter table industry.fact_multiples_ps add constraint fact_multiples_ps_region_fk foreign key (region_id) references industry.dim_region(region_id);
alter table industry.fact_rnd add constraint fact_rnd_industry_fk foreign key (industry_id) references industry.dim_industry(industry_id);
alter table industry.fact_rnd add constraint fact_rnd_vintage_fk foreign key (vintage_id) references industry.dim_vintage(vintage_id);
alter table industry.fact_rnd add constraint fact_rnd_region_fk foreign key (region_id) references industry.dim_region(region_id);
