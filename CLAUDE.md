# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
pip install -r requirements.txt   # Install dependencies
streamlit run app.py              # Run the dashboard (serves at http://localhost:8501)
```

There is no test suite, linter config, or build step in this repo. The entire application is a single file (`app.py`).

## What this is

A Streamlit financial dashboard intended for **passive display on a Fire TV** (kiosk mode), deployed to Streamlit Cloud. This "always-on, no interaction" target drives several design choices: heavy custom CSS to hide Streamlit chrome, burn-in-prevention animations, and timed auto-refresh rather than user-triggered updates.

## Architecture

Everything lives in `app.py`, organized into labeled sections (CONFIG, CSS, UTILITY, DATA FETCHING, CHART, DISPLAY, SIDEBAR, MAIN). Key cross-cutting concepts:

- **Data sources (two of them):**
  - `get_most_active_stocks()` hits an **undocumented Yahoo Finance screener endpoint** (`query1.finance.yahoo.com/.../most_actives`) with a browser User-Agent. This is the primary feed and is fragile — it can break or rate-limit without notice. `st.session_state['cached_stocks']` holds the last good payload as a fallback so the display degrades gracefully.
  - `get_financial_data()` uses `yfinance` per-symbol for growth screening. Because this is one network call per ticker, `screen_growth_stocks()` deliberately caps itself to the top ~35 stocks to avoid rate limits.

- **Caching + refresh interplay:** `@st.cache_data(ttl=...)` (60s for the screener, 300s for financials) is the freshness mechanism — TTL expiry, not manual clearing, is what bounds staleness. The dashboard body lives in a nested `@st.fragment(run_every=refresh_interval)` (`render_dashboard()` defined inside `main()`), so only that fragment reruns on the interval; the sidebar and the CSS injection are not rebuilt, which avoids the full-page flicker. Sidebar interactions trigger a normal full rerun, which re-reads `run_every` and picks up an interval the user just changed. The interval is dynamic via `get_refresh_interval()` / `is_market_open()` (US/Eastern, 9:30–16:00 weekdays). The only caller of `st.cache_data.clear()` is the "Force Refresh" sidebar button. (Note: the README still describes the old `streamlit-autorefresh` + "clear every 5th refresh" design — that has been replaced by fragments and is no longer accurate.)

- **Styling is two layers — native theme + custom CSS.** `.streamlit/config.toml` defines a native dark `[theme]` that mirrors the `COLORS` palette (accent `#00d4ff`, bg `#0a0e27`, green/red deltas, chart series colors, dataframe header). This styles Streamlit's own chrome (sidebar, widgets, dataframes) without fragile selectors. On top of that, `inject_custom_css()` writes one large `<style>` block (via `unsafe_allow_html=True`) targeting internal DOM, e.g. `div[data-testid="stMetric"]`, `[data-testid="stMetricDelta"]`, `stDataFrame`. Those `data-testid` selectors are **not** a public API and can change between Streamlit versions — assume the CSS block may need re-tuning after any version bump, but the `config.toml` theme should survive. **Keep the two palettes in sync:** `COLORS` in `app.py`, the `:root` CSS variables, and `config.toml` all hardcode the same hex values. Sector cards, the header, and growth badges are rendered as raw HTML strings rather than native widgets.

- **Sector classification:** `SECTOR_MAP` is a large hardcoded ticker→sector dictionary in `app.py`. `get_sector_for_symbol()` checks it first, then falls back to yfinance's `info['sector']`. Unmapped tickers become `'Other'` and are filtered out of the sector visualizations.

- **Config flow:** `DEFAULT_CONFIG` seeds `st.session_state['config']`; `render_sidebar()` mutates it live each run. There is no persistence between sessions.

## Notes / gotchas

- `requirements.txt` pins `streamlit>=1.57.0`, so current APIs are available and in use: `@st.fragment(run_every=...)` for the refresh loop, native `[theme]` in `config.toml`, and the `width='stretch'` parameter (which has replaced the deprecated `use_container_width=True` throughout — keep using `width=` for new widgets/charts).
- `requirements.txt` lists no pinned `streamlit-autorefresh`; the import has been removed. Don't reintroduce it — the fragment handles refresh.
- The "Rel. Volume" intraday metric is now a true RVOL: it's the median of per-stock `regularMarketVolume / averageDailyVolume3Month` across the fetched stocks. The avg-volume and 52-week-high/low fields are read straight from the screener payload (no extra per-symbol yfinance calls), so they're available for every fetched stock. The "New Highs"/"New Lows" breadth metrics count stocks trading within 5% of their 52-week high/low. All three are computed in `calculate_breadth_indicators()`.
- The README is partially stale (still lists `streamlit-autorefresh`, "periodic cache clearing every 5 refreshes", and a `market_dashboard/` project dir that doesn't exist). Treat this file as the source of truth over the README for architecture.
