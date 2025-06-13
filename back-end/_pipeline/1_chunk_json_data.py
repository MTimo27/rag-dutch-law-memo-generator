import os
import json
import re
from tqdm import tqdm
from transformers import AutoTokenizer

INPUT_DIR = "../_data/rechtspraak-json"
OUTPUT_FILE = "../_data/chunks.jsonl"
MIN_WORDS_PER_PARA = 50    # merge paragraphs shorter than this
MAX_WORDS_PER_CHUNK = 200   # initial sentence‑based chunk size
MIN_TOKENS = 50    # minimum tokens per chunk
MAX_TOKENS = 512   # maximum tokens per chunk
SENTENCE_SPLIT_REGEX = re.compile(r'(?<=[\.\!\?])\s+')

tokenizer = AutoTokenizer.from_pretrained("intfloat/multilingual-e5-large")

def split_into_sentences(text):
    return SENTENCE_SPLIT_REGEX.split(text)

def get_quarter_from_date(date_str):
    try:
        month = int(date_str.split("-")[1])
        return (month - 1) // 3 + 1
    except Exception:
        return None

def get_token_count(text):
    return len(tokenizer.tokenize(text))

def create_token_bounded_chunks(sentences, min_tokens=MIN_TOKENS, max_tokens=MAX_TOKENS):
    chunks = []
    current_sentences = []
    current_text = ""
    
    for sentence in sentences:
        # Test adding this sentence
        test_text = current_text + (" " if current_text else "") + sentence
        test_tokens = get_token_count(test_text)
        
        if test_tokens <= max_tokens:
            # Safe to add this sentence
            current_sentences.append(sentence)
            current_text = test_text
        else:
            # Adding this sentence would exceed max_tokens
            if current_sentences:
                # Check if current chunk meets minimum requirement
                current_tokens = get_token_count(current_text)
                if current_tokens >= min_tokens:
                    chunks.append(current_text.strip())
                    current_sentences = [sentence]
                    current_text = sentence
                else:
                    # Current chunk too small, try to add sentence anyway
                    # and handle overflow by truncating
                    current_sentences.append(sentence)
                    current_text = test_text
                    truncated = truncate_to_max_tokens(current_text, max_tokens)
                    chunks.append(truncated.strip())
                    current_sentences = []
                    current_text = ""
            else:
                # No current chunk, but single sentence is too long
                truncated = truncate_to_max_tokens(sentence, max_tokens)
                if get_token_count(truncated) >= min_tokens:
                    chunks.append(truncated.strip())
                # If truncated sentence is still too small, we'll lose it
                # (this is an edge case with very short sentences that somehow have many tokens)
    
    # Handle remaining sentences
    if current_sentences and current_text:
        current_tokens = get_token_count(current_text)
        if current_tokens >= min_tokens:
            chunks.append(current_text.strip())
        elif chunks:
            # Try to merge with previous chunk if it won't exceed max_tokens
            last_chunk = chunks[-1]
            merged = last_chunk + " " + current_text
            if get_token_count(merged) <= max_tokens:
                chunks[-1] = merged
            # Otherwise, we lose this small chunk
    
    return chunks

def truncate_to_max_tokens(text, max_tokens):
    tokens = tokenizer.tokenize(text)
    if len(tokens) <= max_tokens:
        return text
    
    truncated_tokens = tokens[:max_tokens]
    return tokenizer.convert_tokens_to_string(truncated_tokens)

def process_paragraphs_to_chunks(paragraphs, min_tokens=MIN_TOKENS, max_tokens=MAX_TOKENS):
    all_chunks = []
    accumulator = []  
    
    for para in paragraphs:
        para_tokens = get_token_count(para)
        
        if para_tokens >= min_tokens:
            # Process any accumulated small paragraphs first
            if accumulator:
                acc_text = " ".join(accumulator)
                acc_tokens = get_token_count(acc_text)
                if acc_tokens >= min_tokens:
                    if acc_tokens <= max_tokens:
                        all_chunks.append(acc_text)
                    else:
                        # Split accumulated text
                        sentences = split_into_sentences(acc_text)
                        chunks = create_token_bounded_chunks(sentences, min_tokens, max_tokens)
                        all_chunks.extend(chunks)
                accumulator = []
            
            # Process current paragraph
            if para_tokens <= max_tokens:
                all_chunks.append(para)
            else:
                # Split large paragraph
                sentences = split_into_sentences(para)
                chunks = create_token_bounded_chunks(sentences, min_tokens, max_tokens)
                all_chunks.extend(chunks)
        else:
            # Accumulate small paragraph
            accumulator.append(para)
            acc_text = " ".join(accumulator)
            acc_tokens = get_token_count(acc_text)
            
            if acc_tokens >= min_tokens:
                if acc_tokens <= max_tokens:
                    all_chunks.append(acc_text)
                    accumulator = []
                else:
                    # Accumulated text is now too large, process it
                    sentences = split_into_sentences(acc_text)
                    chunks = create_token_bounded_chunks(sentences, min_tokens, max_tokens)
                    all_chunks.extend(chunks)
                    accumulator = []
    
    # Handle any remaining accumulated paragraphs
    if accumulator:
        acc_text = " ".join(accumulator)
        acc_tokens = get_token_count(acc_text)
        if acc_tokens >= min_tokens:
            if acc_tokens <= max_tokens:
                all_chunks.append(acc_text)
            else:
                sentences = split_into_sentences(acc_text)
                chunks = create_token_bounded_chunks(sentences, min_tokens, max_tokens)
                all_chunks.extend(chunks)
        # If final accumulated text is too small, we lose it
    
    return all_chunks

