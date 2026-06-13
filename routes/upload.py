from flask import session, request, redirect
from werkzeug.utils import secure_filename
from . import app
from file_utils import normalize_filename, get_s3_client, get_user_prefix, BUCKET_NAME
import os

@app.route("/upload", methods=["POST"])
def upload():
    if "username" not in session:
        return redirect("/login")

    files = request.files.getlist("file")
    s3 = get_s3_client()
    prefix = get_user_prefix()

    for file in files:
        if file and file.filename:
            filename = secure_filename(normalize_filename(file.filename))
            s3_key = os.path.join(prefix, filename).replace("\\", "/")
            s3.upload_fileobj(file, BUCKET_NAME, s3_key)

    return redirect("/dashboard")
