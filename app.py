import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import re

# === 1. Page & Style Configuration ===
st.set_page_config(
    page_title="KTT Branch Operation Dashboard",
    page_icon="📈",
    layout="wide"
)

# === 1.5. Theme Configuration ===

THEMES = {
    "Cinematic Dark": {
        "plotly_template": "plotly_dark",
        "chart": {
            "text": "#e9ecef", "sub_text": "#ced4da", "grid": "rgba(255,255,255,0.1)",
            "bg": "rgba(0,0,0,0)"
        },
        "css": """
    /* Global Background (Dark Gradient) */
    .stApp {
        background: radial-gradient(circle at 50% 10%, #1a1d21 0%, #0e1117 100%);
        color: #e9ecef;
    }
    .analysis-card {
        background-color: rgba(255, 255, 255, 0.05); /* Glass */
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
    }
    .insight-box {
        background: linear-gradient(135deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0.02) 100%);
        border-left: 4px solid #3bc9db;
    }
    .insight-title { color: #e9ecef; }
    .insight-text { color: #ced4da; }
    
    /* Metrics */
    div[data-testid="stMetricLabel"] { color: #adb5bd !important; }
    div[data-testid="stMetricValue"] { color: #f1f3f5 !important; }
    
    /* Summary Card (Hub) */
    .summary-card {
        background-color: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    .card-title { color: #e9ecef; }
    .card-sub { color: #adb5bd; }
    
    /* Highlight specific header (e.g. Gangbuk/Gangwon) - Yellow on Dark */
    .highlight-title .card-title {
        background-color: #ffd43b;
        color: #212529 !important;
        box-shadow: 0 0 10px rgba(255, 212, 59, 0.5);
    }
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] { background-color: rgba(255, 255, 255, 0.03); }
    .stTabs [data-baseweb="tab"] { color: #adb5bd; }
    .stTabs [aria-selected="true"] {
        background-color: rgba(59, 201, 219, 0.15) !important;
        color: #3bc9db !important;
    }
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #151820;
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }
    """
    },
    "Expert Premium": {
        "plotly_template": "plotly_white",
        "chart": {
            "text": "#212529", "sub_text": "#495057", "grid": "rgba(0,0,0,0.05)",
            "bg": "rgba(255,255,255,0.5)"
        },
        "css": """
    .stApp { background-color: #ecf0f5; background-image: linear-gradient(to right bottom, #ecf0f5, #f3f6f9); color: #212529; }
    .analysis-card { background-color: #ffffff; border: 1px solid rgba(0, 0, 0, 0.05); box-shadow: 0 10px 25px -5px rgba(50, 50, 93, 0.05); }
    .insight-box { background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%); border-left: 5px solid #339af0; box-shadow: 0 4px 6px rgba(0,0,0,0.02); }
    .insight-title { color: #1c2e4a; }
    .insight-text { color: #4b5563; }
    div[data-testid="stMetricLabel"] { color: #868e96 !important; }
    div[data-testid="stMetricValue"] { color: #212529 !important; }
    .summary-card { background-color: #ffffff; border: 1px solid rgba(0,0,0,0.08); box-shadow: 0 2px 8px rgba(0,0,0,0.04); }
    .summary-card:hover { border-color: rgba(51, 154, 240, 0.5); }
    .card-title { color: #343a40; }
    .card-sub { color: #868e96; }
    .highlight-title .card-title { background-color: #ffd43b; color: #212529 !important; box-shadow: 0 4px 10px rgba(255, 212, 59, 0.4); }
    .stTabs [data-baseweb="tab"] { background-color: #ffffff; border: 1px solid #e9ecef; color: #868e96; }
    .stTabs [aria-selected="true"] { background-color: #339af0 !important; color: #ffffff !important; box-shadow: 0 4px 10px rgba(51, 154, 240, 0.3); }
    [data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid #edf2f7; }
    ::-webkit-scrollbar-track { background: #f1f3f5; }
    ::-webkit-scrollbar-thumb { background: #adb5bd; }
    """
    },
    "Executive Navy": {
        "plotly_template": "plotly_dark",
        "chart": {
            "text": "#f1f5f9", "sub_text": "#cbd5e1", "grid": "rgba(255,255,255,0.08)",
            "bg": "#0f172a"
        },
        "css": """
    /* Executive Navy (Deep Slate Blue & Gold) */
    .stApp { background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%); color: #f8fafc; }
    .analysis-card { background-color: rgba(30, 41, 59, 0.7); border: 1px solid rgba(255, 255, 255, 0.05); box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3); }
    .insight-box { background: rgba(30, 41, 59, 0.4); border-left: 4px solid #fbbf24; }
    .insight-title { color: #fbbf24; }
    .insight-text { color: #e2e8f0; }
    div[data-testid="stMetricLabel"] { color: #94a3b8 !important; }
    div[data-testid="stMetricValue"] { color: #f1f5f9 !important; }
    .summary-card { background-color: rgba(30, 41, 59, 0.6); border: 1px solid rgba(148, 163, 184, 0.1); }
    .card-title { color: #f8fafc; }
    .card-sub { color: #94a3b8; }
    .highlight-title .card-title { background-color: #fbbf24; color: #0f172a !important; box-shadow: 0 0 15px rgba(251, 191, 36, 0.3); }
    .stTabs [data-baseweb="tab"] { color: #94a3b8; }
    .stTabs [aria-selected="true"] { background-color: rgba(251, 191, 36, 0.1) !important; color: #fbbf24 !important; border: 1px solid #fbbf24; }
    [data-testid="stSidebar"] { background-color: #020617; border-right: 1px solid #1e293b; }
    ::-webkit-scrollbar-track { background: #0f172a; }
    ::-webkit-scrollbar-thumb { background: #475569; }
    """
    },
    "Corporate Clean": {
        "plotly_template": "plotly_white",
        "chart": {
            "text": "#111827", "sub_text": "#4b5563", "grid": "rgba(0,0,0,0.06)",
            "bg": "#ffffff"
        },
        "css": """
    /* Corporate Clean (Indigo & White) */
    .stApp { background-color: #f9fafb; color: #111827; }
    .analysis-card { background-color: #ffffff; border: 1px solid #e5e7eb; box-shadow: none; border-radius: 8px; }
    .insight-box { background: #eef2ff; border-left: 4px solid #4f46e5; }
    .insight-title { color: #4338ca; }
    .insight-text { color: #374151; }
    div[data-testid="stMetricLabel"] { color: #6b7280 !important; }
    div[data-testid="stMetricValue"] { color: #111827 !important; }
    .summary-card { background-color: #ffffff; border: 1px solid #e5e7eb; border-radius: 6px; }
    .summary-card:hover { transform: translateY(-2px); transition: transform 0.2s; border-color: #4f46e5; }
    .card-title { color: #111827; font-weight: 600; }
    .card-sub { color: #6b7280; }
    .highlight-title .card-title { background-color: #4f46e5; color: #ffffff !important; box-shadow: 0 4px 6px rgba(79, 70, 229, 0.3); }
    .stTabs [data-baseweb="tab"] { background-color: white; border: 1px solid #d1d5db; color: #6b7280; }
    .stTabs [aria-selected="true"] { background-color: #4f46e5 !important; color: #ffffff !important; }
    [data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid #e5e7eb; }
    """
    },
    "Obsidian Pro": {
        "plotly_template": "plotly_dark",
        "chart": {
            "text": "#ffffff", "sub_text": "#a3a3a3", "grid": "#262626",
            "bg": "#000000"
        },
        "css": """
    /* Obsidian Pro (Pitch Black & Monochrome) */
    .stApp { background-color: #000000; color: #ffffff; }
    .analysis-card { background-color: #000000; border: 1px solid #333333; border-radius: 0px; }
    .insight-box { background: #0a0a0a; border-left: 2px solid #ffffff; border-radius: 0px; }
    .insight-title { color: #ffffff; font-family: monospace; }
    .insight-text { color: #d4d4d4; font-family: monospace; }
    div[data-testid="stMetricLabel"] { color: #737373 !important; font-family: monospace; }
    div[data-testid="stMetricValue"] { color: #ffffff !important; font-family: monospace; }
    .summary-card { background-color: #000000; border: 1px solid #333333; border-radius: 0px; }
    .summary-card:hover { border-color: #ffffff; }
    .card-title { color: #ffffff; font-family: monospace; text-transform: uppercase; }
    .card-sub { color: #737373; font-family: monospace; }
    .highlight-title .card-title { background-color: #ffffff; color: #000000 !important; border: 1px solid #ffffff; box-shadow: none; }
    .stTabs [data-baseweb="tab"] { background-color: #000000; border: 1px solid #333333; color: #737373; font-family: monospace; border-radius: 0px; }
    .stTabs [aria-selected="true"] { background-color: #ffffff !important; color: #000000 !important; border-radius: 0px; }
    [data-testid="stSidebar"] { background-color: #000000; border-right: 1px solid #333333; }
    """
    }
}

