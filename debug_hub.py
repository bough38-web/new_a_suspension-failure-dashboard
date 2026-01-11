import pandas as pd
import os

# Mock constants from app.py
HUB_BRANCH_MAP = {
    "강남/서부": ["강남", "수원", "분당", "강동", "용인", "평택", "인천", "강서", "부천", "안산", "안양", "관악"],
    "강북/강원": ["중앙", "강북", "서대문", "고양", "의정부", "남양주", "강릉", "원주"],
    "부산/경남": ["동부산", "남부산", "창원", "서부산", "김해", "울산", "진주"],
    "전남/전북": ["광주", "전주", "익산", "북광주", "순천", "제주", "목포"],
    "충남/충북": ["서대전", "충북", "천안", "대전", "충남서부"],
    "대구/경북": ["동대구", "서대구", "구미", "포항"]
}

def load_data():
    if os.path.exists("data.xlsx"):
        xls = pd.ExcelFile("data.xlsx")
        for sheet in xls.sheet_names:
            if "시각화" in sheet:
                return pd.read_excel("data.xlsx", sheet_name=sheet, header=None)
    return None

def process_total_df(df):
    if df is None: return None
    
    header_row = 3
    for i in range(min(50, len(df))):
        val = str(df.iloc[i, 0]).strip()
        if "구분" in val: 
            header_row = i; break
    
    print(f"Header Row: {header_row}")
    
    ranges = {"Total": (1, 13), "SP": (15, 27), "KPI": (28, 40)}
    col_names = ["L형 건", "i형 건", "L+i형 건", "L형 정지율", "i형 정지율", "L+i형 정지율",
                 "L형 월정료", "i형 월정료", "L+i형 월정료", "L형료 정지율", "i형료 정지율", "L+i형료 정지율"]
    
    parsed = []
    print("\n--- Inspecting Row Processing ---")
    for i in range(header_row + 1, min(header_row + 50, len(df))): # Inspect first 50 rows
        row = df.iloc[i]
        org = str(row[0]).strip()
        if not org or org == 'nan': continue
        
        # Check matching logic
        is_hub = org in HUB_BRANCH_MAP.keys()
        is_br = False; hub_name = org
        
        if is_hub: 
            print(f"Row {i}: '{org}' identified as HUB")
            hub_name = org
        else:
            for h, brs in HUB_BRANCH_MAP.items():
                if org in brs: is_br = True; hub_name = h; break
            if is_br:
                pass # print(f"Row {i}: '{org}' identified as BRANCH of {hub_name}")
            else:
                print(f"Row {i}: '{org}' NOT MATCHED")
        
        if not (is_hub or is_br): continue
        
        if is_hub and hub_name == "강남/서부":
            print(f"\n--- DEBUG: Inspecting '강남/서부' Raw Values ---")
            for section, (start, end) in ranges.items():
                print(f"  Section {section} [{start}:{end}]: {row[start:end].values}")
        
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

def main():
    raw = load_data()
    if raw is None:
        print("Could not load data.xlsx")
        return
        
    df_total = process_total_df(raw)
    
    print("\n--- Summary of Processed Data for HUBS ---")
    if df_total is not None and not df_total.empty:
        hubs = df_total[df_total['구분'] == '본부']
        print(f"Total Hub Rows: {len(hubs)}")
        print(hubs.head())
        
        print("\n--- Values Check ---")
        for hub in HUB_BRANCH_MAP.keys():
            d = hubs[(hubs['본부'] == hub) & (hubs['데이터셋'] == 'KPI')]
            if d.empty:
                print(f"{hub}: NO DATA for KPI")
            else:
                rate = d[d['지표'].str.contains('L\+i형.*정지율')]['값'].mean()
                cnt = d[d['지표'] == 'L+i형 건']['값'].sum()
                print(f"{hub}: Rate={rate}, Count={cnt}")
    else:
        print("df_total is empty.")

if __name__ == "__main__":
    main()
