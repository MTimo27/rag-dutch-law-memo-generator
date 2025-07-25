# RAG-DUTCH-LAW-MEMO-GENERATOR

A full-stack legal AI prototype for generating Dutch legal memos from administrative court rulings using Retrieval-Augmented Generation (RAG). This proof-of-concept system was developed as part of a Bachelor thesis at the University of Twente by Mihai Timoficiuc and demonstrates a RAG-based approach for generating legally grounded, citation-verifiable memos in Dutch social security law.

*Live preview: memo-generator.netlify.app*
*Note: The platform may be temporarily unavailable due to hosting limitations.*

## Project Overview

Traditional legal memo drafting requires manual review of long case law documents. This project automates the process by combining:

- **Semantic Retrieval** from Dutch case law (Rechtspraak.nl)
- **LLM-based Memo Generation** (GPT-4.1)
- **Structured Prompting & Role Priming**
- **Citation Enforcement & Evaluation**
- **Optional Post-Generation Review** using a second-pass LLM

This system is built to minimize hallucinations and ensure every claim in the output memo is traceable to a real ECLI (European Case Law Identifier).

## Getting Started

### Environment Configuration

Before running the backend, you need to set up the following environment variables:

- `OPENAI_API_KEY`: API key for GPT-4.1 access via OpenAI
- `SUPABASE_URL`: URL of your Supabase project
- `SUPABASE_SERVICE_ROLE`: Service role key with insert/query rights
- `DEEP_INFRA_API_TOKEN`: Used for running the embeddings model on a third party server 
- `ANTHROPIC_API_KEY`: API key for Claude models access via Anthropic
- `APP_ENV`: Set to `development` or `production` as needed

A template is provided at: back-end/.env.example

### Backend Setup (Python + FastAPI)

```bash
cd back-end

# Create virtual environment (recommended)
python -m venv .venv

# Activate it (on Unix/macOS)
source .venv/bin/activate

# Or activate it (on Windows)
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start FastAPI server
uvicorn app.main:app --reload
````

### Frontend Setup (React + Vite)

```bash
cd front-end
npm install
npm run dev
```

## Legal Corpus Construction

The system uses a curated set of 200 XML rulings from [Rechtspraak.nl](https://www.rechtspraak.nl/) in the domain of Dutch social security law (e.g. AOW, WIA, WW). These are parsed and converted into JSON using a custom script that combines:

- **Metadata extraction** using [`rechtspraak-js`](https://github.com/digitalheir/rechtspraak-js)
- **Full-text extraction** using `xml2js`
- **Section filtering** to retain only `OVERWEGINGEN` and `BESLISSING` and `ABSTRACT`

---

## Rechtspraak XML to JSON Conversion

The conversion script relies on the [`rechtspraak-js`](https://github.com/digitalheir/rechtspraak-js) utility.

> 📌 **Important:** This library is not actively updated on npm. You must clone and build it locally.

### Steps

1. Clone the tool:
   ```bash
    git clone https://github.com/digitalheir/rechtspraak-js
    ```

2. Build it using Node.js:

   ```bash
   cd rechtspraak-js
   npm install
   npm run build
   ```

3. Copy the `rechtspraak-js` folder into your project directory:

   ```bash
   cp -r rechtspraak-js back-end/_utils/rechtspraak-js/
   ```

4. Run the converter script:

   ```bash
   node 0.1_convert_xml_to_json.js
   ```

The script will:

* Read XML files from `_data/rechtspraak-xml/`
* Convert and save them as JSON in `_data/rechtspraak-json/`

---

## System Pipeline

1. User fills a structured legal intake form (frontend)
2. Query embedding (using `multilingual-e5-large`)
3. Top-k case law chunks are retrieved from Supabase (`pgvector`)
4. GPT-4.1 generates a memo citing specific ECLI fragments
5. *(Optional)* A second LLM refines the memo and validates citation grounding
6. Evaluation scripts compute citation precision, recall, and hallucination flags

---

## Evaluation Metrics

* **Citation Precision / Recall / F1**
* **Semantic Grounding**: cosine similarity of sentences vs. source chunks
* **Hallucination Detection**: fabricated citations or ungrounded statements
* **LLM-Based Review**: sentence-level agreement with GPT-4.1 judgments

---

## AI Tool Usage

The development of this project made use of modern AI coding assistants to accelerate iteration in the short 10 week timeline and improve code quality. Specifically:

- **GitHub Copilot** was used for real-time code suggestions and auto-completion during backend and frontend development.
- **ChatGPT (GPT-4.1)** and **Claude (Sonnet 4)** were used to ask technical questions, troubleshoot issues, and refine code.
- The **frontend UI** was designed and scaffolded using [**Lovable.dev**](https://lovable.dev/), an AI-powered design and component generator for React projects.

These tools enhanced productivity but all architecture, logic, and evaluation design decisions were made by the author. After using the tools and services, the author thoroughly reviewed and edited the content as needed, taking full responsibility for the final outcome.

## 📄 License

This project is licensed under the **GNU General Public License v3.0 (GPLv3)** due to its integration of components from [`rechtspraak-js`](https://github.com/digitalheir/rechtspraak-js), which is also GPL-licensed.

By using or modifying this codebase, you agree to:

- Publish any derivative work under **GPLv3-compatible** license terms
- Provide access to the **source code** if you distribute modified versions
- Use this project for **non-commercial, research, and educational purposes**

For full legal terms, see the [GPLv3 License](https://www.gnu.org/licenses/gpl-3.0.en.html).

---

If your goal is personal learning, research, or academic work, **you are free to use, modify, and share this project** under these terms.

> ⚠️ Commercial use is not permitted without ensuring full GPLv3 compliance and permission from all upstream components.

---

## Citation

This system accompanies the paper:

**Legal Memorandum Generation Using Retrieval-Augmented Large
Language Models: A Case Study for Dutch Law**
*Mihai Timoficiuc, Hao Chen, Marcos R. Machado*
*University of Twente, Faculty of Behavioural, Management and Social Sciences, Department of High-Tech Business and
Entrepreneurship, AE Enschede, 7500, Netherlands*

---

## 📬 Contact

For academic inquiries, collaboration, or bug reports, reach out to:

*Corresponding author: Hao Chen (h.chen-3@utwente.nl, Tel. +31 534897784).
*Email addresses: mihaitimoficiuc@gmail.com (Mihai Timoficiuc), h.chen-3@utwente.nl (Hao Chen),
m.r.machado@utwente.nl (Marcos R. Machado)



