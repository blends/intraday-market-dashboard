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

- **Caching + refresh interplay:** `@st.cache_data(ttl=...)` (60s for the screener, 300s for financials) is combined with `streamlit-autorefresh` (`st_autorefresh`) which forces a full-script rerun on an interval. The interval itself is dynamic via `get_refresh_interval()` / `is_market_open()` (US/Eastern, 9:30–16:00 weekdays). Every 5th refresh, `main()` calls `st.cache_data.clear()` to prevent stale data and memory growth.

- **Styling is selector-based and fragile:** `inject_custom_css()` writes one large `<style>` block (via `unsafe_allow_html=True`) that targets Streamlit's internal DOM, e.g. `div[data-testid="stMetric"]`, `[data-testid="stMetricDelta"]`, `stDataFrame`. These internal `data-testid` selectors are not a public API and can change between Streamlit versions — assume CSS may need re-tuning after any version bump. Sector cards, the header, and growth badges are also rendered as raw HTML strings rather than native widgets.

- **Sector classification:** `SECTOR_MAP` is a large hardcoded ticker→sector dictionary in `app.py`. `get_sector_for_symbol()` checks it first, then falls back to yfinance's `info['sector']`. Unmapped tickers become `'Other'` and are filtered out of the sector visualizations.

- **Config flow:** `DEFAULT_CONFIG` seeds `st.session_state['config']`; `render_sidebar()` mutates it live each run. There is no persistence between sessions.

## Notes / gotchas

- The README references a `.streamlit/config.toml` for theming, but **that file does not exist** in the repo — theming currently lives entirely in the CSS block.
- `requirements.txt` pins `streamlit>=1.37.0`, which predates many current APIs (fragments, native `st.metric` borders/sparklines, the `width=` parameter that replaces the now-deprecated `use_container_width`).
- The "Rel. Volume" intraday metric is an acknowledged placeholder/estimate, not a true RVOL (no historical average volume is fetched).
