# from flask import Flask, render_template, request, redirect, url_for, session, flash
# from flask_pymongo import PyMongo

# app = Flask(__name__)
# app.config["MONGO_URI"] = "mongodb://localhost:27017/VoiceBridgeData"
# app.secret_key = "E@syP@ssw0d@key"  # Change this to a strong secret key
# mongo = PyMongo(app)

# # Collection reference
# users = mongo.db.users 

# @app.route('/')
# def home_default(): 
#     return render_template('home.html')

# @app.route('/login.html')
# def login():
#     return render_template('login.html')

# @app.route('/reg.html')
# def reg():
#     return render_template('reg.html')

# @app.route('/dashboard.html')
# def dashboard():
#     return render_template('dashboard.html')

# @app.route('/about.html')
# def about():
#     return render_template('about.html')

# @app.route('/about-logged-in.html')
# def aboutloggedin():
#     return render_template('about-logged-in.html')

# @app.route('/home.html')
# def home():
#     return render_template('home.html')

# @app.route('/logout')
# def logout():
#     session.clear()
#     flash("You have been logged out.", "info")
#     return redirect(url_for('home'))

# if __name__=="__main__":
#     app.run(debug=True)

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import uuid
from datetime import datetime
import shutil
import os
from transcript import perform_transcription


app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb://localhost:27017/VoiceBridgeData"
app.secret_key = "E@syP@ssw0d@key"  # Change this to a strong secret key
app.config['UPLOAD_FOLDER'] = 'static/uploads/'  # Define the folder to store uploaded files
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}    # File type config for dp
app.config['VIDEO_UPLOAD_FOLDER'] = 'static/upload_vids'  # Folder config for videos
app.config['ALLOWED_VIDEO_EXTENSIONS'] = {'mp4'}    # File type config for videos

mongo = PyMongo(app)

# Collection reference
users = mongo.db.users
transcript_collection = mongo.db.Org_Transcript

@app.route('/')
def home_default(): 
    return render_template('home.html')

@app.route('/login.html')
def login():
    return render_template('login.html')

@app.route('/viewer.html')
def viewer():
    if 'username' in session:
        videos = list(mongo.db.videos.find({"username": session['username']}).sort("upload_time", -1))

        if videos:
            latest_video = videos[0]
            source = os.path.join('static', 'upload_vids', latest_video['filename'])
            destination_folder = os.path.join('static', 'status')
            destination = os.path.join(destination_folder, 'current.mp4')

            os.makedirs(destination_folder, exist_ok=True)

            # Only move if the current.mp4 doesn't exist or is different
            if os.path.exists(source):
                # Remove previous current.mp4 if exists
                if os.path.exists(destination):
                    os.remove(destination)
                shutil.move(source, destination)

        return render_template('viewer.html', videos=videos)
    return redirect(url_for('login'))

@app.route('/reg.html')
def reg():
    return render_template('reg.html')

@app.route('/dashboard.html')
def dashboard():
    if 'username' in session:
        return render_template('dashboard.html', username=session['username'])
    return redirect(url_for('login'))

@app.route('/about.html')
def about():
    return render_template('about.html')

@app.route('/about-logged-in.html')
def about_logged_in():
    return render_template('about-logged-in.html')

@app.route('/home.html')
def home():
    return render_template('home.html')

# Profile Route
@app.route('/profile')
def profile():
    if 'username' in session:
        user = users.find_one({"username": session['username']})
        return render_template('profile.html', user=user)
    return redirect(url_for('login'))

# Function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Profile pic Route
@app.route('/upload_profile_pic', methods=['POST'])
def upload_profile_pic():
    if 'username' in session:
        user = users.find_one({"username": session['username']})
        
        if 'profile_pic' not in request.files:
            flash('No file part', 'danger')
            return redirect(url_for('profile'))

        file = request.files['profile_pic']
        if file.filename == '':
            flash('No selected file', 'danger')
            return redirect(url_for('profile'))

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

            # Delete old profile pic (except default.jpg)
            if user.get('profile_pic') and user['profile_pic'] != 'default.jpg':
                old_file_path = os.path.join(app.config['UPLOAD_FOLDER'], user['profile_pic'])
                if os.path.exists(old_file_path):
                    os.remove(old_file_path)

            # Save new profile picture
            file.save(file_path)

            # Update user's profile picture in the database
            users.update_one(
                {"username": session['username']},
                {"$set": {"profile_pic": filename}}
            )

            flash('Profile picture updated!', 'success')
            return redirect(url_for('profile'))
    
    return redirect(url_for('login'))


# Profile update Route
@app.route('/update_profile', methods=['POST'])
def update_profile():
    if 'username' in session:
        user = users.find_one({"username": session['username']})
        
        # Get updated details from the form
        fullname = request.form.get('fullname')
        email = request.form.get('email')
        username = request.form.get('username')

        # Validate if the username is already taken
        if username != user['username'] and users.find_one({"username": username}):
            flash("Username already exists!", 'danger')
            return redirect(request.url)

        # Update the user's profile details in the database
        users.update_one(
            {"username": session['username']},
            {"$set": {"fullname": fullname, "email": email, "username": username}}
        )
        
        # Update session username if it was changed
        if username != user['username']:
            session['username'] = username

        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile'))
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('home'))

