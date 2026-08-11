from flask import Flask, jsonify, request
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from flask_cors import CORS
from dotenv import load_dotenv
from video import VideoProcessor
from models import db, User
import os
import logging

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-key-change-me")
# Render's local filesystem is wiped on every restart/redeploy unless the
# DB lives on an attached persistent Disk -- DATABASE_URL should point
# there in production (e.g. sqlite:////var/data/users.db once a Disk is
# mounted at /var/data). Defaults to the old relative path for local dev.
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///users.db")

# The deployed frontend (Vercel) and backend (Render) are on different
# domains, so the session cookie needs SameSite=None to be sent on those
# cross-site requests. Secure=True requires HTTPS, which is why this only
# applies when actually deployed (Render sets RENDER=true) -- local dev
# runs over plain http and needs the permissive defaults instead.
if os.getenv("RENDER"):
    app.config["SESSION_COOKIE_SAMESITE"] = "None"
    app.config["SESSION_COOKIE_SECURE"] = True

db.init_app(app)

login_manager = LoginManager(app)


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


@login_manager.unauthorized_handler
def unauthorized():
    return jsonify({"error": "Authentication required"}), 401


# Vite dev server runs on 5173; supports_credentials is required for the session cookie
frontend_origins = [o.strip() for o in os.getenv("FRONTEND_ORIGIN", "http://localhost:5173").split(",") if o.strip()]
CORS(app, supports_credentials=True, origins=frontend_origins)

processor = VideoProcessor()

os.makedirs("./videos", exist_ok=True)
os.makedirs("./audios", exist_ok=True)
os.makedirs("./audios/chunks", exist_ok=True)

with app.app_context():
    db.create_all()


@app.route("/api/auth/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400
    if User.query.filter_by(username=username).first():
        return jsonify({"error": "Username already taken"}), 409

    user = User(username=username)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    login_user(user)
    return jsonify({"user": user.to_dict()}), 201


@app.route("/api/auth/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""

    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "Invalid username or password"}), 401

    login_user(user)
    return jsonify({"user": user.to_dict()})


@app.route("/api/auth/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    return jsonify({"ok": True})


@app.route("/api/auth/me", methods=["GET"])
def me():
    if not current_user.is_authenticated:
        return jsonify({"user": None})
    return jsonify({"user": current_user.to_dict()})


@app.route("/api/process", methods=["POST"])
@login_required
def api_process_video():
    try:
        data = request.get_json() or {}
        url = data.get("url")
        method = data.get("method", "extractive")
        percentage = data.get("percentage", 25) / 100.0

        if not url:
            return jsonify({"error": "URL is required"}), 400
        if not url.startswith(("https://www.youtube.com/", "https://youtu.be/")):
            return jsonify({"error": "Please provide a valid YouTube URL"}), 400

        logger.info(f"Processing video: {url} with method: {method}")
        result = processor.process_video(url, method, percentage)
        return jsonify(result)

    except Exception as e:
        logger.error(f"Error processing video: {str(e)}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
