from flask import Flask, render_template, request, redirect, url_for, flash
import os
import json

app = Flask(__name__)

# Для безопасности
app.secret_key = "your_secret_key"  # Секретный ключ для сессий и сообщений

# Пути для хранения файлов (в корневой директории)
UPLOAD_FOLDER = '/uploads'
PREVIEW_FOLDER = '/previews'
DATA_FILE = '/data.json'

# Создаем папки, если их нет
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PREVIEW_FOLDER, exist_ok=True)
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump([], f)

# Загрузка данных из JSON
def load_data():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        with open(DATA_FILE, "w") as f:
            json.dump([], f)
        return []

# Сохранение данных в JSON
def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

@app.route("/")
def index():
    videos = load_data()
    return render_template("index.html", videos=videos)

@app.route("/upload", methods=["GET", "POST"])
def upload():
    if request.method == "POST":
        video_file = request.files.get("video")
        preview_file = request.files.get("preview")
        title = request.form.get("title")

        if video_file and video_file.filename.endswith((".mp4", ".webm", ".ogg")):
            video_filename = video_file.filename
            video_filepath = os.path.join(UPLOAD_FOLDER, video_filename)
            video_file.save(video_filepath)

            preview_filename = None
            if preview_file and preview_file.filename.endswith((".jpg", ".jpeg", ".png")):
                preview_filename = preview_file.filename
                preview_filepath = os.path.join(PREVIEW_FOLDER, preview_filename)
                preview_file.save(preview_filepath)

            videos = load_data()
            videos.append({
                "title": title,
                "filename": video_filename,
                "preview": preview_filename,
            })
            save_data(videos)

            return redirect(url_for("index"))

    return render_template("upload.html")

@app.route("/video/<filename>")
def video(filename):
    videos = load_data()
    video = next((v for v in videos if v["filename"] == filename), None)
    if video:
        return render_template("video.html", video=video)
    return "Видео не найдено", 404

@app.route("/admin")
def admin():
    videos = load_data()
    return render_template("admin.html", videos=videos)

@app.route("/admin/delete/<filename>", methods=["POST"])
def delete_video(filename):
    videos = load_data()
    video_to_delete = next((v for v in videos if v["filename"] == filename), None)
    if video_to_delete:
        # Удаление файлов
        video_path = os.path.join(UPLOAD_FOLDER, video_to_delete["filename"])
        if video_to_delete["preview"]:
            preview_path = os.path.join(PREVIEW_FOLDER, video_to_delete["preview"])
            os.remove(preview_path)
        os.remove(video_path)

        # Удаление из данных
        videos = [v for v in videos if v["filename"] != filename]
        save_data(videos)

        flash('Видео удалено успешно!', 'success')
    return redirect(url_for("admin"))

@app.route("/admin/edit/<filename>", methods=["GET", "POST"])
def edit_video(filename):
    videos = load_data()
    video = next((v for v in videos if v["filename"] == filename), None)

    if not video:
        return "Видео не найдено", 404

    if request.method == "POST":
        new_title = request.form.get("title")
        new_preview = request.files.get("preview")

        # Обновление названия
        video["title"] = new_title

        # Обработка нового превью
        if new_preview and new_preview.filename.endswith((".jpg", ".jpeg", ".png")):
            new_preview_filename = new_preview.filename
            new_preview_path = os.path.join(PREVIEW_FOLDER, new_preview_filename)
            new_preview.save(new_preview_path)
            # Удаляем старое превью
            if video["preview"]:
                old_preview_path = os.path.join(PREVIEW_FOLDER, video["preview"])
                os.remove(old_preview_path)
            video["preview"] = new_preview_filename

        # Сохранение изменений в JSON
        save_data(videos)

        flash('Видео обновлено успешно!', 'success')
        return redirect(url_for("admin"))

    return render_template("edit_video.html", video=video)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80, debug=True)
