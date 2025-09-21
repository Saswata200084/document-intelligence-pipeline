import boto3
import os
import json
import urllib.parse
import fitz  # PyMuPDF for PDF parsing

# Initialize AWS clients
s3_client = boto3.client('s3')
bedrock_client = boto3.client(service_name='bedrock-runtime')

# Environment variable for destination bucket
OUTPUT_BUCKET = os.environ['OUTPUT_BUCKET']
MODEL_ID = "amazon.nova-pro-v1:0"

def extract_text_from_pdf(pdf_bytes):
    """Extracts text from PDF bytes using PyMuPDF."""
    text = ""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    for page in doc:
        text += page.get_text()
    return text.strip()

def lambda_handler(event, context):
    """
    AWS Lambda function:
    - Triggered when a PDF is uploaded to S3.
    - Extracts text from the PDF.
    - Sends content to Amazon Bedrock for summarization.
    - Saves summary JSON back to S3.
    """

    try:
        # Get S3 event details
        input_bucket = event['Records'][0]['s3']['bucket']['name']
        input_key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'])

        # Download the PDF file
        pdf_object = s3_client.get_object(Bucket=input_bucket, Key=input_key)
        pdf_bytes = pdf_object['Body'].read()

        # Extract text
        document_text = extract_text_from_pdf(pdf_bytes)

        # Prompt for summarization
        prompt_text = (
            "Summarize the following PDF content into clear sections with headings: "
            "Summary, Key Points, and Conclusion.\n\n"
            f"Document Content:\n{document_text[:5000]}"  # limit for safety
        )

        # Prepare payload
        payload = {
            "messages": [
                {
                    "role": "user",
                    "content": [{"text": prompt_text}]
                }
            ]
        }

        # Call Bedrock
        response = bedrock_client.invoke_model(
            modelId=MODEL_ID,
            contentType="application/json",
            accept="application/json",
            body=json.dumps(payload)
        )

        # Extract response
        response_body = json.loads(response['body'].read())
        summary_text = str(response_body.get("output", "")).strip()

        # Define summary file key
        summary_key = input_key.replace(".pdf", "_summary.json")

        # Upload summary to S3
        s3_client.put_object(
            Bucket=OUTPUT_BUCKET,
            Key=summary_key,
            Body=json.dumps({"summary": summary_text}, indent=2),
            ContentType="application/json"
        )

        return {
            "statusCode": 200,
            "body": f"Summary generated and saved as {summary_key} in {OUTPUT_BUCKET}"
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "error": str(e)
        }
