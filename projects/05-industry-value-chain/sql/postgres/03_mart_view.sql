-- Project 5 — wide analytical mart. Run after seed.
set search_path = industry, public;

create or replace view industry.mart_industry_wide as
select
  i.industry_id,
  i.industry_name,
  i.sector_group,
  i.is_financial,
  f_div.num_firms as div_num_firms,
  f_div.dividends as div_dividends,
  f_div.payout as div_payout,
  f_div.dividends_plus_buybacks as div_dividends_plus_buybacks,
  f_div.cash_return_pct_net_income as div_cash_return_pct_net_income,
  f_div.fcfe as div_fcfe,
  f_div.net_cash_returned_pct_fcfe as div_net_cash_returned_pct_fcfe,
  f_ff.num_firms as ff_num_firms,
  f_ff.dividends as ff_dividends,
  f_ff.buybacks as ff_buybacks,
  f_ff.equity_issuance as ff_equity_issuance,
  f_ff.net_equity_change_usd as ff_net_equity_change_usd,
  f_ff.net_equity_change_pct_book_equity as ff_net_equity_change_pct_book_equity,
  f_ff.debt_repaid as ff_debt_repaid,
  f_ff.debt_raised as ff_debt_raised,
  f_ff.net_debt_change_usd as ff_net_debt_change_usd,
  f_ff.net_debt_change_pct_total_debt as ff_net_debt_change_pct_total_debt,
  f_ff.change_in_lease_debt as ff_change_in_lease_debt,
  f_gr.num_firms as gr_num_firms,
  f_gr.roc as gr_roc,
  f_gr.reinvestment_rate as gr_reinvestment_rate,
  f_gr.expected_growth_ebit as gr_expected_growth_ebit,
  f_mgn.num_firms as mgn_num_firms,
  f_mgn.gross_margin as mgn_gross_margin,
  f_mgn.net_margin as mgn_net_margin,
  f_mgn.pretax_operating_margin as mgn_pretax_operating_margin,
  f_mgn.pretax_lease_rnd_adj_operating_margin as mgn_pretax_lease_rnd_adj_operating_margin,
  f_mgn.ebitda_sales as mgn_ebitda_sales,
  f_mgn.ebitdarnd_sales as mgn_ebitdarnd_sales,
  f_mgn.rnd_sales as mgn_rnd_sales,
  f_mgn.sga_sales as mgn_sga_sales,
  f_mgn.sbc_sales as mgn_sbc_sales,
  f_pe.num_firms as pe_num_firms,
  f_pe.current_pe as pe_current_pe,
  f_pe.trailing_pe as pe_trailing_pe,
  f_pe.forward_pe as pe_forward_pe,
  f_pe.expected_growth as pe_expected_growth,
  f_pe.peg as pe_peg,
  f_ps.num_firms as ps_num_firms,
  f_ps.price_sales as ps_price_sales,
  f_ps.ev_sales as ps_ev_sales,
  f_ps.net_margin as ps_net_margin,
  f_ps.pretax_operating_margin as ps_pretax_operating_margin,
  f_rnd.num_firms as rnd_num_firms,
  f_rnd.rnd_capitalized_usd_m as rnd_rnd_capitalized_usd_m,
  f_rnd.cap_rnd_pct_invested_capital as rnd_cap_rnd_pct_invested_capital,
  f_rnd.rnd_ltm_usd_m as rnd_rnd_ltm_usd_m,
  f_rnd.current_rnd_pct_revenue as rnd_current_rnd_pct_revenue,
  f_rnd.rnd_cagr_5y as rnd_rnd_cagr_5y
from industry.dim_industry i
left join industry.fact_dividends_fcfe f_div on f_div.industry_id = i.industry_id
left join industry.fact_financing_flows f_ff on f_ff.industry_id = i.industry_id
left join industry.fact_growth_fundamental_eb f_gr on f_gr.industry_id = i.industry_id
left join industry.fact_margins f_mgn on f_mgn.industry_id = i.industry_id
left join industry.fact_multiples_pe f_pe on f_pe.industry_id = i.industry_id
left join industry.fact_multiples_ps f_ps on f_ps.industry_id = i.industry_id
left join industry.fact_rnd f_rnd on f_rnd.industry_id = i.industry_id;
