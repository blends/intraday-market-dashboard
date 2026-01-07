"""
Market Dashboard v2.0 - Streamlit Application
A polished, dynamic financial dashboard optimized for Fire TV passive display
Features: Animated metric cards, sector analysis, intraday metrics, auto-refresh
"""

import streamlit as st
import pandas as pd
import numpy as np
import requests
import yfinance as yf
from datetime import datetime, time as dt_time
import time
import pytz
from typing import Dict, List, Tuple, Optional
import plotly.graph_objects as go
import plotly.express as px
from streamlit_autorefresh import st_autorefresh

# ============================================================================
# PAGE CONFIG - Must be first Streamlit command
# ============================================================================

st.set_page_config(
    page_title="Market Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============================================================================
# CONFIGURATION
# ============================================================================

DEFAULT_CONFIG = {
    'refresh_interval_market_open': 5,      # minutes
    'refresh_interval_market_closed': 30,   # minutes
    'stock_count': 75,                      # Increased for better sector coverage
    'top_gainers_count': 10,
    'top_losers_count': 5,
    'volume_leaders_count': 10,
    'growth_revenue_threshold': 100,
    'growth_eps_threshold': 25,
    'growth_min_price': 10.00,
    'growth_min_volume': 100000,
    'exclude_biotech': True,
}

# Color palette matching the HTML example
COLORS = {
    'bg_primary': '#0a0e27',
    'bg_secondary': '#1a1f3a',
    'bg_card': 'rgba(255, 255, 255, 0.05)',
    'positive': '#00ff88',
    'negative': '#ff3366',
    'accent': '#00d4ff',
    'accent_secondary': '#667eea',
    'accent_tertiary': '#764ba2',
    'warning': '#ffa500',
    'text_primary': '#ffffff',
    'text_secondary': '#8892b0',
    'border': 'rgba(255, 255, 255, 0.1)',
}

# Sector mapping for classification - expanded list
SECTOR_MAP = {
    'Technology': ['NVDA', 'AAPL', 'MSFT', 'GOOGL', 'GOOG', 'META', 'INTC', 'AMD', 'AVGO', 'ORCL', 'CRM', 'ADBE', 
                   'NOW', 'PLTR', 'SNOW', 'NET', 'DDOG', 'ZS', 'CRWD', 'PANW', 'MDB', 'TEAM', 'WDAY', 'SHOP',
                   'SQ', 'UBER', 'ABNB', 'DASH', 'COIN', 'HOOD', 'RBLX', 'U', 'DOCS', 'ZM', 'OKTA', 'TWLO',
                   'DELL', 'HPQ', 'HPE', 'IBM', 'CSCO', 'QCOM', 'TXN', 'MU', 'LRCX', 'KLAC', 'AMAT', 'ASML',
                   'MRVL', 'ON', 'SWKS', 'QRVO', 'ADI', 'NXPI', 'MPWR', 'MCHP', 'SMCI', 'ARM', 'IONQ', 'RGTI',
                   'QUBT', 'QBTS', 'BBAI', 'AI', 'PATH', 'ASAN', 'FROG', 'GTLB', 'ESTC', 'CFLT', 'CRWV'],
    'Healthcare': ['UNH', 'JNJ', 'PFE', 'ABBV', 'MRK', 'LLY', 'TMO', 'ABT', 'CVS', 'CI', 'HUM', 'CNC', 'ELV',
                   'ISRG', 'DHR', 'BMY', 'AMGN', 'GILD', 'VRTX', 'REGN', 'BIIB', 'MRNA', 'ZTS', 'SYK', 'BDX',
                   'MDT', 'BSX', 'EW', 'A', 'IQV', 'ILMN', 'DXCM', 'ALGN', 'HOLX', 'MTD', 'WAT', 'IDXX'],
    'Financial': ['JPM', 'BAC', 'WFC', 'GS', 'MS', 'C', 'BLK', 'SCHW', 'AXP', 'V', 'MA', 'PYPL', 'SOFI',
                  'COF', 'USB', 'PNC', 'TFC', 'AIG', 'MET', 'PRU', 'AFL', 'ALL', 'TRV', 'CB', 'PGR', 'HIG',
                  'ICE', 'CME', 'SPGI', 'MCO', 'MSCI', 'FIS', 'FISV', 'GPN', 'ADP', 'PAYX', 'WU', 'AFRM',
                  'UPST', 'LC', 'NU', 'RKT', 'UWMC', 'OPEN', 'AGNC', 'NLY', 'STWD', 'BXMT', 'KEY', 'CFG'],
    'Consumer': ['AMZN', 'TSLA', 'HD', 'MCD', 'NKE', 'SBUX', 'TGT', 'COST', 'WMT', 'DIS', 'NFLX', 'LOW',
                 'TJX', 'ROST', 'CMG', 'YUM', 'DPZ', 'ORLY', 'AZO', 'BBY', 'DLTR', 'DG', 'KR', 'SYY', 'GIS',
                 'K', 'KHC', 'MDLZ', 'HSY', 'MKC', 'CPB', 'SJM', 'CAG', 'HRL', 'TSN', 'PEP', 'KO', 'PM', 'MO',
                 'STZ', 'TAP', 'BUD', 'DEO', 'EL', 'CL', 'PG', 'KMB', 'CHD', 'CLX', 'CLORX', 'NIO', 'RIVN',
                 'LCID', 'FSR', 'LI', 'XPEV', 'GM', 'F', 'STLA', 'TM', 'HMC', 'RACE', 'APTV', 'BWA', 'LEA'],
    'Energy': ['XOM', 'CVX', 'COP', 'SLB', 'EOG', 'OXY', 'MPC', 'VLO', 'PSX', 'HAL', 'BKR', 'DVN', 'FANG',
               'PXD', 'HES', 'MRO', 'APA', 'OVV', 'CTRA', 'EQT', 'AR', 'RRC', 'SWN', 'CHK', 'CNQ', 'SU', 'CVE',
               'IMO', 'ENB', 'TRP', 'KMI', 'WMB', 'OKE', 'TRGP', 'LNG', 'PLUG', 'FCEL', 'BE', 'ENPH', 'SEDG',
               'RUN', 'NOVA', 'ARRY', 'FLNC', 'STEM', 'CHPT', 'EVGO', 'BLNK', 'SMR', 'OKLO', 'NNE', 'LEU',
               'CCJ', 'UEC', 'UUUU', 'DNN', 'URG', 'NXE'],
    'Industrial': ['CAT', 'BA', 'UPS', 'HON', 'GE', 'MMM', 'LMT', 'RTX', 'DE', 'UNP', 'CSX', 'NSC', 'FDX',
                   'DAL', 'UAL', 'LUV', 'AAL', 'ALK', 'JBLU', 'SAVE', 'GD', 'NOC', 'HII', 'LHX', 'TDG', 'TXT',
                   'EMR', 'ROK', 'ETN', 'ITW', 'PH', 'IR', 'DOV', 'SWK', 'GNRC', 'TT', 'CARR', 'OTIS', 'JCI',
                   'FAST', 'GWW', 'AAON', 'WSO', 'WCC', 'CNH', 'AGCO', 'PCAR', 'CMI', 'JOBY', 'ACHR', 'LILM'],
    'Materials': ['LIN', 'APD', 'ECL', 'SHW', 'FCX', 'NEM', 'NUE', 'DOW', 'DD', 'PPG', 'ALB', 'EMN', 'CE',
                  'VMC', 'MLM', 'STLD', 'CLF', 'X', 'AA', 'CENX', 'ATI', 'RS', 'CMC', 'WOR', 'RGLD', 'FNV',
                  'WPM', 'GOLD', 'AEM', 'KGC', 'AU', 'HL', 'CDE', 'AG', 'PAAS', 'SILV', 'EXK', 'MAG', 'NGD',
                  'SSRM', 'BTG', 'GFI', 'HBM', 'SCCO', 'TECK', 'RIO', 'BHP', 'VALE'],
    'Utilities': ['NEE', 'DUK', 'SO', 'D', 'AEP', 'EXC', 'SRE', 'XEL', 'PEG', 'ED', 'WEC', 'ES', 'DTE', 'FE',
                  'PPL', 'AES', 'CMS', 'CNP', 'NI', 'EVRG', 'ATO', 'NJR', 'OGS', 'NWN', 'AWK', 'WTRG'],
    'Real Estate': ['AMT', 'PLD', 'CCI', 'EQIX', 'SPG', 'O', 'WELL', 'AVB', 'DLR', 'PSA', 'EQR', 'VTR', 'ARE',
                    'BXP', 'SLG', 'VNO', 'KIM', 'REG', 'FRT', 'HST', 'MAR', 'HLT', 'IHG', 'H', 'WH', 'CHH',
                    'INVH', 'AMH', 'SUI', 'ELS', 'IIPR', 'COLD', 'TRNO', 'STAG'],
    'Communication': ['T', 'VZ', 'TMUS', 'CMCSA', 'CHTR', 'DISH', 'LUMN', 'FYBR', 'USM', 'LSCC', 'LITE',
                      'VIAV', 'CIEN', 'INFN', 'COMM', 'CALX', 'IRDM', 'GSAT', 'ASTS', 'LUNR', 'RDW', 'SPIR'],
}

# ============================================================================
# CUSTOM CSS - Polished dark theme with animations
# ============================================================================

def inject_custom_css():
    """Inject comprehensive custom CSS for polished TV display"""
    st.markdown("""
<style>
    /* ========== IMPORTS ========== */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    /* ========== ROOT VARIABLES ========== */
    :root {
        --bg-primary: #0a0e27;
        --bg-secondary: #1a1f3a;
        --bg-card: rgba(255, 255, 255, 0.05);
        --positive: #00ff88;
        --negative: #ff3366;
        --accent: #00d4ff;
        --accent-secondary: #667eea;
        --accent-tertiary: #764ba2;
        --text-primary: #ffffff;
        --text-secondary: #8892b0;
        --border: rgba(255, 255, 255, 0.1);
    }
    
    /* ========== GLOBAL STYLES ========== */
    .stApp {
        background: linear-gradient(135deg, var(--bg-primary) 0%, var(--bg-secondary) 100%);
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Hide Streamlit branding for kiosk mode */
    #MainMenu, footer, header, .stDeployButton { visibility: hidden !important; }
    [data-testid="stToolbar"] { display: none !important; }
    [data-testid="stDecoration"] { display: none !important; }
    [data-testid="stStatusWidget"] { display: none !important; }
    
    /* Reclaim header space */
    .main .block-container {
        padding-top: 0.5rem !important;
        padding-bottom: 1rem !important;
        max-width: 100% !important;
    }
    
    /* ========== ANIMATIONS ========== */
    @keyframes shimmer {
        0% { background-position: 0% 50%; }
        100% { background-position: 200% 50%; }
    }
    
    @keyframes scan {
        0% { transform: translateX(-100%); }
        100% { transform: translateX(100%); }
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }
    
    @keyframes borderGlow {
        0%, 100% { 
            border-color: rgba(102, 126, 234, 0.5);
            box-shadow: 0 0 15px rgba(102, 126, 234, 0.2);
        }
        50% { 
            border-color: rgba(118, 75, 162, 0.8);
            box-shadow: 0 0 25px rgba(118, 75, 162, 0.4);
        }
    }
    
    @keyframes subtleShift {
        0%, 100% { transform: translate(0, 0); }
        25% { transform: translate(1px, 1px); }
        50% { transform: translate(0, 2px); }
        75% { transform: translate(-1px, 1px); }
    }
    
    /* ========== METRIC CARDS ========== */
    div[data-testid="stMetric"] {
        background: linear-gradient(145deg, rgba(30, 30, 46, 0.9), rgba(42, 42, 62, 0.9));
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 16px 20px;
        position: relative;
        overflow: hidden;
        transition: all 0.3s ease;
    }
    
    div[data-testid="stMetric"]:hover {
        transform: translateY(-3px);
        background: linear-gradient(145deg, rgba(35, 35, 55, 0.95), rgba(50, 50, 70, 0.95));
        box-shadow: 0 10px 30px rgba(0, 212, 255, 0.15);
        border-color: rgba(0, 212, 255, 0.3);
    }
    
    /* Scanning animation ONLY for intraday indicators section */
    .intraday-section div[data-testid="stMetric"] {
        animation: subtleShift 300s ease-in-out infinite;
    }
    
    .intraday-section div[data-testid="stMetric"]::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 2px;
        background: linear-gradient(90deg, transparent, var(--accent), transparent);
        animation: scan 3s linear infinite;
    }
    
    /* Metric labels */
    div[data-testid="stMetric"] label {
        color: var(--text-secondary) !important;
        font-size: 0.85rem !important;
        font-weight: 500 !important;
        text-transform: uppercase;
        letter-spacing: 1.5px;
    }
    
    /* Metric values */
    div[data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: var(--text-primary) !important;
        font-size: 1.75rem !important;
        font-weight: 700 !important;
    }
    
    /* Delta indicators */
    div[data-testid="stMetric"] [data-testid="stMetricDelta"] {
        font-size: 0.9rem !important;
        font-weight: 600 !important;
    }
    
    div[data-testid="stMetric"] [data-testid="stMetricDelta"][data-testid-delta-type="positive"] {
        color: var(--positive) !important;
    }
    
    div[data-testid="stMetric"] [data-testid="stMetricDelta"][data-testid-delta-type="negative"] {
        color: var(--negative) !important;
    }
    
    /* ========== HEADERS ========== */
    .main-title {
        font-size: 2rem;
        font-weight: 700;
        background: linear-gradient(90deg, var(--accent), #0099ff, var(--accent));
        background-size: 200% auto;
        -webkit-background-clip: text;
        background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: shimmer 3s linear infinite;
    }
    
    .section-header {
        color: var(--accent);
        font-size: 1.2rem;
        font-weight: 600;
        margin: 15px 0 12px 0;
        padding-bottom: 8px;
        border-bottom: 1px solid rgba(0, 212, 255, 0.3);
    }
    
    /* ========== MARKET STATUS BADGE ========== */
    .market-badge {
        display: inline-block;
        padding: 8px 16px;
        border-radius: 20px;
        font-size: 0.9rem;
        font-weight: 600;
        animation: pulse 2s infinite;
        white-space: nowrap;
    }
    
    .market-badge.bullish {
        background: rgba(0, 255, 136, 0.15);
        border: 2px solid var(--positive);
        color: var(--positive);
    }
    
    .market-badge.bearish {
        background: rgba(255, 51, 102, 0.15);
        border: 2px solid var(--negative);
        color: var(--negative);
    }
    
    .market-badge.neutral {
        background: rgba(0, 212, 255, 0.15);
        border: 2px solid var(--accent);
        color: var(--accent);
    }
    
    /* ========== DATA TABLES ========== */
    div[data-testid="stDataFrame"] {
        background: var(--bg-card);
        backdrop-filter: blur(10px);
        border: 1px solid var(--border);
        border-radius: 12px;
        overflow: hidden;
    }
    
    div[data-testid="stDataFrame"] th {
        background: rgba(0, 212, 255, 0.1) !important;
        color: var(--accent) !important;
        font-weight: 600 !important;
        border-bottom: 2px solid rgba(0, 212, 255, 0.3) !important;
    }
    
    div[data-testid="stDataFrame"] td {
        color: var(--text-primary) !important;
        border-bottom: 1px solid rgba(255, 255, 255, 0.05) !important;
    }
    
    /* ========== SECTOR CARDS ========== */
    .sector-card {
        background: linear-gradient(145deg, rgba(30, 30, 46, 0.8), rgba(42, 42, 62, 0.8));
        border: 1px solid var(--border);
        border-radius: 10px;
        padding: 15px;
        text-align: center;
        transition: all 0.3s ease;
    }
    
    .sector-card:hover {
        transform: translateY(-2px);
        border-color: rgba(0, 212, 255, 0.4);
    }
    
    .sector-name {
        color: var(--text-secondary);
        font-size: 0.85rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 8px;
    }
    
    .sector-value {
        font-size: 1.4rem;
        font-weight: 700;
    }
    
    .sector-value.positive { color: var(--positive); }
    .sector-value.negative { color: var(--negative); }
    
    /* ========== BADGES ========== */
    .growth-badge {
        background: linear-gradient(135deg, var(--accent-secondary), var(--accent-tertiary));
        color: white;
        padding: 4px 10px;
        border-radius: 5px;
        font-size: 0.8rem;
        font-weight: 600;
        display: inline-block;
        margin-left: 10px;
    }
    
    .star-performer {
        background: linear-gradient(135deg, #ffd700, #ffed4e);
        color: var(--bg-primary);
        padding: 3px 8px;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 700;
        margin-left: 6px;
    }
    
    .volume-pill {
        background: rgba(0, 212, 255, 0.15);
        border: 1px solid rgba(0, 212, 255, 0.3);
        color: var(--accent);
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 0.85rem;
    }
    
    /* ========== TIMESTAMP ========== */
    .last-updated {
        text-align: center;
        color: var(--text-secondary);
        font-size: 0.85rem;
        padding: 15px 0;
        border-top: 1px solid var(--border);
        margin-top: 20px;
    }
    
    /* ========== PLOTLY CHART CONTAINERS ========== */
    div[data-testid="stPlotlyChart"] {
        background: var(--bg-card);
        backdrop-filter: blur(10px);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 10px;
    }
    
    /* ========== RESPONSIVE ADJUSTMENTS FOR TV ========== */
    @media (min-width: 1920px) {
        .main-title { font-size: 2.5rem; }
        div[data-testid="stMetric"] [data-testid="stMetricValue"] {
            font-size: 2.25rem !important;
        }
        .section-header { font-size: 1.4rem; }
    }
    
    /* ========== BURN-IN PREVENTION ========== */
    .dashboard-wrapper {
        animation: subtleShift 300s ease-in-out infinite;
    }
</style>
""", unsafe_allow_html=True)


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def is_market_open() -> bool:
    """Check if US stock market is currently open"""
    et = pytz.timezone('US/Eastern')
    now = datetime.now(et)
    if now.weekday() >= 5:
        return False
    market_open = dt_time(9, 30)
    market_close = dt_time(16, 0)
    return market_open <= now.time() <= market_close


def get_refresh_interval(config: Dict) -> int:
    """Get appropriate refresh interval based on market status"""
    if is_market_open():
        return config['refresh_interval_market_open'] * 60 * 1000  # Convert to ms
    return config['refresh_interval_market_closed'] * 60 * 1000


def format_volume(volume: float) -> str:
    """Format volume with appropriate suffix"""
    if pd.isna(volume) or volume == 0:
        return "N/A"
    if volume >= 1_000_000_000:
        return f"{volume/1_000_000_000:.2f}B"
    elif volume >= 1_000_000:
        return f"{volume/1_000_000:.1f}M"
    elif volume >= 1_000:
        return f"{volume/1_000:.1f}K"
    return str(int(volume))


def format_change(change: float) -> str:
    """Format percentage change with sign"""
    if pd.isna(change):
        return "N/A"
    if change >= 0:
        return f"+{change:.2f}%"
    return f"{change:.2f}%"


def format_large_number(num: float) -> str:
    """Format large numbers with suffix"""
    if pd.isna(num) or num == 0:
        return "N/A"
    if num >= 1_000_000_000_000:
        return f"${num/1_000_000_000_000:.2f}T"
    if num >= 1_000_000_000:
        return f"${num/1_000_000_000:.2f}B"
    if num >= 1_000_000:
        return f"${num/1_000_000:.1f}M"
    return f"${num:,.0f}"


def get_market_status(avg_change: float) -> Tuple[str, str, str]:
    """Get market status class, emoji, and text"""
    if avg_change > 2:
        return "bullish", "📈", "BULLISH - Strong Rally"
    elif avg_change > 0.5:
        return "bullish", "📈", "BULLISH - Moderate Gains"
    elif avg_change > -0.5:
        return "neutral", "➡️", "NEUTRAL - Mixed Trading"
    elif avg_change > -2:
        return "bearish", "📉", "BEARISH - Moderate Decline"
    return "bearish", "📉", "BEARISH - Heavy Selling"


def get_sector_for_symbol(symbol: str, info: Dict = None) -> str:
    """Get sector for a stock symbol"""
    # First check our mapping
    for sector, symbols in SECTOR_MAP.items():
        if symbol in symbols:
            return sector
    # Fall back to yfinance info if provided
    if info and 'sector' in info:
        return info.get('sector', 'Other')
    return 'Other'


# ============================================================================
# DATA FETCHING FUNCTIONS
# ============================================================================

@st.cache_data(ttl=60, show_spinner=False)
def get_most_active_stocks(count: int = 75) -> List[Dict]:
    """Fetch most active stocks from Yahoo Finance screener"""
    url = "https://query1.finance.yahoo.com/v1/finance/screener/predefined/saved"
    params = {'scrIds': 'most_actives', 'start': 0, 'count': count}
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=15)
        if response.status_code == 200:
            data = response.json()
            return data['finance']['result'][0]['quotes']
    except Exception as e:
        st.session_state['last_error'] = f"API Error: {str(e)}"
    return []


