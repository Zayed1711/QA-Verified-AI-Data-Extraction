# Zero-Hallucination AI Data Pipeline

An enterprise-grade, self-healing data extraction pipeline. This tool leverages the Gemini 2.5 Flash API to process unstructured text and PDFs, using a custom Python QA-loop to strictly validate output and force automated retries if the LLM hallucinates or misses data.

## The Problem
Standard AI wrappers are unsafe for enterprise data migration because LLMs fail silently and hallucinate numbers. 

## The Solution
This pipeline acts as a "QA Gatekeeper." It intercepts the AI's JSON output, runs strict validation checks (e.g., ensuring numeric values exist, catching missing keys), and automatically feeds errors back into the prompt to force the AI to correct itself *before* finalizing the data.

## Core Features
* **Automated QA Loop:** Self-corrects AI hallucinations in real-time.
* **Bulk PDF Processing:** Scans directories and extracts unstructured text natively.
* **Deterministic Output:** Forces rigid JSON architecture and exports to clean CSV spreadsheets.

## Tech Stack
* Python 3
* Google GenAI SDK (Gemini 2.5 Flash)
* PyPDF
