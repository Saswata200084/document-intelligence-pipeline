import boto3
import os
import json
import urllib.parse
import fitz  # PyMuPDF

# AWS Clients
s3_client = boto3.client('s3')
bedrock_client = boto3.client(service_name='bedrock-runtime')

# Env variables
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
    - Triggered when a second PDF is uploaded to S3.
    - Extracts text and generates a summary (like the first function).
    - Fetches the previous summary from OUTPUT_BUCKET.
    - Uses Amazon Bedrock to compare summaries.
    - Stores the comparison result back to S3.
    """

    try:
        # Get S3 event details
        input_bucket = event['Records'][0]['s3']['bucket']['name']
        input_key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'])

        # Download new PDF
        pdf_object = s3_client.get_object(Bucket=input_bucket, Key=input_key)
        pdf_bytes = pdf_object['Body'].read()

        # Extract text
        document_text = extract_text_from_pdf(pdf_bytes)

        # Generate summary prompt
        summary_prompt = (
            "Summarize the following PDF content into clear sections with headings: "
            "Summary, Key Points, and Conclusion.\n\n"
            f"Document Content:\n{document_text[:5000]}"
        )

        # Bedrock request for new summary
        summary_payload = {
            "messages": [
                {"role": "user", "content": [{"text": summary_prompt}]}
            ]
        }

        response = bedrock_client.invoke_model(
            modelId=MODEL_ID,
            contentType="application/json",
            accept="application/json",
            body=json.dumps(summary_payload)
        )
        response_body = json.loads(response['body'].read())
        new_summary = str(response_body.get("output", "")).strip()

        # Fetch previous summary (assuming key naming convention *_summary.json)
        previous_summary_key = input_key.replace(".pdf", "_previous_summary.json")
        try:
            prev_obj = s3_client.get_object(Bucket=OUTPUT_BUCKET, Key=previous_summary_key)
            prev_summary = json.loads(prev_obj['Body'].read().decode("utf-8")).get("summary", "")
        except s3_client.exceptions.NoSuchKey:
            prev_summary = "No previous summary found."

        # Compare prompt
        compare_prompt = (
            "Compare the following two document summaries. Highlight similarities, differences, "
            "and changes in meaning.\n\n"
            f"Previous Summary:\n{prev_summary}\n\n"
            f"New Summary:\n{new_summary}"
        )

        compare_payload = {
            "messages": [
                {"role": "user", "content": [{"text": compare_prompt}]}
            ]
        }

        compare_response = bedrock_client.invoke_model(
            modelId=MODEL_ID,
            contentType="application/json",
            accept="application/json",
            body=json.dumps(compare_payload)
        )
        compare_body = json.loads(compare_response['body'].read())
        comparison_result = str(compare_body.get("output", "")).strip()

        # Save new summary
        new_summary_key = input_key.replace(".pdf", "_summary.json")
        s3_client.put_object(
            Bucket=OUTPUT_BUCKET,
            Key=new_summary_key,
            Body=json.dumps({"summary": new_summary}, indent=2),
            ContentType="application/json"
        )

        # Save comparison
        comparison_key = input_key.replace(".pdf", "_comparison.json")
        s3_client.put_object(
            Bucket=OUTPUT_BUCKET,
            Key=comparison_key,
            Body=json.dumps({"comparison": comparison_result}, indent=2),
            ContentType="application/json"
        )

        return {
            "statusCode": 200,
            "body": f"New summary saved as {new_summary_key} and comparison saved as {comparison_key} in {OUTPUT_BUCKET}"
        }

    except Exception as e:
        return {"statusCode": 500, "error": str(e)}
