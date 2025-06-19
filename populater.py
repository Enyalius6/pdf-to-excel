import json
import re
from pathlib import Path

def clean_number(value_str):
    """
    Clean and convert a string value to float
    Handles accounting format where negative numbers are in parentheses: (1,250,000)
    Also removes commas and whitespace from numbers
    """
    if not value_str:
        return 0
    
    # Remove commas and whitespace from the number string
    # Example: "1,250,000" becomes "1250000"
    cleaned = re.sub(r'[,\s]', '', value_str)
    
    # Handle negative values in parentheses - ACCOUNTING FORMAT
    # In accounting, negative numbers are often shown as (1,250,000) instead of -1,250,000
    # This is where we detect brackets and convert to negative
    if cleaned.startswith('(') and cleaned.endswith(')'):
        # Remove the parentheses and add a minus sign
        # Example: "(1250000)" becomes "-1250000"
        cleaned = '-' + cleaned[1:-1]
    
    try:
        return float(cleaned)
    except ValueError:
        # If conversion fails, return 0 as default
        return 0

def extract_value_from_text(text, pattern):
    """
    Extract a numeric value using regex pattern
    Uses multiple regex flags for flexible matching across lines and case-insensitive
    """
    match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE | re.DOTALL)
    if match:
        # Extract the captured group (the number) and clean it
        return clean_number(match.group(1))
    return 0

