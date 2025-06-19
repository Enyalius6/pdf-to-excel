import json
import shutil
from pathlib import Path

def validate_balance_sheet(populated_data):
    """
    Validate basic accounting equation: Assets = Liabilities + Equity
    Returns validation results and metrics
    """
    total_assets = populated_data.get("assets", {}).get("total_assets", 0)
    total_liabilities = populated_data.get("liabilities", {}).get("total_liabilities", 0)
    total_equity = populated_data.get("equity", {}).get("total_equity", 0)
    total_liab_equity = populated_data.get("total_liabilities_and_equity", 0)
    
    calculated_total = total_liabilities + total_equity
    balance_difference = abs(total_assets - calculated_total)
    stated_difference = abs(total_assets - total_liab_equity)
    
    validation_results = {
        "total_assets": total_assets,
        "total_liabilities": total_liabilities,
        "total_equity": total_equity,
        "calculated_total": calculated_total,
        "stated_total": total_liab_equity,
        "balance_difference": balance_difference,
        "stated_difference": stated_difference,
        "is_balanced": balance_difference < 1.0,
        "matches_stated": stated_difference < 1.0
    }
    return validation_results

def count_extracted_fields(populated_data):
    """Count how many fields were successfully extracted (non-zero) and collect missing fields."""
    extracted_count = 0
    total_count = 0
    missing_fields = []

    def count_fields(obj, prefix=""):
        nonlocal extracted_count, total_count, missing_fields
        if isinstance(obj, dict):
            for key, value in obj.items():
                if key in ["company_name", "report_date", "report_title"]:
                    continue
                field_path = f"{prefix}.{key}" if prefix else key
                if isinstance(value, (int, float)):
                    total_count += 1
                    if value != 0:
                        extracted_count += 1
                    else:
                        missing_fields.append(field_path)
                elif isinstance(value, dict):
                    count_fields(value, field_path)
    count_fields(populated_data)
    extraction_rate = (extracted_count / total_count * 100) if total_count > 0 else 0
    return {
        "extracted_fields": extracted_count,
        "total_fields": total_count,
        "extraction_rate": extraction_rate,
        "missing_fields": missing_fields
    }

def main():
    input_path = Path("data") / "populated_balance_sheet.json"
    validated_dir = Path("Validated")
    mistakes_dir = Path("Mistakes detected")
    validated_dir.mkdir(exist_ok=True)
    mistakes_dir.mkdir(exist_ok=True)

    if not input_path.exists():
        print(f"File not found: {input_path}")
        return

    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    validation = validate_balance_sheet(data)
    field_stats = count_extracted_fields(data)

    print("Validation Results:")
    print(json.dumps(validation, indent=2))
    print("Field Extraction Stats:")
    print(json.dumps({k: v for k, v in field_stats.items() if k != "missing_fields"}, indent=2))

    if field_stats["missing_fields"]:
        print("\nFields not matched (missing or zero):")
        for field in field_stats["missing_fields"]:
            print(f"  - {field}")

    if validation["is_balanced"]:
        print("Balance sheet is VALID. Moving to Validated folder.")
        shutil.move(str(input_path), validated_dir / input_path.name)
    else:
        print("Balance sheet is INVALID. Moving to Mistakes detected folder.")
        shutil.move(str(input_path), mistakes_dir / input_path.name)

if __name__ == "__main__":
    main()
