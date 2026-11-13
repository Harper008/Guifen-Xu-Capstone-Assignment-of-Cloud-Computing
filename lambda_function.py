import boto3
import io
import os
from PIL import Image
from urllib.parse import unquote_plus

s3 = boto3.client("s3")
OUTPUT_BUCKET = os.environ["OUTPUT_BUCKET"]


def lambda_handler(event, context):
    # Supports an S3 upload event or input from Step Functions.
    if "Records" in event:
        record = event["Records"][0]
        source_bucket = record["s3"]["bucket"]["name"]
        source_key = unquote_plus(record["s3"]["object"]["key"])
    else:
        source_bucket = event["bucket"]
        source_key = event["key"]

    response = s3.get_object(Bucket=source_bucket, Key=source_key)
    image_data = response["Body"].read()

    with Image.open(io.BytesIO(image_data)) as image:
        image.thumbnail((300, 300))
        image_format = (image.format or "JPEG").upper()

        if image_format not in ("JPEG", "PNG"):
            raise ValueError("Please use a JPEG or PNG image.")

        if image_format == "JPEG" and image.mode not in ("RGB", "L"):
            image = image.convert("RGB")

        output = io.BytesIO()
        image.save(output, format=image_format)

    output_key = f"thumbnails/{source_key}"
    content_type = "image/png" if image_format == "PNG" else "image/jpeg"

    s3.put_object(
        Bucket=OUTPUT_BUCKET,
        Key=output_key,
        Body=output.getvalue(),
        ContentType=content_type
    )

    return {
        "status": "SUCCEEDED",
        "sourceBucket": source_bucket,
        "sourceKey": source_key,
        "destinationBucket": OUTPUT_BUCKET,
        "destinationKey": output_key
    }