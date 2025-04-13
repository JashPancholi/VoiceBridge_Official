from flask import Flask, render_template, request, redirect,send_file, url_for, session, flash, jsonify,Response
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
from transcript import perform_transcription
from translate import perform_translation
from transvideo import translate_video
import uuid,os,shutil,time,io
from gridfs import GridFS
from bson.objectid import ObjectId
from PIL import Image
from moviepy import VideoFileClip



app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb://localhost:27017/VoiceBridgeData"
app.secret_key = "E@syP@ssw0d@key"  # Change this to a strong secret key
app.config['UPLOAD_FOLDER'] = 'static/uploads/'  # Define the folder to store uploaded files
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}    # File type config for dp
app.config['VIDEO_UPLOAD_FOLDER'] = 'static/upload_vids'  # Folder config for videos
app.config['ALLOWED_VIDEO_EXTENSIONS'] = {'mp4'}    # File type config for videos
app.config['THUMBNAIL_FOLDER'] = 'static/Thumbnail/'
mongo = PyMongo(app)

# Collection reference
users = mongo.db.users
transcript_collection = mongo.db.transcripts
translation_collection = mongo.db.TranslatedResults
fs = GridFS(mongo.db)

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

            if os.path.exists(source):
                if os.path.exists(destination):
                    os.remove(destination)
                shutil.move(source, destination)

        # Check if translated video exists
        translated_video_path = os.path.join('static', 'completed', 'translated_video.mp4')
        translated_video_exists = os.path.exists(translated_video_path)

        return render_template(
            'viewer.html',
            videos=videos,
            translated_video_exists=translated_video_exists
        )
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
    
     # Check if translated_video.mp4 exists and delete it if found
    translated_video_path = 'static/completed/translated_video.mp4'
    if os.path.exists(translated_video_path):
        try:
            os.remove(translated_video_path)
            print(f"Deleted existing file: {translated_video_path}")
        except Exception as e:
            print(f"Error deleting file {translated_video_path}: {str(e)}")
            # Continue with the upload process even if deletion fails
            
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
    voice_choice = request.form.get("Voice")  # Default to John

    filename = "static/status/current.mp4"  # Set the filename for MongoDB use

    # Always start with transcription
    segments, mp3_path = perform_transcription(filename, source_lang)
    formatted_transcript = format_segments_to_text(segments)
        # Now uses the updated perform_translation
    translated_segments = perform_translation(segments, source_lang, target_lang)
    formatted_translation = format_segments_to_text([
        {"start": seg["start"], "end": seg["end"], "text": seg["text"]}
        for seg in translated_segments
    ])   


    if action_type == 'translate':
        cond = translate_video(filename, mp3_path, translated_segments, target_lang, voice_choice)
        if cond:
            print("video translated successfully")

            translated_video_path = "static/completed/translated_video.mp4"
            username = session.get("username")
            metadata = {
                "username": username,
                "source_language": source_lang,
                "target_language": target_lang,
                "datetime": datetime.now()
            }

            video_id = save_translated_video_to_db(translated_video_path, metadata)

            if video_id:
                document = {
                    "username": username,
                    "filename": os.path.basename(filename),
                    "source_language": source_lang,
                    "target_language": target_lang,
                    "datetime": datetime.now(),
                    "translated_text": formatted_translation.strip(),
                    "original_text": formatted_transcript.strip(),
                    "translated_video": video_id
                }
                translation_collection.insert_one(document)
                print(f"Translation and DB insert successful for {filename}")
            else:
                print("Failed to save translated video to DB.")
     
     
    
    elif(action_type == 'transcribe'):
        username = session.get("username")
        try:
            document = {
                "username": username,
                "filename": os.path.basename(filename),
                "source_language": source_lang,
                "target_language": target_lang,
                "datetime": datetime.now(),
                "translated_text": formatted_translation.strip(),
                "original_text": formatted_transcript.strip(),
                "translated_video": None
            }
            translation_collection.insert_one(document)
            print(f"Translation and DB insert successful for {filename}")
        except Exception as e:
                print("Error saving to MongoDB:", e)
    
      
    return jsonify({
        'transcript': formatted_transcript,
        'translation': formatted_translation
    })
    
def format_segments_to_text(segments):
    """Format segments into a readable text with timestamps"""
    formatted_text = ""
    for segment in segments:
        formatted_text += f"[{segment['start']:.2f}s -> {segment['end']:.2f}s] {segment['text']}\n"
    return formatted_text

