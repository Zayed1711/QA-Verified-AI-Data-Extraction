import asyncio
import os
import json
from pypdf import PdfReader
from google import genai
from google.genai import types
from dotenv import load_dotenv

# --- DATABASE & VALIDATION IMPORTS ---
from pydantic import BaseModel, Field, ValidationError
from typing import Optional
from sqlalchemy.orm import sessionmaker
from models import engine, Document, FinancialMetric

# Initialize Environment and Client
load_dotenv()
client = genai.Client()

# Creates a secure session factory to talk to PostgreSQL
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

CONCURRENCY_LIMIT = 15

# --- THE PYDANTIC GATEKEEPER ---
class FinancialExtraction(BaseModel):
    company_name: str = Field(..., description="The name of the company")
    total_revenue: Optional[float] = Field(None, description="Total revenue as a number")
    net_profit: Optional[float] = Field(None, description="Net profit as a number")

async def process_document(file_name, semaphore):
    """Reads a single PDF, extracts data, and forces strict validation."""
    async with semaphore:
        file_path = os.path.join("messy_data", file_name)
        
        try:
            reader = PdfReader(file_path)
            raw_text = "".join([page.extract_text() for page in reader.pages])

            prompt = f"""
            Extract the financial data from this document.
            You must return ONLY a raw JSON object. No markdown formatting. No conversational text.
            If a value is missing, return null. Do not hallucinate numbers.
            
            Required keys: "company_name", "total_revenue", "net_profit"
            
            Data:
            {raw_text}
            """

            response = await client.aio.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.0
                )
            )

            raw_json = json.loads(response.text)
            
            # --- VALIDATION LAYER ---
            validated_data = FinancialExtraction(**raw_json)
            extracted_data = validated_data.model_dump()
            extracted_data["source_file"] = file_name
            extracted_data["status"] = "SUCCESS"
            
            print(f"[\u2713] Clean extraction and validation completed for: {file_name}")
            return extracted_data

        except ValidationError as e:
            print(f"[\u26A0] Validation Error in {file_name}: AI hallucinated incorrect data types.")
            return {"source_file": file_name, "status": "ERROR", "error_message": str(e)}
        except Exception as e:
            print(f"[\u2717] Error processing {file_name}: {str(e)}")
            return {"source_file": file_name, "status": "ERROR", "error_message": str(e)}


async def main():
    print("--- Initiating Async Data Pipeline ---")
    
    data_dir = "messy_data"
    if not os.path.exists(data_dir):
        print(f"CRITICAL: '{data_dir}' folder not found.")
        return

    pdf_files = [f for f in os.listdir(data_dir) if f.endswith(".pdf")]
    print(f"Found {len(pdf_files)} documents to process. Booting {CONCURRENCY_LIMIT} concurrent workers...\n")

    semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)
    tasks = [process_document(f, semaphore) for f in pdf_files]

    # Run extraction
    results = await asyncio.gather(*tasks)

    # --- INJECT DATA INTO POSTGRESQL CLOUD VAULT ---
    print("\n--- Securing Data in PostgreSQL ---")
    db = SessionLocal()
    
    try:
        success_count = 0
        error_count = 0
        
        for res in results:
            # 1. Audit Log
            doc_record = Document(
                file_name=res["source_file"],
                status=res["status"],
                error_message=res.get("error_message")
            )
            db.add(doc_record)
            db.flush() 
            
            # 2. Financial Metrics
            if res["status"] == "SUCCESS":
                metric_record = FinancialMetric(
                    document_id=doc_record.id, 
                    company_name=res.get("company_name", "UNKNOWN"),
                    total_revenue=res.get("total_revenue"),
                    net_profit=res.get("net_profit")
                )
                db.add(metric_record)
                success_count += 1
            else:
                error_count += 1
                
        db.commit()
        print(f"[\u2713] Transaction Complete: {success_count} clean records secured, {error_count} errors logged.")
        
    except Exception as e:
        db.rollback() 
        print(f"[\u2717] CRITICAL DATABASE ERROR: Transaction Rolled Back. {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(main())