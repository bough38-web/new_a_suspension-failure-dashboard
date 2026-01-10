import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import re

# === 1. 페이지 및 스타일 설정 ===
st.set_page_config(
    page_title="KTT 지사별 운영 현황 분석",
    page_icon="📈",
    layout="wide"
)

# 고급 CSS (Pretendard 폰트, 카드 디자인)
st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    
    html, body, [class*="css"] {
        font-family: 'Pretendard', sans-serif !important;
    }
    
    /* 분석 카드 스타일 */
    .analysis-card {
        background-color: #fff;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        border: 1px solid #f1f3f5;
        margin-bottom: 20px;
    }
    .insight-box {
        background-color: #f8f9fa;
        border-left: 5px solid #228be6;
        padding: 15px;
        border-radius: 4px;
        margin-bottom: 20px;
    }
    .insight-title {
        font-weight: 700;
        color: #212529;
        margin-bottom: 8px;
        font-size: 1.1em;
    }
    .insight-text {
        color: #495057;
        font-size: 0.95em;
        line-height: 1.6;
    }
    
    /* 탭 및 사이드바 */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { border-radius: 8px; background-color: #fff; border: 1px solid #e9ecef; }
    .stTabs [aria-selected="true"] { background-color: #e7f5ff !important; border-color: #1c7ed6 !important; color: #1c7ed6 !important; }
    [data-testid="stSidebar"] { background-color: #f8f9fa; border-right: 1px solid #e9ecef; }
</style>
""", unsafe_allow_html=True)

# === 2. 설정 및 상수 ===
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

# 정렬 순서
PREFERRED_ORDER = ["강북강원", "본부", "중앙", "강북", "서대문", "고양", "의정부", "남양주", "강릉", "원주"]
def sort_key(name):
    try: return PREFERRED_ORDER.index(name)
    except: return 999

# 색상 팔레트
COLORS = ['#228be6', '#fa5252', '#40c057', '#fcc419', '#7950f2', '#e64980']

# === 3. 데이터 로드 및 처리 함수 ===

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
    uploaded = st.sidebar.file_uploader("📂 엑셀 파일 업로드 (.xlsx)", type=['xlsx'])
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
            is_br = False; hub_name = None
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

# === 4. 데이터 가공 (BM 조건별 분리) ===
def process_branch_bm_data(df_total, branch_name):
    """지사의 Total 데이터에서 L형, i형 데이터를 분리하여 정리"""
    # KPI 데이터셋 기준 (가장 중요)
    mask = (df_total['지사'] == branch_name) & (df_total['데이터셋'] == 'KPI')
    df = df_total[mask]
    
    if df.empty: return None

    # 데이터 추출 함수
    def get_val(metric):
        v = df[df['지표'] == metric]['값'].values
        return v[0] if len(v) > 0 else 0.0

    bm_data = [
        {
            "BM": "L형",
            "건수": get_val("L형 건"),
            "금액": get_val("L형 월정료"),
            "정지율": get_val("L형 정지율") * 100 if get_val("L형 정지율") < 1 else get_val("L형 정지율"), # %보정
            "부실율": 0.0 # 스냅샷에 부실율 BM별 구분이 없다면 0 또는 별도 로직
        },
        {
            "BM": "i형",
            "건수": get_val("i형 건"),
            "금액": get_val("i형 월정료"),
            "정지율": get_val("i형 정지율") * 100 if get_val("i형 정지율") < 1 else get_val("i형 정지율"),
            "부실율": 0.0
        }
    ]
    return pd.DataFrame(bm_data)

def generate_text_insight(df_bm, df_trend_susp, df_trend_fail):
    """데이터 기반 텍스트 자동 해석 생성"""
    insights = []
    
    # 1. BM 비교
    top_vol = df_bm.sort_values('금액', ascending=False).iloc[0]
    insights.append(f"💰 **운영 규모**: **{top_vol['BM']}**이 전체 월정료의 대다수를 차지하며 주력 상품군입니다.")
    
    high_risk_bm = df_bm.sort_values('정지율', ascending=False).iloc[0]
    if high_risk_bm['정지율'] > 2.0: # 임계치 예시
        insights.append(f"⚠️ **리스크 관리**: **{high_risk_bm['BM']}**의 정지율이 **{high_risk_bm['정지율']:.2f}%**로 높게 나타나 집중 관리가 필요합니다.")
    else:
        insights.append(f"✅ **리스크 관리**: BM별 정지율은 전반적으로 안정적인 수준입니다.")

    # 2. 추이 분석
    if not df_trend_susp.empty:
        latest = df_trend_susp.iloc[-1]['비율']
        prev = df_trend_susp.iloc[-2]['비율'] if len(df_trend_susp) > 1 else latest
        diff = latest - prev
        
        trend_str = "상승" if diff > 0 else "하락" if diff < 0 else "유지"
        icon = "🔴" if diff > 0.1 else "🔵" if diff < -0.1 else "⚪"
        
        insights.append(f"{icon} **추이 분석**: 전월 대비 정지율이 **{abs(diff):.2f}%p {trend_str}**했습니다. (현재 {latest:.2f}%)")
    
    return "\n\n".join(insights)

# === 5. UI 구성 ===

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2702/2702602.png", width=50)
    st.title("Admin Dashboard")
    excel_src = get_excel_file()
    
    st.markdown("---")
    # 메뉴 구조 변경
    mode = st.radio("분석 모드", ["🔍 지사별 상세 분석", "📊 전체 현황 스냅샷", "📈 전체 추이 비교"])

# === 메인 로직 ===

if not excel_src:
    st.warning("⚠️ 데이터를 분석할 엑셀 파일을 업로드해주세요.")
    st.stop()

# 데이터 로드
df_total = load_total_data(excel_src)
df_susp = load_rate_data(excel_src, "suspension")
df_fail = load_rate_data(excel_src, "failure")

if df_total is None: st.error("데이터 로드 실패"); st.stop()

# ----------------- 1. 지사별 상세 분석 (New) -----------------
if "지사별 상세 분석" in mode:
    st.title("🔍 지사별 운영 현황 상세 분석")
    
    # 지사 선택
    col_sel, _ = st.columns([1, 2])
    with col_sel:
        all_branches_sorted = sorted(ALL_BRANCHES, key=sort_key)
        target_branch = st.selectbox("분석할 지사를 선택하세요", all_branches_sorted)
    
    # 데이터 준비
    df_bm = process_branch_bm_data(df_total, target_branch)
    
    # 지사 추이 데이터 필터링
    trend_s = df_susp[df_susp['지사'] == target_branch].sort_values('날짜') if df_susp is not None else pd.DataFrame()
    trend_f = df_fail[df_fail['지사'] == target_branch].sort_values('날짜') if df_fail is not None else pd.DataFrame()

    if df_bm is None:
        st.warning("선택한 지사의 상세 데이터가 없습니다.")
    else:
        # --- A. 텍스트 인사이트 (자동 생성) ---
        insight_text = generate_text_insight(df_bm, trend_s, trend_f)
        st.markdown(f"""
        <div class="insight-box">
            <div class="insight-title">💡 {target_branch} 운영 인사이트</div>
            <div class="insight-text">{insight_text.replace('\n', '<br>')}</div>
        </div>
        """, unsafe_allow_html=True)

        # --- B. BM 조건별 비교 (Bar Chart) ---
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("##### 📊 BM별 물량(금액) 비교")
            fig_bar = px.bar(
                df_bm, x='BM', y='금액', color='BM',
                text_auto=',.0f',
                color_discrete_sequence=COLORS,
                title=f"{target_branch} BM별 월정료 현황"
            )
            fig_bar.update_layout(
                plot_bgcolor="white", height=350, showlegend=False,
                yaxis_title="월정료 (천원)", xaxis_title=None
            )
            st.plotly_chart(fig_bar, use_container_width=True)
            
        with col2:
            st.markdown("##### ⚠️ BM별 리스크(정지율) 분포")
            # Scatter Plot for Risk
            fig_scat = px.scatter(
                df_bm, x='정지율', y='금액',
                size='건수', color='BM',
                size_max=40,
                color_discrete_sequence=COLORS,
                hover_data=['건수']
            )
            fig_scat.update_layout(
                plot_bgcolor="white", height=350,
                xaxis_title="정지율 (%)", yaxis_title="월정료 규모",
                xaxis=dict(showgrid=True, gridcolor='#eee'),
                yaxis=dict(showgrid=True, gridcolor='#eee')
            )
            st.plotly_chart(fig_scat, use_container_width=True)

        # --- C. 월별 추이 분석 (Dual Axis Line Chart) ---
        st.markdown("##### 📈 월별 리스크 추이 (정지율 vs 부실율)")
        
        fig_trend = make_subplots(specs=[[{"secondary_y": True}]])
        
        if not trend_s.empty:
            fig_trend.add_trace(
                go.Scatter(x=trend_s['날짜'], y=trend_s['비율'], name="정지율", 
                           mode='lines+markers', line=dict(color=COLORS[0], width=3)),
                secondary_y=False
            )
        if not trend_f.empty:
            fig_trend.add_trace(
                go.Scatter(x=trend_f['날짜'], y=trend_f['비율'], name="부실율", 
                           mode='lines+markers', line=dict(color=COLORS[1], width=3, dash='dot')),
                secondary_y=True
            )
            
        fig_trend.update_layout(
            hovermode="x unified",
            plot_bgcolor="white", height=400,
            legend=dict(orientation="h", y=1.1),
            xaxis=dict(tickformat="%y년 %-m월", showgrid=True, gridcolor='#f1f3f5')
        )
        fig_trend.update_yaxes(title_text="정지율 (%)", secondary_y=False, showgrid=True, gridcolor='#f1f3f5')
        fig_trend.update_yaxes(title_text="부실율 (%)", secondary_y=True, showgrid=False)
        
        st.plotly_chart(fig_trend, use_container_width=True)

# ----------------- 2. 전체 현황 스냅샷 (기존 기능) -----------------
elif "전체 현황 스냅샷" in mode:
    st.title("📊 전체 지사 운영 현황 스냅샷")
    
    # 필터
    sel_hub = st.selectbox("본부 필터", ["전체"] + list(HUB_BRANCH_MAP.keys()))
    raw_branches = ALL_BRANCHES if sel_hub == "전체" else HUB_BRANCH_MAP.get(sel_hub, [])
    sel_brs = st.multiselect("지사 필터", sorted(raw_branches, key=sort_key), default=sorted(raw_branches, key=sort_key)[:5])
    
    # 탭 구성
    t1, t2, t3 = st.tabs(["📌 Total", "⚡ SP 기준", "📉 KPI"])
    
    def render_tab(key):
        mask = df_total['데이터셋'] == key
        if sel_hub != "전체" or sel_brs:
            df_v = df_total[mask & (df_total['구분'] == '지사') & (df_total['지사'].isin(sel_brs))]
        else:
            df_v = df_total[mask & (df_total['구분'] == '본부')]
            df_v['지사'] = df_v['본부']
        
        if df_v.empty: st.info("데이터 없음"); return
        
        # Chart
        m_type = st.radio("지표", ["건수", "금액", "비율"], key=f"snap_{key}", horizontal=True)
        if m_type == "건수": cols = ["L형 건", "i형 건", "L+i형 건"]; fmt = ",.0f"
        elif m_type == "금액": cols = ["L형 월정료", "i형 월정료", "L+i형 월정료"]; fmt = ",.0f"
        else: cols = [c for c in df_total['지표'].unique() if '정지율' in c and 'L+i' in c]; fmt = ".2f"
        
        df_c = df_v[df_v['지표'].isin(cols)].copy()
        df_c['sort_idx'] = df_c['지사'].apply(sort_key)
        df_c = df_c.sort_values(['sort_idx', '값'], ascending=[True, False])
        
        fig = px.bar(df_c, x='지사', y='값', color='지표', barmode='group', text_auto=fmt, color_discrete_sequence=COLORS)
        fig.update_layout(plot_bgcolor="white", height=500, xaxis_title=None)
        st.plotly_chart(fig, use_container_width=True)

    with t1: render_tab("Total")
    with t2: render_tab("SP")
    with t3: render_tab("KPI")

# ----------------- 3. 전체 추이 비교 (기존 기능) -----------------
else:
    st.title("📈 전체 지사 추이 비교 분석")
    type_r = st.radio("분석 항목", ["정지율", "부실율"], horizontal=True)
    
    target_df = df_susp if type_r == "정지율" else df_fail
    
    if target_df is None: st.error("데이터 없음"); st.stop()
    
    sel_hub = st.selectbox("본부 선택", ["전체"] + list(HUB_BRANCH_MAP.keys()), key='trend_hub')
    raw_branches = ALL_BRANCHES if sel_hub == "전체" else HUB_BRANCH_MAP.get(sel_hub, [])
    sel_brs = st.multiselect("비교할 지사 선택", sorted(raw_branches, key=sort_key), default=sorted(raw_branches, key=sort_key)[:5])
    
    if sel_brs:
        df_v = target_df[target_df['지사'].isin(sel_brs)].copy()
        df_v['sort_idx'] = df_v['지사'].apply(sort_key)
        df_v = df_v.sort_values(['sort_idx', '날짜'])
        
        fig = go.Figure()
        for branch in df_v['지사'].unique():
            d = df_v[df_v['지사'] == branch]
            fig.add_trace(go.Scatter(
                x=d['날짜'], y=d['비율'], mode='lines+markers', name=branch,
                line=dict(width=3), marker=dict(size=8)
            ))
            
        fig.update_layout(
            hovermode="x unified", plot_bgcolor="white", height=550,
            xaxis=dict(tickformat="%y년 %-m월", showgrid=True, gridcolor='#f1f3f5'),
            yaxis=dict(ticksuffix="%", tickformat=".2f", showgrid=True, gridcolor='#f1f3f5')
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("지사를 선택해주세요.")
