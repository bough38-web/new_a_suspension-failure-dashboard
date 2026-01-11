import pandas as pd

try:
    file_path = "data.xlsx"
    xls = pd.ExcelFile(file_path)
    
    print("Sheets:", xls.sheet_names)
    
    # Use actual names found
    target_sheets = [s for s in xls.sheet_names if "정지율" in s or "부실율" in s]
    
    for sheet in target_sheets:
        df = pd.read_excel(xls, sheet_name=sheet, header=None)
        print(f"\n--- Sheet: {sheet} ---")
        row0 = df.iloc[0].tolist()
        headers = [str(x).strip() for x in row0 if pd.notna(x)]
        print("Headers found:", headers)
        
        if "강북/강원" in headers or "강북강원" in headers:
            print(f">> Hub column FOUND in {sheet}")
        else:
            print(f">> Hub column NOT found in {sheet}")
except Exception as e:
    print(e)
