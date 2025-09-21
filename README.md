# PDF Summarizer & Comparator with AWS Lambda & Bedrock

This project provides **two AWS Lambda functions** that work with PDF files and Amazon Bedrock:

---

## 🚀 Features
- **Lambda 1: Summarizer (`lambda_function.py`)**
  - Triggered when a PDF is uploaded to S3.
  - Extracts text from the PDF.
  - Generates a structured summary using Amazon Bedrock.
  - Saves the summary in S3 as JSON.

- **Lambda 2: Comparator (`lambda_compare.py`)**
  - Triggered when another PDF is uploaded.
  - Generates a summary for the new PDF.
  - Fetches the previous summary from S3.
  - Uses Bedrock to **compare both summaries**.
  - Saves both the new summary and the comparison as JSON.

---
