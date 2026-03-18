import torch
from transformers import M2M100ForConditionalGeneration, M2M100Tokenizer
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

def perform_translation(segments, source_lang="en", target_lang="hi"):

    # Load M2M100
    model_name = "facebook/m2m100_1.2B"
    tokenizer = M2M100Tokenizer.from_pretrained(model_name)
    model = M2M100ForConditionalGeneration.from_pretrained(model_name).to(device)
    print(f"Using device: {device}")

    translated_segments = []
    for i in range(0, len(segments), 4):
        group_segments = []
        for j in range(i, min(i + 4, len(segments))):
            group_segments.append(f" *** {segments[j]['text'].strip()}")

        group_string = "".join(group_segments)

        tokenizer.src_lang = source_lang
        inputs = tokenizer(group_string, return_tensors="pt", truncation=True, max_length=512).to(device)
        with torch.no_grad():
            translated_tokens = model.generate(
                **inputs,
                forced_bos_token_id=tokenizer.get_lang_id(target_lang),
                max_length=512
            )
        translated_group = tokenizer.decode(translated_tokens[0], skip_special_tokens=True)
        translated_sentences = [s.strip() for s in translated_group.split("***") if s.strip()]

        for idx, j in enumerate(range(i, min(i + 4, len(segments)))):
            translated_segments.append({
                "start": segments[j]["start"],
                "end": segments[j]["end"],
                "text": translated_sentences[idx] if idx < len(translated_sentences) else ""
            })
            
    print("translation done")

    cleaned_translated_segments = clean_timestamps(translated_segments)  
    print("cleaning")

    formatted_text = ""
    for segment in cleaned_translated_segments:
        formatted_text += f"[{segment['start']:.2f}s -> {segment['end']:.2f}s] {segment['text']}\n"

    print(formatted_text)

    return cleaned_translated_segments


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