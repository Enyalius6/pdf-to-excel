import json
import os
from pathlib import Path
from pdf_processor import process_pdf
from populater import populate_from_files
import pandas as pd
from datetime import datetime
from validator import validate_balance_sheet, count_extracted_fields

def test_single_pdf(pdf_path, template_path):
    """Test extraction accuracy for a single PDF"""
    print(f"\n=== Testing: {pdf_path.name} ===")
    
    try:
        # Step 1: Extract text from PDF
        print("  Step 1: Extracting text from PDF...")
        process_pdf(pdf_path)
        
        # Step 2: Find the generated text file
        base_name = pdf_path.stem
        text_file_path = Path("data") / f"{base_name}_text.txt"
        
        if not text_file_path.exists():
            return {"error": f"Text file not generated: {text_file_path}"}
        
        # Step 3: Populate balance sheet
        print("  Step 2: Populating balance sheet...")
        output_path = Path("data") / f"{base_name}_populated.json"
        populated_data = populate_from_files(template_path, text_file_path, output_path)
        
        # Step 4: Validate results
        print("  Step 3: Validating results...")
        validation = validate_balance_sheet(populated_data)
        field_stats = count_extracted_fields(populated_data)
        
        # Step 5: Compile test results
        test_result = {
            "pdf_name": pdf_path.name,
            "company_name": populated_data.get("company_name", "Unknown"),
            "report_date": populated_data.get("report_date", "Unknown"),
            "validation": validation,
            "field_extraction": field_stats,
            "success": True,
            "timestamp": datetime.now().isoformat()
        }
        
        # Print summary
        print(f"  -> Company: {test_result['company_name']}")
        print(f"  -> Date: {test_result['report_date']}")
        print(f"  -> Fields extracted: {field_stats['extracted_fields']}/{field_stats['total_fields']} ({field_stats['extraction_rate']:.1f}%)")
        print(f"  -> Balance sheet balanced: {validation['is_balanced']}")
        print(f"  -> Balance difference: ${validation['balance_difference']:,.2f}")
        
        return test_result
        
    except Exception as e:
        error_result = {
            "pdf_name": pdf_path.name,
            "error": str(e),
            "success": False,
            "timestamp": datetime.now().isoformat()
        }
        print(f"  -> ERROR: {str(e)}")
        return error_result

def run_accuracy_tests():
    """Run accuracy tests on all PDFs in downloads folder"""
    print("=== BALANCE SHEET EXTRACTION ACCURACY TEST ===")
    
    # Setup paths
    downloads_folder = Path("downloads")
    template_path = Path("template.json")
    results_folder = Path("test_results")
    results_folder.mkdir(exist_ok=True)
    
    # Validate prerequisites
    if not downloads_folder.exists():
        print("ERROR: Downloads folder not found!")
        return
    
    if not template_path.exists():
        print("ERROR: Template.json not found!")
        return
    
    # Find all PDF files
    pdf_files = []
    for root, dirs, files in os.walk(downloads_folder):
        for file in files:
            file_path = Path(root) / file
            if file_path.suffix.lower() == '.pdf':
                pdf_files.append(file_path)
    
    if not pdf_files:
        print("ERROR: No PDF files found in downloads folder!")
        return
    
    print(f"Found {len(pdf_files)} PDF files to test")
    
    # Run tests
    all_results = []
    successful_tests = 0
    
    for i, pdf_path in enumerate(pdf_files, 1):
        print(f"\n{'='*50}")
        print(f"TEST {i}/{len(pdf_files)}")
        print(f"{'='*50}")
        
        result = test_single_pdf(pdf_path, template_path)
        all_results.append(result)
        
        if result.get("success", False):
            successful_tests += 1
    
    # Generate summary report
    generate_test_report(all_results, successful_tests, len(pdf_files))
    
    return all_results

