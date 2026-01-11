import pandas as pd
import os
import re

# Mocking the constants and functions from app.py for testing
HUB_BRANCH_MAP = {
    "강남/서부": ["강남", "수원", "분당", "강동", "용인", "평택", "인천", "강서", "부천", "안산", "안양", "관악"],
    "강북/강원": ["중앙", "강북", "서대문", "고양", "의정부", "남양주", "강릉", "원주"],
    "부산/경남": ["동부산", "남부산", "창원", "서부산", "김해", "울산", "진주"],
    "전남/전북": ["광주", "전주", "익산", "북광주", "순천", "제주", "목포"],
    "충남/충북": ["서대전", "충북", "천안", "대전", "충남서부"],
    "대구/경북": ["동대구", "서대구", "구미", "포항"]
}
ALL_BRANCHES = [b for branches in HUB_BRANCH_MAP.values() for b in branches]

HUB_NAME_MAP = {
    "강북강원": "강북/강원", "부산경남": "부산/경남", "전남전북": "전남/전북",
    "충남충북": "충남/충북", "대구경북": "대구/경북", "강남서부": "강남/서부"
}

def parse_date_robust(date_str):
    try:
        s = str(date_str).strip()
        match = re.match(r'^(\d{2})[/.](?:\s*)(\d{1,2})', s)
        if match:
            yy, mm = match.groups()
            return f"20{yy}-{int(mm):02d}-01"
        return None
    except: return None

def load_data_from_search(sheet_keyword):
    # Search for data.xlsx
    if os.path.exists("data.xlsx"):
        try:
            xls = pd.ExcelFile("data.xlsx")
            for sheet in xls.sheet_names:
                if sheet_keyword in sheet:
                    print(f"  Found sheet matching '{sheet_keyword}': {sheet}")
                    return pd.read_excel("data.xlsx", sheet_name=sheet, header=None)
            print(f"  ❌ No sheet matching '{sheet_keyword}' found in data.xlsx")
        except Exception as e:
            print(f"  ❌ Error reading Excel: {e}")
    else:
        print("  ❌ data.xlsx not found")
    return None

def process_total_df(df):
    if df is None: return None
    try:
        header_row = 3
        for i in range(min(20, len(df))):
            if str(df.iloc[i, 0]).strip() == "구분": header_row = i; break
        
        print(f"  Header row detected at index: {header_row}")
        
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
    except Exception as e:
        print(f"  ❌ Error processing total df: {e}")
        return None

def main():
    print("=== Verifying Data Loading ===")
    
    print("\n1. Testing 'Total Data' (Sheet: 시각화)")
    raw_total = load_data_from_search("시각화")
    if raw_total is not None:
        df_total = process_total_df(raw_total)
        if df_total is not None and not df_total.empty:
            print(f"  ✅ Total Data Processed: {len(df_total)} rows")
            print(f"  Detailed Sample:\n{df_total.head(2)}")
        else:
            print("  ❌ Failed to process Total Data")
    
    print("\n2. Testing 'Suspension Data' (Sheet: 정지율)")
    raw_susp = load_data_from_search("정지율")
    if raw_susp is not None:
        # Just check if it loaded, strict parsing is in app.py custom logic which assumes specific columns
        print(f"  ✅ Suspension Sheet Loaded: {raw_susp.shape}")
    
    print("\n3. Testing 'Failure Data' (Sheet: 부실율)")
    raw_fail = load_data_from_search("부실율")
    if raw_fail is not None:
         print(f"  ✅ Failure Sheet Loaded: {raw_fail.shape}")

if __name__ == "__main__":
    main()
