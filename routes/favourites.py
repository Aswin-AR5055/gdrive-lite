from flask import render_template, redirect, session, request
import os, datetime
import boto3
from db_schema import get_db_connection
from translations import get_translations
from .profile import get_user_profile
from file_utils import get_storage_info, get_user_prefix, normalize_filename, get_s3_client, BUCKET_NAME
from . import app

s3 = get_s3_client()


@app.route('/favourites')
def favourites():
    if "username" not in session:
        return redirect("/login")

    lang = request.args.get("lang", "en")
    translations = get_translations(lang)

    files = get_user_favourites()
    file_dates = {}
    file_sizes = {}

    for f in files:
        key = f"{get_user_prefix()}{f}"
        try:
            # Fetch metadata from S3
            obj = s3.head_object(Bucket=BUCKET_NAME, Key=key)
            file_dates[f] = obj["LastModified"].isoformat()
            file_sizes[f] = obj["ContentLength"]
        except Exception:
            # File missing from S3 → remove from favourites
            remove_favourite(f)
            file_dates[f] = ""
            file_sizes[f] = 0

    profile = get_user_profile()
    used_mb, max_mb, percent_used = get_storage_info()

    return render_template(
        "favourites.html",
        user=session["username"],
        files=files,
        file_dates=file_dates,
        file_sizes=file_sizes,
        bio=profile["bio"],
        profile_pic=profile["profile_pic"],
        used_mb=used_mb,
        max_mb=max_mb,
        percent_used=percent_used,
        translations=translations,
        lang=lang,
        active_page="favourites"
    )


def get_user_favourites():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT filename FROM favourites WHERE username=%s", (session["username"],))
    rows = c.fetchall()
    conn.close()

    existing_files = []
    for row in rows:
        filename = row[0]
        key = f"{get_user_prefix()}{filename}"
        try:
            s3.head_object(Bucket=BUCKET_NAME, Key=key)
            if filename not in existing_files:
                existing_files.append(filename)
        except Exception:
            # If file not in S3 anymore, remove from favourites
            remove_favourite(filename)

    return existing_files


def add_favourite(filename):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT 1 FROM favourites WHERE username=%s AND filename=%s", (session["username"], filename))
    if not c.fetchone():
        c.execute("INSERT INTO favourites (username, filename) VALUES (%s, %s)", (session["username"], filename))
    conn.commit()
    conn.close()


def remove_favourite(filename):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("DELETE FROM favourites WHERE username=%s AND filename=%s", (session["username"], filename))
    conn.commit()
    conn.close()
