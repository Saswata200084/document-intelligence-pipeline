# PDF Summarizer with AWS Lambda & Bedrock

This project provides an **AWS Lambda function** that generates a **summary** of uploaded PDF documents.  

When a PDF is uploaded to an input S3 bucket:
1. Lambda is triggered.
2. The PDF is downloaded and text is extracted.
3. The extracted text is sent to **Amazon Bedrock (Claude 3 Nova Pro)**.
4. A structured summary is generated.
5. The summary is saved to an output S3 bucket as JSON.

---

## 🚀 Features
- Automated document summarization
- Uses **Amazon Bedrock (Claude 3 Nova Pro)** for AI summarization
- Stores structured summary in JSON format
- Event-driven workflow with S3 triggers

---

## 📂 Project Structure
