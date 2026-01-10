import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import re

# === 1. 페이지 및 스타일 설정 (UI/UX 고급화) ===
st.set_page_config(
    page_title="KTT 정지/부실 관리 대시보드",
    page_icon="📊",
    layout="wide"
)

# 고급 CSS 주입 (Pretendard 폰트, 카드 디자인, 호버 효과)
st.markdown("""
<style>
    /* 폰트 적용 */
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    
    html, body, [class*="css"] {
        font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, Roboto, 'Helvetica Neue', 'Segoe UI', 'Apple SD Gothic Neo', 'Noto Sans KR', 'Malgun Gothic', sans-serif !important;
    }
    
    /* 메트릭 카드 디자인 */
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        border: 1px solid #e9ecef;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.02);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px rgba(0, 0, 0, 0.05);
        border-color: #228be6;
    }
    
    /* 탭 스타일 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #f8f9fa;
        border-radius: 10px;
        border: 1px solid #e9ecef;
        color: #495057;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        background-color: #e7f5ff !important;
        color: #1c7ed6 !important;
        border-color: #1c7ed6 !important;
    }
    
    /* 사이드바 */
    [data-testid="stSidebar"] {
        background-color: #f8f9fa;
        border-right: 1px solid #e9ecef;
    }
</style>
""", unsafe_allow_html=True)

# === 2. 설정 및 상수 ===
DEFAULT_EXCEL_FILE = "data.xlsx"

# 본부-지사 매핑
HUB_BRANCH_MAP = {
    "강남/서부": ["강남", "수원", "분당", "강동", "용인", "평택", "인천", "강서", "부천", "안산", "안양", "관악"],
    "강북/강원": ["중앙", "강북", "서대문", "고양", "의정부", "남양주", "강릉", "원주"],
    "부산/경남": ["동부산", "남부산", "창원", "서부산", "김해", "울산", "진주"],
    "전남/전북": ["광주", "전주", "익산", "북광주", "순천", "제주", "목포"],
    "충남/충북": ["서대전", "충북", "천안", "대전", "충남서부"],
    "대구/경북": ["동대구", "서대구", "구미", "포항"]
}
ALL_BRANCHES = [b for branches in HUB_BRANCH_MAP.values() for b in branches]

# ★ 커스텀 정렬 순서 (요청하신 순서 반영)
PREFERRED_ORDER = [
    "강북강원", "본부", # 본부 우선
    "중앙", "강북", "서대문", "고양", "의정부", "남양주", "강릉", "원주", # 강북/강원
    "강남", "수원", "분당", # 예시...
]

# 컬러 팔레트 (Prism 스타일)
COLOR_PALETTE = [
    '#228be6', '#fa5252', '#40c057', '#fcc419', '#7950f2', '#e64980', 
    '#15aabf', '#82c91e', '#fd7e14', '#20c997', '#868e96', '#be4bdb'
]

# === 3. 데이터 로드 로직 ===

def sort_key(name):
    """커스텀 정렬 키 생성 함수"""
    try:
        return PREFERRED_ORDER.index(name)
    except:
        return 999 # 목록에 없으면 뒤로 보냄

def parse_date_robust(date_str):
    """날짜 파싱: (e) 등 특수문자 제거 후 YYYY-MM-01 변환"""
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
        
        # 헤더 자동 탐지
        header_row = 3
        for i in range(min(15, len(df))):
            if str(df.iloc[i, 0]).strip() == "구분":
                header_row = i; break
        
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
            if br_name in ["강북강원", "부산경남", "전남전북", "충남충북", "대구경북", "강남서부"]: hub_name = br_name
            
            for _, row in sub.iterrows():
                date_val = parse_date_robust(row['d'])
                if not date_val: continue
                try: val = float(str(row['v']).replace(',', ''))
                except: val = 0.0
                
                processed.append({
                    "날짜": date_val, "본부": hub_name, "지사": br_name, "비율": val * 100
                })
                
        res = pd.DataFrame(processed)
        if not res.empty:
            res['날짜'] = pd.to_datetime(res['날짜'])
            res['월'] = res['날짜'].dt.strftime('%y년 %-m월')
        return res
    except: return None

