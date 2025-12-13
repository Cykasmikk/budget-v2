import pandas as pd

def get_category_sum(filename, category):
    df = pd.read_excel(filename)
    # Backend logic uses "Category" column
    if "Category" not in df.columns or "Amount" not in df.columns:
        return 0
    
    filtered = df[df["Category"] == category]
    return filtered["Amount"].sum()

file_a = "second_sample_budget.xlsx" # The big one (Old)
cat_sum = get_category_sum(file_a, "Cloud Infrastructure")

print(f"File A ({file_a}) Cloud Infra Sum: {cat_sum:,.2f}")