# --- Sidebar Theme Selection ---
with st.sidebar:
    st.markdown("### 🎨 테마 설정")
    sel_theme = st.selectbox("UI 테마 선택", list(THEMES.keys()), index=0)

cur_theme = THEMES[sel_theme]

# --- Shared CSS (Base) ---
st.markdown(f"""
<style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    
    html, body, [class*="css"] {{
        font-family: 'Pretendard', sans-serif !important;
    }}
    
    .analysis-card {{
        border-radius: 16px; padding: 24px;
        margin-bottom: 24px; transition: transform 0.2s ease;
    }}
    .analysis-card:hover {{ transform: translateY(-2px); }}
    
    .insight-box {{
        border-radius: 12px; padding: 20px;
        margin-bottom: 20px;
    }}
    .insight-title {{ font-size: 1.1em; font-weight: bold; margin-bottom: 8px; }}
    .insight-text {{ font-size: 0.95em; line-height: 1.6; }}
    
    /* Metric Common */
    [data-testid="stMetric"] {{ text-align: center; margin: 0 auto; border-radius: 12px; padding: 16px; }}
    [data-testid="stMetricLabel"] {{ justify-content: center; width: 100%; font-weight: 600; }}
    [data-testid="stMetricValue"] {{ justify-content: center; width: 100%; font-weight: 700; }}
    [data-testid="stMetricDelta"] {{ justify-content: center; width: 100%; display: flex; flex-direction: row-reverse; gap: 4px;}}
    [data-testid="stMetricDelta"] > div {{ justify-content: center; }}

    /* Summary Card Common */
    .summary-card {{
        border-radius: 12px; padding: 15px;
        text-align: center; margin-bottom: 10px;
        transition: transform 0.2s;
        display: flex; flex-direction: column; align-items: center; justify-content: center;
    }}
    .summary-card:hover {{ transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.2); }}
    
    .card-title {{ font-size: 1.1em; font-weight: bold; margin-bottom: 5px; }}
    .card-val {{ font-size: 1.5em; font-weight: bold; color: #3bc9db; }}
    .card-rate-high {{ color: #ff6b6b; }}
    .card-rate-ok {{ color: #69db7c; }}
    
    .highlight-title .card-title {{
        padding: 4px 8px;
        border-radius: 6px;
        display: inline-block;
    }}

    /* Tabs Common */
    .stTabs [data-baseweb="tab-list"] {{ gap: 12px; border-radius: 12px; padding: 8px; }}
    .stTabs [data-baseweb="tab"] {{ height: 40px; border-radius: 8px; font-weight: 600; border: none; }}

    /* Scrollbar Common */
    ::-webkit-scrollbar {{ width: 8px; height: 8px; }}
    ::-webkit-scrollbar-thumb {{ border-radius: 4px; }}
    
    /* INJECT DYNAMIC THEME CSS */
    {cur_theme['css']}
</style>
""", unsafe_allow_html=True)

# === 2. Settings & Constants ===
DEFAULT_EXCEL_FILE = "data.xlsx"

# Global Constants
HUB_BRANCH_MAP = {
    "강남/서부": ["강남", "서부", "강서", "송파", "충청", "대전", "전주/전북", "광주/전남", "제주"],
    "강북/강원": ["중앙", "강북", "서대문", "고양", "의정부", "남양주", "강릉", "원주"],
    "부산/경남": [],
    "대구/경북": [],
    "충남/충북": [],
    "전남/전북": []
}

HUB_NAME_MAP = {
    "강북강원": "강북/강원", "부산경남": "부산/경남", "전남전북": "전남/전북",
    "충남충북": "충남/충북", "대구경북": "대구/경북", "강남서부": "강남/서부"
}

ALL_BRANCHES = [br for branches in HUB_BRANCH_MAP.values() for br in branches]

PREFERRED_ORDER = ["강북강원", "강북/강원", "본부", "중앙", "강북", "서대문", "고양", "의정부", "남양주", "강릉", "원주"]
COLORS = ['#3bc9db', '#ff6b6b', '#69db7c', '#ffd43b', '#da77f2', '#ff8787', '#22b8cf', '#ced4da']

