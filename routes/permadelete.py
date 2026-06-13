from flask import redirect, session
from . import app
from werkzeug.utils import secure_filename
from file_utils import normalize_filename, get_s3_client, get_trash_prefix, BUCKET_NAME
import os

@app.route("/permadelete/<filename>")
def permadelete(filename):
    if "username" not in session:
        return redirect("/login")

    safe_filename = secure_filename(normalize_filename(filename))
    trash_prefix = get_trash_prefix()
    s3_key = os.path.join(trash_prefix, safe_filename).replace("\\", "/")

    s3 = get_s3_client()
    s3.delete_object(Bucket=BUCKET_NAME, Key=s3_key)

    return redirect("/dashboard")
