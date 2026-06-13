from flask import render_template, session, redirect, request
from . import app
from file_utils import get_storage_info, get_trash_prefix, get_s3_client, BUCKET_NAME
from .profile import get_user_profile
from translations import get_translations

@app.route("/trash")
def trash():
    if "username" not in session:
        return redirect("/login")

    lang = request.args.get("lang", "en")
    translations = get_translations(lang)

    s3 = get_s3_client()
    trash_prefix = get_trash_prefix()

    trashed = []
    try:
        response = s3.list_objects_v2(Bucket=BUCKET_NAME, Prefix=trash_prefix)
        if "Contents" in response:
            trashed = [obj["Key"].replace(trash_prefix, "", 1) for obj in response["Contents"]]
    except Exception:
        trashed = []

    profile = get_user_profile()
    used_mb, max_mb, percent_used = get_storage_info()

    return render_template(
        "trash.html",
        user=session["username"],
        trashed=trashed,
        bio=profile["bio"],
        profile_pic=profile["profile_pic"],
        used_mb=used_mb,
        max_mb=max_mb,
        percent_used=percent_used,
        translations=translations,
        lang=lang,
        active_page="trash",
    )
