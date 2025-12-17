import io
import structlog
import pandas as pd
from typing import List
from decimal import Decimal
from src.domain.budget import BudgetEntry
from src.application.ports import ExcelParser

class PandasExcelParser(ExcelParser):
    """
    Implementation of ExcelParser using Pandas.
    """
    
    def __init__(self):
        self.logger = structlog.get_logger()

    def parse(self, file_content: bytes) -> List[BudgetEntry]:
        """
        Parses Excel content using Pandas.
        Supports multiple sheets.
        Assumes columns: Date, Category, Amount, Description.
        """
        self.logger.info("parsing_file_start")
        
        # Read all sheets at once (sheet_name=None returns a dict of sheet_name -> DataFrame)
        # We read without header initially to detect it manually per sheet
        all_sheets = pd.read_excel(io.BytesIO(file_content), sheet_name=None, header=None)
        
        all_entries = []
        skipped_rows: List[str] = []
        
        for sheet_name, raw_df in all_sheets.items():
            self.logger.info("parsing_sheet", sheet=sheet_name)
            
            if raw_df.empty:
                continue

            # Header Detection on first 20 rows
            header_row_index = 0
            found_header = False
            keywords = ["date", "amount", "debit", "credit", "cost", "description", "merchant", "payee", "category"]
            
            temp_head = raw_df.head(20)
            
            for i, row in temp_head.iterrows():
                row_str = " ".join([str(x).lower() for x in row.values])
                matches = sum(1 for k in keywords if k in row_str)
                if matches >= 2:
                    header_row_index = i
                    found_header = True
                    self.logger.debug("header_detected", sheet=sheet_name, row_index=i)
                    break
            
            if not found_header:
                self.logger.warn("no_header_found_skipping_sheet", sheet=sheet_name)
                continue

            # Slice the dataframe to respect the header
            # specific row becomes header, subsequent rows are data
            new_header = raw_df.iloc[header_row_index]
            df = raw_df.iloc[header_row_index + 1:].copy()
            df.columns = new_header
            df.reset_index(drop=True, inplace=True)
            
            self.logger.info("columns_found", sheet=sheet_name, columns=list(df.columns))
            
            # Intelligent Column Mapping
            column_map = {
                "Transaction Date": "Date",
                "Post Date": "Date",
                "Debit": "Amount",
                "Cost": "Amount",
                "Merchant": "Description",
                "Payee": "Description"
            }
            df.rename(columns=column_map, inplace=True)
            
            # Ensure Date is datetime
            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'], errors='coerce').dt.date

            for _, row in df.iterrows():
                # Skip rows with invalid dates (or empty rows handling)
                if pd.isna(row.get("Date")):
                    skipped_rows.append(f"Sheet '{sheet_name}' Row {row.name}: Missing or Invalid Date")
                    continue
                    
                date_val = row["Date"]

                try:
                    # 1. Robust Amount Parsing (Handle accounting negative format like '(100.00)')
                    raw_amount = str(row["Amount"]) if "Amount" in df.columns and not pd.isna(row["Amount"]) else "0"
                    # Remove currency symbols and spaces
                    clean_amount = raw_amount.replace(",", "").replace("$", "").replace(" ", "")
                    
                    # Handle parentheses for negative numbers (e.g. "(500)" -> "-500")
                    if clean_amount.startswith("(") and clean_amount.endswith(")"):
                        clean_amount = "-" + clean_amount[1:-1]
                    
                    try:
                        amount_decimal = Decimal(clean_amount)
                    except Exception:
                        self.logger.warn("invalid_amount_format", value=raw_amount, row_index=row.name)
                        amount_decimal = Decimal("0")
                        skipped_rows.append(f"Sheet '{sheet_name}' Row {row.name}: Invalid Amount '{raw_amount}' (Defaulted to 0)")

                    # 2. Robust String Parsing (Description/Project)
                    # Force conversion to string, handle NaNs
                    desc_val = row["Description"] if "Description" in df.columns else "Unknown"
                    if pd.isna(desc_val):
                        final_desc = "Unknown"
                    else:
                        final_desc = str(desc_val).strip()
                        # Clean common merchant garbage
                        import re
                        final_desc = re.sub(r'AMZN Mktp.*', 'Amazon', final_desc, flags=re.IGNORECASE)
                        final_desc = re.sub(r'Uber.*', 'Uber', final_desc, flags=re.IGNORECASE)
                        final_desc = re.sub(r'Lyft.*', 'Lyft', final_desc, flags=re.IGNORECASE)
                        final_desc = re.sub(r'\d{4,}', '', final_desc).strip()

                    proj_val = row.get("Project")
                    if pd.isna(proj_val):
                        final_proj = "General"
                    else:
                        final_proj = str(proj_val).strip()

                    # 3. Robust Category Parsing (AI Inference Prep)
                    raw_cat = row.get("Category")
                    if pd.isna(raw_cat) or str(raw_cat).strip() == "":
                        final_cat = "Uncategorized"
                    else:
                        final_cat = str(raw_cat).strip()

                    entry = BudgetEntry(
                        date=date_val,
                        category=final_cat,
                        amount=amount_decimal,
                        description=final_desc,
                        project=final_proj
                    )
                    all_entries.append(entry)
                except Exception as e:
                    # Catch-all to prevent one bad row from crashing the whole file
                    self.logger.error("skipping_row_crash", error=str(e), row=row.to_dict())
                    skipped_rows.append(f"Sheet '{sheet_name}' Row {row.name}: Crash - {str(e)}")

        return all_entries, skipped_rows
