# 🛡️ Zero-Hallucination Data Pipeline

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688.svg)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Cloud-336791.svg)
![Pydantic](https://img.shields.io/badge/Pydantic-v2-E92063.svg)
![Gemini](https://img.shields.io/badge/LLM-Gemini_2.5_Flash-orange.svg)

## Overview
Standard LLM wrappers are dangerous for enterprise operations because they silently hallucinate dates, financial figures, and legal clauses. 

The **Zero-Hallucination Pipeline** is an asynchronous, defensively engineered extraction engine. It intercepts probabilistic AI outputs, forces strict deterministic type-checking via Pydantic, and injects clean data into a secure relational cloud database. If the AI hallucinates, the pipeline catches it, logs the error, and prevents database corruption.

Designed specifically for high-liability sectors (Legal Operations, Logistics, Finance) that require 100% mathematical certainty from unstructured PDFs.

## 🏗️ Core Architecture
1. **The Ingestion Layer:** FastAPI web server accepts asynchronous PDF uploads.
2. **The Extraction Engine:** `asyncio` manages concurrent worker pools to extract raw text and prompt the LLM.
3. **The Gatekeeper:** Pydantic strictly validates the JSON payload. If `net_profit` is returned as a string instead of a float, the payload is rejected.
4. **The Vault:** SQLAlchemy executes an ACID transaction, linking an operations audit log to the extracted metrics in a cloud-hosted PostgreSQL database.

## ✨ Key Features
* **Strict Schema Enforcement:** Zero unstructured data enters the database.
* **Asynchronous Concurrency:** Processes multiple documents simultaneously utilizing `asyncio.Semaphore` for rate-limit protection.
* **ACID Transactions:** Automated rollback mechanisms prevent partial data injection during API drops.
* **Automated Audit Logging:** Every document processed (Success or Error) is logged with its exact failure trace for operations review.

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone [https://github.com/yourusername/zero-hallucination-pipeline.git](https://github.com/yourusername/zero-hallucination-pipeline.git)
cd zero-hallucination-pipeline
