from flask import session, redirect, send_file, request
from . import app
from file_utils import get_s3_client, get_user_prefix, normalize_filename
import zipfile, io

BUCKET_NAME = "your-bucket-name"

@app.route("/download_zip", methods=["POST"])
def download_zip():
    if "username" not in session:
        return redirect("/login")

    files = request.form.getlist("selected_files")
    if not files:
        return redirect("/dashboard")

    s3 = get_s3_client()
    user_prefix = get_user_prefix()

    # Create an in-memory ZIP
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
        for f in files:
            safe_filename = normalize_filename(f)
            s3_key = f"{user_prefix}{safe_filename}"
            try:
                obj = s3.get_object(Bucket=BUCKET_NAME, Key=s3_key)
                zipf.writestr(safe_filename, obj['Body'].read())
            except Exception:
                pass  # Skip missing files

    zip_buffer.seek(0)
    return send_file(
        zip_buffer,
        mimetype="application/zip",
        as_attachment=True,
        download_name="files.zip"
    )
