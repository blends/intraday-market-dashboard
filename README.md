# Market Dashboard for passive displays

A polished, dynamic financial dashboard built with Streamlit, optimized for passive display on Fire TV devices. Features animated metric cards, sector analysis, intraday indicators, and reliable auto-refresh.

## What's New

- **Animated Metric Cards**: Glassmorphism effects with scanning light animations
- **Sector Performance**: Real-time sector breakdown with treemap visualization
- **Intraday Indicators**: A/D ratio, breadth, relative volume, strong movers
- **Reliable Auto-Refresh**: Using `streamlit-autorefresh` component (not JavaScript injection)
- **Enhanced CSS**: Full kiosk mode, burn-in prevention, TV-optimized styling
- **Better Performance**: Optimized caching with TTL, periodic cache clearing
- **More Stocks**: Increased default to 75 stocks for better sector coverage

## 🖥️ Screenshots

The dashboard features:
- Animated header with market status badge
- 6 primary metrics with scanning light effect
- 5 intraday indicators (A/D ratio, breadth, relative volume)
- Top movers chart (horizontal bar)
- Volume leaders chart (vertical bar with gain/loss coloring)
- Sector performance metrics + treemap
- Gainers/Losers tables
- Volume leaders table
- Growth stocks screener (4/4 criteria)

## Quick Start

### Local Development

```bash
cd market_dashboard

# Install dependencies
pip install -r requirements.txt

# Run the dashboard
streamlit run app.py
```

Access at `http://localhost:8501`

### Fire TV Deployment

1. **Deploy to Streamlit Cloud**:
   - Push to GitHub
   - Connect at [share.streamlit.io](https://share.streamlit.io)
   - One-click deploy

2. **On Fire TV**:
   - Install "Fully Kiosk Browser" (recommended) or "Silk Browser"
   - Navigate to your dashboard URL
   - Enable fullscreen/kiosk mode

## Configuration

### Via Sidebar (Runtime)
- Refresh intervals (market open/closed)
- Growth screening thresholds
- Number of stocks to fetch
- Biotech exclusion toggle

### Via config.toml (Theme)
Edit `.streamlit/config.toml`:
```toml
[theme]
primaryColor = "#00d4ff"      # Accent color
backgroundColor = "#0a0e27"   # Main background
secondaryBackgroundColor = "#1a1f3a"
textColor = "#ffffff"
```

## Features Explained

### Metric Cards
Custom CSS creates the polished look:
- Glassmorphism background with backdrop blur
- Scanning light animation (cyan accent)
- Hover lift effect with glow
- Burn-in prevention (subtle position shift)

### Intraday Indicators

| Indicator | Description |
|-----------|-------------|
| **A/D Ratio** | Advance/Decline ratio - bullish >1.5, bearish <0.67 |
| **Strong Gainers** | Stocks up more than 5% |
| **Strong Losers** | Stocks down more than 5% |
| **Rel. Volume** | Approximate relative volume vs baseline |
| **Breadth** | Percentage of stocks advancing |

### Sector Performance
- Aggregates stocks by sector
- Shows average change per sector
- Treemap visualization with color coding
- Top 10 sectors displayed

### Growth Stock Screener
Screens for stocks meeting ALL criteria:
1. Revenue Growth ≥ 100% (configurable)
2. EPS Growth ≥ 25% (configurable)
3. Price ≥ $10 (configurable)
4. 50-day avg volume ≥ 100,000
5. Not biotech/pharma (configurable)

## Technical Details

### Auto-Refresh
Uses `streamlit-autorefresh` component:
- Market open: 5 min (configurable)
- Market closed: 30 min (configurable)
- Periodic cache clearing every 5 refreshes

### Caching Strategy
```python
@st.cache_data(ttl=60)   # Market data - 1 min
@st.cache_data(ttl=300)  # Financial details - 5 min
```

### Performance Optimizations
- TTL-based caching prevents stale data
- Periodic cache clearing prevents memory growth
- Limited API calls for growth screening (top 35 stocks)
- Efficient DataFrame operations

### CSS Architecture
- Global CSS injection via `st.markdown`
- No iframe-based components
- Native Streamlit components with custom styling
- CSS animations for visual polish

## Project Structure

```
market_dashboard_v2/
├── app.py                    # Main application
├── requirements.txt          # Dependencies
├── README.md                 # This file
└── .streamlit/
    └── config.toml           # Theme configuration
```

## Color Palette

| Color | Hex | Usage |
|-------|-----|-------|
| Background Primary | `#0a0e27` | Main background |
| Background Secondary | `#1a1f3a` | Cards, gradient |
| Positive | `#00ff88` | Gains, bullish |
| Negative | `#ff3366` | Losses, bearish |
| Accent | `#00d4ff` | Headers, highlights |
| Accent Secondary | `#667eea` | Badges, gradients |
| Text Primary | `#ffffff` | Main text |
| Text Secondary | `#8892b0` | Labels, subtitles |

## Known Limitations

1. **Streamlit Re-execution**: Full script re-runs on refresh (framework limitation)
2. **Chart Flickering**: Charts redraw completely on update
3. **Growth Screening**: Limited to 35 stocks to avoid API rate limits
4. **Sector Classification**: Uses predefined mapping + yfinance fallback

## License

MIT License - Use freely for personal or commercial purposes.

## Credits

- [Streamlit](https://streamlit.io/) - Web framework
- [yfinance](https://github.com/ranaroussi/yfinance) - Yahoo Finance API
- [Plotly](https://plotly.com/) - Interactive charts
- [streamlit-autorefresh](https://github.com/kmcgrady/streamlit-autorefresh) - Auto-refresh component
