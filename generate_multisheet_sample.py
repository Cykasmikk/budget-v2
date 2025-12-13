import pandas as pd
import random
from datetime import datetime, timedelta

# Output file name
OUTPUT_FILE = "sample_budget.xlsx"

def generate_sheet_data(provider, base_amount, num_rows):
    data = []
    start_date = datetime(2024, 1, 1)
    
    services = {
        "AWS": ["EC2", "S3", "RDS", "Lambda", "EKS"],
        "Azure": ["Virtual Machines", "Blob Storage", "SQL Database", "Functions", "AKS"],
        "GCP": ["Compute Engine", "Cloud Storage", "Cloud SQL", "Cloud Functions", "GKE"]
    }
    
    service_list = services.get(provider, ["Service"])
    
    for _ in range(num_rows):
        service = random.choice(service_list)
        date = start_date + timedelta(days=random.randint(0, 364))
        amount = round(base_amount * (random.random() * 0.5 + 0.75), 2) # +/- 25% variance
        
        data.append({
            "Transaction Date": date.strftime("%Y-%m-%d"),
            "Category": "Cloud Infrastructure",
            "Description": f"{provider} {service} - Usage Charge",
            "Amount": amount,
            "Project": f"{provider} Migration"
        })
    return pd.DataFrame(data)

# Create 3 Sheets
df_aws = generate_sheet_data("AWS", 5000, 100)   # ~500k
df_azure = generate_sheet_data("Azure", 4000, 80) # ~320k
df_gcp = generate_sheet_data("GCP", 3000, 60)     # ~180k

# Calculate exact expected total for verification
total_expected = df_aws["Amount"].sum() + df_azure["Amount"].sum() + df_gcp["Amount"].sum()
print(f"Generating Multi-Sheet Excel...")
print(f"AWS Sheet Total:   ${df_aws['Amount'].sum():,.2f}")
print(f"Azure Sheet Total: ${df_azure['Amount'].sum():,.2f}")
print(f"GCP Sheet Total:   ${df_gcp['Amount'].sum():,.2f}")
print(f"GRAND TOTAL:       ${total_expected:,.2f}")

# Write to Excel with multiple sheets
with pd.ExcelWriter(OUTPUT_FILE, engine='openpyxl') as writer:
    df_aws.to_excel(writer, sheet_name='AWS Infra', index=False)
    df_azure.to_excel(writer, sheet_name='Azure Data', index=False)
    df_gcp.to_excel(writer, sheet_name='GCP Analytics', index=False)

print(f"Successfully created {OUTPUT_FILE}")
