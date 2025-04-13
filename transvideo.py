import torch
import os
from moviepy import VideoFileClip
from pydub import AudioSegment
import math
import soundfile as sf
from TTS.api import TTS
import pyrubberband as pyrb
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

def concatenate_short_segments(adjusted_segments, lang):
    """
    Concatenate segments that are shorter than min_duration seconds and 
    start immediately after the previous segment ends.
    For Hindi language, replaces periods (.) with spaces.
    
    Args:
        adjusted_segments: List of dictionaries containing segment information
        min_duration: Minimum duration in seconds for a standalone segment
        lang: Language code (e.g., "en", "hi")
        
    Returns:
        Modified list with concatenated segments
    """
    if not adjusted_segments:
        return []
    
    # Create a new list to store the concatenated segments
    concatenated = []
    
    # Start with the first segment
    current_group = [adjusted_segments[0]]  # Initialize with first segment only
    
    # Process remaining segments
    for i in range(1, len(adjusted_segments)):
        current_segment = adjusted_segments[i]
        last_segment = current_group[-1]  # Get the last segment in the current group
        
        # Check if this segment starts immediately after the last segment in the current group
        if (current_segment['start'] - last_segment['end']) < 1:
            # If the segment is short, add it to the current group
            if current_segment['end'] - current_segment['start'] < 3:
                current_group.append(current_segment)
            else:
                # If it's not short but still connects, add it to the group and finalize
                current_group.append(current_segment)
                # Combine all segments in the current group
                combined_text = ' '.join(dict.fromkeys([seg['text'] for seg in current_group]))
                
                # Replace periods with spaces for Hindi language
                if lang == "hi":
                    combined_text = combined_text.replace(".", " ")
                    combined_text = combined_text.replace(",", " ")
                combined_segment = {
                    'start': current_group[0]['start'],
                    'end': current_group[-1]['end'],
                    'text': combined_text
                }
                concatenated.append(combined_segment)
                
                # Reset for the next group (safely)
                if i + 1 < len(adjusted_segments):
                    current_group = [adjusted_segments[i + 1]]
                else:
                    current_group = []
                    break  # No more segments to process
        else:
            # This segment doesn't connect with the previous one
            # Finalize the current group if it exists
            if current_group:
                combined_text = ' '.join(dict.fromkeys([seg['text'] for seg in current_group]))
                
                # Replace periods with spaces for Hindi language
                if lang == "hi":
                    combined_text = combined_text.replace(".", " ")
                
                combined_segment = {
                    'start': current_group[0]['start'],
                    'end': current_group[-1]['end'],
                    'text': combined_text
                }
                concatenated.append(combined_segment)
            
            # Start a new group with the current segment
            current_group = [current_segment]
    
    # Don't forget to process the last group if it exists
    if current_group:
        combined_text = ' '.join(dict.fromkeys([seg['text'] for seg in current_group]))
        
        # Replace periods with spaces for Hindi language
        if lang == "hi":
            combined_text = combined_text.replace(".", " ")
        
        combined_segment = {
            'start': current_group[0]['start'],
            'end': current_group[-1]['end'],
            'text': combined_text
        }
        concatenated.append(combined_segment)
    
    return concatenated




def generate_speech_for_segments(adjusted_segments, target_language, speaker_name):
    """
    Generate speech for each segment and ensure it fits within its timestamp.
    
    Args:
        adjusted_segments: List of segments with start, end, and text
        target_language: Target language code (e.g., 'en', 'fr', 'de')
        speaker_name: Name of the speaker to use
        
    Returns:
        List of segments with added 'audio_file' field
    """
    tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2")
    tts.to(device)
    print(f"Using device: {device}")
    speech_segments = []
    
    for i, segment in enumerate(adjusted_segments):
        text = segment["text"]
        start_time = segment["start"]
        end_time = segment["end"]
        duration = end_time - start_time
            
        # Generate speech for this segment
        temp_file = f"temp_speech/segment_{i}.wav"
        
        try:
            # Generate speech
            tts.tts_to_file(
                text=text,
                file_path=temp_file,
                speaker=speaker_name,
                language=target_language,
                split_sentences=True
            )
            
            # Load the generated audio to check its duration
            audio = AudioSegment.from_wav(temp_file)
            speech_duration = len(audio) / 1000  # Convert ms to seconds
            
            # Check if speech is longer than the segment duration
            if speech_duration > duration:
                # Speed up the audio to fit within the segment
                speed_factor = speech_duration / duration
                if speed_factor > 1:  # Only speed up if it's not too extreme
                    y, sr = sf.read(temp_file)
                    y_stretched = pyrb.time_stretch(y, sr, speed_factor)
                    # Verify the new length
                    expected_length = int(len(y) / speed_factor)
                    actual_length = len(y_stretched)
                    print(f"Expected length: {expected_length}, Actual length: {actual_length}")            
                    sf.write(temp_file, y_stretched, sr)
                else:
                    print(f"Warning: Speech for segment {i} is too long ({speech_duration:.2f}s) for its duration ({duration:.2f}s)")
            
            # Add the audio file to the segment
            segment["audio_file"] = temp_file
            speech_segments.append(segment)
            
        except Exception as e:
            print(f"Error generating speech for segment {i}: {e}")
    
    return speech_segments

