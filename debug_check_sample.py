import pandas as pd
import sys

def check_file(filename):
    print(f"--- Checking {filename} ---")
    try:
        # Read all sheets like the backend does logic
        all_sheets = pd.read_excel(filename, sheet_name=None, header=None)
        total_sum = 0
        total_rows = 0
        
        for sheet_name, raw_df in all_sheets.items():
            print(f"Sheet: {sheet_name}")
            # Try to find header (same logic as backend roughly)
            # Just simply look for 'Amount' column in raw dump for quick check
            # Or better, just sum anything that looks numeric to get 'potential' max
            
            # Replicate backend parse strictly
            header_row_index = 0
            found_header = False
            keywords = ["date", "amount", "debit", "credit", "cost", "description", "merchant", "payee", "category"]
            
            # limit to 20
            temp_head = raw_df.head(20)
            for i, row in temp_head.iterrows():
                row_str = " ".join([str(x).lower() for x in row.values])
                matches = sum(1 for k in keywords if k in row_str)
                if matches >= 2:
                    header_row_index = i
                    found_header = True
                    break
            
            if not found_header:
                print("  No Header Found!")
                continue
                
            print(f"  Header found at row {header_row_index}")
            new_header = raw_df.iloc[header_row_index]
            df = raw_df.iloc[header_row_index + 1:].copy()
            df.columns = new_header
            df.reset_index(drop=True, inplace=True)
            
            # Map columns
            # Column mapping...
            amount_col = None
            for col in df.columns:
                if str(col).lower() in ['amount', 'debit', 'cost']:
                    amount_col = col
                    break
            
            if amount_col:
                # Sum
                sheet_sum = pd.to_numeric(df[amount_col], errors='coerce').sum()
                print(f"  Sheet Sum: {sheet_sum:,.2f}")
                total_sum += sheet_sum
                total_rows += len(df)
            else:
                print("  No Amount column found")

        print(f"Total Sum: {total_sum:,.2f}")
        print(f"Total Rows: {total_rows}")
        
    except Exception as e:
        print(f"Error reading {filename}: {e}")

check_file("sample_budget.xlsx")
check_file("second_sample_budget.xlsx")
