"""
Generate Mock Invoices for RLM Showcase
Generates 50 text invoices and 1 policy document.
Invoice #42 will contain a policy violation.
"""

import os
import random
import datetime

OUTPUT_DIR = "mock_data"

def ensure_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

def generate_invoice(inv_id: int) -> str:
    date = (datetime.datetime.now() - datetime.timedelta(days=random.randint(1, 30))).strftime("%Y-%m-%d")
    vendor = random.choice(["Acme Corp", "Globex", "Initech", "Umbrella Corp", "Stark Ind"])
    
    items = []
    total = 0
    
    # Normal items
    if inv_id == 42:
        # The Violation!
        items.append(("Business Class Flight - Paris", 4500.00))
        total += 4500.00
    else:
        # Standard items
        if random.random() > 0.5:
             amt = random.randint(100, 500)
             items.append(("Office Supplies", amt))
             total += amt
        if random.random() > 0.7:
             amt = random.randint(50, 200)
             items.append(("Team Lunch", amt))
             total += amt

    # Format
    content = f"""INVOICE #{inv_id:03d}
Date: {date}
Vendor: {vendor}
----------------------------------------
Description                  Amount
----------------------------------------
"""
    for desc, amt in items:
        content += f"{desc:<28} ${amt:.2f}\n"
    
    content += "----------------------------------------\n"
    content += f"TOTAL                        ${total:.2f}\n"
    
    return content

def generate_policy() -> str:
    return """GLOBAL EXPENSE POLICY 2026
    
1. TRAVEL
- Economy class only for flights under 6 hours.
- Business class requires VP approval.
- Maximum flight cost without prior auth: $2,500.

2. MEALS
- Daily limit: $75 per person.
- No alcohol expensed without client present.

3. APPROVALS
- Invoices > $1,000 require Manager approval.
- Invoices > $5,000 require Director approval.
"""

def main():
    ensure_dir(OUTPUT_DIR)
    
    # Generate Policy
    with open(os.path.join(OUTPUT_DIR, "Policy_Document.txt"), "w") as f:
        f.write(generate_policy())
    
    # Generate 50 Invoices
    all_invoices = []
    for i in range(1, 51):
        content = generate_invoice(i)
        filename = f"Invoice_{i:03d}.txt"
        with open(os.path.join(OUTPUT_DIR, filename), "w") as f:
            f.write(content)
        all_invoices.append(content)
        
    print(f"Generated 50 invoices and policy in '{OUTPUT_DIR}'")

if __name__ == "__main__":
    main()
