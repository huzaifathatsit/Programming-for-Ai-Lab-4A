from flask import Flask, render_template, request, jsonify, send_file
from scraper import Scraper
import os
import csv

app = Flask(__name__)

# Global scraper instance
scraper_instance = None

@app.route("/", methods=["GET", "POST"])
def index():
    return render_template("index.html")

@app.route("/start", methods=["POST"])
def start():
    global scraper_instance
    url = request.form.get("url")
    pages = int(request.form.get("pages"))

    scraper_instance = Scraper(url, pages)
    return jsonify({"status": "started"})

@app.route("/progress")
def progress():
    global scraper_instance
    if not scraper_instance:
        return jsonify({"progress": 0, "logs": [], "finished": False, "pages_scanned": 0, "emails_found": 0})

    still_running = scraper_instance.step()
    progress = scraper_instance.progress
    logs = scraper_instance.logs[-5:]  # send last 5 logs

    # Get current stats
    pages_scanned = len(scraper_instance.visited)
    emails_found = len(scraper_instance.emails)

    finished = not still_running
    response_data = {
        "progress": progress,
        "logs": logs,
        "finished": finished,
        "pages_scanned": pages_scanned,
        "emails_found": emails_found
    }

    if finished:
        # Include emails in final response
        emails, _ = scraper_instance.get_results()
        response_data["emails"] = emails

    return jsonify(response_data)
@app.route("/download/<filename>")
def download_file(filename):
    if filename not in ["emails.txt", "emails.csv"]:
        return "File not found", 404

    # Use absolute path relative to the app directory
    app_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(app_dir, "output", filename)
    print(f"Attempting to download: {file_path}")
    print(f"Current working directory: {os.getcwd()}")
    print(f"File exists: {os.path.exists(file_path)}")

    if not os.path.exists(file_path):
        return "File not found", 404

    try:
        return send_file(file_path, as_attachment=True, download_name=filename)
    except Exception as e:
        print(f"Error sending file: {e}")
        return str(e), 500

if __name__ == "__main__":
    app.run(debug=True)

