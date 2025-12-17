import pandas as pd
import random
from datetime import datetime, timedelta

# Output file name
OUTPUT_FILE = "second_sample_budget.xlsx"

# Categories and Vendors
categories = [
    "Cloud Infrastructure", "Data Center", "Staffing & Contractors", 
    "Hardware & Networking", "Software Licenses", "Training & Travel"
]

vendors = {
    "Cloud Infrastructure": ["AWS", "Azure", "GCP"],
    "Data Center": ["Equinix", "Digital Realty"],
    "Staffing & Contractors": ["Randstad", "Robert Half", "Toptal"],
    "Hardware & Networking": ["Dell", "Cisco", "Juniper"],
    "Software Licenses": ["Microsoft", "Atlassian", "Slack"],
    "Training & Travel": ["Pluralsight", "Udemy", "Delta Airlines"]
}

# Generate Data
data = []
start_date = datetime(2024, 1, 1)

for _ in range(200): # 200 Transactions
    cat = random.choice(categories)
    vendor = random.choice(vendors[cat])
    
    # Random date within 2024
    date = start_date + timedelta(days=random.randint(0, 364))
    
    # Amount variance (Different from original sample)
    base_amount = random.randint(5000, 50000)
    if cat == "Cloud Infrastructure":
        base_amount *= 3  # Higher cloud costs
    
    # Add some anomalies
    if random.random() < 0.05:
        base_amount *= 5
        
    data.append({
        "Transaction Date": date.strftime("%Y-%m-%d"),
        "Category": cat,
        "Description": f"{vendor} Invoice - {random.randint(1000,9999)}",
        "Amount": round(base_amount, 2),
        "Project": random.choice(["Cloud Migration 2.0", "AI Platform", "Legacy Maintenance"])
    })

# Create DataFrame
df = pd.DataFrame(data)

# Save to Excel
try:
    df.to_excel(OUTPUT_FILE, index=False)
    print(f"Successfully created {OUTPUT_FILE}")
    print(df.head())
except ImportError:
    print("Error: openpyxl or pandas not found. Installing...")
    import subprocess
    subprocess.check_call(["pip", "install", "pandas", "openpyxl"])
    df.to_excel(OUTPUT_FILE, index=False)
    print(f"Successfully created {OUTPUT_FILE} after installing deps")