def populate_balance_sheet(text_content, template):
    """
    Populate the balance sheet template with values extracted from PDF text
    This function uses regex patterns to find account numbers and their corresponding values
    """
    populated = template.copy()
    
    # === COMPANY INFORMATION EXTRACTION ===
    # Extract company info - look for pattern like "XYZ, Inc."
    company_match = re.search(r'([A-Z]+),?\s*Inc\.?', text_content)
    if company_match:
        populated["company_name"] = company_match.group(1).strip()
    
    # Extract report date - look for "As of December 31, 2018" pattern
    date_match = re.search(r'As of\s+([^\n]+)', text_content, re.IGNORECASE)
    if date_match:
        populated["report_date"] = date_match.group(1).strip()
    
    # === ASSETS SECTION ===
    # Current Assets - Cash Components
    # Pattern explanation: r'1010\s+Checking\s+(\d+(?:,\d+)*)'
    # - 1010: Account number
    # - \s+: One or more whitespace characters
    # - Checking: Account name
    # - \s+: More whitespace
    # - (\d+(?:,\d+)*): Capture group for number with optional commas
    
    populated["assets"]["current_assets"]["cash"]["1010_checking"] = extract_value_from_text(
        text_content, r'1010\s+Checking\s+(\d+(?:,\d+)*)'
    )
    populated["assets"]["current_assets"]["cash"]["1020_savings"] = extract_value_from_text(
        text_content, r'1020\s+Savings\s+(\d+(?:,\d+)*)'
    )
    populated["assets"]["current_assets"]["cash"]["1030_petty_cash"] = extract_value_from_text(
        text_content, r'1030\s+Petty\s+Cash\s+(\d+(?:,\d+)*)'
    )
    # Total cash is the sum of all cash accounts
    populated["assets"]["current_assets"]["cash"]["total_cash"] = extract_value_from_text(
        text_content, r'Total\s+Cash\s+(\d+(?:,\d+)*)'
    )
    
    # Other Current Assets
    populated["assets"]["current_assets"]["1100_accounts_receivable"] = extract_value_from_text(
        text_content, r'1100\s+Accounts\s+Receivable\s+(\d+(?:,\d+)*)'
    )
    populated["assets"]["current_assets"]["1200_work_in_process"] = extract_value_from_text(
        text_content, r'1200\s+Work\s+in\s+Process\s+(\d+(?:,\d+)*)'
    )
    
    # Other Current Assets - Subcategory
    populated["assets"]["current_assets"]["other_current_assets"]["1310_prepaid_rent"] = extract_value_from_text(
        text_content, r'1310\s+Prepaid\s+Rent\s+(\d+(?:,\d+)*)'
    )
    populated["assets"]["current_assets"]["other_current_assets"]["1320_prepaid_liability_insurance"] = extract_value_from_text(
        text_content, r'1320\s+Prepaid\s+Liability\s+Insurance\s+(\d+(?:,\d+)*)'
    )
    populated["assets"]["current_assets"]["other_current_assets"]["total_other_current_assets"] = extract_value_from_text(
        text_content, r'Total\s+Other\s+Current\s+Assets\s+(\d+(?:,\d+)*)'
    )
    
    # Total Current Assets - Sum of all current asset categories
    populated["assets"]["current_assets"]["total_current_assets"] = extract_value_from_text(
        text_content, r'Total\s+Current\s+Assets\s+(\d+(?:,\d+)*)'
    )
    
    # === NON-CURRENT ASSETS (Fixed Assets) ===
    # These are long-term assets like equipment, real estate, etc.
    populated["assets"]["non_current_assets"]["1400_net_computer_equipment"] = extract_value_from_text(
        text_content, r'1400\s+Net\s+Computer\s+Equipment\s+(\d+(?:,\d+)*)'
    )
    populated["assets"]["non_current_assets"]["1500_net_furniture_fixtures_equipment"] = extract_value_from_text(
        text_content, r'1500\s+Net\s+Furniture,\s+Fixtures,\s+&\s+Equipment\s+(\d+(?:,\d+)*)'
    )
    populated["assets"]["non_current_assets"]["1600_net_field_equipment"] = extract_value_from_text(
        text_content, r'1600\s+Net\s+Field\s+Equipment\s+(\d+(?:,\d+)*)'
    )
    populated["assets"]["non_current_assets"]["1700_net_real_estate"] = extract_value_from_text(
        text_content, r'1700\s+Net\s+Real\s+Estate\s+(\d+(?:,\d+)*)'
    )
    populated["assets"]["non_current_assets"]["1800_net_leasehold_improvements"] = extract_value_from_text(
        text_content, r'1800\s+Net\s+Leasehold\s+Improvements\s+(\d+(?:,\d+)*)'
    )
    populated["assets"]["non_current_assets"]["1900_other_assets"] = extract_value_from_text(
        text_content, r'1900\s+Other\s+Assets\s+(\d+(?:,\d+)*)'
    )
    populated["assets"]["non_current_assets"]["total_non_current_assets"] = extract_value_from_text(
        text_content, r'Total\s+Non-Current\s+Assets\s+(\d+(?:,\d+)*)'
    )
    
    # TOTAL ASSETS - Sum of current and non-current assets
    populated["assets"]["total_assets"] = extract_value_from_text(
        text_content, r'Total\s+Assets\s+(\d+(?:,\d+)*)'
    )
    
    # === LIABILITIES SECTION ===
    # Current Liabilities (due within one year)
    populated["liabilities"]["current_liabilities"]["2000_accounts_payable"] = extract_value_from_text(
        text_content, r'2000\s+Accounts\s+Payable\s+(\d+(?:,\d+)*)'
    )
    populated["liabilities"]["current_liabilities"]["2100_deferred_taxes"] = extract_value_from_text(
        text_content, r'2100\s+Deferred\s+Taxes\s+(\d+(?:,\d+)*)'
    )
    populated["liabilities"]["current_liabilities"]["2200_line_of_credit_borrowing"] = extract_value_from_text(
        text_content, r'2200\s+Line\s+of\s+Credit\s+Borrowing\s+(\d+(?:,\d+)*)'
    )
    populated["liabilities"]["current_liabilities"]["2300_current_portion_long_term_debt"] = extract_value_from_text(
        text_content, r'2300\s+Current\s+Portion\s+of\s+Long-Term\s+Debt\s+(\d+(?:,\d+)*)'
    )
    populated["liabilities"]["current_liabilities"]["2400_other_current_liabilities"] = extract_value_from_text(
        text_content, r'2400\s+Other\s+Current\s+Liabilities\s+(\d+(?:,\d+)*)'
    )
    populated["liabilities"]["current_liabilities"]["total_current_liabilities"] = extract_value_from_text(
        text_content, r'Total\s+Current\s+Liabilities\s+(\d+(?:,\d+)*)'
    )
    
    # Non-Current Liabilities (long-term debt, due after one year)
    populated["liabilities"]["non_current_liabilities"]["2500_long_term_debt"] = extract_value_from_text(
        text_content, r'2500\s+Long-Term\s+Debt\s+(\d+(?:,\d+)*)'
    )
    populated["liabilities"]["non_current_liabilities"]["2600_other_liabilities"] = extract_value_from_text(
        text_content, r'2600\s+Other\s+Liabilities\s+(\d+(?:,\d+)*)'
    )
    populated["liabilities"]["non_current_liabilities"]["total_non_current_liabilities"] = extract_value_from_text(
        text_content, r'Total\s+Non-Current\s+Liabilities\s+(\d+(?:,\d+)*)'
    )
    
    # TOTAL LIABILITIES - Sum of current and non-current liabilities
    populated["liabilities"]["total_liabilities"] = extract_value_from_text(
        text_content, r'Total\s+Liabilities\s+(\d+(?:,\d+)*)'
    )
    
    # === EQUITY SECTION ===
    # Owner's equity in the company
    populated["equity"]["3000_capital_stock"] = extract_value_from_text(
        text_content, r'3000\s+Capital\s+Stock\s+(\d+(?:,\d+)*)'
    )
    
    # SPECIAL CASE: Treasury Stock - Always negative, shown in parentheses
    # This is the SECOND place where brackets are handled as negative
    # Treasury stock represents company's own shares that were bought back
    # Pattern looks for: "3100 Treasury Stock (1,250,000)"
    treasury_match = re.search(r'3100\s+Treasury\s+Stock\s+\((\d+(?:,\d+)*)\)', text_content, re.IGNORECASE)
    if treasury_match:
        # Explicitly make it negative since treasury stock reduces equity
        # The clean_number function would also handle this, but we're being explicit here
        populated["equity"]["3100_treasury_stock"] = -clean_number(treasury_match.group(1))
    
    # Retained earnings - accumulated profits kept in the business
    populated["equity"]["3200_retained_earnings"] = extract_value_from_text(
        text_content, r'3200\s+Retained\s+Earnings\s+(\d+(?:,\d+)*)'
    )
    populated["equity"]["total_equity"] = extract_value_from_text(
        text_content, r'Total\s+Equity\s+(\d+(?:,\d+)*)'
    )
    
    # === BALANCE SHEET EQUATION CHECK ===
    # Total Liabilities + Equity should equal Total Assets
    populated["total_liabilities_and_equity"] = extract_value_from_text(
        text_content, r'Total\s+Liabilities\s+and\s+Equity\s+(\d+(?:,\d+)*)'
    )
    
    return populated

