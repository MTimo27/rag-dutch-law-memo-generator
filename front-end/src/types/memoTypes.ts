
export interface MemoFormData {
  disputedDecision: string;
  desiredOutcome: string;
  criticalFacts: string;
  applicableLaw: string;
  recipients: string;
  isPredefinedCase?: boolean;
}

export interface FeedbackData {
  chunkRelevance: Record<string, boolean>;
  chunkComments: Record<string, string>;
  memoId: string;
  generalComment?: string;
  createdAt?: string;
}

export interface MemoData {
  id: string;
  content: string;
  formData: MemoFormData;
  chunks: unknown[];
  createdAt: string;
  feedback?: FeedbackData | null;
}

export interface PredefinedCase {
  id: string;
  name: string;
  formData: MemoFormData;
}

export interface JurisprudenceMetadata {
  title: string;
  procedure: string;
  subject: string;
  court: string;
  date: string;
  ecli: string;
  quarter: string;
  section?: string;
  chunk_index?: number;
  sub_chunk_index?: number;
}

export interface JurisprudenceChunk {
  ecli: string;
  metadata: JurisprudenceMetadata;
  text: string;
  id: string;
  sub_chunk_index: string;
  chunk_index: string;
  similarity: number;
}

export interface MemoApiResponse {
  memo: string;
  chunks: JurisprudenceChunk[];
  evaluation: EvaluationResult;
}

export interface DatabaseInfoResponse {
  chunks: JurisprudenceChunk[];
}

export interface EvaluationResult {
  citation_precision: number;
  citation_recall: number;
  predicted_eclis: string[];
  reference_eclis: string[];
  fabricated_eclis: number;
  ungrounded_statements: number;
  ungrounded_sentences: string[];
  hallucinated: boolean;
  threshold: number;
  similarity_metric: "cosine" | "dot" | "euclidean";
  num_sentences: number;
  num_chunks: number;
  ungrounded_ratio: number;
}
