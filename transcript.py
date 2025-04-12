import torch
import whisper
from moviepy import VideoFileClip
from pydub import AudioSegment
import os

def transcribe_video(input_mp4="static/status/current.mp4", output_mp3="static/status/audio_file_OP.mp3"):
    # Load the video file
    video_clip = VideoFileClip(input_mp4)
    audio_clip = video_clip.audio
    audio_clip.write_audiofile(output_mp3)
    audio_clip.close()
    video_clip.close()
    print(f"Audio extracted successfully: {output_mp3}")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

    try:
        whisper_model = whisper.load_model("large-v3", device=device)
        print("Whisper model loaded successfully.")
    except Exception as e:
        print("Error loading Whisper model:", e)
        return None

    try:
        result = whisper_model.transcribe(output_mp3, language="en")
        print("Transcription completed successfully.")
        return result["segments"]
    except Exception as e:
        print("Error during transcription:", e)
        return None
    
def perform_transcription(mp4_path, lang):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    audio_folder = os.path.join("static", "audio")
    os.makedirs(audio_folder, exist_ok=True)

    mp3_path = os.path.join(audio_folder, "temp_audio.mp3")
    video = VideoFileClip(mp4_path)
    video.audio.write_audiofile(mp3_path)
    video.close()

    model = whisper.load_model("large-v3-turbo").to(device)
    if(lang=='nan'):
        result = model.transcribe(mp3_path, language=lang)
    else:
        result = model.transcribe(mp3_path, language=lang)

    return result["segments"]