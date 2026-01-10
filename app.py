import streamlit as st
import pandas as pd
import plotly.express as px
import os

# === 1. 페이지 및 스타일 설정 ===
st.set_page_config(
    page_title="정지/부실 관리 통합 대시보드",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 스타일 커스터마이징
st.markdown("""
<style>
    .metric-card {
        background-color: white; border-radius: 12px; padding: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05); border: 1px solid #e9ecef; margin-bottom: 20px;
    }
    [data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid #e9ecef; }
    .stTabs [data-baseweb="tab"] { background-color: #ffffff; border-radius: 8px; border: 1px solid #e9ecef; }
    .stTabs [aria-selected="true"] { background-color: #e7f5ff; color: #1c7ed6; border-color: #1c7ed6; }
</style>
""", unsafe_allow_html=True)

# === 2. 설정 및 파일 로드 로직 ===

# 깃허브(로컬)에 저장된 기본 파일명
DEFAULT_FILES = {
    "total": "data_total.csv",
    "suspension": "data_suspension.csv",
    "failure": "data_failure.csv"
}

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

# === 3. 데이터 로딩 함수 (하이브리드 방식) ===

def get_data_source(key_name, label):
    """
    1순위: 사용자가 수동 업로드한 파일
    2순위: 깃허브(로컬)에 있는 기본 파일
    """
    # 사이드바의 파일 업로더
    uploaded = st.sidebar.file_uploader(label, type=['csv'], key=key_name)
    
    if uploaded is not None:
        return uploaded # 수동 파일 사용
    
    # 수동 파일 없으면 기본 파일 확인
    default_path = DEFAULT_FILES[key_name]
    if os.path.exists(default_path):
        return default_path # 깃허브 파일 사용
    
    return None # 파일 없음

@st.cache_data
def load_total_data(source):
    if source is None: return None
    # 파일 객체인지 경로인지 확인하여 읽기
    df = pd.read_csv(source, header=None)
    
    header_row = 3
    ranges = {"Total": (1, 13), "SP": (15, 27), "KPI": (29, 41)}
    col_names = [
        "L형 건", "i형 건", "L+i형 건", "L형 건 정지율", "i형 건 정지율", "L+i형 건 정지율",
        "L형 월정료", "i형 월정료", "L+i형 월정료", "L형 월정료 정지율", "i형 월정료 정지율", "L+i형 월정료 정지율"
    ]
    
    parsed_data = []
    for i in range(header_row + 1, len(df)):
        row = df.iloc[i]
        org_name = str(row[0]).strip()
        
        is_hub = org_name in HUB_BRANCH_MAP.keys()
        is_branch = False; hub_name = None
        
        if is_hub: hub_name = org_name
        else:
            for hub, branches in HUB_BRANCH_MAP.items():
                if org_name in branches: is_branch = True; hub_name = hub; break
        
        if not (is_hub or is_branch): continue
        
        for section, (start, end) in ranges.items():
            vals = row[start:end].values
            for idx, val in enumerate(vals):
                try: num_val = float(str(val).replace(',', '').replace('-', '0'))
                except: num_val = 0.0
                parsed_data.append({
                    "본부": hub_name, "지사": org_name, "구분": "본부" if is_hub else "지사",
                    "데이터셋": section, "지표": col_names[idx], "값": num_val
                })
    return pd.DataFrame(parsed_data)

@st.cache_data
def load_rate_data(source):
    if source is None: return None
    df = pd.read_csv(source, header=None)
    processed_list = []
    num_cols = df.shape[1]
    
    for i in range(0, num_cols, 2):
        if i+1 >= num_cols: break
        branch_name = str(df.iloc[0, i]).strip()
        if pd.isna(branch_name) or branch_name == 'nan': continue
        
        sub_df = df.iloc[1:, [i, i+1]].copy()
        sub_df.columns = ["date_raw", "rate"]
        sub_df = sub_df.dropna()
        
        hub_name = "기타"
        for hub, branches in HUB_BRANCH_MAP.items():
            if branch_name in branches: hub_name = hub; break
        if branch_name in ["강북강원", "부산경남", "전남전북", "충남충북", "대구경북"]: hub_name = branch_name 
             
        for _, row in sub_df.iterrows():
            date_str = str(row['date_raw'])
            try:
                if '/' in date_str: yy, mm = date_str.split('/'); full_date = f"20{yy}-{mm}-01"
                else: full_date = date_str
            except: continue
            try: rate_val = float(str(row['rate']).replace(',', ''))
            except: rate_val = 0.0
            
            processed_list.append({"날짜": full_date, "본부": hub_name, "지사": branch_name, "비율": rate_val * 100})
            
    df_result = pd.DataFrame(processed_list)
    df_result['날짜'] = pd.to_datetime(df_result['날짜'])
    return df_result

# === 4. 사이드바 UI ===
with st.sidebar:
    st.title("🎛️ 대시보드 제어")
    
    # 1. 모드 선택
    selected_mode = st.radio("분석 모드", ["📊 현황 스냅샷 (Total/SP)", "📈 시계열 트렌드 (Rate)"])
    st.markdown("---")
    
    # 2. 파일 수동 업로드 (Expander로 숨김 처리하여 깔끔하게)
    with st.expander("📂 데이터 파일 수동 업데이트", expanded=False):
        st.info("파일을 업로드하면 깃허브 데이터 대신 사용됩니다.")
        source_total = get_data_source("total", "총정지 데이터 (시각화.csv)")
        source_susp = get_data_source("suspension", "정지율 데이터")
        source_fail = get_data_source("failure", "부실율 데이터")
    
    st.markdown("---")
    
    # 3. 공통 필터
    selected_hub = st.selectbox("본부 필터", ["전체"] + list(HUB_BRANCH_MAP.keys()))
    if selected_hub == "전체": available_branches = ALL_BRANCHES
    else: available_branches = HUB_BRANCH_MAP.get(selected_hub, [])
    
    selected_branches = st.multiselect("지사 필터", available_branches, default=available_branches[:5] if selected_hub == "전체" else available_branches)

# === 5. 메인 콘텐츠 ===

if "스냅샷" in selected_mode:
    st.title("📊 정지 및 SP 현황 스냅샷")
    
    # 데이터 로드 (Total)
    df_total = load_total_data(source_total)
    
    if df_total is None:
        st.error(f"데이터 파일이 없습니다. 깃허브에 '{DEFAULT_FILES['total']}' 파일이 있는지 확인하거나, 사이드바에서 수동으로 업로드하세요.")
    else:
        tab1, tab2, tab3 = st.tabs(["📌 Total (총정지)", "⚡ SP 기준", "📉 KPI (부실율)"])
        
        def render_tab(dataset_key):
            mask = (df_total['데이터셋'] == dataset_key)
            if selected_hub != "전체" or selected_branches:
                mask_branch = mask & (df_total['구분'] == '지사') & (df_total['지사'].isin(selected_branches))
                df_viz = df_total[mask_branch]
            else:
                mask_hub = mask & (df_total['구분'] == '본부')
                df_viz = df_total[mask_hub]
                df_viz['지사'] = df_viz['본부']

            if df_viz.empty: st.warning("데이터 없음"); return

            # KPI Cards
            c1, c2, c3 = st.columns(3)
            try:
                tot = df_viz[df_viz['지표'] == 'L+i형 건']['값'].sum()
                fee = df_viz[df_viz['지표'] == 'L+i형 월정료']['값'].sum()
                rate = df_viz[df_viz['지표'] == 'L+i형 건 정지율']['값'].mean()
                c1.metric("총 정지 건수", f"{int(tot):,}건")
                c2.metric("총 월정료", f"{int(fee/1000):,}천원")
                c3.metric("평균 정지율", f"{rate*100:.2f}%" if dataset_key != 'KPI' else f"{rate:.2f}%")
            except: pass

            # Chart
            st.markdown("#### 지사별 비교 차트")
            m_type = st.radio("지표 선택", ["건수", "금액", "비율"], horizontal=True, key=f"m_{dataset_key}")
            
            if m_type == "건수": cols = ["L형 건", "i형 건", "L+i형 건"]; fmt = ",.0f"
            elif m_type == "금액": cols = ["L형 월정료", "i형 월정료", "L+i형 월정료"]; fmt = ",.0f"
            else: cols = ["L형 건 정지율", "i형 건 정지율", "L+i형 건 정지율"]; fmt = ".2f"
            
            df_c = df_viz[df_viz['지표'].isin(cols)].sort_values("값", ascending=False)
            fig = px.bar(df_c, x='지사', y='값', color='지표', barmode='group', text_auto=fmt, height=450)
            fig.update_layout(xaxis_title=None, plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)

        with tab1: render_tab("Total")
        with tab2: render_tab("SP")
        with tab3: render_tab("KPI")

else: # 시계열 모드
    st.title("📈 정지율/부실율 트렌드")
    type_r = st.radio("항목 선택", ["정지율", "부실율"], horizontal=True)
    
    src = source_susp if type_r == "정지율" else source_fail
    df_rate = load_rate_data(src)
    
    if df_rate is None:
         st.error(f"데이터 파일이 없습니다. 깃허브 파일명이나 수동 업로드를 확인하세요.")
    else:
        if selected_branches: df_v = df_rate[df_rate['지사'].isin(selected_branches)]
        elif selected_hub != "전체": df_v = df_rate[df_rate['본부'] == selected_hub]
        else: df_v = df_rate
        
        if df_v.empty: st.warning("데이터 없음")
        else:
            fig = px.line(df_v, x='날짜', y='비율', color='지사', markers=True)
            fig.update_layout(yaxis_title="비율(%)", hovermode="x unified", height=500)
            st.plotly_chart(fig, use_container_width=True)
            
            # MoM 분석
            st.markdown("### 🚨 전월 대비 급등/급락 지사")
            dates = sorted(df_v['날짜'].unique())
            if len(dates) >= 2:
                curr, prev = dates[-1], dates[-2]
                df_p = df_v.pivot(index='지사', columns='날짜', values='비율')
                changes = []
                for b in df_p.index:
                    try:
                        c_val, p_val = df_p.loc[b, curr], df_p.loc[b, prev]
                        changes.append({"지사": b, "당월": c_val, "전월": p_val, "증감": c_val - p_val})
                    except: pass
                
                df_ch = pd.DataFrame(changes)
                c1, c2 = st.columns(2)
                with c1: 
                    st.caption("🔺 증가 상위 3개")
                    st.dataframe(df_ch.sort_values("증감", ascending=False).head(3).style.format("{:.2f}"))
                with c2: 
                    st.caption("🔻 감소 상위 3개")
                    st.dataframe(df_ch.sort_values("증감", ascending=True).head(3).style.format("{:.2f}"))

st.markdown("---")
st.caption("Data Source: GitHub Repository (Default) or Manual Upload")