# === 4. UI 구성 ===

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2702/2702602.png", width=50)
    st.title("Dashboard")
    excel_src = get_excel_file()
    
    if excel_src: st.success("데이터 로드 완료")
    else: st.info("엑셀 파일이 필요합니다.")
    
    st.markdown("---")
    mode = st.radio("분석 모드", ["📊 현황 스냅샷", "📈 추이 분석 (정지/부실)"])
    
    st.markdown("---")
    sel_hub = st.selectbox("본부 선택", ["전체"] + list(HUB_BRANCH_MAP.keys()))
    
    # 지사 선택 (커스텀 정렬 적용)
    raw_branches = ALL_BRANCHES if sel_hub == "전체" else HUB_BRANCH_MAP.get(sel_hub, [])
    sorted_branches = sorted(raw_branches, key=sort_key)
    
    default_sel = sorted_branches[:5] if sel_hub == "전체" else sorted_branches
    sel_brs = st.multiselect("지사 선택", sorted_branches, default=default_sel)

# === 메인 로직 ===

if not excel_src:
    st.warning("⚠️ 데이터를 불러올 수 없습니다. 엑셀 파일을 업로드해주세요.")
    st.stop()

if "스냅샷" in mode:
    st.title("📊 정지 및 SP 현황 스냅샷")
    df = load_total_data(excel_src)
    
    if df is None or df.empty:
        st.error("스냅샷 데이터를 찾을 수 없습니다.")
    else:
        t1, t2, t3 = st.tabs(["📌 Total (총정지)", "⚡ SP 기준", "📉 KPI (부실율)"])
        def render_snap(key):
            mask = df['데이터셋'] == key
            if sel_hub != "전체" or sel_brs:
                df_v = df[mask & (df['구분'] == '지사') & (df['지사'].isin(sel_brs))]
            else:
                df_v = df[mask & (df['구분'] == '본부')]
                df_v['지사'] = df_v['본부']
            
            if df_v.empty: st.info("데이터 없음"); return
            
            # KPI Cards
            c1, c2, c3 = st.columns(3)
            with c1: 
                v = df_v[df_v['지표']=='L+i형 건']['값'].sum()
                st.metric("총 건수", f"{int(v):,}")
            with c2:
                v = df_v[df_v['지표']=='L+i형 월정료']['값'].sum()
                st.metric("총 월정료", f"{int(v/1000):,}천원")
            with c3:
                v = df_v[df_v['지표'].str.contains('L\+i형.*정지율')]['값'].mean()
                # KPI는 이미 % 단위일 수 있으므로 상황에 맞게 조정 (여기서는 *100 처리)
                disp_val = v * 100 if key != 'KPI' else v
                st.metric("평균 정지율", f"{disp_val:.2f}%")
            
            # Chart
            m_type = st.radio("지표 유형", ["건수", "금액", "비율"], key=f"r_{key}", horizontal=True)
            if m_type == "건수": cols = ["L형 건", "i형 건", "L+i형 건"]; fmt = ",.0f"
            elif m_type == "금액": cols = ["L형 월정료", "i형 월정료", "L+i형 월정료"]; fmt = ",.0f"
            else: cols = [c for c in df['지표'].unique() if '정지율' in c and 'L+i' in c]; fmt = ".2f"
            
            df_c = df_v[df_v['지표'].isin(cols)].copy()
            # 정렬
            df_c['sort_idx'] = df_c['지사'].apply(sort_key)
            df_c = df_c.sort_values(['sort_idx', '값'], ascending=[True, False])
            
            fig = px.bar(
                df_c, x='지사', y='값', color='지표', 
                barmode='group', text_auto=fmt,
                color_discrete_sequence=COLOR_PALETTE
            )
            fig.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Pretendard"),
                xaxis_title=None,
                height=500
            )
            st.plotly_chart(fig, use_container_width=True)

        with t1: render_snap("Total")
        with t2: render_snap("SP")
        with t3: render_snap("KPI")

