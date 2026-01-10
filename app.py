import streamlit as st
import pandas as pd
import plotly.express as px
import os
import re

# === 1. 페이지 설정 ===
st.set_page_config(
    page_title="정지/부실 관리 대시보드",
    page_icon="📊",
    layout="wide"
)

st.markdown("""
<style>
    .metric-card {
        background-color: white; border-radius: 12px; padding: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05); border: 1px solid #e9ecef; margin-bottom: 20px;
    }
    [data-testid="stSidebar"] { background-color: #f8f9fa; border-right: 1px solid #e9ecef; }
</style>
""", unsafe_allow_html=True)

# === 2. 설정 ===
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

# === 3. 데이터 로드 및 처리 함수 ===

def parse_date_robust(date_str):
    """날짜 문자열에서 (e)나 .04 같은 특수문자를 제거하고 YYYY-MM-01 형태로 변환"""
    try:
        s = str(date_str).strip()
        # 정규식: 숫자2자리 + 구분자(/또는.) + 숫자1~2자리 추출 (예: 25/10(e) -> 25, 10)
        match = re.match(r'^(\d{2})[/.](?:\s*)(\d{1,2})', s)
        if match:
            yy, mm = match.groups()
            return f"20{yy}-{int(mm):02d}-01"
        return None
    except:
        return None

def find_sheet_by_keyword(excel_file, keywords):
    """키워드가 포함된 시트를 자동으로 찾음"""
    try:
        xls = pd.ExcelFile(excel_file)
        sheet_names = xls.sheet_names
        for sheet in sheet_names:
            for keyword in keywords:
                if keyword in sheet: return sheet
        return None
    except:
        return None

def get_excel_file():
    uploaded = st.sidebar.file_uploader("📂 엑셀 파일 수동 업로드 (.xlsx)", type=['xlsx'])
    if uploaded: return uploaded
    if os.path.exists(DEFAULT_EXCEL_FILE): return DEFAULT_EXCEL_FILE
    return None

@st.cache_data
def load_total_data(file_source):
    if not file_source: return None
    try:
        sheet_name = find_sheet_by_keyword(file_source, ["시각화", "0901", "Sheet1"])
        if not sheet_name: return None
        
        df = pd.read_excel(file_source, sheet_name=sheet_name, header=None)
        
        header_row = 3
        # 헤더 위치 자동 보정
        for i in range(min(10, len(df))):
            if str(df.iloc[i, 0]).strip() == "구분":
                header_row = i; break

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
                try:
                    vals = row[start:end].values
                    for idx, val in enumerate(vals):
                        try: num_val = float(str(val).replace(',', '').replace('-', '0'))
                        except: num_val = 0.0
                        parsed_data.append({
                            "본부": hub_name, "지사": org_name, "구분": "본부" if is_hub else "지사",
                            "데이터셋": section, "지표": col_names[idx], "값": num_val
                        })
                except: continue
        return pd.DataFrame(parsed_data)
    except: return None

@st.cache_data
def load_rate_data(file_source, type_key):
    if not file_source: return None
    try:
        # 시트 찾기
        keywords = ["정지율"] if type_key == "suspension" else ["부실율"]
        sheet_name = find_sheet_by_keyword(file_source, keywords)
        if not sheet_name: return None
        
        df = pd.read_excel(file_source, sheet_name=sheet_name, header=None)
        
        processed_list = []
        num_cols = df.shape[1]
        
        for i in range(0, num_cols, 2):
            if i+1 >= num_cols: break
            branch_name = str(df.iloc[0, i]).strip()
            if pd.isna(branch_name) or branch_name == 'nan': continue
            
            sub_df = df.iloc[1:, [i, i+1]].copy()
            sub_df.columns = ["date_raw", "rate"]
            sub_df = sub_df.dropna()
            
            # 본부 매핑 (엑셀 헤더의 축약형 이름도 처리)
            hub_name = "기타"
            for hub, branches in HUB_BRANCH_MAP.items():
                if branch_name in branches: hub_name = hub; break
            if branch_name in ["강북강원", "부산경남", "전남전북", "충남충북", "대구경북"]: hub_name = branch_name 
                 
            for _, row in sub_df.iterrows():
                # 날짜 파싱 오류 해결 (핵심 수정)
                full_date = parse_date_robust(row['date_raw'])
                if not full_date: continue
                
                try: rate_val = float(str(row['rate']).replace(',', ''))
                except: rate_val = 0.0
                
                processed_list.append({"날짜": full_date, "본부": hub_name, "지사": branch_name, "비율": rate_val * 100})
                
        df_result = pd.DataFrame(processed_list)
        if not df_result.empty:
            df_result['날짜'] = pd.to_datetime(df_result['날짜'])
        return df_result
    except Exception as e:
        return None

