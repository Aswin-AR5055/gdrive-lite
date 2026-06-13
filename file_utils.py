import unicodedata
import os
from flask import session
import boto3

# Initialize S3 client
def get_s3_client():
    """
    Returns a boto3 S3 client using credentials from environment variables.
    """
    return boto3.client(
        "s3",
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name=os.getenv("AWS_REGION"),
    )

# S3 bucket name
BUCKET_NAME = os.getenv("BUCKET_NAME")

# ---------- Filename Utilities ----------
def normalize_filename(name):
    """
    Normalize unicode filenames to ASCII.
    """
    return unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")

# ---------- S3 Path Utilities ----------
def get_user_prefix():
    """Return the S3 key prefix for this user's files (like a folder)."""
    return f"uploads/{session['username']}/"

def get_trash_prefix():
    """Return the S3 key prefix for this user's trash."""
    return f"trash/{session['username']}/"

# ---------- Storage Info ----------
def get_storage_info():
    """
    Returns the total size of the user's files on S3 in MB.
    Returns (used_mb, max_mb, percent_used)
    max_mb and percent_used can be None or implemented later if needed.
    """
    s3 = get_s3_client()
    total_bytes = 0
    prefix = get_user_prefix()

    try:
        paginator = s3.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=BUCKET_NAME, Prefix=prefix):
            if "Contents" in page:
                total_bytes += sum(obj["Size"] for obj in page["Contents"] if not obj["Key"].endswith("/"))
    except Exception:
        total_bytes = 0

    used_mb = round(total_bytes / (1024 * 1024), 2)
    max_mb = None  # Can set a limit if you want
    percent_used = None
    return used_mb, max_mb, percent_used

# ---------- Optional: Helper to check if object exists ----------
def s3_object_exists(s3_key):
    s3 = get_s3_client()
    try:
        s3.head_object(Bucket=BUCKET_NAME, Key=s3_key)
        return True
    except Exception:
        return False