def sort_key(name):
    try: return PREFERRED_ORDER.index(name)
    except: return 999

# === 3. Data Loading Functions ===

def parse_date_robust(date_str):
    """Parses dates like '25/10(e)', '25/11.04', '44800'(Excel) into '2025-10-01'"""
    try:
        s = str(date_str).strip()
        # Handle Excel float dates (approx chk)
        if s.replace('.','',1).isdigit() and 30000 < float(s) < 60000:
            return pd.to_datetime(float(s), unit='D', origin='1899-12-30').strftime("%Y-%m-%d")
            
        # Regex: Start with 2 digits (Year), separator, 1-2 digits (Month)
        match = re.match(r'^(\d{2})[/.](?:\s*)(\d{1,2})', s)
        if match:
            yy, mm = match.groups()
            return f"20{yy}-{int(mm):02d}-01"
        
        # Try Std Pandas
        dt = pd.to_datetime(s, errors='coerce')
        if not pd.isna(dt):
            return dt.strftime("%Y-%m-%d")
            
        return None
    except: return None

def load_data_from_source(source, sheet_keyword, file_keyword):
    """Loads dataframe from Excel or CSV source"""
    if source is None: return None
    
    # 1. Excel File
    if hasattr(source, 'name') and source.name.endswith('.xlsx'):
        try:
            xls = pd.ExcelFile(source)
            for sheet in xls.sheet_names:
                if sheet_keyword in sheet:
                    return pd.read_excel(source, sheet_name=sheet, header=None)
        except: pass
    
    # 2. Local Excel Path
    if isinstance(source, str) and source.endswith('.xlsx') and os.path.exists(source):
         try:
            xls = pd.ExcelFile(source)
            for sheet in xls.sheet_names:
                if sheet_keyword in sheet:
                    return pd.read_excel(source, sheet_name=sheet, header=None)
         except: pass
    
    # 3. Local CSV Search
    for f in os.listdir('.'):
        if file_keyword in f and f.endswith('.csv'):
            return pd.read_csv(f, header=None)
            
    return None

@st.cache_data
def load_total_data():
    uploaded = st.session_state.get('uploaded_file')
    if uploaded: return load_data_from_source(uploaded, "시각화", "시각화")
    return load_data_from_source("data.xlsx", "시각화", "시각화")

@st.cache_data
def load_rate_data(type_key):
    uploaded = st.session_state.get('uploaded_file')
    kw_sheet = "정지율" if type_key == "suspension" else "부실율"
    kw_file = "기관정지율" if type_key == "suspension" else "기관부실율"
    if uploaded: return load_data_from_source(uploaded, kw_sheet, kw_file)
    return load_data_from_source("data.xlsx", kw_sheet, kw_file)

def process_total_df(df):
    if df is None: return None
    try:
        header_row = 3
        # Robust Header Search
        for i in range(min(50, len(df))):
            val = str(df.iloc[i, 0]).strip()
            if "구분" in val: 
                header_row = i; break
        
        # Corrected Ranges based on file analysis
        ranges = {"Total": (1, 13), "SP": (15, 27), "KPI": (28, 40)}
        col_names = ["L형 건", "i형 건", "L+i형 건", "L형 정지율", "i형 정지율", "L+i형 정지율",
                     "L형 월정료", "i형 월정료", "L+i형 월정료", "L형료 정지율", "i형료 정지율", "L+i형료 정지율"]
        
        parsed = []
        for i in range(header_row + 1, len(df)):
            row = df.iloc[i]
            org = str(row[0]).strip()
            if not org or org == 'nan': continue
            
            is_hub = org in HUB_BRANCH_MAP.keys()
            is_br = False; hub_name = org
            if is_hub: hub_name = org
            else:
                for h, brs in HUB_BRANCH_MAP.items():
                    if org in brs: is_br = True; hub_name = h; break
            if not (is_hub or is_br): continue
            
            for section, (start, end) in ranges.items():
                try:
                    vals = row[start:end].values
                    for idx, val in enumerate(vals):
                        try: num = float(str(val).replace(',', '').replace('-', '0'))
                        except: num = 0.0
                        parsed.append({
                            "본부": hub_name, "지사": org, "구분": "본부" if is_hub else "지사",
                            "데이터셋": section, "지표": col_names[idx], "값": num
                        })
                except: continue
        return pd.DataFrame(parsed)
    except: return None

def process_rate_df(df):
    if df is None: return None
    try:
        processed = []
        # Robust Iteration
        for i in range(0, df.shape[1], 2):
            if i+1 >= df.shape[1]: break
            br_name = str(df.iloc[0, i]).strip()
            if pd.isna(br_name) or br_name == 'nan': continue
            
            # Application of Name Mapping for Consistency (e.g. 강북강원 -> 강북/강원)
            if br_name in HUB_NAME_MAP:
                br_name = HUB_NAME_MAP[br_name]
            
            sub = df.iloc[1:, [i, i+1]].copy()
            sub.columns = ["d", "v"]
            sub = sub.dropna(subset=['d']) # Drop only if date is missing
            
            hub_name = "기타"
            real_name = HUB_NAME_MAP.get(br_name, br_name)
            if real_name in HUB_BRANCH_MAP.keys(): hub_name = real_name
            else:
                for h, brs in HUB_BRANCH_MAP.items():
                    if br_name in brs: hub_name = h; break
            
            for _, row in sub.iterrows():
                date_val = parse_date_robust(row['d'])
                if not date_val: continue
                try: val = float(str(row['v']).replace(',', ''))
                except: val = 0.0
                processed.append({"날짜": date_val, "본부": hub_name, "지사": br_name, "비율": val * 100})
        
        res = pd.DataFrame(processed)
        if not res.empty:
            res['날짜'] = pd.to_datetime(res['날짜'])
            res['월'] = res['날짜'].dt.strftime('%y년 %-m월')
        return res
    except: return None

# === 4. Data Processing Logic (Helpers) ===
def process_branch_bm_data(df_total, branch_name):
    # Use 'Total' dataset to match Hub Summary values (e.g. Row 6 Cols E/F)
    mask = (df_total['지사'] == branch_name) & (df_total['데이터셋'] == 'Total')
    df = df_total[mask]
    if df.empty: return None

    def get_val(metric):
        v = df[df['지표'] == metric]['값'].values
        return v[0] if len(v) > 0 else 0.0

    bm_data = [
        {
            "BM": "L형", "건수": get_val("L형 건"), "금액": get_val("L형 월정료"),
            "정지율": get_val("L형 정지율") * 100 if get_val("L형 정지율") < 1 else get_val("L형 정지율")
        },
        {
            "BM": "i형", "건수": get_val("i형 건"), "금액": get_val("i형 월정료"),
            "정지율": get_val("i형 정지율") * 100 if get_val("i형 정지율") < 1 else get_val("i형 정지율")
        }
    ]
    return pd.DataFrame(bm_data)

