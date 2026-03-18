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
    For Hindi language, replaces periods (.) and commas (,) with spaces,
    and replaces English digits with Hindi digits.
    
    Args:
        adjusted_segments: List of dictionaries containing segment information
        lang: Language code (e.g., "en", "hi")
        
    Returns:
        Modified list with concatenated segments
    """
    if not adjusted_segments:
        return []
    
    # Mapping for English to Hindi digits
    en_digits = "0123456789"
    hi_digits = "०१२३४५६७८९"
    digit_trans = str.maketrans(en_digits, hi_digits)
    
    concatenated = []
    current_group = [adjusted_segments[0]]
    
    for i in range(1, len(adjusted_segments)):
        current_segment = adjusted_segments[i]
        last_segment = current_group[-1]
        
        if (current_segment['start'] - last_segment['end']) < 1:
            if current_segment['end'] - current_segment['start'] < 3:
                current_group.append(current_segment)
            else:
                current_group.append(current_segment)
                combined_text = ' '.join(dict.fromkeys([seg['text'] for seg in current_group]))
                
                if lang == "hi":
                    combined_text = combined_text.replace(".", " ").replace(",", " ")
                    combined_text = combined_text.translate(digit_trans)
                
                combined_segment = {
                    'start': current_group[0]['start'],
                    'end': current_group[-1]['end'],
                    'text': combined_text
                }
                concatenated.append(combined_segment)
                
                if i + 1 < len(adjusted_segments):
                    current_group = [adjusted_segments[i + 1]]
                else:
                    current_group = []
                    break
        else:
            if current_group:
                combined_text = ' '.join(dict.fromkeys([seg['text'] for seg in current_group]))
                if lang == "hi":
                    combined_text = combined_text.replace(".", " ").replace(",", " ")
                    combined_text = combined_text.translate(digit_trans)
                combined_segment = {
                    'start': current_group[0]['start'],
                    'end': current_group[-1]['end'],
                    'text': combined_text
                }
                concatenated.append(combined_segment)
            current_group = [current_segment]
    
    if current_group:
        combined_text = ' '.join(dict.fromkeys([seg['text'] for seg in current_group]))
        if lang == "hi":
            combined_text = combined_text.replace(".", " ").replace(",", " ")
            combined_text = combined_text.translate(digit_trans)
        combined_segment = {
            'start': current_group[0]['start'],
            'end': current_group[-1]['end'],
            'text': combined_text
        }
        concatenated.append(combined_segment)
    
    return concatenated


def generate_speech_for_segments(adjusted_segments, target_language, speaker_name):
    """
    Generate speech for each segment and ensure it fits within its timestamp
    using the speed parameter of XTTS-v2. Only speeds up audio, never slows it down.
    Maximum speed-up is limited to 1.5x to maintain natural speech quality.
    
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
    
    # Create directory for temporary speech files
    os.makedirs("temp_speech", exist_ok=True)
    
    for i, segment in enumerate(adjusted_segments):
        text = segment["text"]
        start_time = segment["start"]
        end_time = segment["end"]
        target_duration = end_time - start_time
        
        if not text.strip():
            print(f"Skipping empty segment {i}")
            continue
            
        # Generate speech for this segment
        temp_file = f"temp_speech/segment_{i}.wav"
        
        try:
            # First, generate speech with default speed to measure duration
            tts.tts_to_file(
                text=text,
                file_path=temp_file,
                speaker=speaker_name,
                language=target_language,
                split_sentences=True
            )
            
            # Load the generated audio to check its duration
            audio = AudioSegment.from_wav(temp_file)
            initial_duration = len(audio) / 1000  # Convert ms to seconds
            
            # Calculate required speed factor
            speed_factor = initial_duration / target_duration
            
            # Only speed up if necessary, never slow down
            if speed_factor <= 1.0:
                # Natural output is already faster than required - don't modify
                print(f"Segment {i}: Natural output ({initial_duration:.2f}s) is already faster than required ({target_duration:.2f}s). Keeping as is.")
            else:
                # Need to speed up - cap at 1.5 as requested
                if speed_factor > 1.5:
                    speed_factor = 1.5
                    print(f"Warning: Segment {i} would require speeding up beyond the limit. Limited to 1.5x speed.")
                
                print(f"Segment {i}: Speeding up to {speed_factor:.2f}x to match target duration")
                
                # Try with speed parameter first
                tts.tts_to_file(
                    text=text,
                    file_path=temp_file,
                    speaker=speaker_name,
                    language=target_language,
                    split_sentences=True,
                    speed=speed_factor
                )
                
                # Verify the new duration
                audio = AudioSegment.from_wav(temp_file)
                adjusted_duration = len(audio) / 1000
                print(f"Segment {i}: Original duration: {initial_duration:.2f}s, " 
                      f"Target: {target_duration:.2f}s, Adjusted: {adjusted_duration:.2f}s")
                
                # If speed parameter didn't work well, fall back to pyrubberband
                if abs(adjusted_duration - target_duration) > 0.5:  # If still off by more than 0.5 seconds
                    print(f"Speed parameter didn't achieve target duration for segment {i}. Falling back to pyrubberband.")
                    y, sr = sf.read(temp_file)
                    fallback_speed = adjusted_duration / target_duration
                    
                    # Also limit the fallback speed to 1.5x
                    if fallback_speed > 1.5:
                        fallback_speed = 1.5
                        print(f"Warning: Limiting fallback speed to 1.5x for segment {i}")
                        
                    y_stretched = pyrb.time_stretch(y, sr, fallback_speed)
                    sf.write(temp_file, y_stretched, sr)
                    
                    # Final verification
                    audio = AudioSegment.from_wav(temp_file)
                    final_duration = len(audio) / 1000
                    print(f"Segment {i}: Final duration after fallback: {final_duration:.2f}s")
            
            # Add the audio file to the segment
            segment["audio_file"] = temp_file
            speech_segments.append(segment)
            
        except Exception as e:
            print(f"Error generating speech for segment {i}: {str(e)}")
            import traceback
            traceback.print_exc()
    
    return speech_segments



