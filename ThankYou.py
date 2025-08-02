from flask import Flask, redirect, jsonify, render_template, abort, request
from flask_compress import Compress
import os
import json
import markdown
import logging
from logging.handlers import RotatingFileHandler
from colorama import init, Fore, Style

#test!

# Initialize color logging for console
init(autoreset=True)

# Flask setup
app = Flask(__name__)
Compress(app)

# Compression settings
app.config['COMPRESS_ALGORITHM'] = ['br', 'gzip']
app.config['COMPRESS_LEVEL'] = 9
app.config['COMPRESS_MIN_SIZE'] = 100
app.config['COMPRESS_MIMETYPES'] = [
    'text/html',
    'text/css',
    'text/xml',
    'application/json',
    'application/javascript',
    'application/xml',
    'text/plain',
    'text/markdown'
]


# Paths
DATA_FOLDER = "Data"
VIEWS_FILE = os.path.join(DATA_FOLDER, "views.json")
HONOUR_FILE = os.path.join(DATA_FOLDER, "honour.json")
GOODBYES_FILE = os.path.join(DATA_FOLDER, "goodbyes.json")
DIARY_FOLDER = "diaries"
LOG_FILE = "activity.log"

# Ensure folders/files exist
os.makedirs(DATA_FOLDER, exist_ok=True)
os.makedirs(DIARY_FOLDER, exist_ok=True)

for file_path, default in [
    (VIEWS_FILE, {"total_views": 0}),
    (HONOUR_FILE, []),
    (GOODBYES_FILE, [])
]:
    if not os.path.exists(file_path):
        with open(file_path, "w") as f:
            json.dump(default, f)

# Logging configuration
file_handler = RotatingFileHandler(LOG_FILE, maxBytes=1_000_000, backupCount=3, delay=True)
file_handler.setLevel(logging.INFO)
file_formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
file_handler.setFormatter(file_formatter)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Add color to console logs
class ColorFormatter(logging.Formatter):
    def format(self, record):
        msg = super().format(record)
        if record.levelno == logging.INFO:
            return f"{Fore.CYAN}{msg}{Style.RESET_ALL}"
        elif record.levelno == logging.WARNING:
            return f"{Fore.YELLOW}{msg}{Style.RESET_ALL}"
        elif record.levelno == logging.ERROR:
            return f"{Fore.RED}{msg}{Style.RESET_ALL}"
        return msg

console_formatter = ColorFormatter("%(asctime)s [%(levelname)s] %(message)s")
console_handler.setFormatter(console_formatter)

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# IP-aware logging
def log_action(action: str):
    cf_ip = request.headers.get("CF-Connecting-IP")
    x_forwarded_for = request.headers.get("X-Forwarded-For")
    ip_chain = x_forwarded_for.split(",") if x_forwarded_for else []
    public_ip = next((ip.strip() for ip in ip_chain if not ip.strip().startswith(('10.', '172.', '192.168.'))), None)
    real_ip = cf_ip or public_ip or request.remote_addr

    logger.info(f"{action} | Real IP: {real_ip}, CF-IP: {cf_ip}, XFF: {x_forwarded_for}, Remote: {request.remote_addr}")

# View counter
def get_and_increment_views():
    try:
        with open(VIEWS_FILE, "r+") as f:
            data = json.load(f)
            data["total_views"] += 1
            f.seek(0)
            json.dump(data, f)
            f.truncate()
        return data["total_views"]
    except Exception as e:
        logger.error(f"Error updating views: {e}")
        return -1

# Routes
@app.route("/")
def home():
    log_action("Viewed Home Page")
    return render_template("home.html")

@app.route("/thankyou")
def thank_you_page():
    log_action("Viewed Thank You Page")
    return render_template("thankyou.html")

@app.route("/why")
def why_page():
    log_action("Viewed Why Page")
    return render_template("why.html")

@app.route("/honour")
def honour_wall():
    try:
        with open(HONOUR_FILE, "r") as f:
            entries = json.load(f)
    except Exception as e:
        logger.error(f"Error loading honour.json: {e}")
        entries = []
    log_action("Viewed Honour Wall")
    return render_template("honour.html", entries=entries)

@app.route("/diaries")
def diaries_page():
    try:
        entries = []
        for filename in sorted(os.listdir(DIARY_FOLDER), reverse=True):
            if filename.endswith(".md"):
                filepath = os.path.join(DIARY_FOLDER, filename)
                with open(filepath, "r", encoding="utf-8") as f:
                    md_content = f.read()
                    html_content = markdown.markdown(md_content, extensions=["fenced_code", "codehilite"])
                    entries.append({
                        "title": filename.replace(".md", ""),
                        "content": html_content
                    })
        log_action("Viewed Diaries Page")
        return render_template("diaries.html", entries=entries)
    except Exception as e:
        logger.error(f"Error loading diaries: {e}")
        abort(500)

@app.route("/goodbyes")
def goodbyes_page():
    try:
        with open(GOODBYES_FILE, "r") as f:
            entries = json.load(f)
    except Exception as e:
        logger.error(f"Error loading goodbyes.json: {e}")
        entries = []
    log_action("Viewed Goodbyes Page")
    return render_template("goodbyes.html", entries=entries)

@app.route("/api/views")
def views_api():
    views = get_and_increment_views()
    log_action("Viewed /api/views")
    return jsonify({"total_views": views})

@app.route("/parkour")
def parkour_page():
    log_action("Viewed Parkour Page")
    return render_template("parkour.html")

@app.route("/weekly")
def weekly_page():
    log_action("Viewed Weekly Page")
    return render_template("weekly.html")

@app.route("/projects")
def projects_page():
    log_action("Viewed Projects Page")
    return render_template("projects.html")

@app.errorhandler(404)
def page_not_found(e):
    log_action("404 Redirect")
    return redirect("/")

# Run the app
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, threaded=False)

#test