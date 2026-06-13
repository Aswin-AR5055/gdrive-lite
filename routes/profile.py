from flask import request, redirect, render_template, session
from . import app
from translations import get_translations
from db_schema import get_db_connection
from werkzeug.utils import secure_filename
from file_utils import get_s3_client
import os, uuid

BUCKET_NAME = "your-bucket-name"
PROFILE_PICS_FOLDER = "profiles"

@app.route("/profile", methods=["GET", "POST"])
def profile():
    if "username" not in session:
        return redirect("/login")

    lang = request.args.get("lang", "en")
    translations = get_translations(lang)

    conn = get_db_connection()
    c = conn.cursor()

    if request.method == "POST":
        bio = request.form.get("bio", "").strip()
        age = request.form.get("age", "")
        try:
            age = int(age) if age else None
        except ValueError:
            age = None

        remove_pic = request.form.get("remove_pic") == "on"
        profile_pic = request.files.get("profile_pic")

        s3 = get_s3_client()

        if profile_pic and profile_pic.filename:
            filename = secure_filename(profile_pic.filename)
            unique_filename = f"{uuid.uuid4().hex}_{filename}"
            s3_key = os.path.join(PROFILE_PICS_FOLDER, unique_filename).replace("\\", "/")

            # Upload new picture
            s3.upload_fileobj(profile_pic, BUCKET_NAME, s3_key)

            c.execute(
                "UPDATE users SET bio=%s, age=%s, profile_pic=%s WHERE username=%s",
                (bio, age, s3_key, session["username"])
            )
        else:
            c.execute(
                "UPDATE users SET bio=%s, age=%s WHERE username=%s",
                (bio, age, session["username"])
            )

        if remove_pic:
            c.execute("SELECT profile_pic FROM users WHERE username=%s", (session["username"],))
            current_pic = c.fetchone()[0]
            if current_pic:
                try:
                    s3.delete_object(Bucket=BUCKET_NAME, Key=current_pic)
                except Exception:
                    pass
            c.execute("UPDATE users SET profile_pic=NULL WHERE username=%s", (session["username"],))

        conn.commit()

    c.execute("SELECT bio, age, profile_pic FROM users WHERE username=%s", (session["username"],))
    row = c.fetchone()
    conn.close()

    return render_template(
        "profile.html",
        user=session["username"],
        bio=row[0] if row else "",
        age=row[1] if row else None,
        profile_pic=row[2] if row else None,  # This will be the S3 key
        translations=translations,
        lang=lang
    )


def get_user_profile():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT bio, profile_pic FROM users WHERE username=%s", (session["username"],))
    row = c.fetchone()
    conn.close()
    return {"bio": row[0], "profile_pic": row[1]} if row else {"bio": "", "profile_pic": None}
