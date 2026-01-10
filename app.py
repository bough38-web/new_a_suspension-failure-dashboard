import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# === 1. 페이지 및 스타일 설정 ===
st.set_page_config(
    page_title="정지/부실 관리 통합 대시보드",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 커스텀 CSS 적용 (카드 디자인, 폰트, 여백 최적화)
st.markdown("""
<style>
    /* 전체 배경 및 폰트 */
    .stApp {
        background-color: #f8f9fa;
        font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, Roboto, 'Helvetica Neue', 'Segoe UI', 'Apple SD Gothic Neo', 'Noto Sans KR', 'Malgun Gothic', sans-serif;
    }
    
    /* 카드 스타일 컨테이너 */
    .metric-card {
        background-color: white;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        border: 1px solid #e9ecef;
        margin-bottom: 20px;
    }
    
    /* 헤더 스타일 */
    h1, h2, h3 {
        color: #343a40;
        font-weight: 700;
    }
    
    /* 사이드바 스타일 */
    [data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e9ecef;
    }
    
    /* 탭 스타일 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 48px;
        white-space: pre-wrap;
        background-color: #ffffff;
        border-radius: 8px;
        border: 1px solid #e9ecef;
        color: #495057;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        background-color: #e7f5ff;
        color: #1c7ed6;
        border-color: #1c7ed6;
    }
</style>
""", unsafe_allow_html=True)

# === 2. 설정 및 데이터 로드 함수 ===

# 파일 경로
FILE_TOTAL = "data_total.csv"
FILE_SUSP = "data_suspension.csv"
FILE_FAIL = "data_failure.csv"

# 본부-지사 매핑
HUB_BRANCH_MAP = {
    "강남/서부": ["강남", "수원", "분당", "강동", "용인", "평택", "인천", "강서", "부천", "안산", "안양", "관악"],
    "강북/강원": ["중앙", "강북", "서대문", "고양", "의정부", "남양주", "강릉", "원주"],
    "부산/경남": ["동부산", "남부산", "창원", "서부산", "김해", "울산", "진주"],
    "전남/전북": ["광주", "전주", "익산", "북광주", "순천", "제주", "목포"],
    "충남/충북": ["서대전", "충북", "천안", "대전", "충남서부"],
    "대구/경북": ["동대구", "서대구", "구미", "포항"]
}

# 모든 지사 리스트 (검색용)
ALL_BRANCHES = [b for branches in HUB_BRANCH_MAP.values() for b in branches]

@st.cache_data
def load_total_data():
    if not os.path.exists(FILE_TOTAL): return None
    df = pd.read_csv(FILE_TOTAL, header=None)
    header_row = 3
    
    # 데이터셋별 컬럼 인덱스 정의
    ranges = {"Total": (1, 13), "SP": (15, 27), "KPI": (29, 41)}
    col_names = [
        "L형 건", "i형 건", "L+i형 건", 
        "L형 건 정지율", "i형 건 정지율", "L+i형 건 정지율",
        "L형 월정료", "i형 월정료", "L+i형 월정료",
        "L형 월정료 정지율", "i형 월정료 정지율", "L+i형 월정료 정지율"
    ]
    
    parsed_data = []
    for i in range(header_row + 1, len(df)):
        row = df.iloc[i]
        org_name = str(row[0]).strip()
        
        is_hub = org_name in HUB_BRANCH_MAP.keys()
        is_branch = False
        hub_name = None
        
        if is_hub:
            hub_name = org_name
        else:
            for hub, branches in HUB_BRANCH_MAP.items():
                if org_name in branches:
                    is_branch = True; hub_name = hub; break
        
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
def load_rate_data(file_path):
    if not os.path.exists(file_path): return None
    df = pd.read_csv(file_path, header=None)
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

# === 3. 메인 레이아웃 구성 ===

# 사이드바 (공통 필터)
with st.sidebar:
    st.image("https://img.icons8.com/color/96/data-configuration.png", width=60)
    st.title("대시보드 설정")
    st.markdown("---")
    
    # 탭 선택 (라디오 버튼 대신 보기 좋은 메뉴)
    selected_mode = st.radio(
        "분석 모드",
        ["📊 현황 스냅샷 (Total/SP)", "📈 시계열 트렌드 (Rate)"],
        captions=["현재 시점의 정지/부실 현황", "기간별 정지율/부실율 변화 추이"]
    )
    
    st.markdown("---")
    
    # 공통 필터링 UI
    st.subheader("🔎 필터링 조건")
    selected_hub = st.selectbox("본부 선택", ["전체"] + list(HUB_BRANCH_MAP.keys()))
    
    # 지사 선택 로직
    if selected_hub == "전체":
        available_branches = ALL_BRANCHES
    else:
        available_branches = HUB_BRANCH_MAP.get(selected_hub, [])
        
    selected_branches = st.multiselect(
        "지사 선택", 
        available_branches, 
        default=available_branches[:5] if selected_hub == "전체" else available_branches,
        placeholder="지사를 선택하세요 (다중 선택 가능)"
    )

# 메인 콘텐츠 영역
if "스냅샷" in selected_mode:
    st.title("📊 정지 및 SP 현황 스냅샷")
    st.markdown("최신 데이터를 기반으로 본부 및 지사별 **정지 건수, 월정료, 정지율**을 분석합니다.")
    
    df_total = load_total_data()
    if df_total is None:
        st.error("데이터 파일을 찾을 수 없습니다. (data_total.csv)")
    else:
        # 데이터셋 탭
        tab1, tab2, tab3 = st.tabs(["📌 Total (총정지)", "⚡ SP 기준", "📉 KPI (부실율)"])
        
        # 탭 렌더링 함수
        def render_snapshot_tab(dataset_key):
            # 데이터 필터링
            mask = (df_total['데이터셋'] == dataset_key)
            
            # 본부/지사 필터링
            if selected_hub != "전체" or selected_branches:
                # 선택된 지사 데이터만 필터링
                mask_branch = mask & (df_total['구분'] == '지사') & (df_total['지사'].isin(selected_branches))
                df_viz = df_total[mask_branch]
            else:
                # 전체 조회 시 본부 레벨 보여주기 (기본)
                mask_hub = mask & (df_total['구분'] == '본부')
                df_viz = df_total[mask_hub]
                df_viz['지사'] = df_viz['본부'] # 시각화를 위해 컬럼 통일

            if df_viz.empty:
                st.warning("선택한 조건에 해당하는 데이터가 없습니다.")
                return

            # --- 1. Top Level Metrics (KPI 카드) ---
            st.markdown("#### 💡 핵심 지표 요약")
            col1, col2, col3 = st.columns(3)
            
            # 지표 계산
            total_cnt = df_viz[df_viz['지표'] == 'L+i형 건']['값'].sum()
            total_fee = df_viz[df_viz['지표'] == 'L+i형 월정료']['값'].sum()
            avg_rate = df_viz[df_viz['지표'] == 'L+i형 건 정지율']['값'].mean()
            
            with col1:
                st.metric(label="총 정지 건수", value=f"{int(total_cnt):,}건")
            with col2:
                st.metric(label="총 월정료 금액", value=f"{int(total_fee/1000):,}천원")
            with col3:
                st.metric(label="평균 정지율", value=f"{avg_rate*100:.2f}%" if dataset_key != 'KPI' else f"{avg_rate:.2f}%") # KPI는 이미 %일수 있음 확인필요

            st.markdown("---")

            # --- 2. Chart Section (고급 차트) ---
            col_chart, col_option = st.columns([3, 1])
            
            with col_option:
                st.markdown("#### ⚙️ 차트 설정")
                metric_type = st.radio(
                    "분석 지표", 
                    ["건수", "금액(월정료)", "비율"],
                    key=f"metric_{dataset_key}"
                )
                
                # 지표 매핑
                if metric_type == "건수":
                    target_cols = ["L형 건", "i형 건", "L+i형 건"]
                    y_axis_format = ",.0f"
                    color_scale = px.colors.qualitative.G10
                elif metric_type == "금액(월정료)":
                    target_cols = ["L형 월정료", "i형 월정료", "L+i형 월정료"]
                    y_axis_format = ",.0f"
                    color_scale = px.colors.qualitative.Pastel
                else:
                    target_cols = ["L형 건 정지율", "i형 건 정지율", "L+i형 건 정지율"]
                    y_axis_format = ".2f"
                    color_scale = px.colors.sequential.Bluered

            with col_chart:
                df_chart = df_viz[df_viz['지표'].isin(target_cols)]
                
                # 정렬 (내림차순)
                df_chart = df_chart.sort_values(by="값", ascending=False)

                fig = px.bar(
                    df_chart, 
                    x='지사', y='값', color='지표', 
                    barmode='group',
                    text_auto=y_axis_format,
                    color_discrete_sequence=color_scale,
                    height=500
                )
                
                fig.update_layout(
                    title=f"<b>{dataset_key} - {metric_type} 지사별 비교</b>",
                    title_font_size=20,
                    xaxis_title=None,
                    yaxis_title=metric_type,
                    legend_title=None,
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(family="Pretendard"),
                    hovermode="x unified"
                )
                fig.update_yaxes(showgrid=True, gridcolor='lightgray')
                st.plotly_chart(fig, use_container_width=True)

            # --- 3. Heatmap & Table (상세 분석) ---
            with st.expander("📂 상세 데이터 및 히트맵 보기", expanded=False):
                st.markdown("#### 지표별 히트맵 분석")
                # 피벗 테이블 생성
                pivot_df = df_viz.pivot_table(index='지사', columns='지표', values='값', aggfunc='sum')
                # 선택된 지표 타입에 맞는 컬럼만 필터링
                pivot_df_filtered = pivot_df[target_cols]
                
                fig_heat = px.imshow(
                    pivot_df_filtered, 
                    text_auto=y_axis_format,
                    aspect="auto",
                    color_continuous_scale="Blues",
                    title=f"{metric_type} 히트맵"
                )
                st.plotly_chart(fig_heat, use_container_width=True)
                
                st.markdown("#### Raw Data")
                st.dataframe(pivot_df_filtered.style.format("{:,.0f}" if metric_type != "비율" else "{:.4f}"))

        with tab1: render_snapshot_tab("Total")
        with tab2: render_snapshot_tab("SP")
        with tab3: render_snapshot_tab("KPI")

# 시계열 트렌드 모드
else:
    st.title("📈 정지율/부실율 트렌드 분석")
    st.markdown("기간별 변화 추이를 분석하고 **급격한 변동이 발생한 지사**를 자동으로 탐지합니다.")
    
    analysis_type = st.radio("", ["정지율 (Suspension)", "부실율 (Failure)"], horizontal=True, label_visibility="collapsed")
    
    # 데이터 로드
    target_file = FILE_SUSP if "정지율" in analysis_type else FILE_FAIL
    df_rate = load_rate_data(target_file)
    
    if df_rate is None:
        st.error(f"데이터 파일을 찾을 수 없습니다. ({target_file})")
    else:
        # 필터링
        if selected_branches:
            df_viz = df_rate[df_rate['지사'].isin(selected_branches)]
        elif selected_hub != "전체":
             df_viz = df_rate[df_rate['본부'] == selected_hub]
        else:
             df_viz = df_rate # 전체
             
        if df_viz.empty:
            st.warning("선택한 조건의 데이터가 없습니다.")
        else:
            # --- 1. Trend Chart ---
            st.markdown("### 🗓️ 월별 추세 그래프")
            
            fig = px.line(
                df_viz, 
                x='날짜', y='비율', color='지사', 
                markers=True,
                line_shape='spline', # 부드러운 곡선
                render_mode='svg'
            )
            fig.update_layout(
                height=500,
                xaxis_title=None,
                yaxis_title="비율 (%)",
                plot_bgcolor="rgba(0,0,0,0)",
                hovermode="x unified",
                legend=dict(orientation="h", y=1.1)
            )
            fig.update_xaxes(showgrid=True, gridcolor='#eee')
            fig.update_yaxes(showgrid=True, gridcolor='#eee', ticksuffix="%")
            st.plotly_chart(fig, use_container_width=True)
            
            # --- 2. Smart Analysis (변동 감지) ---
            st.markdown("### 🚨 전월 대비 변동 분석 (MoM)")
            
            # 최근 날짜와 직전 날짜 찾기
            dates = sorted(df_viz['날짜'].unique())
            if len(dates) >= 2:
                curr_date = dates[-1]
                prev_date = dates[-2]
                
                # 피벗으로 변환하여 계산
                df_pivot = df_viz.pivot(index='지사', columns='날짜', values='비율')
                
                # 증감 계산
                changes = []
                for branch in df_pivot.index:
                    curr_val = df_pivot.loc[branch, curr_date]
                    prev_val = df_pivot.loc[branch, prev_date]
                    diff = curr_val - prev_val
                    changes.append({
                        "지사": branch, 
                        "당월": curr_val, 
                        "전월": prev_val, 
                        "증감(%p)": diff,
                        "상태": "🔴 증가" if diff > 0 else "🔵 감소"
                    })
                
                df_changes = pd.DataFrame(changes)
                
                # 화면 분할 (급상승 / 급하락)
                col_inc, col_dec = st.columns(2)
                
                with col_inc:
                    st.markdown(f"#### 🔺 증가 상위 지사 ({curr_date.strftime('%Y-%m')})")
                    top_inc = df_changes.sort_values("증감(%p)", ascending=False).head(5)
                    # 스타일링된 데이터프레임
                    st.dataframe(
                        top_inc[["지사", "당월", "전월", "증감(%p)"]].style.format({"당월":"{:.2f}%", "전월":"{:.2f}%", "증감(%p)":"+{:.2f}%p"}).background_gradient(subset=["증감(%p)"], cmap="Reds"),
                        use_container_width=True
                    )
                    
                with col_dec:
                    st.markdown(f"#### 🔻 감소(개선) 상위 지사 ({curr_date.strftime('%Y-%m')})")
                    top_dec = df_changes.sort_values("증감(%p)", ascending=True).head(5)
                    st.dataframe(
                        top_dec[["지사", "당월", "전월", "증감(%p)"]].style.format({"당월":"{:.2f}%", "전월":"{:.2f}%", "증감(%p)":"{:.2f}%p"}).background_gradient(subset=["증감(%p)"], cmap="Blues_r"),
                        use_container_width=True
                    )
            else:
                st.info("전월 대비 증감을 계산하기 위해 최소 2개월 이상의 데이터가 필요합니다.")

# 푸터
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #868e96; font-size: 14px;'>
        © 2025 Suspension & Failure Management Dashboard | Powered by Streamlit & Plotly <br>
        데이터 업데이트: 2025.10.31 기준
    </div>
    """, 
    unsafe_allow_html=True
)