@st.cache_data(ttl=300, show_spinner=False)
def get_financial_data(symbol: str) -> Optional[Dict]:
    """Fetch detailed financial data for a stock using yfinance"""
    try:
        stock = yf.Ticker(symbol)
        info = stock.info
        
        # Revenue growth
        revenue_growth = None
        yoy_growth = info.get('revenueGrowth')
        if yoy_growth is not None:
            revenue_growth = yoy_growth * 100
        
        # EPS growth
        eps_growth = None
        trailing_eps = info.get('trailingEps', 0)
        forward_eps = info.get('forwardEps', 0)
        if trailing_eps and trailing_eps != 0 and forward_eps:
            eps_growth = ((forward_eps - trailing_eps) / abs(trailing_eps)) * 100
        
        if eps_growth is None:
            yoy_earnings = info.get('earningsGrowth')
            if yoy_earnings is not None:
                eps_growth = yoy_earnings * 100
        
        return {
            'revenue_growth': revenue_growth,
            'eps_growth': eps_growth,
            'avg_volume_50d': info.get('averageVolume', 0),
            'industry': info.get('industry', 'Unknown'),
            'sector': info.get('sector', 'Unknown'),
            'current_price': info.get('currentPrice', info.get('regularMarketPrice', 0)),
            'market_cap': info.get('marketCap', 0),
            'pe_ratio': info.get('trailingPE', None),
            'fifty_two_week_high': info.get('fiftyTwoWeekHigh', 0),
            'fifty_two_week_low': info.get('fiftyTwoWeekLow', 0),
        }
    except Exception:
        return None


