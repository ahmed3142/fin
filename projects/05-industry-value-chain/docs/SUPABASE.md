# Load the warehouse into Supabase (web)

No connection string, driver, or secret needed — everything is copy-paste into the
Supabase **SQL Editor**. Files live in [`../sql/postgres/`](../sql/postgres/).

## 1. Create / open a project
[app.supabase.com](https://app.supabase.com) → **New project** (free tier is fine).
Wait until the database is provisioned.

## 2. Run the four SQL files, in order
Left sidebar → **SQL Editor** → **New query**. Paste and **Run** each file:

1. `sql/postgres/01_schema.sql`  → creates schema `industry` + all tables (PK/FK/comments)
2. `sql/postgres/02_seed.sql`    → inserts the data (94 industries × 8 facts)
3. `sql/postgres/03_mart_view.sql` → creates `industry.mart_industry_wide`
4. `sql/postgres/04_rls.sql`     → enables Row Level Security + a public-read policy per table

Each should report success. (Run them in this order — 02 needs 01, etc.)

## 3. Expose the schema to the API (once)
**Project Settings → API → Exposed schemas** → add **`industry`** → save.
Now every table is reachable via the auto-generated REST + GraphQL API.

## 4. Verify
Run in the SQL Editor:
```sql
select count(*) as industries from industry.dim_industry;      -- expect 94
select count(*) from industry.mart_industry_wide;              -- expect 94
```
Then browse **Table Editor → schema `industry`** → open `mart_industry_wide`.

## 5. Sample queries (the thesis)
**Biggest reported-vs-adjusted margin gaps (the R&D distortion):**
```sql
select industry_name,
       round(mgn_pretax_operating_margin, 3)                as reported_margin,
       round(mgn_pretax_lease_rnd_adj_operating_margin, 3)  as adjusted_margin,
       round(mgn_rnd_sales, 3)                              as rnd_sales
from industry.mart_industry_wide
where not is_financial
order by abs(mgn_pretax_lease_rnd_adj_operating_margin - mgn_pretax_operating_margin) desc
limit 10;
```
**Does EV/Sales line up with the adjusted margin? (top-priced industries):**
```sql
select industry_name,
       round(ps_ev_sales, 2)                                as ev_sales,
       round(mgn_pretax_operating_margin, 3)                as reported,
       round(mgn_pretax_lease_rnd_adj_operating_margin, 3)  as adjusted
from industry.mart_industry_wide
where not is_financial and ps_ev_sales is not null
order by ps_ev_sales desc
limit 15;
```
**Leverage-funded capital return (buybacks while raising debt):**
```sql
select industry_name,
       round(ff_net_equity_change_usd, 0) as net_equity_change_usd,
       round(ff_net_debt_change_usd, 0)   as net_debt_change_usd
from industry.mart_industry_wide
where ff_net_equity_change_usd < 0 and ff_net_debt_change_usd > 0
order by ff_net_debt_change_usd desc
limit 15;
```

## 6. Read it from anywhere (REST)
With the schema exposed and the public-read policy in place:
```
GET https://<PROJECT-REF>.supabase.co/rest/v1/mart_industry_wide?select=industry_name,ps_ev_sales,mgn_pretax_operating_margin
Headers:  apikey: <your anon key>   Accept-Profile: industry
```

## Alternative — CSV import (no SQL)
If you prefer the UI: run `01_schema.sql` only, then **Table Editor → import data from CSV**
using the files in `sql/postgres/csv/` (one per table). Load the dims first, then the facts.

## Notes
- The public-read RLS policy is **read-only** and intended for a portfolio/demo. Remove it
  or tighten it before putting anything sensitive behind the same project.
- Data © Aswath Damodaran (NYU Stern), educational use — see the repo `NOTICE`.