"""
def generate_speech_for_segments(adjusted_segments, target_language, speaker_name):
    
    Generate speech for each segment and ensure it fits within its timestamp.
    
    Args:
        adjusted_segments: List of segments with start, end, and text
        target_language: Target language code (e.g., 'en', 'fr', 'de')
        speaker_name: Name of the speaker to use
        
    Returns:
        List of segments with added 'audio_file' field
    
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
                if speed_factor > 1.2:  # Only speed up if it's not too extreme
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
    
    return speech_segments"""

def combine_speech_segments(speech_segments, output_file, original_audio_file):
    """
    Combine all speech segments into one audio file with proper pauses.
    The original audio is muted only during speech segments, and the translated speech is overlaid.
    Background sounds, music, and non-speech parts of the original audio are preserved.
    
    Args:
        speech_segments: List of segments with start, end, and audio_file
        output_file: Path to the output audio file
        original_audio_file: Path to the original audio file
        volume_reduction: Not used anymore since we're muting the speech parts
    """
    # Load the original audio
    original_audio = AudioSegment.from_file(original_audio_file)
    
    # Create a copy of the original audio to work with
    final_audio = original_audio
    
    # Process each speech segment
    for segment in speech_segments:
        start_ms = int(segment["start"] * 1000)  # Convert to milliseconds
        end_ms = int(segment["end"] * 1000)      # Convert to milliseconds
        
        # Create a silent segment of the same duration as the speech segment
        silent_segment = AudioSegment.silent(duration=end_ms - start_ms)
        
        # Replace the original audio with silence during the speech segment
        final_audio = final_audio[:start_ms] + silent_segment + final_audio[end_ms:]
        
        # Load the translated speech audio
        speech_audio = AudioSegment.from_wav(segment["audio_file"])
        
        # Overlay the translated speech onto the final audio at the correct position
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
    combine_speech_segments(speech_segments, "translated_audio.wav", mp3_path)
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



