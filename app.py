import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import re

# === 1. Page & Style Configuration (Expert UI/UX) ===
st.set_page_config(
    page_title="KTT Branch Operation Dashboard",
    page_icon="📈",
    layout="wide"
)

st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    
    html, body, [class*="css"] {
        font-family: 'Pretendard', sans-serif !important;
    }
    
    /* Global Background & Text */
    .stApp {
        background-color: #f8f9fa;
        color: #212529;
    }

    /* Analysis Card Style */
    .analysis-card {
        background-color: #ffffff;
        border-radius: 16px;
        padding: 24px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.03);
        border: 1px solid #f1f3f5;
        margin-bottom: 24px;
        transition: transform 0.2s ease;
    }
    .analysis-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 30px rgba(0,0,0,0.06);
    }
    
    /* Insight Box */
    .insight-box {
        background-color: #f1f3f5;
        border-left: 4px solid #228be6;
        padding: 20px;
        border-radius: 8px;
        margin-bottom: 24px;
    }
    .insight-title {
        font-weight: 700;
        color: #343a40;
        margin-bottom: 12px;
        font-size: 1.05em;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .insight-text {
        color: #495057;
        font-size: 0.95em;
        line-height: 1.6;
    }
    
    /* Metric Style */
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        padding: 16px;
        border-radius: 12px;
        border: 1px solid #e9ecef;
        box-shadow: 0 2px 5px rgba(0,0,0,0.02);
    }
    div[data-testid="stMetric"] label {
        font-size: 0.9em;
        color: #868e96;
    }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        font-size: 1.6em;
        font-weight: 700;
        color: #212529;
    }

    /* Expander Style */
    .streamlit-expanderHeader {
        font-weight: 600;
        font-family: 'Pretendard';
        background-color: #ffffff;
        border-radius: 8px;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] { 
        height: 44px; border-radius: 8px; background-color: #ffffff; 
        border: 1px solid #dee2e6; font-weight: 600; color: #495057;
        font-size: 0.9em;
    }
    .stTabs [aria-selected="true"] { 
        background-color: #e7f5ff !important; border-color: #1c7ed6 !important; 
        color: #1c7ed6 !important; 
    }
    
    [data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid #e9ecef; }
</style>
""", unsafe_allow_html=True)

# === 2. Settings & Constants ===
DEFAULT_EXCEL_FILE = "data.xlsx"

HUB_BRANCH_MAP = {
    "강남/서부": ["강남", "수원", "분당", "강동", "용인", "평택", "인천", "강서", "부천", "안산", "안양", "관악"],
    "강북/강원": ["중앙", "강북", "서대문", "고양", "의정부", "남양주", "강릉", "원주"],
    "부산/경남": ["동부산", "남부산", "창원", "서부산", "김해", "울산", "진주"],
    "전남/전북": ["광주", "전주", "익산", "북광주", "순천", "제주", "목포"],
    "충남/충북": ["서대전", "충북", "천안", "대전", "충남서부"],
    "대구/경북": ["동대구", "서대구", "구미", "포항"]
}
ALL_BRANCHES = [b for branches in HUB_BRANCH_MAP.values() for b in branches]

# Updated Sort Order
PREFERRED_ORDER = ["강북강원", "본부", "중앙", "강북", "서대문", "고양", "의정부", "남양주", "강릉", "원주"]
def sort_key(name):
    try: return PREFERRED_ORDER.index(name)
    except: return 999

# Palette
COLORS = ['#228be6', '#fa5252', '#40c057', '#fcc419', '#7950f2', '#e64980', '#15aabf', '#868e96']

# === 3. Data Loading Functions ===

def parse_date_robust(date_str):
    try:
        s = str(date_str).strip()
        match = re.match(r'^(\d{2})[/.](?:\s*)(\d{1,2})', s)
        if match:
            yy, mm = match.groups()
            return f"20{yy}-{int(mm):02d}-01"
        return None
    except: return None

def find_sheet_by_keyword(excel_file, keywords):
    try:
        xls = pd.ExcelFile(excel_file)
        for sheet in xls.sheet_names:
            for kw in keywords:
                if kw in sheet: return sheet
        return None
    except: return None

def get_excel_file():
    uploaded = st.sidebar.file_uploader("📂 Upload Excel File (.xlsx)", type=['xlsx'])
    if uploaded: return uploaded
    if os.path.exists(DEFAULT_EXCEL_FILE): return DEFAULT_EXCEL_FILE
    return None

@st.cache_data
def load_total_data(file_source):
    if not file_source: return None
    try:
        sheet = find_sheet_by_keyword(file_source, ["시각화", "0901", "Sheet1"])
        if not sheet: return None
        df = pd.read_excel(file_source, sheet_name=sheet, header=None)
        
        header_row = 3
        for i in range(min(20, len(df))):
            if str(df.iloc[i, 0]).strip() == "구분": header_row = i; break
        
        ranges = {"Total": (1, 13), "SP": (15, 27), "KPI": (29, 41)}
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

@st.cache_data
def load_rate_data(file_source, type_key):
    if not file_source: return None
    try:
        kw = ["정지율"] if type_key == "suspension" else ["부실율"]
        sheet = find_sheet_by_keyword(file_source, kw)
        if not sheet: return None
        df = pd.read_excel(file_source, sheet_name=sheet, header=None)
        processed = []
        
        for i in range(0, df.shape[1], 2):
            if i+1 >= df.shape[1]: break
            br_name = str(df.iloc[0, i]).strip()
            if pd.isna(br_name) or br_name == 'nan': continue
            
            sub = df.iloc[1:, [i, i+1]].copy()
            sub.columns = ["d", "v"]
            sub = sub.dropna()
            
            hub_name = "기타"
            for h, brs in HUB_BRANCH_MAP.items():
                if br_name in brs: hub_name = h; break
            if br_name in ["강북강원", "부산경남", "전남전북", "충남충북", "대구경북"]: hub_name = br_name
            
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

# === 4. Data Processing ===
def process_branch_bm_data(df_total, branch_name):
    mask = (df_total['지사'] == branch_name) & (df_total['데이터셋'] == 'KPI')
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
    """Calculate summary stats for each hub"""
    mask_kpi = (df_total['데이터셋'] == 'KPI') & (df_total['구분'] == '본부')
    df = df_total[mask_kpi]
    summary = []
    
    for hub in HUB_BRANCH_MAP.keys():
        d = df[df['본부'] == hub]
        if d.empty: continue
        
        try:
            cnt = d[d['지표'] == 'L+i형 건']['값'].sum()
            amt = d[d['지표'] == 'L+i형 월정료']['값'].sum()
            rate = d[d['지표'].str.contains('L\+i형.*정지율')]['값'].mean()
            # If rate < 1, assume it needs *100.
            if rate < 1: rate *= 100
                
            summary.append({
                "본부": hub,
                "총건수": cnt,
                "총금액": amt,
                "정지율": rate
            })
        except: continue
        
    return pd.DataFrame(summary)

# === 5. UI Layout ===

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2702/2702602.png", width=50)
    st.title("Admin Dashboard")
    excel_src = get_excel_file()
    
    st.markdown("---")
    mode = st.radio("MENU", ["🔍 지사별 상세 분석", "📊 전체 현황 스냅샷", "📈 전체 추이 비교"])

# === Main Logic ===

if not excel_src:
    st.warning("⚠️ Please upload the Excel file to proceed.")
    st.stop()

# Load Data
df_total = load_total_data(excel_src)
df_susp = load_rate_data(excel_src, "suspension")
df_fail = load_rate_data(excel_src, "failure")

if df_total is None: st.error("Data Load Failed"); st.stop()

# --- TOP SECTION: Hub Status (Collapsible) ---
with st.expander("🏢 본부별 운영 현황 요약 (펼치기/접기)", expanded=True):
    hub_summ = get_hub_summary(df_total)
    if not hub_summ.empty:
        # Create columns dynamically
        cols = st.columns(len(hub_summ))
        for idx, row in hub_summ.iterrows():
            with cols[idx % len(cols)]:
                st.markdown(f"**{row['본부']}**")
                st.caption(f"건수: {int(row['총건수']):,} / 금액: {int(row['총금액']/1000):,}천")
                st.metric("정지율", f"{row['정지율']:.2f}%")
    else:
        st.info("본부 데이터가 없습니다.")

# ----------------- 1. Branch Detail Analysis -----------------
if "지사별 상세 분석" in mode:
    st.title("🔍 지사별 운영 현황 상세 분석")
    
    with st.sidebar:
        st.markdown("---")
        st.subheader("필터링 설정")
        hub_options = ["전체"] + list(HUB_BRANCH_MAP.keys())
        # Default Hub: Gangbuk/Gangwon
        default_hub_idx = hub_options.index("강북/강원") if "강북/강원" in hub_options else 0
        sel_hub_detail = st.selectbox("본부 선택", hub_options, index=default_hub_idx)
        
        raw_branches = ALL_BRANCHES if sel_hub_detail == "전체" else HUB_BRANCH_MAP.get(sel_hub_detail, [])
        sorted_branches = sorted(raw_branches, key=sort_key)
        target_branch = st.selectbox("지사 선택", sorted_branches)

    df_bm = process_branch_bm_data(df_total, target_branch)
    trend_s = df_susp[df_susp['지사'] == target_branch].sort_values('날짜') if df_susp is not None else pd.DataFrame()
    trend_f = df_fail[df_fail['지사'] == target_branch].sort_values('날짜') if df_fail is not None else pd.DataFrame()

    if df_bm is None:
        st.warning("선택한 지사의 상세 데이터가 없습니다.")
    else:
        insight_text = generate_text_insight(df_bm, trend_s)
        st.markdown(f"""
        <div class="insight-box">
            <div class="insight-title">💡 {target_branch} 운영 인사이트</div>
            <div class="insight-text">{insight_text.replace('\n', '<br>')}</div>
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("##### 📊 BM별 물량(금액) 비교")
            fig_bar = px.bar(
                df_bm, x='BM', y='금액', color='BM',
                text_auto=',.0f', color_discrete_sequence=COLORS,
            )
            fig_bar.update_layout(
                plot_bgcolor="white", height=350, showlegend=False,
                yaxis_title="월정료 (천원)", xaxis_title=None,
                font=dict(family="Pretendard"),
                margin=dict(t=30, b=0, l=0, r=0)
            )
            # Prevent overlap on bar chart by adjusting text position if needed
            fig_bar.update_traces(textposition='auto')
            st.plotly_chart(fig_bar, use_container_width=True)
            
        with col2:
            st.markdown("##### ⚠️ BM별 리스크(정지율) 분포")
            fig_scat = px.scatter(
                df_bm, x='정지율', y='금액',
                size='건수', color='BM', size_max=40,
                color_discrete_sequence=COLORS,
                hover_data=['건수']
            )
            fig_scat.update_layout(
                plot_bgcolor="white", height=350,
                xaxis_title="정지율 (%)", yaxis_title="월정료 규모",
                xaxis=dict(showgrid=True, gridcolor='#f1f3f5'),
                yaxis=dict(showgrid=True, gridcolor='#f1f3f5'),
                font=dict(family="Pretendard"),
                margin=dict(t=30, b=0, l=0, r=0)
            )
            st.plotly_chart(fig_scat, use_container_width=True)

        st.markdown("##### 📈 월별 리스크 추이")
        fig_trend = make_subplots(specs=[[{"secondary_y": True}]])
        
        if not trend_s.empty:
            # Only label the last point to prevent overlap
            last_pt = trend_s.iloc[-1]
            fig_trend.add_trace(
                go.Scatter(x=trend_s['날짜'], y=trend_s['비율'], name="정지율", 
                           mode='lines+markers', 
                           line=dict(color=COLORS[0], width=3),
                           hovertemplate="날짜: %{x|%y.%m}<br>정지율: %{y:.2f}%"),
                secondary_y=False
            )
            # Add annotation for the last point
            fig_trend.add_annotation(
                x=last_pt['날짜'], y=last_pt['비율'],
                text=f"{last_pt['비율']:.2f}%",
                showarrow=False,
                yshift=10,
                font=dict(color=COLORS[0], weight="bold")
            )

        if not trend_f.empty:
            last_pt_f = trend_f.iloc[-1]
            fig_trend.add_trace(
                go.Scatter(x=trend_f['날짜'], y=trend_f['비율'], name="부실율", 
                           mode='lines+markers', 
                           line=dict(color=COLORS[1], width=3, dash='dot'),
                           hovertemplate="날짜: %{x|%y.%m}<br>부실율: %{y:.2f}%"),
                secondary_y=True
            )
            fig_trend.add_annotation(
                x=last_pt_f['날짜'], y=last_pt_f['비율'],
                text=f"{last_pt_f['비율']:.2f}%",
                showarrow=False,
                yshift=-15,
                yref="y2",
                font=dict(color=COLORS[1], weight="bold")
            )
            
        fig_trend.update_layout(
            hovermode="x unified", plot_bgcolor="white", height=400,
            legend=dict(orientation="h", y=1.1),
            xaxis=dict(tickformat="%y년 %-m월", showgrid=True, gridcolor='#f1f3f5'),
            font=dict(family="Pretendard"),
            margin=dict(t=50, b=0, l=0, r=0)
        )
        fig_trend.update_yaxes(title_text="정지율 (%)", secondary_y=False, showgrid=True, gridcolor='#f1f3f5')
        fig_trend.update_yaxes(title_text="부실율 (%)", secondary_y=True, showgrid=False)
        st.plotly_chart(fig_trend, use_container_width=True)

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
        
        # Default Selection: Gang-neung, Won-ju, Nam-yang-ju + others
        defaults = ["남양주", "강릉", "원주", "의정부", "고양"]
        default_sel = [b for b in sorted_branches if b in defaults]
        # If none found (e.g. different hub selected), fallback to first 5
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
        
        m_type = st.radio("지표", ["건수", "금액", "비율"], key=f"snap_{key}", horizontal=True)
        if m_type == "건수": cols = ["L형 건", "i형 건", "L+i형 건"]; fmt = ",.0f"
        elif m_type == "금액": cols = ["L형 월정료", "i형 월정료", "L+i형 월정료"]; fmt = ",.0f"
        else: cols = [c for c in df_total['지표'].unique() if '정지율' in c and 'L+i' in c]; fmt = ".2f"
        
        df_c = df_v[df_v['지표'].isin(cols)].copy()
        df_c['sort_idx'] = df_c['지사'].apply(sort_key)
        df_c = df_c.sort_values(['sort_idx', '값'], ascending=[True, False])
        
        fig = px.bar(df_c, x='지사', y='값', color='지표', barmode='group', text_auto=fmt, color_discrete_sequence=COLORS)
        fig.update_layout(plot_bgcolor="white", height=500, xaxis_title=None, font=dict(family="Pretendard"))
        # Ensure percent format for rate
        if m_type == "비율":
             fig.update_traces(texttemplate='%{y:.2f}%')
        st.plotly_chart(fig, use_container_width=True)

    with t1: render_tab("Total")
    with t2: render_tab("SP")
    with t3: render_tab("KPI")

# ----------------- 3. Overall Trend Comparison -----------------
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
        
        # Default Selection: Gang-neung, Won-ju, Nam-yang-ju + others
        defaults = ["남양주", "강릉", "원주", "의정부", "고양"]
        default_sel = [b for b in sorted_branches if b in defaults]
        if not default_sel: default_sel = sorted_branches[:5]

        sel_brs = st.multiselect("비교할 지사 선택", sorted_branches, default=default_sel)
    
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
                line=dict(width=3, color=color), marker=dict(size=8, color=color),
                hovertemplate=f"<b>{branch}</b><br>%{{x|%y.%m}}<br>{type_r}: %{{y:.2f}}%<extra></extra>"
            ))
            
            # Label only the last point to avoid overlap
            last_val = d.iloc[-1]
            fig.add_annotation(
                x=last_val['날짜'], y=last_val['비율'],
                text=f"{last_val['비율']:.2f}%",
                showarrow=False,
                yshift=10,
                font=dict(color=color, size=11, weight="bold")
            )
            
        fig.update_layout(
            hovermode="x unified", plot_bgcolor="white", height=550,
            xaxis=dict(tickformat="%y년 %-m월", showgrid=True, gridcolor='#f1f3f5'),
            yaxis=dict(ticksuffix="%", tickformat=".2f", showgrid=True, gridcolor='#f1f3f5'),
            font=dict(family="Pretendard"),
            margin=dict(r=20) # Add margin for last point labels
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("비교할 지사를 선택해주세요.")
