from PyPDF2 import PdfReader
import re
import csv
import pdfplumber
import json


# Function to remove rule numbers from the text
def remove_rule_numbers(text):
    # Regex pattern to match multiple formats of rule numbers
    rule_number_pattern = r'\b([A-Z]+(?:.\d+)+|[A-Z]+.\d+|[A-Z]{1,2})\b'
    # Remove all matches of the rule numbers
    cleaned_text = re.sub(rule_number_pattern, '', text)
    return cleaned_text


def extract_text_with_pdfplumber(pdf_path, output_txt_path, header_footer_margin=50):
    """
    Extracts text from a PDF using pdfplumber, while preserving bullets, indentation,
    and excluding headers/footers.

    Args:
        pdf_path (str): Path to the PDF file.
        output_txt_path (str): Path to save the extracted text.
        header_footer_margin (int): Margin in points (approx. pixels) to exclude as header/footer.
    """
    def is_in_main_body(y, page_height):
        """Check if y-coordinate is outside header/footer margins."""
        return header_footer_margin < y < page_height - header_footer_margin


    with pdfplumber.open(pdf_path) as pdf, open(output_txt_path, "w", encoding="utf-8") as output_file:
        for page_num, page in enumerate(pdf.pages):
            output_file.write(f"--- Page {page_num + 1} ---\n")  # Separate pages for clarity
            page_height = page.height

            # Extract all text with positional information
            words_with_positions = page.extract_words()

            # Initialize variables to group text intelligently
            grouped_lines = []
            current_line = []

            for word in words_with_positions:
                top = word['top']
                text = word['text']

                # Skip words in the header or footer margin
                if not is_in_main_body(top, page_height):
                    continue

                # Keep grouping words into the same line based on their vertical positions
                if not current_line or abs(top - current_line[-1]['top']) < 5:  # Same line tolerance
                    current_line.append(word)
                else:
                    # Finalize the previous line
                    grouped_lines.append(current_line)
                    current_line = [word]  # Start a new line

            # Add the last line if there's any
            if current_line:
                grouped_lines.append(current_line)

            # Process grouped lines into properly formatted text
            for line in grouped_lines:
                line_text = " ".join(word['text'] for word in line)

                # Preserve bullets or indentations
                if line_text.strip().startswith(("•", "-")):
                    output_file.write(line_text.strip() + "\n")
                else:
                    output_file.write(line_text.strip() + "\n")  # Regular text

    print(f"Extracted text saved to: {output_txt_path}")

def split_text_by_page(text_file, output_json):
    """
    Splits a text file into a dictionary based on page numbers and saves it as JSON.

    Args:
        text_file (str): Path to the extracted text file.
        output_json (str): Path to save the dictionary as a JSON file.
    """
    page_content_dict = {}

    with open(text_file, "r", encoding="utf-8") as file:
        text = file.read()

    # Split text by the recognized page markers (e.g., "--- Page X ---")
    pages = text.split("--- Page ")

    for page in pages:
        if page.strip():  # Skip empty splits
            parts = page.split("---", 1)  # Split into page number and page content
            if len(parts) == 2:
                page_number, content = parts
                page_number = page_number.strip()  # Clean up "Page X"
                page_content_dict[page_number] = content.strip()
            elif len(parts) == 1: # Edge case for 'Page 1'
                page,pagecontent = parts
                page_content_dict[page] = pagecontent.strip()

    # Save the dictionary to a JSON file
    with open(output_json, "w", encoding="utf-8") as json_file:
        json.dump(page_content_dict, json_file, indent=4)
        print(f"Text split by page and saved to {output_json}")

    return page_content_dict


# Path to the PDF file
pdf_path = "../../dataset/docs/FSAE_Rules_2024_V1.pdf" 
output_txt_path  = '../files/cln_rules.txt'
text_json = '../files/cln_rules.json'
# Define header and footer dimensions
header_height = 50  # Points (1 inch = 72 points)
footer_height = 50  # Points

# Extract text from the PDF
cln_text = extract_text_with_pdfplumber(pdf_path, output_txt_path, header_footer_margin=50)
page_content_dict = split_text_by_page(output_txt_path, text_json)