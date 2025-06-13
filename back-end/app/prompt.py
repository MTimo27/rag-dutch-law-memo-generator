def build_query(form: dict) -> str:
    return (
        f"Betwist besluit: {form['disputedDecision']}\n"
        f"Gewenst resultaat: {form['desiredOutcome']}\n"
        f"Kritieke feiten: {form['criticalFacts']}\n"
        f"Toepasselijke wet: {form['applicableLaw']}\n"
        f"Doelgroep: {form['recipients']}"
    )

def build_prompt(question: str, chunks: list[dict]) -> str:
    # 1. Role and task instructions
    # "You are a legal assistant specialized in Dutch social security cases. "
    # "Use only the statements below for your analysis. "
    # "Refer to the correct ECLI code in each relevant sentence. "
    # "Do not use knowledge outside these statements.\n\n"
    role_instruction = (
        "Je bent een juridisch assistent gespecialiseerd in Nederlandse sociale zekerheidszaken. "
        "Gebruik uitsluitend de onderstaande uitspraken voor je analyse. "
        "Verwijs in elke relevante zin naar de juiste ECLI-code. "
        "Gebruik geen kennis buiten deze uitspraken.\n\n"
    )

    # 2. User query
    question_section = f"### Vraag:\n{question.strip()}\n\n"

    # 3. Selected case fragments
    refs_section = "### Geselecteerde uitspraken:\n"
    refs = "\n\n".join(
        f"- ECLI: {c['ecli']}\n"
        f"  Titel: {c['metadata'].get('title', 'Onbekend')}\n"
        f"  Instantie: {c['metadata'].get('court', 'Onbekend')}\n"
        f"  Datum: {c['metadata'].get('date', 'Onbekend')}\n"
        f"  Sectie: {c['metadata'].get('section', 'Onbekend')}\n"
        f"  Fragment: {c['text']}\n"
        f"  Relevantiescore: {c['metadata'].get('similarity', 'Onbekend')}"
        for c in chunks
    )

    # 4. Enhanced memo instruction
    memo_instruction = (
        "\n\n### Memo:\n"
        "Schrijf een juridisch memorandum dat uitlegt hoe de bovenstaande uitspraken relevant zijn voor de vraag.\n"
        "Pas de jurisprudentie concreet toe op de feiten van de zaak.\n"
        "Vergelijk overeenkomsten en verschillen tussen de uitspraken en de situatie van de cliënt.\n"
        "Gebruik alleen de meest relevante uitspraken en groepeer vergelijkbare rechtspraak waar mogelijk.\n"
        "Verwijs expliciet naar de ECLI-code van elke uitspraak die je bespreekt.\n\n"
        "Gebruik de volgende structuur:\n"
        "1. Vraaganalyse: Geef kort de kern van het juridische probleem weer.\n"
        "2. Toepassing jurisprudentie: Analyseer relevante uitspraken en pas deze toe op de vraag en de feiten.\n"
        "3. Conclusie: Geef een juridisch onderbouwd advies of antwoord. Beoordeel de kans van slagen en noem mogelijke vervolgstappen.\n"
    )

    # Final assembly
    return role_instruction + question_section + refs_section + refs + memo_instruction

# LLM #2: REVIEW & REFINE MEMO
def build_reviewer_prompt(draft: str, chunks: list[dict]) -> str:
    # 1. Role instruction
    role_instruction = (
        "Je bent een juridisch assistent gespecialiseerd in Nederlandse sociale zekerheidszaken. "
        "Je controleert of een gegenereerde memo juridisch accuraat is en volledig gebaseerd is op de opgehaalde gerechtelijke uitspraken.\n\n"
    )

    # 2. Input: Original draft memo
    draft_section = f"### Oorspronkelijke Memo:\n{draft.strip()}\n\n"

    # 3. Input: Retrieved case fragments
    refs_section = "### Geselecteerde uitspraken:\n"
    refs = "\n\n".join(
        f"- ECLI: {c['ecli']}\n"
        f"  Titel: {c['metadata'].get('title', 'Onbekend')}\n"
        f"  Instantie: {c['metadata'].get('court', 'Onbekend')}\n"
        f"  Datum: {c['metadata'].get('date', 'Onbekend')}\n"
        f"  Sectie: {c['metadata'].get('section', 'Onbekend')}\n"
        f"  Fragment: {c['text']}\n"
        f"  Relevantiescore: {c['metadata'].get('similarity', 'Onbekend')}"
        for c in chunks
    )

    # 4. Review instruction
    review_instruction = (
        "\n\n### Instructie:\n"
        "Herschrijf de bovenstaande memo zodat deze alleen gebruik maakt van de opgehaalde fragmenten. "
        "Verwijder ongefundeerde uitspraken, voeg expliciete verwijzingen naar ECLI-codes toe, en verbeter de juridische helderheid. "
        "De herziene memo moet volledig herleidbaar zijn tot de opgehaalde fragmenten en vrij zijn van hallucinaties of externe kennis.\n"
    )

    # Final assembly
    return role_instruction + refs_section + refs + draft_section + review_instruction
