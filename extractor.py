import os
import json
import csv
from pypdf import PdfReader
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Load variables from the .env file
load_dotenv()

# Grab the API key 
GOOGLE_API_KEY = os.getenv("GEMINI_API_KEY")

# Make sure the key actually loaded
if not GOOGLE_API_KEY:
    raise ValueError("🚨 CRITICAL: API Key not found. Please check your .env file.")

# Initialize Client securely
client = genai.Client(api_key=GOOGLE_API_KEY)


client = genai.Client(api_key=GOOGLE_API_KEY)

# PDF Processing 
def extract_text_from_pdf(pdf_path):
    """Opens a PDF and extracts all text into a single string."""
    try:
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
        return text
    except Exception as e:
        return f"Error reading PDF: {e}"

# THE QA validation to check for data integrity and completeness 
def validate_extraction(parsed_data):
    required_keys = ["company_name", "total_revenue", "net_profit"]
    for key in required_keys:
        if key not in parsed_data:
            return False, f"Missing required key: '{key}'"
    for key, value in parsed_data.items():
        if not value or value == "null" or value == "None":
            return False, f"The value for '{key}' is empty. You must extract a value or state 'Not Mentioned'."
    if not any(char.isdigit() for char in str(parsed_data.get("total_revenue", ""))):
        return False, "The 'total_revenue' field does not contain any numbers."
    return True, "Data is clean and verified."

# THE EXTRACTION WITH QA 
def extract_with_qa_loop(messy_text, filename, max_retries=3):
    system_instruction = """
    You are an elite data extraction assistant. Extract:
    - Company Name
    - Total Revenue
    - Net Profit
    Respond ONLY with a valid JSON object. No markdown.
    {"company_name": "", "total_revenue": "", "net_profit": ""}
    """
    attempt = 1
    error_feedback = ""

    while attempt <= max_retries:
        print(f"  [File: {filename}] Attempt {attempt}/{max_retries}...")
        
        prompt = f"Extract data from this text:\n\n{messy_text}"
        if error_feedback:
            prompt += f"\n\nWARNING: Your previous attempt failed QA because: {error_feedback}. Fix this."

        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.0,
                response_mime_type="application/json",
            )
        )

        try:
            parsed_data = json.loads(response.text)
            is_valid, message = validate_extraction(parsed_data)

            if is_valid:
                print(f"  ✅ QA PASS: Data locked in for {filename}.")
                # Add the filename to the data so we know where it came from
                parsed_data['source_file'] = filename 
                return parsed_data
            else:
                print(f"  ❌ QA FAIL: {message} Forcing retry...")
                error_feedback = message 
                attempt += 1

        except json.JSONDecodeError:
            print("  ❌ QA FAIL: Invalid JSON syntax.")
            error_feedback = "Your output was not valid JSON syntax."
            attempt += 1

    print(f"  🚨 CRITICAL: Failed to extract clean data for {filename}.")
    return None

# THE BULK PROCESSOR 
def process_directory(input_folder, output_csv_path):
    print(f"\n--- Starting Bulk Pipeline in '{input_folder}' ---\n")
    
    all_clean_data = []
    
    # Loop through every file in the messy_data folder
    for filename in os.listdir(input_folder):
        file_path = os.path.join(input_folder, filename)
        
        if filename.endswith(".pdf"):
            print(f"Processing PDF: {filename}")
            raw_text = extract_text_from_pdf(file_path)
            
            # Send the text into the QA loop
            clean_data = extract_with_qa_loop(raw_text, filename)
            if clean_data:
                all_clean_data.append(clean_data)
        
        elif filename.endswith(".txt"):
            print(f"Processing Text File: {filename}")
            with open(file_path, 'r', encoding='utf-8') as file:
                raw_text = file.read()
            
            clean_data = extract_with_qa_loop(raw_text, filename)
            if clean_data:
                all_clean_data.append(clean_data)

    # SAVE TO SPREADSHEET 
    if all_clean_data:
        print("\n--- Generating Clean Spreadsheet ---")
        keys = all_clean_data[0].keys() # Get the column headers
        with open(output_csv_path, 'w', newline='', encoding='utf-8') as output_file:
            dict_writer = csv.DictWriter(output_file, fieldnames=keys)
            dict_writer.writeheader()
            dict_writer.writerows(all_clean_data)
        print(f"✅ SUCCESS: All clean data saved to {output_csv_path}")
    else:
        print("\n⚠️ No valid data was extracted.")

# EXECUTION 
if __name__ == "__main__":
    # Define folders
    INPUT_DIR = "messy_data"
    OUTPUT_FILE = "clean_database.csv"
    
    # Check if the folder exists, if not, create it
    if not os.path.exists(INPUT_DIR):
        os.makedirs(INPUT_DIR)
        print(f"Created folder '{INPUT_DIR}'. Please put some .txt or .pdf files in there and run again.")
    else:
        # Run 
        process_directory(INPUT_DIR, OUTPUT_FILE)