# Register route
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    fullname = data.get('fullname')
    email = data.get('email')
    username = data.get('username')
    password = data.get('password')

    # Priority-based password validation
    if len(password) < 8:
        return jsonify({"success": False, "redirect": False, "message": "Password must be at least 8 characters long."})
    elif not any(char.isdigit() for char in password):
        return jsonify({"success": False, "redirect": False, "message": "Password must include at least one digit."})
    elif not any(char.isupper() for char in password):
        return jsonify({"success": False, "redirect": False, "message": "Password must include at least one uppercase letter."})
    elif not any(char.islower() for char in password):
        return jsonify({"success": False, "redirect": False, "message": "Password must include at least one lowercase letter."})
    elif not any(char in '!@#$%^&*()_+-=[]{}|;:,.<>?/' for char in password):
        return jsonify({"success": False, "redirect": False, "message": "Password must include at least one special character."})

    # Check if email or username already exists
    if users.find_one({"email": email}):
        return jsonify({"success": False, "redirect": False, "message": "Email already registered."})
    if users.find_one({"username": username}):
        return jsonify({"success": False, "redirect": False, "message": "Username already taken."})

    # Hash password before storing
    hashed_password = generate_password_hash(password)

    users.insert_one({
        "fullname": fullname,
        "email": email,
        "username": username,
        "password": hashed_password,
        "profile_pic": "default.jpg"
    })

    return jsonify({"success": True})

# Login route
@app.route('/login', methods=['POST'])
def login_user():
    data = request.json
    identifier = data.get('username')  # can be email or username
    password = data.get('password')

    # Find user with either username or email
    user = users.find_one({
        "$or": [
            {"username": identifier},
            {"email": identifier}
        ]
    })

    if not user or not check_password_hash(user['password'], password):
        return jsonify({"success": False, "message": "Invalid username/email or password."})

    session['username'] = user['username']  # Store the actual username in session
    return jsonify({"success": True})

# Upload video route
@app.route('/upload_video', methods=['POST'])
def upload_video():
    if 'username' not in session:
        return jsonify({"success": False, "message": "Not logged in."}), 403

    if 'video' not in request.files:
        return jsonify({"success": False, "message": "No video uploaded."})

    video = request.files['video']
    if video.filename == '':
        return jsonify({"success": False, "message": "No selected file."})

    if video and video.filename.lower().endswith('.mp4'):
        original_filename = secure_filename(video.filename)  # For display
        filename = f"{uuid.uuid4().hex}_{original_filename}"  # For saving
        os.makedirs(app.config['VIDEO_UPLOAD_FOLDER'], exist_ok=True)
        filepath = os.path.join(app.config['VIDEO_UPLOAD_FOLDER'], filename)
        video.save(filepath)

        mongo.db.videos.insert_one({
            "username": session['username'],
            "filename": filename,
            "original_filename": original_filename,
            "filepath": filepath,
            "upload_time": datetime.now()
        })

        return jsonify({"success": True, "filename": filename, "original_filename": original_filename})

    return jsonify({"success": False, "message": "Invalid file type. Only .mp4 allowed."})

# Transcribe route
@app.route('/transcribe', methods=['POST'])
def transcribe():
    filename = request.form.get('filename')
    if filename:
        source = os.path.join('static', 'upload_vids', filename)
        destination = os.path.join('static', 'status', 'current.mp4')

        # Move and rename the file
        shutil.move(source, destination)

        return redirect(url_for('viewer'))
    return "No file selected", 400

# Translate route
@app.route('/translate', methods=['POST'])
def translate():
    filename = request.form.get('filename')
    if filename:
        source = os.path.join('static', 'upload_vids', filename)
        destination = os.path.join('static', 'status', 'current.mp4')

        shutil.move(source, destination)

        return redirect(url_for('viewer'))
    return "No file selected", 400

@app.route('/process', methods=['POST'])
def process_action():
    source_lang = request.form.get('sourceLang')
    target_lang = request.form.get('targetLang')
    action_type = request.form.get('actionType')

    transcript_text, translation_text = "", ""

    if action_type == 'transcribe':
        transcript_text = perform_transcription('static/status/current.mp4', source_lang)
    elif action_type == 'translate':
        transcript_text = perform_transcription('static/status/current.mp4', source_lang)
        translation_text = perform_translation(transcript_text, source_lang, target_lang)

    return jsonify({
        'transcript': transcript_text,
        'translation': translation_text
    })
    
@app.route('/save_transcript', methods=['POST'])
def save_transcript():
    try:
        data = request.get_json()
        transcript = data.get('transcript', 'transcript not saved by user')
        video_name = data.get('video_name')
        username = data.get('username')
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        transcript_collection.insert_one({
            "username": username,
            "video_name": video_name,
            "transcript": transcript,
            "timestamp": timestamp
        })

        return jsonify({"status": "success", "message": "Transcript saved successfully!"})
    except Exception as e:
        print(f"Error in /save_transcript: {e}")
        return jsonify({"status": "error", "message": "Failed to save transcript."})

if __name__ == "__main__":
    app.run(debug=True)
