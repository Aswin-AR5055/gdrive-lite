from flask import redirect, session
from . import app
from werkzeug.utils import secure_filename
from file_utils import normalize_filename, get_s3_client, get_user_prefix, get_trash_prefix, BUCKET_NAME

@app.route("/trash/<filename>")
def download_trash_file(filename):
    if "username" not in session:
        return redirect("/login")

    s3 = get_s3_client()
    safe_filename = secure_filename(normalize_filename(filename))
    key = f"{get_trash_prefix()}{safe_filename}"

    try:
        url = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": BUCKET_NAME, "Key": key},
            ExpiresIn=3600  # 1 hour
        )
    except s3.exceptions.ClientError:
        return "<h3>File not found in trash</h3><br><a href='/dashboard'>⬅ Back</a>"

    return redirect(url)


@app.route("/delete/<path:filename>")
def delete(filename):
    if "username" not in session:
        return redirect("/login")

    s3 = get_s3_client()
    safe_filename = secure_filename(normalize_filename(filename))
    src_key = f"{get_user_prefix()}{safe_filename}"
    dst_key = f"{get_trash_prefix()}{safe_filename}"

    try:
        # Move file to trash
        s3.copy_object(
            Bucket=BUCKET_NAME,
            CopySource={"Bucket": BUCKET_NAME, "Key": src_key},
            Key=dst_key
        )
        s3.delete_object(Bucket=BUCKET_NAME, Key=src_key)
    except s3.exceptions.ClientError:
        pass

    return redirect("/dashboard")


@app.route("/restore/<filename>")
def restore(filename):
    if "username" not in session:
        return redirect("/login")

    s3 = get_s3_client()
    safe_filename = secure_filename(normalize_filename(filename))
    trash_key = f"{get_trash_prefix()}{safe_filename}"
    user_key = f"{get_user_prefix()}{safe_filename}"

    try:
        # Move file back to user folder
        s3.copy_object(
            Bucket=BUCKET_NAME,
            CopySource={"Bucket": BUCKET_NAME, "Key": trash_key},
            Key=user_key
        )
        s3.delete_object(Bucket=BUCKET_NAME, Key=trash_key)
    except s3.exceptions.ClientError:
        pass

    return redirect("/dashboard")