with open(OUTPUT_FILE, "w", encoding="utf-8") as fout:
    total_chunks = 0
    skipped_small = 0
    truncated_large = 0
    
    for filename in tqdm(os.listdir(INPUT_DIR), desc="Processing JSON files"):
        if not filename.endswith(".json"):
            continue

        try:
            path = os.path.join(INPUT_DIR, filename)
            data = json.load(open(path, "r", encoding="utf-8"))

            # Pull relevant metadata fields from data['metadata']
            meta = data.get("metadata", {})
            ecli = meta.get("_id", "")

            # title may be a dict with '@value' or a plain string
            raw_title = meta.get("title", "")
            title = raw_title.get("@value", "") if isinstance(raw_title, dict) else raw_title
            
            # abstract may be dict with '@value'
            raw_abs = meta.get("abstract", {})
            abstract = raw_abs.get("@value", "") if isinstance(raw_abs, dict) else raw_abs or ""
            # procedure may be list or string
            proc = meta.get("procedure", [])
            procedure = proc[0] if isinstance(proc, list) and proc else (proc if isinstance(proc, str) else "")
            # judgement date
            judgment_date = meta.get("date", meta.get("issued", ""))
            quarter = get_quarter_from_date(judgment_date)
            # subject may be list or string
            subj = meta.get("subject", [])
            subject = subj[0] if isinstance(subj, list) and subj else (subj if isinstance(subj, str) else "")
            # court from creator.rdfs:label[0].@value
            creator = meta.get("creator", {})
            if isinstance(creator, dict):
                labels = creator.get("rdfs:label", [])
                court = labels[0].get("@value", "") if isinstance(labels, list) and labels else ""
            else:
                court = ""

            # Process abstract as its own chunk if it meets token requirements
            if abstract and abstract.strip():
                abstract_tokens = get_token_count(abstract.strip())
                if abstract_tokens >= MIN_TOKENS:
                    if abstract_tokens <= MAX_TOKENS:
                        abs_text = abstract.strip()
                    else:
                        abs_text = truncate_to_max_tokens(abstract.strip(), MAX_TOKENS)
                        truncated_large += 1
                    
                    abs_chunk = {
                        "ecli": ecli,
                        "text": abs_text,
                        "metadata": {
                            "title": title,
                            "procedure": procedure,
                            "subject": subject,
                            "court": court,
                            "date": judgment_date, 
                            "quarter": quarter,
                            "section": "ABSTRACT",
                            "chunk_index": -1,
                            "sub_chunk_index": 0
                        }
                    }
                    fout.write(json.dumps(abs_chunk, ensure_ascii=False) + "\n")
                    total_chunks += 1
                else:
                    skipped_small += 1

            # Process sections
            sections = data.get("fullText", [])
            for sec in sections:
                section_title = sec.get("title", "").upper().strip()
                paras = [p.strip() for p in sec.get("paragraphs", []) if p.strip()]
                if not paras:
                    continue

                # Create token-bounded chunks from paragraphs
                chunks = process_paragraphs_to_chunks(paras, MIN_TOKENS, MAX_TOKENS)
                
                # Write chunks
                for idx, chunk_text in enumerate(chunks):
                    chunk = {
                        "ecli": ecli,
                        "text": chunk_text,
                        "metadata": {
                            "title": title,
                            "procedure": procedure,
                            "subject": subject,
                            "court": court,
                            "date": judgment_date, 
                            "quarter": quarter,
                            "section": section_title,
                            "chunk_index": idx,
                            "sub_chunk_index": 0
                        }
                    }
                    fout.write(json.dumps(chunk, ensure_ascii=False) + "\n")
                    total_chunks += 1

        except Exception as e:
            print(f"Failed on {filename}: {e}")

    print(f"\nProcessing complete!")
    print(f"Total chunks created: {total_chunks}")
    print(f"Small chunks skipped: {skipped_small}")
    print(f"Large chunks truncated: {truncated_large}")