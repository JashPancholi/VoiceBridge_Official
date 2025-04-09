import torch
import whisper
from transformers import M2M100ForConditionalGeneration, M2M100Tokenizer
import os
from moviepy import VideoFileClip
from pydub import AudioSegment
import app.py

sr="en"
de="fr"

input_mp4 = "stevevid.mp4"

# Output MP3 file
output_mp3 = "audio_file_OP.mp3"

# Load the video file
video_clip = VideoFileClip(input_mp4)

# Extract the audio and save it as an MP3 file
audio_clip = video_clip.audio
audio_clip.write_audiofile(output_mp3)

# Close the clips to free resources
audio_clip.close()
video_clip.close()

print(f"Audio extracted successfully: {output_mp3}")

# Check if CUDA (GPU support) is available
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using device: {device}")






# Step 2: Load Silero VAD model and move it to GPU
model, utils = torch.hub.load(repo_or_dir='snakers4/silero-vad', model='silero_vad')
(get_speech_timestamps, _, read_audio, _, _) = utils
model.to(device)  # Move Silero VAD model to GPU

# Step 3: Convert MP3 to WAV (if necessary)
def convert_mp3_to_wav(mp3_file):
    wav_file = os.path.splitext(mp3_file)[0] + ".wav"
    audio = AudioSegment.from_mp3(mp3_file)
    audio.export(wav_file, format="wav")
    print(f"Converted MP3 to WAV: {wav_file}")
    return wav_file

# Input MP3 file
mp3_file = output_mp3

# Check if the input file is MP3 and convert it to WAV
if mp3_file.lower().endswith(".mp3"):
    wav_file = convert_mp3_to_wav(mp3_file)
else:
    wav_file = mp3_file  # Assume the input is already a WAV file

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


# Load the Whisper model
try:
    whisper_model = whisper.load_model("large-v3-turbo")
    print("Whisper model loaded successfully.")
except Exception as e:
    print("Error loading Whisper model:", e)
    exit()

# Transcribe the audio file
try:
    result = whisper_model.transcribe(output_mp3, language=sr)
    print("Transcription completed successfully.")
    print("Transcription Result (First 5 Segments):", result["segments"][:5])  # Debug: Print first 5 segments
except Exception as e:
    print("Error during transcription:", e)
    exit()

# Extract segments and timestamps
segments = result["segments"]
if not segments:
    print("No transcription segments found. Please check the audio file.")
    exit()
else:
    print(f"Extracted {len(segments)} segments from the transcription.")

# Authenticate and load the M2M-100 model
try:
    model_name = "facebook/m2m100_1.2B" 
    tokenizer = M2M100Tokenizer.from_pretrained(model_name)
    translation_model = M2M100ForConditionalGeneration.from_pretrained(model_name).to(device)
    print("M2M-100 model and tokenizer loaded successfully.")
except Exception as e:
    print("Error loading M2M-100 model:", e)
    exit()


# Process segments in groups of up to 4
 # Index for translated sentences

for i in range(0, len(segments), 4):  # Change step size to 4
    print(f"\nProcessing Group {i//4 + 1} (Segments {i+1} to {min(i + 4, len(segments))})")

    translated_index = 0

    # Combine up to 4 segments into one formatted string
    group_segments = []
    for j in range(i, min(i + 4, len(segments))):  # Handle fewer than 4 segments
        start = segments[j]["start"]
        end = segments[j]["end"]
        text = segments[j]["text"].strip()
        group_segments.append(f" *** {text}")
    
    # Join the formatted segments into a single string
    group_string = "".join(group_segments)
    print("Group String (Input to Translation Model):\n", group_string)

    # translation process starts from here -krish
    # Tokenize, translate, and decode using M2M-100
    try:
        tokenizer.src_lang = sr  # Source language
        inputs = tokenizer(
            group_string,
            return_tensors="pt",
            truncation=True,
            max_length=512 
        ).to(device)

        with torch.no_grad():  # Disable gradient calculation for inference
            translated_tokens = translation_model.generate(
                **inputs,
                forced_bos_token_id=tokenizer.get_lang_id(de),  # Target language
                max_length=512  # Explicitly set max_length for generation
            )

        translated_group = tokenizer.decode(translated_tokens[0], skip_special_tokens=True)
        print("Translated Group (Raw Output from Model):\n", translated_group)
    except Exception as e:
        print("Error during translation:", e)
        continue

    # Split the translated text into individual sentences using the timestamp regex
    translated_sentences = translated_group.split("***")
    translated_sentences = [sentence.strip() for sentence in translated_sentences if sentence.strip()]
    print("Translated Sentences (After Splitting):\n", translated_sentences)

    # Replace the original text in `segment["text"]` with the translated text
    for j in range(i, min(i + 4, len(segments))):
        if translated_index < len(translated_sentences):  # Ensure we don't go out of bounds
            segments[j]["text"] = translated_sentences[translated_index].strip()
            print(f"Segment {j+1}: Updated text to '{segments[j]['text']}'")
            translated_index += 1
        else:
            segments[j]["text"] = ""
            print(f"Segment {j+1}: No more translated sentences available.")

# Function to clean up empty timestamps
def clean_timestamps(segments):
    cleaned_segments = []  # List to store the cleaned segments
    previous_segment = None  # To keep track of the last non-empty segment

    for segment in segments:
        text = segment["text"].strip()  # Strip whitespace to check if the text is empty
        start_time = segment["start"]
        end_time = segment["end"]

        if text:  # If the segment has non-empty text
            if previous_segment is not None:
                # If there was a previous non-empty segment, finalize it
                cleaned_segments.append(previous_segment)
            # Start a new segment
            previous_segment = {"start": start_time, "end": end_time, "text": text}
        else:
            # If the segment is empty, extend the previous segment's end time
            if previous_segment is not None:
                previous_segment["end"] = end_time

    # Append the last non-empty segment if it exists
    if previous_segment is not None:
        cleaned_segments.append(previous_segment)

    return cleaned_segments




# Clean the segments after translation
cleaned_segments = clean_timestamps(segments)


# Print the cleaned segments
print("\nCleaned Segments (Merged Empty Timestamps):")
for segment in cleaned_segments:
    print(f"[{segment['start']:.2f}s -> {segment['end']:.2f}s] {segment['text']}")


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
    """
    Adjust transcription timestamps based on VAD-detected speech regions and combine contiguous regions.
    Args:
        cleaned_segments (list): List of transcription segments with 'start', 'end', and 'text'.
        vad_timestamps (list): List of VAD-detected speech regions with 'start' and 'end' times.
        max_gap (float): Maximum allowed gap (in seconds) between contiguous regions.
    Returns:
        list: Adjusted transcription segments with combined timestamps.
    """
    # Step 1: Combine contiguous VAD regions
    combined_vad_regions = combine_contiguous_vad_regions(vad_timestamps)

    # Debug: Print combined VAD regions
    print("\nCombined VAD Regions:")
    for region in combined_vad_regions:
        print(f"Speech detected from {region['start']:.2f}s to {region['end']:.2f}s")

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

    return adjusted_segments
# Final output with corrected translaition and timestamps is saved here "adjusted_segments" -Krish
adjusted_segments = adjust_timestamps_with_vad(cleaned_segments, vad_timestamps)

# Print the adjusted segments
print("Adjusted Segments:")
for segment in adjusted_segments:
    print(f"[{segment['start']:.2f}s -> {segment['end']:.2f}s] {segment['text']}")

"""

"""
