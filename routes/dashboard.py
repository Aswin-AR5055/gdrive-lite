from flask import render_template, session, redirect, request
from .profile import get_user_profile
from translations import get_translations
from .favourites import get_user_favourites
from file_utils import get_storage_info, get_user_prefix, get_s3_client, BUCKET_NAME
from . import app

@app.route("/dashboard")
def dashboard():
    if "username" not in session:
        return redirect("/login")

    username = session["username"]
    lang = request.args.get("lang", "en")
    translations = get_translations(lang)
    profile = get_user_profile()
    favourites = get_user_favourites()

    prefix = get_user_prefix()
    s3 = get_s3_client()

    files = []
    file_dates = {}
    file_sizes = {}

    try:
        response = s3.list_objects_v2(Bucket=BUCKET_NAME, Prefix=prefix)
        if "Contents" in response:
            for obj in response["Contents"]:
                key = obj["Key"]
                if key.endswith("/"):
                    continue
                # Get just the filename, not the full path
                filename = key[len(prefix):]  
                files.append(filename)
                file_dates[filename] = obj["LastModified"]
                file_sizes[filename] = round(obj["Size"] / 1024, 2)  # size in KB
    except Exception as e:
        print("Error fetching files from S3:", e)
        files = []

    used_mb, max_mb, percent_used = get_storage_info()

    return render_template(
        "index.html",
        user=username,
        files=files,
        used_mb=used_mb,
        max_mb=max_mb,
        percent_used=percent_used,
        translations=translations,
        lang=lang,
        bio=profile["bio"],
        profile_pic=profile["profile_pic"],
        file_dates=file_dates,
        file_sizes=file_sizes,
        trashed=[],
        favourites=favourites,
        active_page="dashboard"
    )