def populate_from_files(template_path, text_file_path, output_path):
    """Populate template from files and save result"""
    # Load template
    with open(template_path, 'r', encoding='utf-8') as f:
        template = json.load(f)
    
    # Load text content
    with open(text_file_path, 'r', encoding='utf-8') as f:
        text_content = f.read()
    
    # Populate the template
    populated = populate_balance_sheet(text_content, template)
    
    # Save populated JSON
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(populated, f, indent=2)
    
    print(f"Populated balance sheet saved to: {output_path}")
    return populated

def main():
    """Main function to populate balance sheet from extracted data"""
    template_path = Path("template.json")
    text_file_path = Path("data/Balance-Sheet-Example_text.txt")
    output_path = Path("data/populated_balance_sheet.json")
    
    if not template_path.exists():
        print(f"Template file not found: {template_path}")
        return
    
    if not text_file_path.exists():
        print(f"Text file not found: {text_file_path}")
        return
    
    try:
        populated = populate_from_files(template_path, text_file_path, output_path)
        
        # Print summary
        print("\n=== Population Summary ===")
        print(f"Company: {populated['company_name']}")
        print(f"Report Date: {populated['report_date']}")
        print(f"Total Assets: ${populated['assets']['total_assets']:,.2f}")
        print(f"Total Liabilities: ${populated['liabilities']['total_liabilities']:,.2f}")
        print(f"Total Equity: ${populated['equity']['total_equity']:,.2f}")
        print(f"Total Liabilities and Equity: ${populated['total_liabilities_and_equity']:,.2f}")
        
    except Exception as e:
        print(f"Error populating balance sheet: {str(e)}")

if __name__ == "__main__":
    main()
