import { createContext, useState, useContext, ReactNode } from "react";

type Language = "nl" | "en";

type Translations = {
  [key: string]: {
    [key in Language]: string;
  };
};

export const translations: Translations = {
  appTitle: {
    en: "Legal Memo Generator",
    nl: "Juridisch Memorandum Generator"
  },
  appDescription: {
    en: "Quickly and efficiently create legal memos for your clients and colleagues",
    nl: "Stel snel en efficiënt juridische memoranda op voor uw cliënten en collega's"
  },
  editor: {
    en: "Editor",
    nl: "Editor"
  },
  preview: {
    en: "Preview",
    nl: "Voorvertoning"
  },
  editorDescription: {
    en: "This tool helps you draft effective legal memos. Answer the questions below and generate your memo.",
    nl: "Dit hulpmiddel helpt u bij het opstellen van effectieve juridische memoranda. Beantwoord de vragen hieronder en genereer uw memo."
  },
  previewEmpty: {
    en: "Fill out the form and generate a memo to view it here.",
    nl: "Vul het formulier in en genereer een memo om het hier te bekijken."
  },
  disputedDecisionQuestion: {
    en: "What is the disputed decision from the agency?",
    nl: "Wat is het betwiste besluit van de instantie?"
  },
  desiredOutcomeQuestion: {
    en: "What is the desired legal outcome?",
    nl: "Wat is het gewenste juridische resultaat?"
  },
  factsQuestion: {
    en: "What facts are important for this case?",
    nl: "Welke feiten zijn belangrijk voor deze zaak?"
  },
  applicableLawQuestion: {
    en: "Which law does the dispute fall under?",
    nl: "Onder welke wet valt het geschil?"
  },
  recipientsQuestion: {
    en: "Who is this memo intended for?",
    nl: "Voor wie is dit memo bedoeld?"
  },
  disputedDecisionPlaceholder: {
    en: "e.g., Termination of WIA benefit due to recovery claim",
    nl: "Bijvoorbeeld: Stopzetting van WIA-uitkering wegens hersteldverklaring."
  },
  desiredOutcomePlaceholder: {
    en: "e.g., Continuation of benefit / Cancellation of repayment",
    nl: "Voortzetting van uitkering / Schrapping van terugvordering"
  },
  factsPlaceholder: {
    en: "e.g., Client was examined by a doctor who confirmed inability to work",
    nl: "Cliënt kreeg een onafhankelijke medische beoordeling die arbeidsongeschiktheid bevestigde."
  },
  selectApplicableLaw: {
    en: "Select applicable law",
    nl: "Selecteer toepasselijke wet"
  },
  selectRecipient: {
    en: "Select recipient",
    nl: "Selecteer ontvanger"
  },
  wia: {
    en: "WIA (disability)",
    nl: "WIA (arbeidsongeschiktheid)"
  },
  ww: {
    en: "WW (unemployment)",
    nl: "WW (werkloosheid)"
  },
  aow: {
    en: "AOW (old age)",
    nl: "AOW (ouderdom)"
  },
  participatiewet: {
    en: "Participatiewet (social assistance)",
    nl: "Participatiewet (bijstand)"
  },
  toeslagenwet: {
    en: "Toeslagenwet (supplements)",
    nl: "Toeslagenwet"
  },
  otherLaw: {
    en: "Other / Unknown",
    nl: "Anders / Onbekend"
  },
  lawyer: {
    en: "Lawyer",
    nl: "Advocaat"
  },
  client: {
    en: "Client",
    nl: "Cliënt"
  },
  judge: {
    en: "Judge",
    nl: "Rechter"
  },
  legalStaff: {
    en: "Legal staff",
    nl: "Juridisch medewerker"
  },
  caseworker: {
    en: "Caseworker",
    nl: "UWV medewerker"
  },
  createMemo: {
    en: "Create Memo",
    nl: "Creëer Memo"
  },
  recipient: {
    en: "RECIPIENT:",
    nl: "ONTVANGER:"
  },
  regarding: {
    en: "REGARDING:",
    nl: "BETREFT:"
  },
  disputedDecision: {
    en: "DISPUTED DECISION:",
    nl: "BETWISTE BESLUIT:"
  },
  relevantFacts: {
    en: "RELEVANT FACTS:",
    nl: "RELEVANTE FEITEN:"
  },
  conclusion: {
    en: "DESIRED OUTCOME:",
    nl: "GEWENSTE UITKOMST:"
  },
  applicableLaw: {
    en: "APPLICABLE LAW:",
    nl: "TOEPASSELIJKE WET:"
  },
  legalAdvice: {
    en: "LEGAL ADVICE:",
    nl: "JURIDISCH ADVIES:"
  },
  basedOn: {
    en: "Based on the provided information about",
    nl: "Gebaseerd op de verstrekte informatie over"
  },
  weAdvise: {
    en: "we advise the following actions:",
    nl: "adviseren wij het volgende te ondernemen:"
  },
  advice1: {
    en: "Gather all relevant documentation related to this issue.",
    nl: "Verzamel alle relevante documentatie met betrekking tot deze kwestie."
  },
  advice2: {
    en: "Establish a detailed protocol for",
    nl: "Stel een gedetailleerd protocol op voor"
  },
  advice3: {
    en: "Ensure clear communication to",
    nl: "Zorg voor een duidelijke communicatie naar"
  },
  advice4: {
    en: "Consider additional legal advice for specific cases.",
    nl: "Overweeg aanvullend juridisch advies voor specifieke casussen."
  },
  preparedBy: {
    en: "Prepared by:",
    nl: "Opgesteld door:"
  },
  lawFirm: {
    en: "Law Firm [Name]",
    nl: "Advocatenkantoor [Naam]"
  },
  contact: {
    en: "Contact Person: [Attorney Name]",
    nl: "Contactpersoon: [Naam Advocaat]"
  },
  email: {
    en: "Email: [email@lawfirm.com]",
    nl: "Email: [email@advocatenkantoor.nl]"
  },
  phone: {
    en: "Phone: [+1 234 567 890]",
    nl: "Telefoon: [+31 123 456 789]"
  },
  memoGenerated: {
    en: "Memo Generated",
    nl: "Memo Gegenereerd"
  },
  memoGeneratedDesc: {
    en: "Your legal memo has been created successfully.",
    nl: "Uw juridisch memo is succesvol aangemaakt."
  },
  missingInfo: {
    en: "Missing information",
    nl: "Ontbrekende informatie"
  },
  missingInfoDesc: {
    en: "Please fill in at least the disputed decision and desired outcome fields.",
    nl: "Vul ten minste de velden betwiste besluit en gewenste uitkomst in."
  },
  copied: {
    en: "Copied to clipboard",
    nl: "Gekopieerd naar klembord"
  },
  copiedDesc: {
    en: "The memo content has been copied to your clipboard.",
    nl: "De inhoud van het memo is naar uw klembord gekopieerd."
  },
  downloaded: {
    en: "Memo downloaded",
    nl: "Memo gedownload"
  },
  downloadedDesc: {
    en: "Your legal memo has been downloaded as a text file.",
    nl: "Uw juridisch memo is gedownload als tekstbestand."
  },
  footer: {
    en: "© 2025 Legal Memo Generator | Developed for Legal Professionals",
    nl: "© 2025 Juridisch Memo Generator | Ontwikkeld voor Juridische Professionals"
  },
  footerDisclaimer: {
    en: "All generated memos should be reviewed by a legal professional before use",
    nl: "Alle gegenereerde memo's moeten worden beoordeeld door een juridisch professional vóór gebruik"
  },
  legalMemoTitle: {
    en: "LEGAL MEMORANDUM",
    nl: "JURIDISCH MEMORANDUM"
  },
  disclaimerTitle: {
    en: "Legal Disclaimer",
    nl: "Juridische Disclaimer"
  },
  disclaimerText1: {
    en: "This AI system is a legal drafting assistant designed to summarize Dutch court rulings. It does not replace legal expertise or make autonomous decisions.",
    nl: "Dit AI-systeem is een hulpmiddel voor het opstellen van juridische memo's op basis van Nederlandse rechtspraak. Het vervangt geen juridisch advies of menselijke beoordeling."
  },
  disclaimerText2: {
    en: "All generated memos must be reviewed by a qualified legal professional before being used. The system relies on a specific subset of Dutch case law and may contain omissions or errors.",
    nl: "Alle gegenereerde teksten moeten worden gecontroleerd door een bevoegde juridisch professional voordat ze worden gebruikt. De inhoud is gebaseerd op een beperkte set uitspraken en kan onnauwkeurigheden bevatten."
  },
  disclaimerText3: {
    en: "Users are encouraged to verify cited rulings and interpret the content as a draft aid only, not as formal legal advice.",
    nl: "Gebruik het memo uitsluitend als conceptversie, niet als definitieve juridische beoordeling."
  },
  disclaimerText4: {
    en: "Never put sensitive or personal data into the system. This system is not intended for sensitive or confidential information, it is only a prototype for demonstration porposes.",
    nl: "Plaats nooit gevoelige of persoonlijke gegevens in het systeem. Dit systeem is niet bedoeld voor gevoelige of vertrouwelijke informatie, het is alleen een prototype voor demonstratiedoeleinden."
  },
  understand: {
    en: "I Understand",
    nl: "Ik Begrijp Het"
  },
  cancel: {
    en: "Cancel",
    nl: "Annuleren"
  },
  referencedJurisprudence: {
    en: "Referenced Jurisprudence",
    nl: "Gerapporteerde Jurisprudentie"
  },
  viewSources: {
    en: "View Sources",
    nl: "Bekijk Bronnen"
  },
  jurisprudenceUsed: {
    en: "Jurisprudence Used",
    nl: "Gebruikte Jurisprudentie"
  },
  subject: {
    en: "Subject",
    nl: "Onderwerp"
  },
  procedure: {
    en: "Procedure",
    nl: "Procedure"
  },
  changesSaved: {
    en: "Changes saved",
    nl: "Wijzigingen opgeslagen"
  },
  changesSavedDesc: {
    en: "Your changes have been saved successfully.",
    nl: "Uw wijzigingen zijn succesvol opgeslagen."
  },
  generatingMemo: {
    en: "Generating Memo",
    nl: "Memo Genereren"
  },
  generatingMemoDesc: {
    en: "Please wait while we create your legal memo...",
    nl: "Een moment geduld terwijl we uw juridisch memo maken..."
  },
  elapsedTime: {
    en: "Elapsed time",
    nl: "Verstreken tijd"
  },
  seconds: {
    en: "seconds",
    nl: "seconden"
  },
  usedData: {
    en: "Database",
    nl: "Database"
  },
  availableDataTitle: {
    en: "Available Jurisprudence Data",
    nl: "Beschikbare Jurisprudentie Gegevens"
  },
  availableDataDescription: {
    en: "This page shows all jurisprudence cases available in the database for memo generation.",
    nl: "Deze pagina toont alle jurisprudentiezaken beschikbaar in de database voor memo-generatie."
  },
  dataRangeStart: {
    en: "Data Range Start",
    nl: "Gegevensbereik Begin"
  },
  dataRangeEnd: {
    en: "Data Range End",
    nl: "Gegevensbereik Einde"
  },
  availableCases: {
    en: "Available Cases",
    nl: "Beschikbare Zaken"
  },
  caseTitle: {
    en: "Case Title",
    nl: "Zaaktitel"
  },
  court: {
    en: "Court",
    nl: "Rechtbank"
  },
  caseDatabase: {
    en: "Case Database Details",
    nl: "Zaakdatabase Details"
  },
  caseDetails: {
    en: "Case Details",
    nl: "Zaakdetails"
  },
  caseReference: {
    en: "Case Reference",
    nl: "Zaakreferentie"
  },
  relevantText: {
    en: "Relevant Text",
    nl: "Relevante Tekst"
  },
  noDataAvailable: {
    en: "No database information is available yet. Please check back later.",
    nl: "Er is nog geen database-informatie beschikbaar. Kom later terug."
  },
  dataDateRange: {
    en: "Database Date Range",
    nl: "Database Datumbereik"
  },
  date: {
    en: "Date",
    nl: "Datum"
  },
  details: {
    en: "Details",
    nl: "Details"
  },
  viewDetails: {
    en: "View details",
    nl: "Bekijk details"
  },
  hideDetails: {
    en: "Hide details",
    nl: "Verberg details"
  },
  memoGenerationFailed: {
    en: "Memo Generation Failed",
    nl: "Memo Generatie Mislukt"
  },
  memoGenerationFailedDesc: {
    en: "There was an error generating your memo. Please try again.",
    nl: "Er is een fout opgetreden bij het genereren van uw memo. Probeer het opnieuw."
  },
  viewOnRechtspraak: {
    en: "View on Rechtspraak.nl",
    nl: "Bekijk op Rechtspraak.nl"
  },
  unknownProcedure: {
    en: "Unknown procedure",
    nl: "Onbekende procedure"
  },
  ecliReference: {
    en: "ECLI Reference",
    nl: "ECLI Referentie"
  },
  rawMarkdown: {
    en: "Raw Markdown",
    nl: "Ruwe Markdown"
  },
  rawMarkdownDesc: {
    en: "View or copy the raw markdown content of your memo",
    nl: "Bekijk of kopieer de ruwe markdown-inhoud van uw memo"
  },
  overallRating: {
    en: "Overall Rating",
    nl: "Algemene Beoordeling"
  },
  additionalFeedback: {
    en: "Additional Feedback",
    nl: "Aanvullende Feedback"
  },
  feedbackPlaceholder: {
    en: "Please share your thoughts about the generated memo...",
    nl: "Deel uw gedachten over het gegenereerde memo..."
  },
  submitFeedback: {
    en: "Submit Feedback",
    nl: "Feedback Versturen"
  },
  feedbackThanks: {
    en: "Thank you for your feedback!",
    nl: "Bedankt voor uw feedback!"
  },
  rateThisSource: {
    en: "Rate this source",
    nl: "Beoordeel deze bron"
  },
  relevanceRating: {
    en: "Relevance Rating",
    nl: "Relevantie Beoordeling"
  },
  testCase1: {
    en: "WW Benefit Denial Case",
    nl: "WW-uitkering Afwijzingszaak"
  },
  testCase2: {
    en: "Social Assistance Recovery Case",
    nl: "Bijstand Terugvorderingszaak"
  },
  testCase3: {
    en: "Housing Benefit Denial Case",
    nl: "Huurtoeslag Afwijzingszaak"
  },
  testCase4: {
    en: "WIA Termination Case",
    nl: "WIA-beëindigingszaak"
  },
  testCase5: {
    en: "AOW Denial Case",
    nl: "AOW Afwijzingszaak"
  },
  selectTestCase: {
    en: "Select Test Case",
    nl: "Selecteer Testzaak"
  },
  selectTestCasePlaceholder: {
    en: "Choose a test case",
    nl: "Kies een testzaak"
  },
  testCaseDescription: {
    en: "Select a predefined test case to automatically fill the form with sample data",
    nl: "Selecteer een vooraf gedefinieerde testzaak om het formulier automatisch te vullen met voorbeeldgegevens"
  },
  feedbackSubmitted: {
    en: "Feedback Submitted",
    nl: "Feedback Verzonden"
  },
  feedbackSubmittedDesc: {
    en: "Your feedback has been submitted successfully.",
    nl: "Uw feedback is succesvol verzonden."
  },
  evaluationResults: {
    en: "Evaluation Results",
    nl: "Evaluatie Resultaten"
  },
  unreliable: {
    en: "Unreliable Content",
    nl: "Onbetrouwbare Inhoud"
  },
  citationAccuracy: {
    en: "Citation Accuracy",
    nl: "Nauwkeurigheid van Citaten"
  },
  fabricatedCitations: {
    en: "Fabricated Citations",
    nl: "Gefabriceerde Citaten"
  },
  ungroundedStatements: {
    en: "Ungrounded Statements",
    nl: "Ongefundeerde Uitspraken"
  },
  hallucinated: {
    en: "Hallucinated Content",
    nl: "Gegenereerde Fictieve Inhoud"
  },
  yes: {
    en: "Yes",
    nl: "Ja"
  },
  citedSources: {
    en: "Cited Sources",
    nl: "Geciteerde Bronnen"
  },
  ecli: {
    en: "ECLI",
    nl: "ECLI"
  },
  retrievedSources: {
    en: "Retrieved Sources",
    nl: "Opgehaalde Bronnen"
  },
  evaluateMemo: {
    en: "Run Automatic Memo Evaluation",
    nl: "Voer Automatische Memo Evaluatie Uit"
  },
  relevant: {
    en: "Relevant",
    nl: "Relevant"
  },
  notRelevant: {
    en: "Not Relevant",
    nl: "Niet Relevant"
  },
  generalMemoFeedback: {
    en: "Did the memo explain the legal situation clearly and correctly? If not, what was unclear or missing?",
    nl: "Legde het memo de juridische situatie duidelijk en correct uit? Zo niet, wat was onduidelijk of ontbrak er?"
  },
  generalFeedbackPlaceholder: {
    en: "Share your general thoughts about this memo generator...",
    nl: "Deel uw algemene gedachten over deze memo-generator..."
  },
  llmDisclaimer: {
    en: "This memo was generated using a large language model (LLM). While we strive for accuracy, please verify all legal information independently. Large language models may produce incorrect or misleading information and should not be relied upon as a sole source of legal advice.",
    nl: "Dit memo is gegenereerd met behulp van een groot taalmodel (LLM). Hoewel we streven naar nauwkeurigheid, verifieer alle juridische informatie onafhankelijk. Grote taalmodellen kunnen onjuiste of misleidende informatie produceren en mogen niet als enige bron van juridisch advies worden vertrouwd."
  },
  searchCases: {
    en: "Search Cases",
    nl: "Zoek Zaken"
  },
  loadingSpinnerTitle: {
    en: "Loading...",
    nl: "Laden..."
  },
  loadingSpinnerDesc: {
    en: "Please wait while we load the data.",
    nl: "Een moment geduld terwijl we de gegevens laden."
  },
  similarity: {
    en: "Similarity",
    nl: "Gelijkenis"
  },
  reevaluateMemo: { 
    en: "Reevaluate Memo",
    nl: "Herbeoordeel Memo"
  },
  evaluationFailed: {
    en: "Evaluation Failed",
    nl: "Evaluatie Mislukt"
  },
  evaluationFailedDesc: {
    en: "There was an error during the evaluation. Please try again.",
    nl: "Er is een fout opgetreden tijdens de evaluatie. Probeer het opnieuw."
  },
  evaluationComplete: {
    en: "Evaluation Complete",
    nl: "Evaluatie Voltooid"
  },
  evaluationCompleteDesc: {
    en: "The memo evaluation has finished. See the results below.",
    nl: "De memo-evaluatie is voltooid. Bekijk de resultaten hieronder."
  },
   selectSimilarityMetric: {
    en: "Select Similarity Metric",
    nl: "Selecteer Similariteitsmaat"
  },
  thresholdValue: {
    en: "Threshold Value",
    nl: "Drempelwaarde"
  },
  reliable: {
    en: "Reliable Content",
    nl: "Betrouwbare Inhoud"
  },
  no: {
    en: "No",
    nl: "Nee"
  },
  citationPrecision: {
    en: "Citation Precision",
    nl: "Precisie van Citaten"
  },
  citationRecall: {
    en: "Citation Recall",
    nl: "Recall van Citaten"
  }
};

type LanguageContextType = {
  language: Language;
  setLanguage: (lang: Language) => void;
  t: (key: string) => string;
};

const LanguageContext = createContext<LanguageContextType | undefined>(undefined);

export const LanguageProvider = ({ children }: { children: ReactNode }) => {
  const [language, setLanguage] = useState<Language>("nl");

  const t = (key: string): string => {
    if (!translations[key]) {
      console.warn(`Translation key "${key}" not found`);
      return key;
    }
    return translations[key][language];
  };

  return (
    <LanguageContext.Provider value={{ language, setLanguage, t }}>
      {children}
    </LanguageContext.Provider>
  );
};

export const useLanguage = () => {
  const context = useContext(LanguageContext);
  if (context === undefined) {
    throw new Error("useLanguage must be used within a LanguageProvider");
  }
  return context;
};
