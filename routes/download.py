from flask import request, redirect, session, abort
import os, mimetypes
import boto3
from werkzeug.utils import secure_filename
from file_utils import normalize_filename, get_user_prefix, get_s3_client, BUCKET_NAME
from . import app

s3 = get_s3_client()

@app.route("/download/<filename>")
def download_file(filename):
    if "username" not in session:
        return redirect("/login")

    safe_filename = secure_filename(normalize_filename(filename))
    key = f"{get_user_prefix()}{safe_filename}"

    # Check if object exists
    try:
        s3.head_object(Bucket=BUCKET_NAME, Key=key)
    except Exception:
        abort(404)

    # Decide inline vs attachment
    ext = safe_filename.split('.')[-1].lower()
    inline_exts = ['txt', 'md', 'py', 'js', 'css', 'html']
    as_attachment = ext not in inline_exts

    mimetype, _ = mimetypes.guess_type(safe_filename)
    content_type = mimetype or "application/octet-stream"

    # Generate presigned URL with proper content disposition
    response = s3.generate_presigned_url(
        "get_object",
        Params={
            "Bucket": BUCKET_NAME,
            "Key": key,
            "ResponseContentType": content_type,
            "ResponseContentDisposition": (
                f'inline; filename="{safe_filename}"' if not as_attachment
                else f'attachment; filename="{safe_filename}"'
            ),
        },
        ExpiresIn=300  # link valid for 5 minutes
    )

    return redirect(response)
