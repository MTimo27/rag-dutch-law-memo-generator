import json
import httpx
import certifi
import time
from pathlib import Path
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
import os
import nltk

nltk.download("punkt", quiet=True)
from nltk.tokenize import sent_tokenize

INPUT_DIR = Path("../reviewer_temperature/results/gpt_temperature/extracted_eval_results")
OUTPUT_DIR = INPUT_DIR  
MODEL_NAME = "gpt-4.1"
TEMPERATURE = 0.2

load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

class Verdict(BaseModel):
    is_hallucinated: bool = Field(..., description="Whether the sentence is hallucinated or ungrounded")
    justification: str = Field(..., description="Short explanation why the sentence is or is not hallucinated")

http_client = httpx.Client(verify=certifi.where())
llm = ChatOpenAI(model=MODEL_NAME, temperature=TEMPERATURE, http_client=http_client)
structured_llm = llm.with_structured_output(Verdict)

prompt = ChatPromptTemplate.from_messages([
    ("system",
     "Je bent een juridisch assistent gespecialiseerd in Nederlandse sociale zekerheidszaken. "
     "Je taak is om te bepalen of een zin uit een memo voldoende juridisch is onderbouwd door de opgehaalde gerechtelijke uitspraken. "
     "Gebruik je juridische expertise én de gelinkte fragmenten. Elke zin moet verwijzen naar relevante fragmenten uit die uitspraken. "
     "Houd rekening met de gelijkenismetriek die door een geautomatiseerd systeem wordt gebruikt om de zin te labelen: {metric}, en de gebruikte drempelwaarde: {threshold}."),
    ("user",
     "### Geselecteerde juridische fragmenten:\n{chunks}\n\n"
     "### Memo-context (1 zin vóór en 1 zin na):\n{context}\n\n"
     "### Zin om te beoordelen:\n\"{sentence}\"\n\n"
     "Is deze zin voldoende onderbouwd door de juridische fragmenten? "
     "Antwoord in JSON-formaat met een boolean 'is_hallucinated' en een korte 'justification'.")
])

for file_path in INPUT_DIR.glob("*.json"):
    print(f"\nProcessing: {file_path.name}")
    with open(file_path, "r", encoding="utf-8") as f:
        cases = json.load(f)

    evaluated = []

    for case in cases:
        print(f"→ Beoordeel case: {case['case_id']}")
        chunk_texts = [chunk["text"] for chunk in case.get("chunks", [])]
        memo_text = case.get("memo_refined", "")
        memo_sentences = sent_tokenize(memo_text)
        all_verdicts = []

        ungrounded_sentences = case.get("evaluation", {}).get("ungrounded_sentences", [])
        for sentence in ungrounded_sentences:
            print(f"  Zin: {sentence[:60]}...")
            try:
                idx = memo_sentences.index(sentence)
                context = []
                if idx > 0:
                    context.append(memo_sentences[idx - 1])
                context.append(sentence)
                if idx + 1 < len(memo_sentences):
                    context.append(memo_sentences[idx + 1])
                context_text = " ".join(context)

                formatted_prompt = prompt.invoke({
                    "chunks": "\n\n".join(chunk_texts),
                    "context": context_text,
                    "sentence": sentence,
                    "metric": case.get("similarity_metric", "cosine"),
                    "threshold": case.get("threshold", 0.7)
                })

                time.sleep(5)  
                result = structured_llm.invoke(formatted_prompt)
                all_verdicts.append({
                    "sentence": sentence,
                    "verdict": result.dict()
                })

            except Exception as e:
                print(f"    [Error] Skipping sentence: {e}")
                all_verdicts.append({
                    "sentence": sentence,
                    "verdict": {"is_hallucinated": False, "justification": f"Error: {e}"}
                })

        evaluated.append({
            "case_id": case["case_id"],
            "similarity_metric": case.get("similarity_metric"),
            "threshold": case.get("threshold"),
            "hallucinated_by_eval": case.get("evaluation", {}).get("hallucinated"),
            "gpt4_structured_verdicts": all_verdicts
        })

    out_path = OUTPUT_DIR / file_path.with_name(file_path.stem + "-reviewed.json").name
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(evaluated, f, indent=2, ensure_ascii=False)

    print(f"Gestructureerde beoordelingen opgeslagen in: {out_path}")