def generate_text_insight(df_bm, df_trend_susp):
    insights = []
    top_vol = df_bm.sort_values('금액', ascending=False).iloc[0]
    insights.append(f"💰 **운영 규모**: **{top_vol['BM']}**이 전체 월정료의 주력 상품군입니다.")
    
    high_risk_bm = df_bm.sort_values('정지율', ascending=False).iloc[0]
    risk_level = "높음" if high_risk_bm['정지율'] > 1.5 else "보통" if high_risk_bm['정지율'] > 0.5 else "양호"
    
    insights.append(f"⚠️ **리스크 분석**: **{high_risk_bm['BM']}**의 정지율이 **{high_risk_bm['정지율']:.2f}%**로 상대적으로 {risk_level} 수준입니다.")

    if not df_trend_susp.empty:
        latest = df_trend_susp.iloc[-1]['비율']
        prev = df_trend_susp.iloc[-2]['비율'] if len(df_trend_susp) > 1 else latest
        diff = latest - prev
        trend_str = "상승 🔴" if diff > 0 else "하락 🔵" if diff < 0 else "유지 ⚪"
        insights.append(f"📈 **추이**: 전월 대비 정지율이 **{abs(diff):.2f}%p {trend_str}**했습니다. (현재 {latest:.2f}%)")
    
    return "\n\n".join(insights)

def get_hub_summary(df_total):
    # Use 'Total' dataset as it contains aggregated Hub data
    mask_hub = (df_total['데이터셋'] == 'Total') & (df_total['구분'] == '본부')
    df = df_total[mask_hub]
    summary = []
    
def get_hub_summary(df_total):
    # Use 'Total' dataset as it contains aggregated Hub data
    mask_hub = (df_total['데이터셋'] == 'Total') & (df_total['구분'] == '본부')
    df = df_total[mask_hub]
    summary = []
    
    for hub in HUB_BRANCH_MAP.keys():
        d = df[df['본부'] == hub]
        if d.empty: continue
        try:
            cnt_total = d[d['지표'] == 'L+i형 건']['값'].sum()
            cnt_l = d[d['지표'] == 'L형 건']['값'].sum()
            cnt_i = d[d['지표'] == 'i형 건']['값'].sum()
            
            amt = d[d['지표'] == 'L+i형 월정료']['값'].sum()
            amt_l = d[d['지표'] == 'L형 월정료']['값'].sum()
            amt_i = d[d['지표'] == 'i형 월정료']['값'].sum()
            
            # Use Exact Matches to avoid mixing with 'Amount Rates' (Col M, etc.)
            rate_total = d[d['지표'] == 'L+i형 정지율']['값'].mean()
            rate_l = d[d['지표'] == 'L형 정지율']['값'].mean()
            rate_i = d[d['지표'] == 'i형 정지율']['값'].mean()
            
            # Normalize rates if < 1 (Excel dec)
            if rate_total < 1: rate_total *= 100
            if rate_l < 1: rate_l *= 100
            if rate_i < 1: rate_i *= 100

            summary.append({
                "본부": hub, 
                "총건수": cnt_total, "L건수": cnt_l, "i건수": cnt_i,
                "총금액": amt, "L금액": amt_l, "i금액": amt_i, 
                "정지율": rate_total, "L정지율": rate_l, "i정지율": rate_i
            })
        except: continue
    return pd.DataFrame(summary)

# === 5. UI & Main Logic ===

with st.sidebar:
    # Use column for better logo alignment if needed, or simple image
    st.markdown("### Admin Dashboard")
    st.caption("Operation & Risk Management")
    
    # External Link
    st.link_button("🔗 상세내역 바로가기", "https://a-management-dashboard-6kyyf824usuawa7kdpf4vj.streamlit.app/", type="primary", use_container_width=True)
    
    st.markdown("---")
    with st.expander("📂 데이터 파일 업로드 (관리자용)"):
        pwd = st.text_input("비밀번호 입력", type="password", key="admin_pwd")
        if pwd == "3867":
            uploaded_file = st.file_uploader("파일 선택 (Excel/CSV)", type=['xlsx', 'csv'])
            if uploaded_file: st.session_state['uploaded_file'] = uploaded_file
        elif pwd:
            st.error("비밀번호 불일치")
    
    st.markdown("---")
    mode = st.radio("MENU", ["🔍 지사별 상세 분석", "📊 전체 현황 스냅샷", "📈 전체 추이 비교"])

# Load & Process
with st.spinner("데이터를 불러오는 중..."):
    raw_total = load_total_data()
    raw_susp = load_rate_data("suspension")
    raw_fail = load_rate_data("failure")

    df_total = process_total_df(raw_total)
    # Ensure df_susp and df_fail are dataframes, even if empty
    df_susp = process_rate_df(raw_susp)
    if df_susp is None: df_susp = pd.DataFrame()
    
    df_fail = process_rate_df(raw_fail)
    if df_fail is None: df_fail = pd.DataFrame()

if df_total is None:
    st.info("👋 데이터 파일을 업로드하거나 프로젝트 폴더에 'data.xlsx' 또는 'csv' 파일을 위치시켜 주세요.")
    st.stop()