# === 4. UI 구성 ===

with st.sidebar:
    st.title("🎛️ 대시보드 설정")
    excel_source = get_excel_file()
    
    if excel_source:
        st.success("파일 로드 완료")
    else:
        st.info("파일을 업로드하거나 data.xlsx를 확인하세요.")

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
        st.error("데이터를 불러올 수 없습니다. '시각화' 시트가 있는지 확인해주세요.")
    else:
        t1, t2, t3 = st.tabs(["Total", "SP", "KPI"])
        def render_tab(key):
            mask = (df_total['데이터셋'] == key)
            if sel_hub != "전체" or sel_branches:
                df_v = df_total[mask & (df_total['구분'] == '지사') & (df_total['지사'].isin(sel_branches))]
            else:
                df_v = df_total[mask & (df_total['구분'] == '본부')]
                df_v['지사'] = df_v['본부']
            
            if df_v.empty: st.info("데이터 없음"); return
            
            c1, c2, c3 = st.columns(3)
            try:
                tot = df_v[df_v['지표']=='L+i형 건']['값'].sum()
                fee = df_v[df_v['지표']=='L+i형 월정료']['값'].sum()
                rate = df_v[df_v['지표']=='L+i형 건 정지율']['값'].mean()
                c1.metric("총 정지", f"{int(tot):,}")
                c2.metric("총 월정료", f"{int(fee/1000):,}천원")
                c3.metric("평균 정지율", f"{rate*100:.2f}%" if key != 'KPI' else f"{rate:.2f}%")
            except: pass
            
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

else:
    st.title("📈 정지율/부실율 트렌드")
    type_r = st.radio("항목", ["정지율", "부실율"], horizontal=True)
    sheet_key = "suspension" if type_r == "정지율" else "failure"
    
    df_rate = load_rate_data(excel_source, sheet_key)
    
    if df_rate is None or df_rate.empty:
        st.error(f"데이터를 불러올 수 없습니다. 엑셀 파일에 '{'기관정지율' if type_r=='정지율' else '기관부실율'}' 관련 시트가 있는지 확인해주세요.")
    else:
        if sel_branches: df_v = df_rate[df_rate['지사'].isin(sel_branches)]
        elif sel_hub != "전체": df_v = df_rate[df_rate['본부'] == sel_hub]
        else: df_v = df_rate
        
        if not df_v.empty:
            fig = px.line(df_v, x='날짜', y='비율', color='지사', markers=True)
            fig.update_layout(hovermode="x unified", yaxis_title="비율 (%)")
            st.plotly_chart(fig, use_container_width=True)
            
            # MoM 분석 테이블
            st.markdown("#### 🔍 전월 대비 변동 분석")
            try:
                dates = sorted(df_v['날짜'].unique())
                if len(dates) >= 2:
                    curr, prev = dates[-1], dates[-2]
                    df_p = df_v.pivot(index='지사', columns='날짜', values='비율')
                    changes = []
                    for b in df_p.index:
                        if curr in df_p.columns and prev in df_p.columns:
                            c_val, p_val = df_p.loc[b, curr], df_p.loc[b, prev]
                            if pd.notna(c_val) and pd.notna(p_val):
                                changes.append({"지사": b, "당월": c_val, "전월": p_val, "증감": c_val - p_val})
                    
                    if changes:
                        df_ch = pd.DataFrame(changes)
                        c1, c2 = st.columns(2)
                        with c1: 
                            st.caption(f"🔺 증가 상위 ({curr.strftime('%Y-%m')})")
                            st.dataframe(df_ch.sort_values("증감", ascending=False).head(5).style.format("{:.2f}"))
                        with c2: 
                            st.caption(f"🔻 감소 상위 ({curr.strftime('%Y-%m')})")
                            st.dataframe(df_ch.sort_values("증감", ascending=True).head(5).style.format("{:.2f}"))
            except Exception as e: st.caption("분석 데이터를 생성할 수 없습니다.")
