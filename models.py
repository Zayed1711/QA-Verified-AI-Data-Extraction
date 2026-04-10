import os
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, String, Numeric, Text, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

# Load the connection string from your .env file
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("CRITICAL: DATABASE_URL not found in .env file.")

# Connect to the Neon PostgreSQL database
engine = create_engine(DATABASE_URL)
Base = declarative_base()


# --- TABLE 1: The Operations Audit Log ---
class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    file_name = Column(String(255), unique=True, nullable=False)
    status = Column(String(50), nullable=False)
    error_message = Column(Text, nullable=True)
    processed_at = Column(DateTime, default=datetime.utcnow)
    
    # Link to the extracted data
    metrics = relationship("FinancialMetric", back_populates="document", cascade="all, delete-orphan")

# --- TABLE 2: The Extracted Financial Data ---
class FinancialMetric(Base):
    __tablename__ = "financial_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"))
    company_name = Column(String(255), nullable=False)
    total_revenue = Column(Numeric(15, 2), nullable=True)
    net_profit = Column(Numeric(15, 2), nullable=True)
    extracted_at = Column(DateTime, default=datetime.utcnow)
    
    document = relationship("Document", back_populates="metrics")

def init_db():
    """Pushes the Python architecture into the live PostgreSQL database."""
    print("Connecting to cloud database...")
    Base.metadata.create_all(bind=engine)
    print("[\u2713] SUCCESS: Database tables 'documents' and 'financial_metrics' created.")

if __name__ == "__main__":
    init_db()