def calculate_sector_performance(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate performance metrics by sector"""
    if df.empty:
        return pd.DataFrame()
    
    # Add sector column
    df = df.copy()
    df['Sector'] = df['Symbol'].apply(lambda x: get_sector_for_symbol(x))
    
    # Group by sector and calculate metrics
    sector_stats = df.groupby('Sector').agg({
        'Change (%)': ['mean', 'count'],
        'Volume': 'sum',
        'Symbol': lambda x: list(x)[:3]  # Top 3 symbols
    }).reset_index()
    
    sector_stats.columns = ['Sector', 'Avg Change', 'Count', 'Total Volume', 'Top Stocks']
    sector_stats = sector_stats.sort_values('Avg Change', ascending=False)
    
    return sector_stats


def calculate_breadth_indicators(df: pd.DataFrame) -> Dict:
    """Calculate market breadth indicators"""
    if df.empty:
        return {}
    
    total = len(df)
    gainers = len(df[df['Change (%)'] > 0])
    losers = len(df[df['Change (%)'] < 0])
    unchanged = total - gainers - losers
    
    # Advance/Decline ratio
    ad_ratio = gainers / losers if losers > 0 else gainers
    
    # New highs/lows (simplified - stocks within 5% of 52-week high/low)
    # This would require additional data, so we'll estimate
    strong_gainers = len(df[df['Change (%)'] > 5])
    strong_losers = len(df[df['Change (%)'] < -5])
    
    return {
        'total': total,
        'gainers': gainers,
        'losers': losers,
        'unchanged': unchanged,
        'gainers_pct': (gainers / total * 100) if total > 0 else 0,
        'ad_ratio': ad_ratio,
        'strong_gainers': strong_gainers,
        'strong_losers': strong_losers,
    }


def screen_growth_stocks(stocks_data: List[Dict], config: Dict) -> List[Dict]:
    """Screen stocks for growth criteria"""
    growth_stocks = []
    biotech_keywords = ['biotech', 'pharmaceutical', 'drug manufacturers', 'biopharm', 'therapeutics']
    
    # Limit to avoid too many API calls
    for stock in stocks_data[:35]:
        symbol = stock.get('symbol', '')
        price = stock.get('regularMarketPrice', 0)
        
        if price < config['growth_min_price']:
            continue
        
        financial_data = get_financial_data(symbol)
        if not financial_data:
            continue
        
        criteria_met = 0
        
        # Revenue growth
        revenue_growth = financial_data.get('revenue_growth')
        if revenue_growth is not None and revenue_growth >= config['growth_revenue_threshold']:
            criteria_met += 1
        
        # EPS growth
        eps_growth = financial_data.get('eps_growth')
        if eps_growth is not None and eps_growth >= config['growth_eps_threshold']:
            criteria_met += 1
        
        # Volume
        if financial_data.get('avg_volume_50d', 0) >= config['growth_min_volume']:
            criteria_met += 1
        
        # Industry check
        industry = financial_data.get('industry', '').lower()
        if config['exclude_biotech']:
            if not any(kw in industry for kw in biotech_keywords):
                criteria_met += 1
        else:
            criteria_met += 1
        
        if criteria_met == 4:
            growth_stocks.append({
                'Symbol': symbol,
                'Name': stock.get('shortName', 'N/A'),
                'Price': price,
                'Change (%)': stock.get('regularMarketChangePercent', 0),
                'Volume': stock.get('regularMarketVolume', 0),
                'Revenue Growth (%)': revenue_growth,
                'EPS Growth (%)': eps_growth,
                'Sector': financial_data.get('sector', 'Unknown'),
            })
    
    return growth_stocks


# ============================================================================
# CHART FUNCTIONS
# ============================================================================

def create_volume_chart(df: pd.DataFrame) -> go.Figure:
    """Create volume leaders bar chart with gain/loss coloring"""
    df = df.head(10).copy()
    
    colors = [COLORS['positive'] if x >= 0 else COLORS['negative'] 
              for x in df['Change (%)']]
    
    fig = go.Figure(data=[
        go.Bar(
            x=df['Symbol'],
            y=df['Volume'] / 1_000_000,
            marker_color=colors,
            marker_line_color=colors,
            marker_line_width=1,
            text=[format_change(x) for x in df['Change (%)']],
            textposition='outside',
            textfont=dict(color=COLORS['text_secondary'], size=11),
            hovertemplate='<b>%{x}</b><br>Volume: %{y:.1f}M<br>Change: %{text}<extra></extra>'
        )
    ])
    
    fig.update_layout(
        title=dict(
            text="📊 Volume Leaders (Millions)",
            font=dict(color=COLORS['accent'], size=18),
            x=0
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color=COLORS['text_secondary'], family='Inter'),
        xaxis=dict(
            showgrid=False,
            color=COLORS['text_secondary'],
            tickfont=dict(size=12)
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='rgba(255,255,255,0.05)',
            color=COLORS['text_secondary'],
            title=dict(text="Volume (M)", font=dict(size=12))
        ),
        margin=dict(l=50, r=30, t=60, b=50),
        height=380,
        hoverlabel=dict(
            bgcolor=COLORS['bg_secondary'],
            font_size=12,
            font_family='Inter'
        )
    )
    
    return fig


def create_sector_heatmap(sector_df: pd.DataFrame) -> go.Figure:
    """Create sector performance treemap"""
    if sector_df.empty:
        return go.Figure()
    
    # Filter out "Other" category for cleaner visualization
    display_df = sector_df[sector_df['Sector'] != 'Other'].copy()
    
    if display_df.empty:
        return go.Figure()
    
    # Use equal sizing for better visual balance (not weighted by count)
    display_df['Size'] = 1
    
    fig = go.Figure(data=[
        go.Treemap(
            labels=display_df['Sector'],
            parents=[''] * len(display_df),
            values=display_df['Size'],
            text=[f"{change:+.2f}%" for change in display_df['Avg Change']],
            textinfo='label+text',
            textfont=dict(size=13, color='white', family='Inter'),
            marker=dict(
                colors=display_df['Avg Change'],
                colorscale=[
                    [0, COLORS['negative']],
                    [0.5, '#2a2a3e'],
                    [1, COLORS['positive']]
                ],
                cmid=0,
                cmin=-5,
                cmax=5,
                line=dict(width=2, color=COLORS['bg_primary'])
            ),
            hovertemplate='<b>%{label}</b><br>Avg Change: %{text}<br>Stocks: %{customdata}<extra></extra>',
            customdata=display_df['Count']
        )
    ])
    
    fig.update_layout(
        title=dict(
            text="Sector Heatmap",
            font=dict(color=COLORS['accent'], size=16),
            x=0
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=10, r=10, t=50, b=10),
        height=320,
    )
    
    return fig


def create_gainers_losers_chart(gainers_df: pd.DataFrame, losers_df: pd.DataFrame) -> go.Figure:
    """Create horizontal bar chart for top movers"""
    # Prepare data
    gainers = gainers_df.head(5).copy()
    losers = losers_df.head(5).copy()
    
    fig = go.Figure()
    
    # Gainers
    fig.add_trace(go.Bar(
        y=gainers['Symbol'],
        x=gainers['Change (%)'],
        orientation='h',
        name='Gainers',
        marker_color=COLORS['positive'],
        text=[f"+{x:.1f}%" for x in gainers['Change (%)']],
        textposition='outside',
        textfont=dict(color=COLORS['positive'], size=11),
        hovertemplate='<b>%{y}</b><br>Change: +%{x:.2f}%<extra></extra>'
    ))
    
    # Losers
    fig.add_trace(go.Bar(
        y=losers['Symbol'],
        x=losers['Change (%)'],
        orientation='h',
        name='Losers',
        marker_color=COLORS['negative'],
        text=[f"{x:.1f}%" for x in losers['Change (%)']],
        textposition='outside',
        textfont=dict(color=COLORS['negative'], size=11),
        hovertemplate='<b>%{y}</b><br>Change: %{x:.2f}%<extra></extra>'
    ))
    
    fig.update_layout(
        title=dict(
            text="🚀 Top Movers",
            font=dict(color=COLORS['accent'], size=18),
            x=0
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color=COLORS['text_secondary'], family='Inter'),
        xaxis=dict(
            showgrid=True,
            gridcolor='rgba(255,255,255,0.05)',
            zeroline=True,
            zerolinecolor='rgba(255,255,255,0.2)',
            title="Change %"
        ),
        yaxis=dict(showgrid=False),
        barmode='relative',
        height=380,
        margin=dict(l=60, r=80, t=60, b=50),
        showlegend=False,
        hoverlabel=dict(bgcolor=COLORS['bg_secondary'])
    )
    
    return fig


# ============================================================================
# DISPLAY FUNCTIONS
# ============================================================================

def display_header(avg_change: float):
    """Display compact dashboard header with title and status"""
    et = pytz.timezone('US/Eastern')
    now = datetime.now(et)
    date_str = now.strftime('%A, %B %d, %Y')
    time_str = now.strftime('%I:%M %p ET')
    
    status_class, emoji, status_text = get_market_status(avg_change)
    market_indicator = "🟢 Open" if is_market_open() else "🔴 Closed"
    
    st.markdown(f"""
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; flex-wrap: wrap; gap: 10px;">
        <div>
            <span class="main-title" style="font-size: 2rem;">Market Dashboard</span>
            <span style="color: {COLORS['text_secondary']}; margin-left: 15px; font-size: 0.95rem;">
                {date_str} • {time_str} • {market_indicator}
            </span>
        </div>
        <div class="market-badge {status_class}">
            {emoji} {status_text} {format_change(avg_change)}
        </div>
    </div>
    """, unsafe_allow_html=True)


def display_metrics_row(df: pd.DataFrame, breadth: Dict, growth_count: int):
    """Display main metrics row"""
    avg_change = df['Change (%)'].mean() if not df.empty else 0
    total_volume = df['Volume'].sum() if not df.empty else 0
    
    cols = st.columns(6)
    
    with cols[0]:
        st.metric(
            "Total Stocks",
            breadth.get('total', 0),
            "Actively tracked"
        )
    
    with cols[1]:
        delta_str = "Bullish" if avg_change > 0 else "Bearish" if avg_change < 0 else "Neutral"
        st.metric(
            "Today's Sentiment",
            f"{avg_change:+.2f}%",
            delta_str,
            delta_color="normal" if avg_change >= 0 else "inverse"
        )
    
    with cols[2]:
        st.metric(
            "Gainers",
            breadth.get('gainers', 0),
            f"{breadth.get('gainers_pct', 0):.0f}%"
        )
    
    with cols[3]:
        losers_pct = 100 - breadth.get('gainers_pct', 0)
        st.metric(
            "Losers",
            breadth.get('losers', 0),
            f"{losers_pct:.0f}%"
        )
    
    with cols[4]:
        st.metric(
            "Total Volume",
            format_volume(total_volume),
            "Today's activity"
        )
    
    with cols[5]:
        st.metric(
            "Growth Stocks",
            growth_count,
            "Meet all criteria"
        )


def display_intraday_metrics(df: pd.DataFrame, breadth: Dict):
    """Display intraday-specific metrics with scanning animation"""
    st.markdown('<div class="section-header">📊 Intraday Indicators</div>', unsafe_allow_html=True)
    
    # Start wrapper div for animation targeting
    st.markdown('<div class="intraday-section">', unsafe_allow_html=True)
    
    cols = st.columns(5)
    
    # Advance/Decline Ratio
    with cols[0]:
        ad_ratio = breadth.get('ad_ratio', 1)
        ad_status = "Bullish" if ad_ratio > 1.5 else "Bearish" if ad_ratio < 0.67 else "Neutral"
        st.metric(
            "A/D Ratio",
            f"{ad_ratio:.2f}",
            ad_status,
            delta_color="normal" if ad_ratio >= 1 else "inverse"
        )
    
    # Strong Movers
    with cols[1]:
        st.metric(
            "Strong Gainers",
            breadth.get('strong_gainers', 0),
            "> 5% gain"
        )
    
    with cols[2]:
        st.metric(
            "Strong Losers",
            breadth.get('strong_losers', 0),
            "> 5% loss"
        )
    
    # Relative Volume (simplified)
    with cols[3]:
        # This is a placeholder - would need historical average volume for true RVOL
        avg_vol_per_stock = df['Volume'].mean() if not df.empty else 0
        rel_vol = avg_vol_per_stock / 50_000_000  # Rough baseline
        st.metric(
            "Rel. Volume",
            f"{rel_vol:.1f}x",
            "vs avg"
        )
    
    # Market breadth percentage
    with cols[4]:
        gainers_pct = breadth.get('gainers_pct', 50)
        if gainers_pct >= 70:
            breadth_status = "Very Strong"
        elif gainers_pct >= 55:
            breadth_status = "Positive"
        elif gainers_pct >= 45:
            breadth_status = "Mixed"
        else:
            breadth_status = "Weak"
        st.metric(
            "Breadth",
            f"{gainers_pct:.0f}%",
            breadth_status,
            delta_color="normal" if gainers_pct >= 50 else "inverse"
        )
    
    # Close the wrapper div
    st.markdown('</div>', unsafe_allow_html=True)


def display_sector_performance(sector_df: pd.DataFrame):
    """Display sector performance cards"""
    st.markdown('<div class="section-header">🏢 Sector Performance</div>', unsafe_allow_html=True)
    
    if sector_df.empty:
        st.info("Sector data not available")
        return
    
    # Filter out "Other" for cleaner display and exclude tiny sectors
    display_df = sector_df[
        (sector_df['Sector'] != 'Other') & 
        (sector_df['Count'] >= 1)
    ].head(10)
    
    if display_df.empty:
        st.info("Sector data not available")
        return
    
    # Create HTML cards for better control over display
    num_sectors = len(display_df)
    cols_per_row = 5
    
    for row_start in range(0, num_sectors, cols_per_row):
        cols = st.columns(cols_per_row)
        for idx, col in enumerate(cols):
            sector_idx = row_start + idx
            if sector_idx < num_sectors:
                row = display_df.iloc[sector_idx]
                change = row['Avg Change']
                color = COLORS['positive'] if change >= 0 else COLORS['negative']
                sign = "+" if change >= 0 else ""
                
                with col:
                    st.markdown(f"""
                    <div style="
                        background: linear-gradient(145deg, rgba(30, 30, 46, 0.8), rgba(42, 42, 62, 0.8));
                        border: 1px solid rgba(255, 255, 255, 0.1);
                        border-radius: 10px;
                        padding: 15px 12px;
                        text-align: center;
                        height: 110px;
                    ">
                        <div style="color: #8892b0; font-size: 0.75rem; font-weight: 500; 
                                    text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 8px;">
                            {row['Sector']}
                        </div>
                        <div style="color: {color}; font-size: 1.5rem; font-weight: 700;">
                            {sign}{change:.2f}%
                        </div>
                        <div style="color: {COLORS['accent']}; font-size: 0.8rem; margin-top: 5px;">
                            {row['Count']} stocks
                        </div>
                    </div>
                    """, unsafe_allow_html=True)


def display_movers_table(df: pd.DataFrame, title: str, emoji: str):
    """Display styled movers table"""
    if df.empty:
        st.info(f"No {title.lower()} data available")
        return
    
    st.markdown(f'<div class="section-header">{emoji} {title}</div>', unsafe_allow_html=True)
    
    # Prepare display dataframe
    display_df = df[['Symbol', 'Name', 'Price', 'Change (%)', 'Volume']].copy()
    display_df['Price'] = display_df['Price'].apply(lambda x: f"${x:.2f}")
    display_df['Change (%)'] = display_df['Change (%)'].apply(format_change)
    display_df['Volume'] = display_df['Volume'].apply(format_volume)
    display_df.columns = ['Symbol', 'Name', 'Price', 'Change', 'Volume']
    
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        height=min(400, 35 * len(display_df) + 38)
    )


def display_growth_stocks(growth_stocks: List[Dict]):
    """Display growth stocks table"""
    st.markdown(f"""
    <div class="section-header">
        💎 High Growth Opportunities 
        <span class="growth-badge">4/4 Criteria Met</span>
        <span style="color: {COLORS['positive']}; margin-left: 10px; font-size: 0.9rem;">
            {len(growth_stocks)} Stocks
        </span>
    </div>
    """, unsafe_allow_html=True)
    
    if not growth_stocks:
        st.info("No stocks currently meet all growth criteria. Adjust thresholds in sidebar settings.")
        return
    
    df = pd.DataFrame(growth_stocks)
    display_df = df[['Symbol', 'Name', 'Sector', 'Price', 'Revenue Growth (%)', 'EPS Growth (%)', 'Change (%)']].copy()
    
    display_df['Price'] = display_df['Price'].apply(lambda x: f"${x:.2f}")
    display_df['Revenue Growth (%)'] = display_df['Revenue Growth (%)'].apply(
        lambda x: f"{x:,.0f}%" if pd.notna(x) else "N/A")
    display_df['EPS Growth (%)'] = display_df['EPS Growth (%)'].apply(
        lambda x: f"{x:,.0f}%" if pd.notna(x) else "N/A")
    display_df['Change (%)'] = display_df['Change (%)'].apply(format_change)
    display_df.columns = ['Symbol', 'Name', 'Sector', 'Price', 'Rev Growth', 'EPS Growth', 'Today']
    
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        height=min(450, 35 * len(display_df) + 38)
    )


def display_volume_leaders(df: pd.DataFrame):
    """Display volume leaders table"""
    st.markdown('<div class="section-header">📊 Volume Leaders</div>', unsafe_allow_html=True)
    
    volume_df = df.nlargest(10, 'Volume').copy()
    volume_df['Rank'] = range(1, len(volume_df) + 1)
    
    display_df = volume_df[['Rank', 'Symbol', 'Name', 'Volume', 'Price', 'Change (%)']].copy()
    display_df['Price'] = display_df['Price'].apply(lambda x: f"${x:.2f}")
    display_df['Change (%)'] = display_df['Change (%)'].apply(format_change)
    display_df['Volume'] = display_df['Volume'].apply(lambda x: f"{format_volume(x)} shares")
    display_df.columns = ['#', 'Symbol', 'Name', 'Volume', 'Price', 'Change']
    
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        height=min(400, 35 * len(display_df) + 38)
    )


# ============================================================================
# SIDEBAR CONFIGURATION
# ============================================================================

def render_sidebar(config: Dict) -> Dict:
    """Render sidebar configuration panel"""
    with st.sidebar:
        st.markdown("## ⚙️ Dashboard Settings")
        
        st.markdown("### ⏱️ Refresh Intervals")
        config['refresh_interval_market_open'] = st.slider(
            "Market Open (min)", 1, 30, config['refresh_interval_market_open'],
            help="Refresh interval when market is open"
        )
        config['refresh_interval_market_closed'] = st.slider(
            "Market Closed (min)", 5, 60, config['refresh_interval_market_closed'],
            help="Refresh interval when market is closed"
        )
        
        st.markdown("### 📈 Growth Criteria")
        config['growth_revenue_threshold'] = st.number_input(
            "Min Revenue Growth %", 0, 500, config['growth_revenue_threshold'])
        config['growth_eps_threshold'] = st.number_input(
            "Min EPS Growth %", 0, 200, config['growth_eps_threshold'])
        config['growth_min_price'] = st.number_input(
            "Min Stock Price $", 0.0, 100.0, config['growth_min_price'])
        config['exclude_biotech'] = st.checkbox(
            "Exclude Biotech/Pharma", config['exclude_biotech'])
        
        st.markdown("### 📊 Display Settings")
        config['stock_count'] = st.slider(
            "Stocks to Fetch", 25, 100, config['stock_count'],
            help="More stocks = better sector coverage but slower load"
        )
        
        st.markdown("---")
        
        if st.button("🔄 Force Refresh", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        
        # Status indicators
        st.markdown("---")
        market_status = "🟢 Open" if is_market_open() else "🔴 Closed"
        refresh_min = config['refresh_interval_market_open'] if is_market_open() else config['refresh_interval_market_closed']
        
        st.markdown(f"""
        **Market:** {market_status}  
        **Refresh:** Every {refresh_min} min  
        **Stocks:** {config['stock_count']}
        """)
    
    return config


# ============================================================================
# MAIN APPLICATION
# ============================================================================

def main():
    """Main application entry point"""
    
    # Initialize session state
    if 'config' not in st.session_state:
        st.session_state['config'] = DEFAULT_CONFIG.copy()
    if 'last_error' not in st.session_state:
        st.session_state['last_error'] = None
    if 'cached_stocks' not in st.session_state:
        st.session_state['cached_stocks'] = None
    if 'last_refresh_time' not in st.session_state:
        st.session_state['last_refresh_time'] = datetime.now(pytz.timezone('US/Eastern'))
    
    config = st.session_state['config']
    
    # Inject custom CSS
    inject_custom_css()
    
    # Render sidebar and get updated config
    config = render_sidebar(config)
    st.session_state['config'] = config
    
    # Auto-refresh component
    refresh_interval = get_refresh_interval(config)
    count = st_autorefresh(interval=refresh_interval, limit=None, key="dashboard_refresh")
    
    # Periodic cache clear to prevent stale data
    if count > 0 and count % 5 == 0:
        st.cache_data.clear()
    
    # Fetch market data
    with st.spinner(""):
        stocks_data = get_most_active_stocks(config['stock_count'])
    
    # Handle data fetch errors
    if not stocks_data:
        if st.session_state['cached_stocks']:
            stocks_data = st.session_state['cached_stocks']
            st.warning("⚠️ Using cached data - live feed temporarily unavailable")
        else:
            st.error("❌ Unable to fetch market data. Please check connection and try again.")
            return
    else:
        st.session_state['cached_stocks'] = stocks_data
        st.session_state['last_error'] = None
        st.session_state['last_refresh_time'] = datetime.now(pytz.timezone('US/Eastern'))
    
    # Convert to DataFrame
    df = pd.DataFrame([{
        'Symbol': s.get('symbol', ''),
        'Name': s.get('shortName', 'N/A'),
        'Price': s.get('regularMarketPrice', 0),
        'Change (%)': s.get('regularMarketChangePercent', 0),
        'Volume': s.get('regularMarketVolume', 0),
    } for s in stocks_data])
    
    # Calculate derived data
    breadth = calculate_breadth_indicators(df)
    sector_df = calculate_sector_performance(df)
    avg_change = df['Change (%)'].mean() if not df.empty else 0
    
    # Sort for display
    gainers_df = df[df['Change (%)'] > 0].nlargest(config['top_gainers_count'], 'Change (%)')
    losers_df = df[df['Change (%)'] < 0].nsmallest(config['top_losers_count'], 'Change (%)')
    
    # Screen growth stocks
    growth_stocks = screen_growth_stocks(stocks_data, config)
    
    # ========== DASHBOARD LAYOUT ==========
    
    # Wrap in div for burn-in prevention
    st.markdown('<div class="dashboard-wrapper">', unsafe_allow_html=True)
    
    # Header
    display_header(avg_change)
    
    # Main metrics row
    display_metrics_row(df, breadth, len(growth_stocks))
    
    st.markdown("---")
    
    # Intraday indicators row
    display_intraday_metrics(df, breadth)
    
    st.markdown("---")
    
    # Charts row
    col1, col2 = st.columns(2)
    
    with col1:
        fig = create_gainers_losers_chart(gainers_df, losers_df)
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    
    with col2:
        fig = create_volume_chart(df.nlargest(10, 'Volume'))
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    
    st.markdown("---")
    
    # Sector Performance
    col1, col2 = st.columns([1, 1])
    
    with col1:
        display_sector_performance(sector_df)
    
    with col2:
        if not sector_df.empty:
            fig = create_sector_heatmap(sector_df)
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    
    st.markdown("---")
    
    # Tables section
    col1, col2 = st.columns(2)
    
    with col1:
        display_movers_table(gainers_df, "Top Gainers", "🚀")
    
    with col2:
        display_movers_table(losers_df, "Top Losers", "📉")
    
    st.markdown("---")
    
    # Volume Leaders
    display_volume_leaders(df)
    
    st.markdown("---")
    
    # Growth Stocks
    display_growth_stocks(growth_stocks)
    
    # Close wrapper
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Footer with timestamp and countdown
    et = pytz.timezone('US/Eastern')
    now = datetime.now(et)
    refresh_min = config['refresh_interval_market_open'] if is_market_open() else config['refresh_interval_market_closed']
    refresh_sec = refresh_min * 60
    
    # Calculate time until next refresh
    last_refresh = st.session_state.get('last_refresh_time', now)
    elapsed = (now - last_refresh).total_seconds()
    remaining = max(0, refresh_sec - elapsed)
    remaining_min = int(remaining // 60)
    remaining_sec = int(remaining % 60)
    
    # Format countdown
    if remaining_min > 0:
        countdown_str = f"{remaining_min}m {remaining_sec}s"
    else:
        countdown_str = f"{remaining_sec}s"
    
    st.markdown(f"""
    <div class="last-updated">
        Last updated: {last_refresh.strftime('%H:%M:%S ET')} • 
        Next refresh in: <strong style="color: {COLORS['accent']};">{countdown_str}</strong> • 
        Interval: {refresh_min} min
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
