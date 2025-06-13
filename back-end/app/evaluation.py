import re
from typing import List
from nltk.tokenize import sent_tokenize
from sklearn.metrics.pairwise import cosine_similarity
from app.rag import embed_query  
import nltk
from scipy.spatial import distance
import numpy as np
from app.rag import embed_batch 

nltk.download('punkt', quiet=True)
nltk.download('punkt_tab', quiet=True)


def compute_similarity(vec1, vec2, metric="cosine") -> float:
    if metric == "cosine":
        return 1 - distance.cosine(vec1, vec2)
    elif metric == "dot":
        return np.dot(vec1, vec2)
    elif metric == "euclidean":
        return np.exp(-distance.euclidean(vec1, vec2))  # normalized
    else:
        raise ValueError(f"Unsupported metric: {metric}")

# Extracts and cleans all valid ECLI citations from the input text.
# Removes trailing punctuation and ensures each match ends in digits.
def extract_eclis_from_text(text: str) -> list[str]:
    raw_matches = re.findall(r"ECLI:\S+", text)
    cleaned = []

    for match in raw_matches:
        clean = re.sub(r"[\*\)\.\,\;\:]+$", "", match)
        if re.match(r"ECLI:[A-Z]{2}:[A-Z]+:\d{4}:\d+$", clean):
            cleaned.append(clean)

    return cleaned

# Computes IR-style precision and recall:
#  - predicted: ECLIs cited by the model (memo)
#  - reference: ECLIs available in retrieved source chunks
# Precision = fraction of predicted ECLIs that are correct
# Recall = fraction of reference ECLIs that were actually cited
def compute_precision_recall(predicted: List[str], reference: List[str]):
    predicted_set = set(predicted)
    reference_set = set(reference)
    tp = predicted_set & reference_set

    precision = len(tp) / len(predicted_set) if predicted_set else 0.0
    recall = len(tp) / len(reference_set) if reference_set else 0.0
    return precision, recall


# Counts how many cited ECLIs are not present in the retrieved set—
# these are treated as fabricated (hallucinated) citations.
def count_fabricated_eclis(cited: List[str], retrieved: List[str]) -> int:
    return sum(1 for e in cited if e not in retrieved)


def get_ungrounded_sentences(
    memo: str,
    chunks: List[dict],
    threshold: float = 0.70,
    similarity_metric: str = "cosine"
) -> list[str]:
    sentences = sent_tokenize(memo)
    chunk_texts = [c["text"] for c in chunks]

    sentence_embeddings = embed_batch(sentences)
    chunk_embeddings = embed_batch(chunk_texts)

    ungrounded_sentences = []
    for sentence, sent_vec in zip(sentences, sentence_embeddings):
        sims = [compute_similarity(sent_vec, chunk_vec, similarity_metric) for chunk_vec in chunk_embeddings]
        if max(sims) < threshold:
            ungrounded_sentences.append(sentence)

    return ungrounded_sentences

def evaluate_memo(
    memo: str,
    chunks: List[dict],
    threshold: float = 0.70,
    similarity_metric: str = "cosine"
) -> dict:
    predicted_eclis = extract_eclis_from_text(memo)
    reference_eclis = [c["ecli"] for c in chunks]

    sentences = sent_tokenize(memo)
    precision, recall = compute_precision_recall(predicted_eclis, reference_eclis)
    fabricated = count_fabricated_eclis(predicted_eclis, reference_eclis)
    ungrounded_sents = get_ungrounded_sentences(memo, chunks, threshold, similarity_metric)
    ungrounded = len(ungrounded_sents)

    return {
        # Citation metrics
        "citation_precision": precision,
        "citation_recall": recall,
        "predicted_eclis": list(set(predicted_eclis)),
        "reference_eclis": list(set(reference_eclis)),
        "fabricated_eclis": fabricated,

        # Grounding metrics
        "ungrounded_statements": ungrounded,
        "ungrounded_sentences": ungrounded_sents,
        "hallucinated": fabricated > 0 or ungrounded > 0,

        # Experiment parameters
        "threshold": threshold,
        "similarity_metric": similarity_metric,

        # Contextual logging
        "num_sentences": len(sentences),
        "num_chunks": len(chunks),
        "ungrounded_ratio": ungrounded / len(sentences) if sentences else 0.0
    }