else: # 추이 분석
    st.title("📈 정지율/부실율 트렌드 분석")
    type_r = st.radio("분석 항목", ["정지율", "부실율"], horizontal=True)
    
    key = "suspension" if type_r == "정지율" else "failure"
    df_r = load_rate_data(excel_src, key)
    
    if df_r is None or df_r.empty:
        st.error(f"{type_r} 데이터를 찾을 수 없습니다.")
    else:
        if sel_brs: df_v = df_r[df_r['지사'].isin(sel_brs)].copy()
        elif sel_hub != "전체": df_v = df_r[df_r['본부'] == sel_hub].copy()
        else: df_v = df_r.copy()
            
        if df_v.empty:
            st.warning("데이터가 없습니다.")
        else:
            # 정렬
            df_v['sort_idx'] = df_v['지사'].apply(sort_key)
            df_v = df_v.sort_values(['sort_idx', '날짜'])
            
            # === 고급 라인 차트 ===
            fig = go.Figure()
            
            unique_branches = df_v['지사'].unique() # 이미 정렬된 순서
            for i, branch_name in enumerate(unique_branches):
                d = df_v[df_v['지사'] == branch_name]
                color = COLOR_PALETTE[i % len(COLOR_PALETTE)]
                
                fig.add_trace(go.Scatter(
                    x=d['날짜'], y=d['비율'],
                    mode='lines+markers',
                    name=branch_name,
                    hovertemplate=f"<b>{branch_name}</b><br>날짜: %{{text}}<br>{type_r}: %{{y:.2f}}%<extra></extra>",
                    text=d['월'],
                    line=dict(width=3, color=color),
                    marker=dict(size=8, color=color, line=dict(width=2, color='white'))
                ))
            
            fig.update_layout(
                hovermode="x unified",
                font=dict(family="Pretendard"),
                xaxis=dict(
                    tickformat="%y년 %-m월", 
                    showgrid=True, gridcolor='#f1f3f5'
                ),
                yaxis=dict(
                    ticksuffix="%", 
                    tickformat=".2f", # 소수점 2자리
                    showgrid=True, gridcolor='#f1f3f5'
                ),
                legend=dict(
                    orientation="h", y=1.1, x=0,
                    bgcolor="rgba(255,255,255,0.8)", bordercolor="#e9ecef", borderwidth=1
                ),
                plot_bgcolor="white",
                height=550,
                transition=dict(duration=500, easing="cubic-in-out")
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # === 상세 테이블 ===
            st.markdown(f"### 📋 {type_r} 상세 현황")
            try:
                latest_date = df_v['날짜'].max()
                prev_date = df_v[df_v['날짜'] < latest_date]['날짜'].max()
                
                piv = df_v.pivot(index='지사', columns='날짜', values='비율')
                if prev_date and latest_date:
                    piv['전월대비'] = piv[latest_date] - piv[prev_date]
                else:
                    piv['전월대비'] = 0.0
                
                piv['sort_key'] = piv.index.map(sort_key)
                piv = piv.sort_values('sort_key').drop(columns=['sort_key'])
                
                display_df = piv[[latest_date, '전월대비']].copy()
                display_df.columns = [f"{latest_date.strftime('%y년 %-m월')} (%)", "전월비 (%p)"]
                
                # 테이블 스타일링 (matplotlib 의존성 제거됨)
                st.dataframe(
                    display_df.style
                    .format("{:.2f}")
                    .background_gradient(cmap="Reds", subset=[display_df.columns[0]])
                    .text_gradient(cmap="RdBu_r", subset=[display_df.columns[1]], vmin=-0.5, vmax=0.5),
                    use_container_width=True
                )
            except Exception as e:
                # matplotlib가 없어서 에러날 경우 기본 테이블로 표시
                st.dataframe(display_df.style.format("{:.2f}"), use_container_width=True)