# --- TOP SECTION: Hub Status ---
with st.expander("🏢 본부별 운영 현황 요약", expanded=True):
    hub_summ = get_hub_summary(df_total)
    if not hub_summ.empty:
        cols = st.columns(len(hub_summ))
        for idx, row in hub_summ.iterrows():
            with cols[idx % len(cols)]:
                label = f"{row['본부']}"
                rate_total = row['정지율']
                rate_l = row['L정지율']; rate_i = row['i정지율']
                
                # Rate Color Logic (Class-based for Theme Support)
                rate_class = "card-rate-high" if rate_total >= 1.0 else "card-rate-ok"
                
                # Check Highlight
                is_target = "강북" in label and "강원" in label
                hl_class = "highlight-title" if is_target else ""

                st.markdown(f"""
                <div class="summary-card {hl_class}">
                    <div class="card-title">{label}</div>
                    <div class="card-val {rate_class}">{rate_total:.2f}%</div>
                    <div class="card-sub" style="margin-bottom:8px;">
                        L: {rate_l:.2f}% | i: {rate_i:.2f}%
                    </div>
                    <div style="font-size:0.9em; border-top:1px solid rgba(128,128,128,0.2); padding-top:8px; width:100%;">
                        <div style="display:flex; justify-content:space-between;">
                            <span>Total</span> <span><b>{int(row['총건수']):,}</b></span>
                        </div>
                        <div style="display:flex; justify-content:space-between; font-size:0.85em; opacity:0.8; margin-bottom:4px;">
                            <span>L: {int(row['L건수']):,}</span> <span>i: {int(row['i건수']):,}</span>
                        </div>
                        <div style="display:flex; justify-content:space-between; border-top:1px dashed rgba(128,128,128,0.2); padding-top:4px;">
                            <span>Amt(천원)</span> <span><b>{int(row['총금액']):,}</b></span>
                        </div>
                        <div style="display:flex; justify-content:space-between; font-size:0.85em; opacity:0.8;">
                            <span>L: {int(row['L금액']):,}</span> <span>i: {int(row['i금액']):,}</span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
    else: st.info("본부 데이터가 없습니다.")

    # [Added Request] Branch Summary for '강북/강원'
    st.markdown("---")
    st.markdown("##### 🌲 강북/강원 지사별 요약")
    
    # Filter for Gangbuk/Gangwon branches
    target_hub = "강북/강원"
    mask_br = (df_total['데이터셋'] == 'Total') & (df_total['구분'] == '지사') & (df_total['본부'] == target_hub)
    df_br_summ = df_total[mask_br]
    
    if not df_br_summ.empty:
        # Get unique branches in preferred order
        br_list = [b for b in HUB_BRANCH_MAP[target_hub] if b in df_br_summ['지사'].unique()]
        
        # Display in rows of 5 or all in one responsive wrap? 
        # Using columns matching the number of branches (max 8) might be tight, let's use columns(len)
        cols_br = st.columns(len(br_list))
        
        for idx, br in enumerate(br_list):
            d = df_br_summ[df_br_summ['지사'] == br]
            if d.empty: continue
            try:
                cnt = d[d['지표'] == 'L+i형 건']['값'].sum()
                amt = d[d['지표'] == 'L+i형 월정료']['값'].sum()
                # Exact match for rate
                rate = d[d['지표'] == 'L+i형 정지율']['값'].mean()
                if rate < 1: rate *= 100
                
                # MoM Calculation (from df_susp)
                mom_html = ""
                if not df_susp.empty:
                    tr = df_susp[df_susp['지사'] == br].sort_values('날짜')
                    if len(tr) >= 2:
                        curr = tr.iloc[-1]['비율']
                        prev = tr.iloc[-2]['비율']
                        diff = curr - prev
                        
                        # Symbol & Color
                        symbol = "▲" if diff > 0 else "▼" if diff < 0 else "-"
                        d_color = "#ff6b6b" if diff > 0 else "#339af0" if diff < 0 else "#adb5bd"
                        
                        mom_html = f"<span style='font-size:0.6em; color:{d_color}; margin-left:4px;'>({symbol}{abs(diff):.2f}%p)</span>"
                
                with cols_br[idx % len(cols_br)]:
                    amt_unit = int(amt / 1000)
                    rate_class = "card-rate-high" if rate >= 1.0 else "card-rate-ok"
                    
                    st.markdown(f"""
                    <div class="summary-card">
                        <div class="card-title">{br}</div>
                        <div class="card-val {rate_class}">{rate:.2f}% {mom_html}</div>
                        <div class="card-sub">{int(cnt):,} / ₩{amt_unit:,}백만</div>
                    </div>
                    """, unsafe_allow_html=True)
            except: continue

# ----------------- 1. Branch Detail Analysis -----------------
if "지사별 상세 분석" in mode:
    st.title("🔍 지사별 운영 현황 상세 분석")
    
    with st.sidebar:
        st.markdown("---")
        st.subheader("필터링 설정")
        hub_options = ["전체"] + list(HUB_BRANCH_MAP.keys())
        default_hub_idx = hub_options.index("강북/강원") if "강북/강원" in hub_options else 0
        sel_hub_detail = st.selectbox("본부 선택", hub_options, index=default_hub_idx)
        
        raw_branches = ALL_BRANCHES if sel_hub_detail == "전체" else HUB_BRANCH_MAP.get(sel_hub_detail, [])
        # Append logic: explicitly add the Hub itself (mapped usually as '강북강원' or '강북/강원' depending on data)
        # Checking if '강북/강원' exists in data as a 'branch' equivalent or if we need to manually key it.
        # Based on previous tasks, '강북/강원' works as a key in process_total_df.
        if sel_hub_detail == "강북/강원" and "강북/강원" not in raw_branches:
             raw_branches = ["강북/강원"] + raw_branches

        sorted_branches = sorted(raw_branches, key=sort_key)
        
        # Default to Gangbuk/Gangwon if present
        def_idx = 0
        if "강북/강원" in sorted_branches:
            def_idx = sorted_branches.index("강북/강원")
            
        target_branch = st.selectbox("지사 선택", sorted_branches, index=def_idx)

    # --- Hub Comparative Insight (Added Request) ---
    if sel_hub_detail != "전체":
        # 1. Prepare Data
        mask_hub = (df_total['데이터셋'] == 'Total') & (df_total['구분'] == '지사') & (df_total['본부'] == sel_hub_detail)
        df_h = df_total[mask_hub]
        
        if not df_h.empty:
            summary_list = []
            valid_branches = [b for b in HUB_BRANCH_MAP.get(sel_hub_detail, []) if b in df_h['지사'].unique()]
            
            # Extract Rate/Amt for each branch
            stats = []
            for br in valid_branches:
                d = df_h[df_h['지사'] == br]
                if d.empty: continue
                try:
                    r = d[d['지표'] == 'L+i형 정지율']['값'].mean()
                    if r < 1: r *= 100
                    amt = d[d['지표'] == 'L+i형 월정료']['값'].sum()
                    stats.append({'br': br, 'rate': r, 'amt': amt})
                except: continue
            
            if stats:
                df_stats = pd.DataFrame(stats)
                worst = df_stats.loc[df_stats['rate'].idxmax()]
                best  = df_stats.loc[df_stats['rate'].idxmin()]
                vol   = df_stats.loc[df_stats['amt'].idxmax()]
                
                # Color logic
                w_color = "#ff6b6b" # Red
                b_color = "#339af0" # Blue
                
                summary_html = f"""
                <div style="display:flex; gap:20px; align-items:center; flex-wrap:wrap;">
                    <div>⚠️ <b>관리 요망 (최고 정지율)</b>: <span style="color:{w_color}; font-weight:bold;">{worst['br']} ({worst['rate']:.2f}%)</span></div>
                    <div style="border-left:1px solid #dee2e6; height:20px;"></div>
                    <div>🏆 <b>우수 지사 (최저 정지율)</b>: <span style="color:{b_color}; font-weight:bold;">{best['br']} ({best['rate']:.2f}%)</span></div>
                    <div style="border-left:1px solid #dee2e6; height:20px;"></div>
                    <div>💰 <b>최대 규모</b>: <b>{vol['br']}</b></div>
                    <div style="border-left:1px solid #dee2e6; height:20px;"></div>
                    <div>📊 <b>평균 정지율</b>: {df_stats['rate'].mean():.2f}%</div>
                </div>
                """
                
                st.markdown(f"""
                <div class="insight-box" style="background: linear-gradient(135deg, rgba(33, 37, 41, 0.02) 0%, rgba(33, 37, 41, 0.05) 100%); border-left: 5px solid #ffd43b;">
                    <div class="insight-title" style="color:{cur_theme['chart']['text']}">📢 {sel_hub_detail} 전체 요약</div>
                    <div class="insight-text" style="color:{cur_theme['chart']['sub_text']}">{summary_html}</div>
                </div>
                """, unsafe_allow_html=True)

    df_bm = process_branch_bm_data(df_total, target_branch)
    
    # Safe filtering
    cols_req = ['지사', '날짜']
    if not df_susp.empty and all(c in df_susp.columns for c in cols_req):
        trend_s = df_susp[df_susp['지사'] == target_branch].sort_values('날짜')
    else: trend_s = pd.DataFrame()

    if not df_fail.empty and all(c in df_fail.columns for c in cols_req):
        trend_f = df_fail[df_fail['지사'] == target_branch].sort_values('날짜')
    else: trend_f = pd.DataFrame()


    if df_bm is None:
        st.warning("선택한 지사의 상세 데이터가 없습니다.")
    else:
        # Insight Section
        insight_text = generate_text_insight(df_bm, trend_s)
        insight_html = insight_text.replace('\\n', '<br>')
        
        # Display Name Logic
        display_branch = "강북강원" if target_branch == "강북강원" else target_branch
        
        st.markdown(f"""
        <div class="insight-box">
            <div class="insight-title">💡 {display_branch} 운영 인사이트</div>
            <div class="insight-text">{insight_html}</div>
        </div>""", unsafe_allow_html=True)

        # 1. BM Detail Analysis Expander
        with st.expander("📊 BM별 상세 분석 (물량 vs 리스크)", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("##### 📦 BM별 물량(건수) 비교")
                fig_bar = px.bar(df_bm, x='BM', y='건수', color='BM', text_auto=',.0f', color_discrete_sequence=COLORS, template=cur_theme['plotly_template'])
                fig_bar.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                    height=350, showlegend=False, 
                    font=dict(family="Pretendard", color=cur_theme['chart']['sub_text']),
                    yaxis=dict(showgrid=True, gridcolor=cur_theme['chart']['grid'])
                )
                st.plotly_chart(fig_bar, use_container_width=True)
            with col2:
                st.markdown("##### 💰 BM별 물량(금액) 비교")
                fig_amt = px.bar(df_bm, x='BM', y='금액', color='BM', text_auto=',.0f', color_discrete_sequence=COLORS, template=cur_theme['plotly_template'])
                fig_amt.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                    height=350, showlegend=False,
                    font=dict(family="Pretendard", color=cur_theme['chart']['sub_text']),
                    yaxis=dict(showgrid=True, gridcolor=cur_theme['chart']['grid']),
                    yaxis_tickformat=',' 
                )
                st.plotly_chart(fig_amt, use_container_width=True)


        # 2. Trend Analysis Expander (Grid View)
        with st.expander("📈 월별 리스크 추이 분석 (본부 + 지사 전체)", expanded=True):
            # Define entities to show: Hub first, then Branches
            if sel_hub_detail != "전체":
                # Dedup using dict.fromkeys to preserve order (Hub First)
                target_list = list(dict.fromkeys([sel_hub_detail] + sorted_branches))
            else:
                # If 'Total' selected, showing all might be too much, but let's follow logic or stick to sorted_branches
                target_list = sorted_branches

            # Create Grid
            cols = st.columns(3)
            
            for idx, entity in enumerate(target_list):
                with cols[idx % 3]:
                    # Display Name Logic
                    display_name = "강북강원" if entity == "강북/강원" else entity
                    
                    # Fetch Data
                    t_s = df_susp[df_susp['지사'] == entity].sort_values('날짜') if not df_susp.empty else pd.DataFrame()
                    t_f = df_fail[df_fail['지사'] == entity].sort_values('날짜') if not df_fail.empty else pd.DataFrame()
                    
                    if t_s.empty and t_f.empty:
                        st.warning(f"{display_name}: 데이터 없음")
                        continue
                        
                    fig = make_subplots(specs=[[{"secondary_y": True}]])
                    
                    # Suspension Rate (Area + Line + Values)
                    if not t_s.empty:
                        fig.add_trace(go.Scatter(
                            x=t_s['날짜'], y=t_s['비율'], name="정지율",
                            mode='lines+markers+text',
                            text=[f"{v:.2f}%" for v in t_s['비율']],
                            textposition="top center", 
                            textfont=dict(size=10, color="#e9ecef"),
                            line=dict(color=COLORS[0], width=3, shape='spline'),
                            marker=dict(size=6, line=dict(width=1, color="#0E1117")),
                            fill='tozeroy', fillcolor=f"rgba{tuple(int(COLORS[0].lstrip('#')[i:i+2], 16) for i in (0, 2, 4)) + (0.1,)}"
                        ), secondary_y=False)

                    # Failure Rate (Dotted Line + Values)
                    if not t_f.empty:
                        fig.add_trace(go.Scatter(
                            x=t_f['날짜'], y=t_f['비율'], name="부실율",
                            mode='lines+markers+text',
                            text=[f"{v:.2f}%" for v in t_f['비율']],
                            textposition="bottom center",
                            textfont=dict(size=10, color=COLORS[1]),
                            line=dict(color=COLORS[1], width=2, dash='dot'),
                            marker=dict(size=5, symbol='diamond')
                        ), secondary_y=True)

                    fig.update_layout(
                        title=dict(text=f"<b>{display_name}</b>", font=dict(size=15, color=cur_theme['chart']['text']), x=0, y=0.95),
                        template=cur_theme['plotly_template'],
                        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                        height=280, 
                        showlegend=True,
                        legend=dict(orientation="h", yanchor="top", y=1.15, xanchor="right", x=1, font=dict(size=10, color=cur_theme['chart']['sub_text'])),
                        margin=dict(l=10, r=10, t=40, b=40),
                        yaxis=dict(showticklabels=False, showgrid=True, gridcolor=cur_theme['chart']['grid'])
                    )
                    
                    # Custom X-Axis Labels (e.g., '25.1, '25.2 ...)
                    all_dates = pd.concat([t_s['날짜'], t_f['날짜']]).unique()
                    all_dates = sorted(all_dates)
                    
                    if len(all_dates) > 0:
                        tick_vals = all_dates
                        tick_texts = []
                        
                        for d_str in all_dates:
                            try:
                                # d_str is 'YYYY-MM-DD'
                                y_str, m_str, _ = str(d_str).split('-')
                                y_short = y_str[2:]
                                m_int = int(m_str)
                                
                                # Requested Format: '25.1
                                lbl = f"'{y_short}.{m_int}"
                                tick_texts.append(lbl)
                            except:
                                tick_texts.append(d_str)

                        fig.update_xaxes(
                            tickmode='array',
                            tickvals=tick_vals,
                            ticktext=tick_texts,
                            showgrid=False,
                            showticklabels=True,
                            tickfont=dict(size=11, color=cur_theme['chart']['sub_text'], weight="bold"),
                            automargin=True
                        )

                    st.plotly_chart(fig, use_container_width=True)

# ----------------- 2. Overall Snapshot -----------------
elif "전체 현황 스냅샷" in mode:
    st.title("📊 전체 지사 운영 현황 스냅샷")
    with st.sidebar:
        st.markdown("---")
        hub_options = ["전체"] + list(HUB_BRANCH_MAP.keys())
        default_hub_idx = hub_options.index("강북/강원") if "강북/강원" in hub_options else 0
        sel_hub = st.selectbox("본부 필터", hub_options, index=default_hub_idx)
        raw_branches = ALL_BRANCHES if sel_hub == "전체" else HUB_BRANCH_MAP.get(sel_hub, [])
        sorted_branches = sorted(raw_branches, key=sort_key)
        defaults = ["중앙","강북","서대문", "고양","의정부", "남양주", "강릉", "원주"]
        default_sel = [b for b in sorted_branches if b in defaults]
        if not default_sel: default_sel = sorted_branches[:5]
        sel_brs = st.multiselect("지사 필터", sorted_branches, default=default_sel)
    
    t1, t2, t3 = st.tabs(["📌 Total", "⚡ SP 기준", "📉 KPI"])
    def render_tab(key):
        mask = df_total['데이터셋'] == key
        if sel_hub != "전체" or sel_brs:
            df_v = df_total[mask & (df_total['구분'] == '지사') & (df_total['지사'].isin(sel_brs))]
        else:
            df_v = df_total[mask & (df_total['구분'] == '본부')]
            df_v['지사'] = df_v['본부']
        if df_v.empty: st.info("데이터 없음"); return
        
        m_type = st.radio("지표", ["건수", "금액"], key=f"snap_{key}", horizontal=True)
        if key == "KPI":
             if m_type == "건수": cols = ["L형 건"]; fmt = ",.0f"
             else: cols = ["L형 월정료"]; fmt = ",.0f"
        else:
            if m_type == "건수": cols = ["L형 건", "i형 건", "L+i형 건"]; fmt = ",.0f"
            else: cols = ["L형 월정료", "i형 월정료", "L+i형 월정료"]; fmt = ",.0f"
        
        df_c = df_v[df_v['지표'].isin(cols)].copy()
        df_c['sort_idx'] = df_c['지사'].apply(sort_key)
        df_c = df_c.sort_values(['sort_idx', '값'], ascending=[True, False])
        
        # 2x2 Grid Layout
        r1_c1, r1_c2 = st.columns(2)
        r2_c1, r2_c2 = st.columns(2)
        
        # --- 1. Pie Chart (Top Left) ---
        with r1_c1:
            df_pie = df_c.groupby('지사')['값'].sum().reset_index()
            fig_pie = px.pie(df_pie, values='값', names='지사', hole=0.4, color_discrete_sequence=COLORS)
            fig_pie.update_traces(textinfo='percent+label', textfont_size=11)
            fig_pie.update_layout(
                title=dict(text=f"<b>지사별 {m_type} 비중</b>", font=dict(color=cur_theme['chart']['text']), x=0.5),
                template=cur_theme['plotly_template'],
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                showlegend=False, margin=dict(t=40, b=10, l=10, r=10), height=350,
                font=dict(family="Pretendard", color=cur_theme['chart']['sub_text'])
            )
            st.plotly_chart(fig_pie, use_container_width=True)

        # --- 2. Bar Chart (Top Right) ---
        with r1_c2:
            fig = px.bar(df_c, x='지사', y='값', color='지표', barmode='group', text_auto=fmt, 
                            color_discrete_sequence=COLORS, template=cur_theme['plotly_template'])
            fig.update_layout(
                title=dict(text=f"<b>지사별 {m_type} (절대값)</b>", font=dict(color=cur_theme['chart']['text']), x=0.5),
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                height=350, xaxis_title=None, 
                font=dict(family="Pretendard", color=cur_theme['chart']['sub_text']),
                yaxis=dict(showgrid=True, gridcolor=cur_theme['chart']['grid']),
                margin=dict(t=40, b=10, l=10, r=10)
            )
            st.plotly_chart(fig, use_container_width=True)
            
        # Prepare Data for Row 2 (Rate-based)
        df_quad = pd.DataFrame()
        try:
             # Identify prefix (L, i, L+i)
             target_prefix = "L+i"
             if "L형" in cols[0] and "L+i" not in cols[0]: target_prefix = "L"
             elif "i형" in cols[0] and "L+i" not in cols[0]: target_prefix = "i"
             rate_col = f"{target_prefix}형 정지율"
             
             # Get Rate Data
             rate_df = df_v[df_v['지표'] == rate_col][['지사', '값']].rename(columns={'값': 'rate'})
             if not rate_df.empty and rate_df['rate'].mean() < 1: rate_df['rate'] *= 100
             # Merge
             df_quad = pd.merge(df_pie, rate_df, on='지사', how='inner')
             
             if not df_quad.empty:
                # --- 3. Quadrant Chart (Bottom Left) ---
                with r2_c1:
                     mean_x = df_quad['값'].mean()
                     mean_y = df_quad['rate'].mean()
                     
                     fig_quad = px.scatter(df_quad, x='값', y='rate', text='지사', color='지사', 
                                         color_discrete_sequence=COLORS)
                     fig_quad.update_traces(textposition='top center', marker=dict(size=12, line=dict(width=1, color='white')))
                     
                     fig_quad.add_hline(y=mean_y, line_width=1, line_dash="dash", line_color=cur_theme['chart']['sub_text'])
                     fig_quad.add_vline(x=mean_x, line_width=1, line_dash="dash", line_color=cur_theme['chart']['sub_text'])
                     
                     fig_quad.update_layout(
                         title=dict(text=f"<b>사분면 분석 ({m_type} vs 정지율)</b>", font=dict(color=cur_theme['chart']['text']), x=0.5),
                         template=cur_theme['plotly_template'],
                         paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                         showlegend=False, height=350,
                         xaxis=dict(title=m_type, showgrid=True, gridcolor=cur_theme['chart']['grid']),
                         yaxis=dict(title="정지율(%)", showgrid=True, gridcolor=cur_theme['chart']['grid']),
                         font=dict(family="Pretendard", color=cur_theme['chart']['sub_text']),
                         margin=dict(l=10, r=10, t=40, b=10)
                     )
                     st.plotly_chart(fig_quad, use_container_width=True)

                # --- 4. Risk Ranking Chart (Bottom Right) ---
                with r2_c2:
                    df_rank = df_quad.sort_values('rate', ascending=True) # Ascending for BarH (Top=Highest?) No barh plots bottom-up usually.
                    # We want Highest Risk at Top? Or Sorted?
                    # Let's simple Ascending sort so Highest is at top in plotly barh default? (Plotly plots Y bottom-to-top)
                    # Actually let's sort Descending (High Risk first)? 
                    # If we use y='지사', x='rate', and orient='h'.
                    
                    fig_risk = px.bar(df_rank, x='rate', y='지사', text='rate', orientation='h',
                                      color='rate', color_continuous_scale='Reds')
                    fig_risk.update_traces(texttemplate='%{x:.2f}%', textposition='inside')
                    fig_risk.update_layout(
                        title=dict(text=f"<b>지사별 정지율 랭킹 ({target_prefix}형 기준)</b>", font=dict(color=cur_theme['chart']['text']), x=0.5),
                        template=cur_theme['plotly_template'],
                        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                        height=350, showlegend=False,
                        xaxis=dict(showgrid=True, gridcolor=cur_theme['chart']['grid'], title="정지율(%)"),
                        yaxis=dict(title=None),
                        font=dict(family="Pretendard", color=cur_theme['chart']['sub_text']),
                        margin=dict(l=10, r=10, t=40, b=10)
                    )
                    st.plotly_chart(fig_risk, use_container_width=True)
                    
        except Exception as e: st.error(f"Quad/Risk Error: {str(e)}")
    
    with t1: render_tab("Total")
    with t2: render_tab("SP")
    with t3: render_tab("KPI")

# ----------------- 3. Overall Trend -----------------
else:
    st.title("📈 전체 지사 추이 비교 분석")
    type_r = st.radio("분석 항목", ["정지율", "부실율"], horizontal=True)
    target_df = df_susp if type_r == "정지율" else df_fail
    
    with st.sidebar:
        st.markdown("---")
        hub_options = ["전체"] + list(HUB_BRANCH_MAP.keys())
        default_hub_idx = hub_options.index("강북/강원") if "강북/강원" in hub_options else 0
        sel_hub = st.selectbox("본부 선택", hub_options, index=default_hub_idx, key='trend_hub')
        raw_branches = ALL_BRANCHES if sel_hub == "전체" else HUB_BRANCH_MAP.get(sel_hub, [])
        sorted_branches = sorted(raw_branches, key=sort_key)
        defaults = ["중앙","강북","서대문", "고양","의정부", "남양주", "강릉", "원주"]
        default_sel = [b for b in sorted_branches if b in defaults]
        if not default_sel: default_sel = sorted_branches[:5]
        sel_brs = st.multiselect("비교할 지사 선택", sorted_branches, default=default_sel)
    
    # Safe rendering
    if not target_df.empty:
        if sel_brs:
            df_v = target_df[target_df['지사'].isin(sel_brs)].copy()
            df_v['sort_idx'] = df_v['지사'].apply(sort_key)
            df_v = df_v.sort_values(['sort_idx', '날짜'])
            
            fig = go.Figure()
            for i, branch in enumerate(df_v['지사'].unique()):
                d = df_v[df_v['지사'] == branch]
                color = COLORS[i % len(COLORS)]
                fig.add_trace(go.Scatter(
                    x=d['날짜'], y=d['비율'], mode='lines+markers', name=branch, 
                    line=dict(width=3, color=color, shape='spline'), 
                    marker=dict(size=8, color=color, line=dict(width=1, color='white')), 
                    hovertemplate=f"<b>{branch}</b><br>%{{x|%y.%m}}<br>{type_r}: %{{y:.2f}}%<extra></extra>"
                ))
                if not d.empty:
                    last_val = d.iloc[-1]
                    fig.add_annotation(
                        x=last_val['날짜'], y=last_val['비율'], text=f"{last_val['비율']:.2f}%", 
                        showarrow=False, yshift=10, 
                        font=dict(color=color, size=11, weight="bold"),
                        bgcolor="rgba(0,0,0,0.6)", borderpad=2, bordercolor=color
                    )
            
            fig.update_layout(
                template=cur_theme['plotly_template'],
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                hovermode="x unified", height=600, 
                xaxis=dict(tickformat="%y.%m", showgrid=True, gridcolor=cur_theme['chart']['grid']), 
                yaxis=dict(ticksuffix="%", tickformat=".2f", showgrid=True, gridcolor=cur_theme['chart']['grid']), 
                font=dict(family="Pretendard", color=cur_theme['chart']['sub_text']), 
                margin=dict(r=20)
            )
            st.plotly_chart(fig, use_container_width=True)
        else: st.info("비교할 지사를 선택해주세요.")
    else: st.warning(f"{type_r} 데이터가 없습니다.")
