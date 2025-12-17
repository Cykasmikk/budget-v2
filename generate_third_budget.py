import pandas as pd
import random
from datetime import datetime, timedelta

# Output file name
OUTPUT_FILE = "third_sample_budget.xlsx"

def generate_data(category, projects, services, base_amount, num_rows):
    data = []
    start_date = datetime(2024, 1, 1)
    
    for _ in range(num_rows):
        project = random.choice(projects)
        service = random.choice(services)
        date = start_date + timedelta(days=random.randint(0, 364))
        amount = round(base_amount * (random.random() * 0.6 + 0.7), 2) 
        
        data.append({
            "Transaction Date": date.strftime("%Y-%m-%d"),
            "Category": category,
            "Description": f"{service} - {project}",
            "Amount": amount,
            "Project": project
        })
    return pd.DataFrame(data)

# Sheet 1: R&D (New Category)
df_rnd = generate_data(
    "Research & Development",
    ["Project Phoenix", "Quantum Encryption Study"],
    ["Lab Equipment", "Prototyping Materials", "External Consultants"],
    8000, 150 # ~$1.2M
)

# Sheet 2: Legal (New Category)
df_legal = generate_data(
    "Legal & Compliance",
    ["ISO 27001 Audit", "GDPR Compliance"],
    ["Baker McKenzie Retainer", "Compliance Software", "Audit Fees"],
    12000, 50 # ~$600k
)

# Sheet 3: Facilities (New Category)
df_facilities = generate_data(
    "Facilities Management",
    ["Melbourne Office Expansion", "Sydney HQ Refit"],
    ["Construction Services", "Furniture Procurement", "HVAC Upgrade"],
    15000, 80 # ~$1.2M
)

# Calculate totals
total_rnd = df_rnd["Amount"].sum()
total_legal = df_legal["Amount"].sum()
total_facilities = df_facilities["Amount"].sum()
grand_total = total_rnd + total_legal + total_facilities

print(f"Generating Third Distinct Budget...")
print(f"R&D Total:        ${total_rnd:,.2f}")
print(f"Legal Total:      ${total_legal:,.2f}")
print(f"Facilities Total: ${total_facilities:,.2f}")
print(f"GRAND TOTAL:      ${grand_total:,.2f}")

with pd.ExcelWriter(OUTPUT_FILE, engine='openpyxl') as writer:
    df_rnd.to_excel(writer, sheet_name='R&D', index=False)
    df_legal.to_excel(writer, sheet_name='Legal', index=False)
    df_facilities.to_excel(writer, sheet_name='Facilities', index=False)

print(f"Successfully created {OUTPUT_FILE}")
