from flask import jsonify, session, request
from file_utils import get_storage_info, get_user_prefix, get_trash_prefix, normalize_filename, get_s3_client, BUCKET_NAME
from werkzeug.utils import secure_filename
import boto3, os
from . import app

s3 = get_s3_client()


@app.route("/delete_selected", methods=["POST"])
def delete_selected():
    if "username" not in session:
        return jsonify({"error": "Not logged in"}), 401

    data = request.get_json()
    files = data.get("files", [])

    user_prefix = get_user_prefix()
    trash_prefix = get_trash_prefix()

    for filename in files:
        safe_filename = secure_filename(normalize_filename(filename))
        src_key = f"{user_prefix}{safe_filename}"
        dst_key = f"{trash_prefix}{safe_filename}"

        # Copy to trash and delete from main
        try:
            s3.copy_object(Bucket=BUCKET_NAME, CopySource={"Bucket": BUCKET_NAME, "Key": src_key}, Key=dst_key)
            s3.delete_object(Bucket=BUCKET_NAME, Key=src_key)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    return jsonify({"success": True})


@app.route("/permadelete_selected", methods=["POST"])
def permadelete_selected():
    if "username" not in session:
        return jsonify({"error": "Not logged in"}), 401

    data = request.get_json()
    files = data.get("files", [])

    trash_prefix = get_trash_prefix()

    for filename in files:
        safe_filename = secure_filename(normalize_filename(filename))
        file_key = f"{trash_prefix}{safe_filename}"

        try:
            s3.delete_object(Bucket=BUCKET_NAME, Key=file_key)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    return jsonify({"success": True})


@app.route("/restore_selected", methods=["POST"])
def restore_selected():
    if "username" not in session:
        return jsonify({"error": "Not logged in"}), 401

    data = request.get_json()
    files = data.get("files", [])

    trash_prefix = get_trash_prefix()
    user_prefix = get_user_prefix()

    for filename in files:
        safe_filename = secure_filename(normalize_filename(filename))
        src_key = f"{trash_prefix}{safe_filename}"
        dst_key = f"{user_prefix}{safe_filename}"

        # Copy back and delete from trash
        try:
            s3.copy_object(Bucket=BUCKET_NAME, CopySource={"Bucket": BUCKET_NAME, "Key": src_key}, Key=dst_key)
            s3.delete_object(Bucket=BUCKET_NAME, Key=src_key)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    return jsonify({"success": True})