def save_translated_video_to_db(video_path, metadata):
    try:
        # Check if the video file exists
        if not os.path.exists(video_path):
            print(f"Error: Video file not found at {video_path}")
            return None
            
        # Generate thumbnail
        thumbnail_path = os.path.join(app.config['THUMBNAIL_FOLDER'], f"{metadata['username']}_{int(time.time())}.jpg")
        
        # Create thumbnail directory if it doesn't exist
        os.makedirs(os.path.dirname(thumbnail_path), exist_ok=True)
        
        # Generate thumbnail with better error handling
        thumbnail_result = generate_thumbnail(video_path, thumbnail_path)
        if not thumbnail_result:
            print(f"Warning: Failed to generate thumbnail for {video_path}")
            # Continue without thumbnail
        
        # Open and save video file to GridFS
        with open(video_path, 'rb') as video_file:
            video_id = fs.put(
                video_file,
                filename=os.path.basename(video_path),
                content_type='video/mp4',
                metadata=metadata
            )
            
        # If thumbnail was generated successfully, save it too
        if thumbnail_result and os.path.exists(thumbnail_path):
            try:
                with open(thumbnail_path, 'rb') as thumbnail_file:
                    thumbnail_id = fs.put(
                        thumbnail_file,
                        filename=os.path.basename(thumbnail_path),
                        content_type='image/jpeg',
                        metadata={'video_id': video_id}
                    )
                    
                # Update metadata with thumbnail_id
                mongo.db.fs.files.update_one({'_id': video_id}, {'$set': {'metadata.thumbnail_id': thumbnail_id}})
            except Exception as thumb_error:
                print(f"Error saving thumbnail to GridFS: {thumb_error}")
                # Continue without thumbnail
                
        return video_id
    except Exception as e:
        print(f"Error saving video to GridFS: {e}")
        import traceback
        traceback.print_exc()
        return None


@app.route('/get_video_history', methods=['GET'])
def get_video_history():
    username = session.get("username")
    if not username:
        return jsonify({"error": "User not logged in"}), 401

    # Fetch the user's video history
    history = list(translation_collection.find({"username": username}))
    
    # Prepare the response data
    videos = []
    for entry in history:
        # Fetch the original filename from the videos collection
        video_info = mongo.db.videos.find_one({"filename": entry["filename"]})
        original_filename = video_info["original_filename"] if video_info else entry["filename"]
        
        # Convert ObjectId to string for JSON serialization
        translated_video_id = str(entry.get("translated_video")) if entry.get("translated_video") else None
        
        video_data = {
            "filename": entry["filename"],
            "original_filename": original_filename,
            "source_language": entry["source_language"],
            "target_language": entry["target_language"],
            "datetime": entry["datetime"],
            "translated_text": entry["translated_text"],
            "original_text": entry["original_text"],
            "translated_video_id": translated_video_id,
            "thumbnail_url": url_for('get_thumbnail', video_id=translated_video_id, _external=True) if translated_video_id else None
        }
        
        videos.append(video_data)
    
    return jsonify(videos)


@app.route('/video/<video_id>')
def get_video(video_id):
    try:
        file_id = ObjectId(video_id)
        grid_out = fs.get(file_id)
        
        # Get file size
        file_size = grid_out.length
        
        # Handle range requests
        range_header = request.headers.get('Range', None)
        if range_header:
            byte_start, byte_end = range_header.replace('bytes=', '').split('-')
            byte_start = int(byte_start)
            byte_end = int(byte_end) if byte_end else file_size - 1
            
            # Skip to the requested position
            grid_out.seek(byte_start)
            data = grid_out.read(byte_end - byte_start + 1)
            
            rv = Response(
                data,
                206,
                mimetype=grid_out.content_type,
                direct_passthrough=True
            )
            rv.headers.add('Content-Range', f'bytes {byte_start}-{byte_end}/{file_size}')
        else:
            # Return the whole file
            rv = Response(
                grid_out,
                200,
                mimetype=grid_out.content_type,
                direct_passthrough=True
            )
        
        rv.headers.add('Accept-Ranges', 'bytes')
        rv.headers.add('Content-Disposition', f'inline; filename={grid_out.filename}')
        return rv
    except Exception as e:
        print(f"Error retrieving video: {e}")
        return "Video not found", 404

@app.route('/thumbnail/<video_id>')
def get_thumbnail(video_id):
    try:
        # Find the video document
        video_file = mongo.db.fs.files.find_one({'_id': ObjectId(video_id)})
        if not video_file:
            return "Video not found", 404
            
        # Get the thumbnail_id from the video metadata
        thumbnail_id = video_file.get('metadata', {}).get('thumbnail_id')
        if not thumbnail_id:
            return "Thumbnail not found", 404
            
        # Retrieve the thumbnail file
        thumbnail = fs.get(ObjectId(thumbnail_id))
        
        # Serve the thumbnail
        return send_file(
            io.BytesIO(thumbnail.read()),
            mimetype='image/jpeg',
            as_attachment=False,
            download_name=f"{video_id}_thumbnail.jpg"
        )
    except Exception as e:
        print(f"Error retrieving thumbnail: {e}")
        return "Thumbnail not found", 404


def generate_thumbnail(video_path, output_path, time=2.0):
    """
    Generate a thumbnail from a video file without using cv2.
    
    :param video_path: Path to the video file
    :param output_path: Path to save the thumbnail
    :param time: Time in seconds at which to take the thumbnail (default: 2 seconds)
    :return: Path to the generated thumbnail
    """
    try:
        # Load the video file
        clip = VideoFileClip(video_path)
        
        # Get a frame at the specified time
        frame = clip.get_frame(time)
        
        # Convert the frame to a PIL Image
        image = Image.fromarray(frame)
        
        # Resize the image while maintaining aspect ratio
        max_size = (320, 180)
        image.thumbnail(max_size, Image.LANCZOS)
        
        # Save the thumbnail
        image.save(output_path, "JPEG", quality=85)
        
        # Close the video clip to free up resources
        clip.close()
        
        return output_path
    except Exception as e:
        print(f"Error generating thumbnail: {e}")
        return None
    
if __name__ == "__main__":
    app.run(debug=True)