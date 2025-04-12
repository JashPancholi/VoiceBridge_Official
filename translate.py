import torch
from transformers import M2M100ForConditionalGeneration, M2M100Tokenizer
from datetime import datetime
from pymongo import MongoClient
import os

def perform_translation(segments, filename, source_lang="en", target_lang="hi"):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # Load M2M100
    model_name = "facebook/m2m100_1.2B"
    tokenizer = M2M100Tokenizer.from_pretrained(model_name)
    model = M2M100ForConditionalGeneration.from_pretrained(model_name).to(device)
    tokenizer.src_lang = source_lang

    translated_segments = []
    for i in range(0, len(segments), 4):
        group_segments = []
        for j in range(i, min(i + 4, len(segments))):
            group_segments.append(f" *** {segments[j]['text'].strip()}")

        group_string = "".join(group_segments)
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
                "original_text": segments[j]["text"],
                "translated_text": translated_sentences[idx] if idx < len(translated_sentences) else ""
            })

    # Store in MongoDB
    try:
        client = MongoClient("mongodb://localhost:27017/")  # update URI as needed
        db = client["YourDBName"]
        collection = db["TranslatedResults"]

        document = {
            "filename": os.path.basename(filename),
            "source_language": source_lang,
            "target_language": target_lang,
            "datetime": datetime.now(),
            "translated_segments": translated_segments
        }

        collection.insert_one(document)
        print(f"Translation and DB insert successful for {filename}")
    except Exception as e:
        print("Error saving to MongoDB:", e)

    return translated_segments