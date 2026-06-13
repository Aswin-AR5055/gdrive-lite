from flask import redirect, session
from . import app
from file_utils import get_s3_client, normalize_filename, BUCKET_NAME
from werkzeug.utils import secure_filename
import os

UPLOADS_FOLDER = "uploads"  # S3 prefix for user files

@app.route("/share/<filename>")
def share(filename):
    if "username" not in session:
        return redirect("/login")

    s3 = get_s3_client()
    safe_filename = secure_filename(normalize_filename(filename))
    s3_key = f"{UPLOADS_FOLDER}/{session['username']}/{safe_filename}"

    try:
        # Generate a temporary signed URL (default: 1 hour)
        file_url = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": BUCKET_NAME, "Key": s3_key},
            ExpiresIn=3600
        )
    except Exception as e:
        return f"<h3>Error generating share link: {str(e)}</h3><br><a href='/dashboard'>⬅ Back</a>"

    return f"<h3>Share this link (valid 1 hour):</h3><a href='{file_url}'>{file_url}</a><br><br><a href='/dashboard'>⬅ Back</a>"
