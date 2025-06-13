import { MemoFormData, MemoData, DatabaseInfoResponse, EvaluationResult, JurisprudenceChunk } from "@/types/memoTypes";
import { environment } from "@/environments/environment";
const { API_URL } = environment;

// ---------------------- Memo Generation ----------------------
export const generateMemo = async (
  formData: MemoFormData,
  memoId: string
): Promise<{ memo: string; chunks: DatabaseInfoResponse["chunks"] }> => {
  const response = await fetch(API_URL + "/generate-memo", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(formData),
  });
  if (!response.ok) throw new Error(`API error: ${response.status}`);
  const data: { memo: string; chunks: DatabaseInfoResponse["chunks"] } = await response.json();

  // Save draft memo without evaluation
  await saveMemoWithFeedback({
    id: memoId,
    content: data.memo,
    formData,
    chunks: data.chunks,
    createdAt: new Date().toISOString(),
    feedback: null,
  });

  return { memo: data.memo, chunks: data.chunks };
};

// ---------------------- Memo Evaluation ----------------------
export const evaluateMemo = async (
  memo: string,
  chunks: DatabaseInfoResponse["chunks"],
  similarityMetric: "cosine" | "dot" | "euclidean" = "cosine",
  threshold: number = 0.7
): Promise<EvaluationResult> => {
  const evalResponse = await fetch(
    `${API_URL}/evaluate-memo?similarity_metric=${similarityMetric}&threshold=${threshold}`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ memo, chunks }),
    }
  );

  if (!evalResponse.ok) {
    throw new Error(`Evaluation API error: ${evalResponse.status}`);
  }

  return await evalResponse.json();
};

// ---------------------- Chunk Listing ----------------------

export const getAllChunks = async (): Promise<DatabaseInfoResponse> => {
  const PAGE_SIZE = 1000;
  const allChunks: JurisprudenceChunk[] = [];
  let offset = 0;
  let keepFetching = true;

  try {
    while (keepFetching) {
      const response = await fetch(`${API_URL}/get-all-chunks?limit=${PAGE_SIZE}&offset=${offset}`);
      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }

      const data = await response.json();
      const chunkBatch: JurisprudenceChunk[] = data.chunks;

      const processedChunks = chunkBatch.map((chunk) => {
        if (chunk.metadata && !chunk.metadata.date) {
          const matches = chunk.ecli.match(/ECLI:[A-Z]{2}:[A-Z]+:(\d{4}):/);
          if (matches && matches[1]) {
            chunk.metadata.date = matches[1];
          }
        }
        return chunk;
      });

      allChunks.push(...processedChunks);
      offset += PAGE_SIZE;
      keepFetching = chunkBatch.length === PAGE_SIZE; // Stop if fewer than PAGE_SIZE returned
    }

    return { chunks: allChunks };
  } catch (error) {
    console.error("Error fetching all chunks:", error);
    throw error;
  }
};

// ---------------------- Memo Insert or Update ----------------------

export const saveMemoWithFeedback = async (memoData: MemoData): Promise<{ id: string }> => {
  try {
    const response = await fetch(API_URL + "/save-memo", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(memoData),
    });

    if (!response.ok) throw new Error("Failed to save memo");

    const result = await response.json();
    return { id: result.id };
  } catch (error) {
    console.error("Error saving memo:", error);
    return { id: memoData.id };
  }
};
