import fitz  # PyMuPDF
import os
from pathlib import Path

def extract_tables_from_page(page):
    """Extract tables from a PDF page using fitz"""
    print(f"  Extracting tables from page {page.number + 1}")
    tables = []
    try:
        # Find tables on the page
        tabs = page.find_tables()
        for tab in tabs:
            # Extract table data
            table_data = tab.extract()
            if table_data:
                # Convert table to string format
                table_str = "\n".join(["\t".join([str(cell) if cell else "" for cell in row]) for row in table_data])
                tables.append(table_str)
                print(f"  -> Extracted table with {len(table_data)} rows")
    except Exception as e:
        print(f"  -> Error extracting tables: {str(e)}")
    
    return tables

def process_pdf(pdf_path):
    """Process a single PDF file"""
    print(f"Processing PDF: {pdf_path}")
    
    try:
        # Open PDF
        pdf_document = fitz.open(pdf_path)
        
        # Initialize content containers
        all_text = []
        all_tables = []
        
        # Process each page
        for page_num in range(len(pdf_document)):
            print(f"  Processing page {page_num + 1}/{len(pdf_document)}")
            page = pdf_document[page_num]
            
            # Extract text
            text = page.get_text()
            if text.strip():
                all_text.append(f"=== PAGE {page_num + 1} TEXT ===\n{text}\n")
            
            # Extract tables
            tables = extract_tables_from_page(page)
            for i, table in enumerate(tables):
                all_tables.append(f"=== PAGE {page_num + 1} TABLE {i + 1} ===\n{table}\n")
            
        pdf_document.close()
        
        # Save extracted content
        save_pdf_content(pdf_path, all_text, all_tables)
        
    except Exception as e:
        print(f"Error processing {pdf_path}: {str(e)}")

def save_pdf_content(pdf_path, texts, tables):
    """Save extracted PDF content to files in data folder"""
    # Create data directory
    os.makedirs('data', exist_ok=True)
    
    base_name = pdf_path.stem
    
    # Save all text content
    if texts:
        text_file = Path('data') / f"{base_name}_text.txt"
        with open(text_file, 'w', encoding='utf-8') as f:
            f.write(f"=== TEXT CONTENT FROM {pdf_path.name} ===\n\n")
            f.write("\n".join(texts))
        print(f"  -> Saved text to: {text_file}")
    
    # Save all table content
    if tables:
        table_file = Path('data') / f"{base_name}_tables.txt"
        with open(table_file, 'w', encoding='utf-8') as f:
            f.write(f"=== TABLE CONTENT FROM {pdf_path.name} ===\n\n")
            f.write("\n".join(tables))
        print(f"  -> Saved tables to: {table_file}")

def process_all_pdfs():
    """Process all PDF files in downloads folder"""
    downloads_folder = Path("downloads")
    
    if not downloads_folder.exists():
        print("Downloads folder not found!")
        return
    
    # Find all PDF files
    pdf_files = []
    for root, dirs, files in os.walk(downloads_folder):
        for file in files:
            file_path = Path(root) / file
            if file_path.suffix.lower() in {'.pdf'}:
                pdf_files.append(file_path)
    
    if not pdf_files:
        print("No PDF files found in downloads folder!")
        return
    
    print(f"Found {len(pdf_files)} PDF files to process")
    
    # Process each PDF
    for i, pdf_path in enumerate(pdf_files, 1):
        print(f"\n=== Processing PDF {i}/{len(pdf_files)} ===")
        process_pdf(pdf_path)
    
    print(f"\n=== PDF Processing Complete ===")
    print(f"Processed {len(pdf_files)} PDF files")

def main():
    """Main function to process all PDFs in downloads folder"""
    try:
        process_all_pdfs()
        print("PDF processing complete!")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
