import pandas as pd
from datetime import datetime, timedelta
import random

def generate_recurring(description, category, amount, project, frequency_days, count, start_offset_days):
    data = []
    start_date = datetime.now() - timedelta(days=start_offset_days)
    
    for i in range(count):
        date = start_date + timedelta(days=i * frequency_days)
        data.append({
            'Transaction Date': date,
            'Category': category,
            'Description': description,
            'Amount': amount,
            'Project': project
        })
    return data

def main():
    try:
        df = pd.read_excel('sample_budget.xlsx')
        # Filter out previous synthetic data to avoid duplicates if re-run
        # simple heuristic: if description is in our list. 
        # But easier to just reload the base or handle it. 
        # For this task, appending is fine as duplicates just mean more rows.
        print(f"Loaded {len(df)} rows.")
    except Exception as e:
        df = pd.DataFrame(columns=['Transaction Date', 'Category', 'Description', 'Amount', 'Project'])

    new_rows = []

    # Add a Hardware Lease (Dell)
    # Assuming a base row structure for consistency, though generate_recurring is better.
    # For direct insertion, we'll create dicts.
    start_date_dell = datetime(2024, 1, 15)
    for i in range(12):
        date_obj = start_date_dell + timedelta(days=30*i)
        new_rows.append({
            'Transaction Date': date_obj,
            'Description': "Dell Financial Services",
            'Amount': 2500.00,
            'Category': "Hardware",
            'Project': "Infra" # Assuming a project
        })

    # Add a Labour Contractor (Upwork)
    start_date_upwork = datetime(2024, 2, 1)
    for i in range(6):
        date_obj = start_date_upwork + timedelta(days=14*i) # Bi-weekly
        new_rows.append({
            'Transaction Date': date_obj,
            'Description': "Upwork Global Inc - J.Doe",
            'Amount': 1200.00,
            'Category': "Contractors",
            'Project': "Engineering" # Assuming a project
        })

    # 1. Base Contracts (from before)
    new_rows.extend(generate_recurring("AWS Support Enterprise", "Hosting/Cloud", 15000.00, "Platform", 30, 12, 360))
    new_rows.extend(generate_recurring("GitHub Enterprise", "Software", 5000.00, "Engineering", 30, 6, 180 + 5))
    new_rows.extend(generate_recurring("Equinix SY4 Lease", "Datacentre", 120000.00, "Infra", 365, 3, 365*2 + 20))
    new_rows.extend(generate_recurring("Atlassian Jira/Confluence", "Software", 3500.00, "Engineering", 30, 12, 360 - 2))

    # 2. Add BULK contracts to force Vertical Scroll
    vendors = [
        ("Slack Technologies", "Software", 2000, "Comms"),
        ("Zoom Video Comms", "Software", 1500, "Comms"),
        ("Figma Professional", "Software", 800, "Design"),
        ("Adobe Creative Cloud", "Software", 1200, "Design"),
        # MYSTERY VENDOR: No Category provided, should infer "Software"
        ("JetBrains IDE", "", 500, "Engineering"), 
        # MYSTERY VENDOR: No Category, should infer "Hosting/Cloud"
        ("DigitalOcean Droplets", "General", 350, "Infra"),
        # IMPERFECT DATA: Negative Accounting Format
        ("AWS Refund (Imperfect)", "Hosting/Cloud", "(150.00)", "Platform"),
        # IMPERFECT DATA: Dirty Currency String
        ("Dirty Money Input", "Misc", "$  2,500.50 ", "Sales"),
        # IMPERFECT DATA: NaN Description (should become 'Unknown' and not crash)
        (float('nan'), "Misc", 100, "General"),
        ("Datadog Pro", "Observability", 4500, "Platform"),
        ("PagerDuty", "Observability", 1100, "Platform"),
        ("Snowflake Computing", "Data", 8000, "Data"),
        ("Tableau Online", "Data", 2200, "Data"),
        ("Salesforce CRM", "Sales", 6000, "Sales"),
        ("HubSpot Marketing", "Marketing", 3000, "Marketing"),
        ("Twilio API", "Comms", 500, "Product"),
        ("SendGrid Email", "Comms", 300, "Product"),
        ("Cloudflare Enterprise", "Security", 5000, "Infra"),
        ("Okta Identity", "Security", 4000, "Infra"),
        ("1Password Business", "Security", 1000, "Infra"),
        ("Miro Team", "Productivity", 600, "Product"),
        ("Notion Team", "Productivity", 400, "Product"),
        ("Linear App", "Productivity", 300, "Engineering"),
        ("Vercel Pro", "Hosting", 200, "Engineering"),
        ("Netlify Teams", "Hosting", 200, "Engineering")
    ]

    for vendor, cat, amt, proj in vendors:
        # Randomize start dates slightly to create a "waterfall" look in Gantt
        offset = random.randint(30, 400)
        new_rows.extend(generate_recurring(
            description=vendor,
            category=cat,
            amount=amt,
            project=proj,
            frequency_days=30,
            count=random.randint(3, 12),
            start_offset_days=offset
        ))

    # 3. Add Long Range Contract (Horizontal Stretch test)
    # 3 Year Archive Contract starting 2 years ago
    new_rows.extend(generate_recurring(
        description="Iron Mountain Archive",
        category="Admin",
        amount=500.00,
        project="Legal",
        frequency_days=365,
        count=5, # 5 years
        start_offset_days=365*2
    ))

    new_df = pd.DataFrame(new_rows)
    combined = pd.concat([df, new_df], ignore_index=True)
    
    # Sort by date
    combined['Transaction Date'] = pd.to_datetime(combined['Transaction Date'])
    combined.sort_values('Transaction Date', inplace=True)

    combined.to_excel('sample_budget.xlsx', index=False)
    print(f"Saved {len(combined)} rows (added {len(new_rows)}) to sample_budget.xlsx")

if __name__ == "__main__":
    main()
