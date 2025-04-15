import torch
import whisper
from moviepy import VideoFileClip
from pydub import AudioSegment
import os
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

def perform_transcription(mp4_path, lang):
    audio_folder = os.path.join("static", "audio")
    os.makedirs(audio_folder, exist_ok=True)

    mp3_path = os.path.join(audio_folder, "temp_audio.mp3")
    video = VideoFileClip(mp4_path)
    video.audio.write_audiofile(mp3_path)
    video.close()

    model = whisper.load_model("large-v3-turbo").to(device)
    print(f"Using device: {device}")
    if(lang=='nan'):
        result = model.transcribe(mp3_path)
    else:
        result = model.transcribe(mp3_path, language=lang)
    print("transcription done.")

    model, utils = torch.hub.load(repo_or_dir='snakers4/silero-vad', model='silero_vad')
    (get_speech_timestamps, _, read_audio, _, _) = utils
    model.to(device)  # Move Silero VAD model to GPU
    print("silero model generated")

    # Check if the input file is MP3 and convert it to WAV
    if mp3_path.lower().endswith(".mp3"):
        wav_file = convert_mp3_to_wav(mp3_path)
    else:
        wav_file = mp3_path  # Assume the input is already a WAV file

    # Step 4: Detect speech regions using Silero VAD
    sampling_rate = 16000  # Silero VAD requires a sampling rate of 16kHz
    audio = read_audio(wav_file, sampling_rate=sampling_rate)
    audio = audio.to(device)

    # Get speech timestamps
    vad_timestamps_sample = get_speech_timestamps(audio, model, sampling_rate=sampling_rate)

    vad_timestamps = [
        {"start": timestamp['start'] / sampling_rate, "end": timestamp['end'] / sampling_rate}
        for timestamp in vad_timestamps_sample
    ]

    print("Detected Speech Timestamps:")
    for timestamp in vad_timestamps:
        print(f"Speech detected from {timestamp['start']:.2f}s to {timestamp['end']:.2f}s")

    adjusted_segments = adjust_timestamps_with_vad(result["segments"], vad_timestamps)
    print("transcription done")

    if wav_file and wav_file != mp3_path and os.path.exists(wav_file):
        try:
            os.remove(wav_file)
            print(f"Temporary WAV file {wav_file} deleted successfully")
        except Exception as e:
            print(f"Error deleting temporary WAV file: {e}")
            
    return adjusted_segments, mp3_path


def convert_mp3_to_wav(mp3_file):
    wav_file = os.path.splitext(mp3_file)[0] + ".wav"
    audio = AudioSegment.from_mp3(mp3_file)
    audio.export(wav_file, format="wav")
    print(f"Converted MP3 to WAV: {wav_file}")
    return wav_file




def combine_contiguous_vad_regions(vad_timestamps):
    if not vad_timestamps:
        return []

    combined_regions = []
    current_region = vad_timestamps[0]

    for region in vad_timestamps[1:]:
        # Ensure timestamps remain in seconds
        gap = region["start"] - current_region["end"]
        
        if gap <= 2:
            # Merge the regions
            current_region["end"] = region["end"]
        else:
            # Add the current region to the result and start a new region
            combined_regions.append(current_region)
            current_region = region

    # Add the last region
    combined_regions.append(current_region) 
    return combined_regions





def adjust_timestamps_with_vad(cleaned_segments, vad_timestamps, max_gap=0.5):
    # Step 1: Combine contiguous VAD regions
    combined_vad_regions = combine_contiguous_vad_regions(vad_timestamps)

    # Step 2: Map combined VAD regions to transcription segments
    adjusted_segments = []

    for segment in cleaned_segments:
        seg_start = round(segment["start"], 2)  # Round to 2 decimal places
        seg_end = round(segment["end"], 2)     # Round to 2 decimal places
        seg_text = segment["text"]

        # Find all VAD regions that overlap with the current segment
        overlapping_vad_regions = []
        for vad_region in combined_vad_regions:
            vad_start = round(vad_region["start"], 2)  # Round to 2 decimal places
            vad_end = round(vad_region["end"], 2)      # Round to 2 decimal places

            # Check if the segment overlaps with the VAD region
            if vad_start < seg_end and vad_end > seg_start:  # Fully relaxed overlap condition
                # Calculate overlap duration
                overlap_start = max(seg_start, vad_start)
                overlap_end = min(seg_end, vad_end)
                overlap_duration = overlap_end - overlap_start

                if overlap_duration > 0:
                    overlapping_vad_regions.append({
                        "vad_start": vad_start,
                        "vad_end": vad_end,
                        "overlap_duration": overlap_duration
                    })

        # Assign the segment to the VAD region with the maximum overlap duration
        if overlapping_vad_regions:
            # Find the VAD region with the maximum overlap duration
            best_vad_region = max(overlapping_vad_regions, key=lambda x: x["overlap_duration"])
            vad_start = best_vad_region["vad_start"]
            vad_end = best_vad_region["vad_end"]

            # Adjust the segment's timestamps based on the best VAD region
            final_start = max(seg_start, vad_start)  # Ensure start is within the VAD region
            final_end = min(seg_end, vad_end)       # Ensure end is within the VAD region

            adjusted_segments.append({
                "start": final_start,
                "end": final_end,
                "text": seg_text
            })
        else:
            print(f"No VAD overlap found for segment [{seg_start:.2f}s -> {seg_end:.2f}s]: '{seg_text}'")
        
    formatted_text = ""
    for segment in adjusted_segments:
        formatted_text += f"[{segment['start']:.2f}s -> {segment['end']:.2f}s] {segment['text']}\n"

    print(formatted_text)
    return adjusted_segments



















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