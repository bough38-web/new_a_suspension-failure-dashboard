import streamlit as st
import pandas as pd
import plotly.express as px
import os

# === 1. 페이지 설정 ===
st.set_page_config(
    page_title="정지/부실 관리 대시보드",
    page_icon="📊",
    layout="wide"
)

# 스타일 적용
st.markdown("""
<style>
    .metric-card {
        background-color: white; border-radius: 12px; padding: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05); border: 1px solid #e9ecef; margin-bottom: 20px;
    }
    [data-testid="stSidebar"] { background-color: #f8f9fa; border-right: 1px solid #e9ecef; }
</style>
""", unsafe_allow_html=True)

# === 2. 파일 설정 ===
# 깃허브에 올릴 엑셀 파일 이름 (이 이름으로 파일을 올려주세요!)
DEFAULT_EXCEL_FILE = "data.xlsx"

# 시트 이름 설정 (엑셀 파일 내부의 시트 이름과 정확히 일치해야 함)
SHEET_NAMES = {
    "total": "시각화(0901)",
    "suspension": "기관정지율",
    "failure": "기관부실율"
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

# === 3. 데이터 로드 함수 ===

def get_excel_file():
    """파일 소스 결정: 수동 업로드 우선, 없으면 로컬 기본 파일"""
    uploaded = st.sidebar.file_uploader("📂 엑셀 파일 수동 업로드 (.xlsx)", type=['xlsx'])
    if uploaded:
        return uploaded
    if os.path.exists(DEFAULT_EXCEL_FILE):
        return DEFAULT_EXCEL_FILE
    return None

@st.cache_data
def load_total_data(file_source):
    if not file_source: return None
    try:
        # 엑셀의 특정 시트 읽기 (헤더 없이 읽음)
        df = pd.read_excel(file_source, sheet_name=SHEET_NAMES["total"], header=None)
        
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
    except Exception as e:
        return None

@st.cache_data
def load_rate_data(file_source, sheet_type):
    if not file_source: return None
    try:
        target_sheet = SHEET_NAMES["suspension"] if sheet_type == "suspension" else SHEET_NAMES["failure"]
        df = pd.read_excel(file_source, sheet_name=target_sheet, header=None)
        
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
                    # 엑셀 날짜 형식(datetime)이거나 문자열일 수 있음
                    if isinstance(date_str, str) and '/' in date_str:
                        yy, mm = date_str.split('/'); full_date = f"20{yy}-{mm}-01"
                    else:
                        full_date = pd.to_datetime(row['date_raw'])
                except: continue
                
                try: rate_val = float(str(row['rate']).replace(',', ''))
                except: rate_val = 0.0
                
                processed_list.append({"날짜": full_date, "본부": hub_name, "지사": branch_name, "비율": rate_val * 100})
                
        df_result = pd.DataFrame(processed_list)
        df_result['날짜'] = pd.to_datetime(df_result['날짜'])
        return df_result
    except Exception as e:
        return None

# === 4. UI 구성 ===

with st.sidebar:
    st.title("🎛️ 대시보드 설정")
    st.info("기본 파일: data.xlsx")
    
    excel_source = get_excel_file()
    
    st.markdown("---")
    mode = st.radio("분석 모드", ["📊 현황 스냅샷 (Total/SP)", "📈 시계열 트렌드 (Rate)"])
    
    st.markdown("---")
    sel_hub = st.selectbox("본부 필터", ["전체"] + list(HUB_BRANCH_MAP.keys()))
    branches = ALL_BRANCHES if sel_hub == "전체" else HUB_BRANCH_MAP.get(sel_hub, [])
    sel_branches = st.multiselect("지사 필터", branches, default=branches[:5] if sel_hub == "전체" else branches)

# === 메인 로직 ===

if not excel_source:
    st.warning("⚠️ 데이터 파일이 없습니다. 깃허브에 'data.xlsx'를 업로드하거나, 사이드바에서 파일을 직접 업로드해주세요.")
    st.stop()

if "스냅샷" in mode:
    st.title("📊 정지 및 SP 현황 스냅샷")
    df_total = load_total_data(excel_source)
    
    if df_total is None or df_total.empty:
        st.error(f"'{SHEET_NAMES['total']}' 시트를 읽을 수 없습니다. 시트 이름을 확인해주세요.")
    else:
        # 탭 및 차트 로직 (이전과 동일, 데이터 소스만 변경됨)
        t1, t2, t3 = st.tabs(["Total", "SP", "KPI"])
        def render_tab(key):
            mask = (df_total['데이터셋'] == key)
            if sel_hub != "전체" or sel_branches:
                df_v = df_total[mask & (df_total['구분'] == '지사') & (df_total['지사'].isin(sel_branches))]
            else:
                df_v = df_total[mask & (df_total['구분'] == '본부')]
                df_v['지사'] = df_v['본부']
            
            if df_v.empty: st.info("데이터 없음"); return
            
            # KPI
            c1, c2, c3 = st.columns(3)
            try:
                tot = df_v[df_v['지표']=='L+i형 건']['값'].sum()
                fee = df_v[df_v['지표']=='L+i형 월정료']['값'].sum()
                rate = df_v[df_v['지표']=='L+i형 건 정지율']['값'].mean()
                c1.metric("총 정지", f"{int(tot):,}")
                c2.metric("총 월정료", f"{int(fee/1000):,}천원")
                c3.metric("평균 정지율", f"{rate*100:.2f}%" if key != 'KPI' else f"{rate:.2f}%")
            except: pass
            
            # Chart
            m_type = st.radio("지표", ["건수", "금액", "비율"], horizontal=True, key=key)
            if m_type == "건수": cols = ["L형 건", "i형 건", "L+i형 건"]
            elif m_type == "금액": cols = ["L형 월정료", "i형 월정료", "L+i형 월정료"]
            else: cols = ["L형 건 정지율", "i형 건 정지율", "L+i형 건 정지율"]
            
            df_c = df_v[df_v['지표'].isin(cols)].sort_values("값", ascending=False)
            fig = px.bar(df_c, x='지사', y='값', color='지표', barmode='group', text_auto=True)
            st.plotly_chart(fig, use_container_width=True)

        with t1: render_tab("Total")
        with t2: render_tab("SP")
        with t3: render_tab("KPI")

else: # 시계열
    st.title("📈 정지율/부실율 트렌드")
    type_r = st.radio("항목", ["정지율", "부실율"], horizontal=True)
    sheet_key = "suspension" if type_r == "정지율" else "failure"
    
    df_rate = load_rate_data(excel_source, sheet_key)
    
    if df_rate is None or df_rate.empty:
        st.error(f"'{SHEET_NAMES[sheet_key]}' 시트를 읽을 수 없습니다.")
    else:
        if sel_branches: df_v = df_rate[df_rate['지사'].isin(sel_branches)]
        elif sel_hub != "전체": df_v = df_rate[df_rate['본부'] == sel_hub]
        else: df_v = df_rate
        
        if not df_v.empty:
            fig = px.line(df_v, x='날짜', y='비율', color='지사', markers=True)
            fig.update_layout(hovermode="x unified")
            st.plotly_chart(fig, use_container_width=True)