def generate_test_report(results, successful_tests, total_tests):
    """Generate comprehensive test report"""
    print(f"\n{'='*60}")
    print("TEST SUMMARY REPORT")
    print(f"{'='*60}")
    
    # Overall statistics
    success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
    print(f"Total PDFs tested: {total_tests}")
    print(f"Successful extractions: {successful_tests}")
    print(f"Success rate: {success_rate:.1f}%")
    
    # Detailed statistics for successful tests
    successful_results = [r for r in results if r.get("success", False)]
    
    if successful_results:
        print(f"\n--- EXTRACTION ACCURACY ---")
        
        # Calculate average extraction rates
        extraction_rates = [r["field_extraction"]["extraction_rate"] for r in successful_results]
        avg_extraction_rate = sum(extraction_rates) / len(extraction_rates)
        
        # Calculate balance sheet accuracy
        balanced_sheets = sum(1 for r in successful_results if r["validation"]["is_balanced"])
        balance_accuracy = (balanced_sheets / len(successful_results) * 100)
        
        print(f"Average field extraction rate: {avg_extraction_rate:.1f}%")
        print(f"Balance sheet accuracy: {balance_accuracy:.1f}% ({balanced_sheets}/{len(successful_results)} balanced)")
        
        # Show individual results
        print(f"\n--- INDIVIDUAL RESULTS ---")
        for result in successful_results:
            status = "✓ BALANCED" if result["validation"]["is_balanced"] else "✗ UNBALANCED"
            print(f"{result['pdf_name']:<30} | {result['field_extraction']['extraction_rate']:>6.1f}% | {status}")
    
    # Show errors
    failed_results = [r for r in results if not r.get("success", False)]
    if failed_results:
        print(f"\n--- ERRORS ---")
        for result in failed_results:
            print(f"{result['pdf_name']:<30} | ERROR: {result.get('error', 'Unknown error')}")
    
    # Save detailed report to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = Path("test_results") / f"accuracy_report_{timestamp}.json"
    
    report_data = {
        "test_timestamp": datetime.now().isoformat(),
        "summary": {
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "success_rate": success_rate,
            "avg_extraction_rate": avg_extraction_rate if successful_results else 0,
            "balance_accuracy": balance_accuracy if successful_results else 0
        },
        "detailed_results": results
    }
    
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, indent=2)
    
    print(f"\nDetailed report saved to: {report_file}")

def main():
    """Main function to run accuracy tests"""
    try:
        results = run_accuracy_tests()
        print(f"\n=== ACCURACY TESTING COMPLETE ===")
        
        # Optionally create a CSV summary for easy analysis
        create_csv_summary(results)
        
    except Exception as e:
        print(f"Error running accuracy tests: {str(e)}")

def create_csv_summary(results):
    """Create CSV summary for easy analysis in Excel"""
    if not results:
        return
    
    # Prepare data for CSV
    csv_data = []
    for result in results:
        if result.get("success", False):
            row = {
                "PDF_Name": result["pdf_name"],
                "Company": result["company_name"],
                "Report_Date": result["report_date"],
                "Fields_Extracted": result["field_extraction"]["extracted_fields"],
                "Total_Fields": result["field_extraction"]["total_fields"],
                "Extraction_Rate_%": round(result["field_extraction"]["extraction_rate"], 1),
                "Is_Balanced": result["validation"]["is_balanced"],
                "Total_Assets": result["validation"]["total_assets"],
                "Total_Liabilities": result["validation"]["total_liabilities"],
                "Total_Equity": result["validation"]["total_equity"],
                "Balance_Difference": round(result["validation"]["balance_difference"], 2),
                "Success": "Yes"
            }
        else:
            row = {
                "PDF_Name": result["pdf_name"],
                "Company": "ERROR",
                "Report_Date": "ERROR",
                "Fields_Extracted": 0,
                "Total_Fields": 0,
                "Extraction_Rate_%": 0,
                "Is_Balanced": False,
                "Total_Assets": 0,
                "Total_Liabilities": 0,
                "Total_Equity": 0,
                "Balance_Difference": 0,
                "Success": "No",
                "Error": result.get("error", "Unknown error")
            }
        csv_data.append(row)
    
    # Save to CSV
    df = pd.DataFrame(csv_data)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_file = Path("test_results") / f"accuracy_summary_{timestamp}.csv"
    df.to_csv(csv_file, index=False)
    print(f"CSV summary saved to: {csv_file}")

if __name__ == "__main__":
    main()
