import pandas as pd

try:
    file_path = "data.xlsx"
    xls = pd.ExcelFile(file_path)
    
    print("Sheets:", xls.sheet_names)
    
    for sheet in ["정지율", "부실율"]:
        if sheet in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=sheet, header=None)
            print(f"\n--- Sheet: {sheet} ---")
            # The app assumes row 0 has branch names every 2 columns
            row0 = df.iloc[0].tolist()
            # print unique non-nan values from row 0
            headers = [str(x).strip() for x in row0 if pd.notna(x)]
            print("Headers found:", headers)
            
            if "강북/강원" in headers or "강북강원" in headers:
                print(">> Hub column FOUND.")
            else:
                print(">> Hub column NOT found.")
except Exception as e:
    print(e)