def combine_speech_segments(speech_segments, output_file, original_audio_file, volume_reduction=0.8):
    """
    Combine all speech segments into one audio file with proper pauses.
    
    Args:
        speech_segments: List of segments with start, end, and audio_file
        output_file: Path to the output audio file
        original_audio_file: Path to the original audio file
        volume_reduction: Factor to reduce the volume of the original audio
    """
    # Load the original audio
    original_audio = AudioSegment.from_file(original_audio_file)
    
    
    # Calculate the reduction in dB (will be negative)
    db_reduction = 20 * math.log10(0.2)  # Approximately -13.98 dB

    # Apply the reduction (add the negative value)
    lowered_original = original_audio + db_reduction

    # Create a silent audio of the same length as the original
    final_audio = AudioSegment.silent(duration=len(original_audio))
    
    # Overlay the lowered original audio
    final_audio = final_audio.overlay(lowered_original)
    
    # Add each speech segment at the correct time
    for segment in speech_segments:
        start_ms = int(segment["start"] * 1000)  # Convert to milliseconds
        
        # Load the speech audio
        speech_audio = AudioSegment.from_wav(segment["audio_file"])
        
        # Overlay the speech onto the final audio at the correct position
        final_audio = final_audio.overlay(speech_audio, position=start_ms)
    
    # Export the final audio
    final_audio.export(output_file, format="wav")
    print(f"Combined audio saved to {output_file}")





def add_audio_to_video(video_file, audio_file, output_file):
    """
    Add the translated audio to the original video using MoviePy v2.0.
    """
    try:
        # Import the required modules from MoviePy v2.0
        from moviepy import VideoFileClip, AudioFileClip
        
        # Load the video and the new audio
        video = VideoFileClip(video_file)
        audio = AudioFileClip(audio_file)
        
        # Make sure audio duration matches video duration
        if audio.duration > video.duration:
            audio = audio.subclip(0, video.duration)
        
        # Set the audio of the video
        video_with_audio = video.with_audio(audio)
        
        # Write the result to a file
        video_with_audio.write_videofile(
            output_file, 
            codec='libx264', 
            audio_codec='aac',
            threads=4,  # Using multiple threads for faster processing
            logger=None  # Suppress progress bar if desired
        )
        
        # Close the clips to free resources
        video.close()
        audio.close()
        video_with_audio.close()
        
        print(f"Successfully created video with new audio: {output_file}")
        return True
    except ImportError as e:
        print(f"Import Error: {e}")
        print("Make sure you have MoviePy v2.0+ installed. Try: pip install --upgrade moviepy")
        return False
    except Exception as e:
        print(f"Error combining video and audio: {str(e)}")
        return False
    
    


def translate_video(mp4_path, mp3_path, adjusted_segments, lang, speaker_name="Luis Moray"):
    adjusted_segments = concatenate_short_segments(adjusted_segments, lang)
    print(adjusted_segments)

    # Create a directory for temporary speech files
    os.makedirs("temp_speech", exist_ok=True)

    speech_segments = generate_speech_for_segments(adjusted_segments, lang, speaker_name)  # Use your target language code
    combine_speech_segments(speech_segments, "translated_audio.wav", mp3_path, volume_reduction=0.2)
    add_audio_to_video(mp4_path, "translated_audio.wav", "static/completed/translated_video.mp4")

    # Clean up temporary files
    import shutil
    shutil.rmtree("temp_speech", ignore_errors=True)

    # Delete the MP3 file
    if os.path.exists(mp3_path):
        try:
            os.remove(mp3_path)
            print(f"Temporary MP3 file {mp3_path} deleted successfully")
        except Exception as e:
            print(f"Error deleting temporary MP3 file: {e}")

    # Delete the translated audio WAV file
    if os.path.exists("translated_audio.wav"):
        try:
            os.remove("translated_audio.wav")
            print(f"Temporary WAV file translated_audio.wav deleted successfully")
        except Exception as e:
            print(f"Error deleting translated_audio.wav: {e}")
    
    return True



