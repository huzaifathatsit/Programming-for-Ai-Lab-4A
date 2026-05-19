import os
from flask import Flask, request, render_template

from detection import detect_animals_image, detect_animals_video
from mapping import generate_map

# Create folders
os.makedirs("uploads", exist_ok=True)
os.makedirs("static", exist_ok=True)
os.makedirs("templates", exist_ok=True)

# Flask App
app = Flask(__name__)

# ---------------- FLASK ROUTES ---------------- #

@app.route('/', methods=['GET', 'POST'])
def home():
    count = None
    alert = False
    media_type = None

    if request.method == 'POST':
        file = request.files['file']
        if file:
            filepath = os.path.join('uploads', file.filename)
            file.save(filepath)

            extension = file.filename.split('.')[-1].lower()
            image_formats = ['jpg', 'jpeg', 'png']
            video_formats = ['mp4', 'avi', 'mov']

            # Image Detection
            if extension in image_formats:
                count, alert = detect_animals_image(filepath)
                media_type = 'image'

            # Video Detection
            elif extension in video_formats:
                count, alert = detect_animals_video(filepath)
                media_type = 'video'

            if alert:
                generate_map()

    return render_template(
        'index.html',
        count=count,
        alert=alert,
        media_type=media_type
    )

@app.route('/map')
def map_view():
    with open('templates/map.html', 'r', encoding='utf-8') as f:
        return f.read()

# ---------------- RUN APP ---------------- #
if __name__ == '__main__':
    app.run(debug=True)
