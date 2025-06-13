import { useState } from "react";
import { useLanguage } from "@/contexts/LanguageContext";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { Skeleton } from "@/components/ui/skeleton";
import { ExternalLink } from "lucide-react";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { FeedbackData, JurisprudenceChunk } from "@/types/memoTypes";

interface JurisprudenceChunksProps {
  chunks: JurisprudenceChunk[];
  isLoading?: boolean;
  showEvaluation?: boolean;
  memoId?: string;
  onFeedbackSubmit?: (feedback: FeedbackData) => void;
  initialFeedback?: FeedbackData | null;
}

export const JurisprudenceChunks = ({ 
  chunks, 
  isLoading = false, 
  showEvaluation = false,
  memoId = "",
  onFeedbackSubmit,
  initialFeedback = null
}: JurisprudenceChunksProps) => {
  const { t } = useLanguage();
  const [openAccordion, setOpenAccordion] = useState<string | null>(null);
  const [chunkRelevance, setChunkRelevance] = useState<Record<string, boolean>>(initialFeedback?.chunkRelevance || {});
  const [chunkComments, setChunkComments] = useState<Record<string, string>>(initialFeedback?.chunkComments || {});
  const [generalComment, setGeneralComment] = useState(initialFeedback?.generalComment || "");
  const [feedbackSubmitted, setFeedbackSubmitted] = useState(!!initialFeedback);

  if (isLoading) {
    return (
      <div className="mt-6 bg-gray-50 p-4 rounded-lg border border-gray-200">
        <div className="space-y-2">
          <Skeleton className="h-8 w-3/4" />
          <Skeleton className="h-8 w-1/2" />
          <Skeleton className="h-8 w-2/3" />
        </div>
      </div>
    );
  }

  if (!chunks || chunks.length === 0) {
    return null;
  }

  const getRechtspraakUrl = (ecli: string) => {
    const ecliMatch = ecli.match(/ECLI:[A-Z]{2}:[A-Z]+:\d+:\d+/);
    const cleanEcli = ecliMatch ? ecliMatch[0] : ecli;
    return `https://uitspraken.rechtspraak.nl/details?id=${cleanEcli}`;
  };

  const handleRelevance = (chunkId: string, isRelevant: boolean) => {
    setChunkRelevance(prev => ({ ...prev, [chunkId]: isRelevant }));
  };

  const handleCommentChange = (chunkId: string, comment: string) => {
    setChunkComments(prev => ({ ...prev, [chunkId]: comment }));
  };

  const handleSubmitFeedback = () => {
    if (onFeedbackSubmit && memoId) {
      const feedback: FeedbackData = {
        chunkRelevance,
        chunkComments,
        generalComment,
        memoId,
        createdAt: new Date().toISOString()
      };
      onFeedbackSubmit(feedback);
      setFeedbackSubmitted(true);
    }
  };

  return (
    <div className="mt-6 bg-gray-50 p-4 rounded-lg border border-gray-200">
      <Accordion type="single" collapsible value={openAccordion || ""} onValueChange={setOpenAccordion}>
        {chunks.map((chunk, index) => {
          const chunkIndex = chunk.metadata.chunk_index ?? index;
          const subChunkIndex = chunk.metadata.sub_chunk_index ?? 0;
          const chunkId = `${chunk.ecli}#${chunkIndex}_${subChunkIndex}`;

          const year = chunk.metadata.date?.slice(0, 4);
          const quarter = chunk.metadata.quarter;

          return (
            <AccordionItem key={chunkId} value={`item-${index}`}>
              <AccordionTrigger className="text-sm py-2">
                <div className="text-left w-full">
                  <div className="flex items-center justify-between w-full">
                    <p className="font-medium text-gray-800 hover:underline flex items-center gap-1">
                      {chunk.metadata.title || chunk.ecli}
                    </p>
                      {year && (
                      <Badge variant="outline" className="ml-2 text-xs">
                        {quarter ? `${year} Q${quarter}` : year}
                      </Badge>
                      )}
                  </div>
                  <div className="flex items-center justify-between text-xs text-gray-500 mt-1">
                    <div>
                      <span>{chunk.metadata.court}</span>
                       {chunk.metadata.procedure && (
                      <Badge variant="secondary" className="text-xs">
                        {chunk.metadata.procedure.replace('procedure#', '')}
                      </Badge>
                    )}
                    </div>
                    <div>
                    {chunk.metadata.procedure && (
                        <Badge variant="secondary" className="text-xs">
                         {t("similarity")}: {(chunk.similarity * 100).toFixed(2)}%
                        </Badge>
                    )}
                    </div>
                  </div>
                </div>
              </AccordionTrigger>
              <AccordionContent className="text-sm text-gray-700">
                <div className="space-y-3">
                  <div className="mb-2">
                    <span className="font-medium text-xs">{t("subject")}:</span> {chunk.metadata.subject}
                  </div>
                  <div className="mb-2">
                    <span className="font-medium text-xs">{t("procedure")}:</span> {chunk.metadata.procedure}
                  </div>
                  <div className="mb-2">
                    <span className="font-medium text-xs">{t("ecliReference")}:</span>{" "}
                    <a 
                      href={getRechtspraakUrl(chunk.ecli)} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="text-primary hover:underline inline-flex items-center"
                    >
                      {chunk.ecli}
                      <ExternalLink className="h-3 w-3 ml-1" />
                    </a>
                  </div>
                  <div className="p-3 bg-white rounded border border-gray-200 text-xs">
                    {chunk.text}
                  </div>

                  {showEvaluation && (
                    <div className="mt-2 p-3 bg-white rounded border border-gray-200">
                      <h5 className="text-xs font-medium mb-2">{t("rateThisSource")}</h5>
                      <div className="flex flex-col gap-2">
                        <div className="flex gap-2">
                          <Button
                            variant={chunkRelevance[chunkId] === true ? "default" : "outline"}
                            size="sm"
                            onClick={() => handleRelevance(chunkId, true)}
                            disabled={feedbackSubmitted}
                          >
                            ✅ {t("relevant")}
                          </Button>
                          <Button
                            variant={chunkRelevance[chunkId] === false ? "destructive" : "outline"}
                            size="sm"
                            onClick={() => handleRelevance(chunkId, false)}
                            disabled={feedbackSubmitted}
                          >
                            ❌ {t("notRelevant")}
                          </Button>
                        </div>

                        <Textarea
                          disabled={feedbackSubmitted}
                          placeholder={t("feedbackPlaceholder") || "Why was this helpful or unhelpful?"}
                          value={chunkComments[chunkId] || ""}
                          onChange={(e) => handleCommentChange(chunkId, e.target.value)}
                          className="mt-2 text-xs min-h-[80px]"
                        />
                      </div>
                    </div>
                  )}
                </div>
              </AccordionContent>
            </AccordionItem>
          );
        })}
      </Accordion>

      {showEvaluation && (
        <div className="mt-6 pt-4 border-t border-gray-200">
          {!feedbackSubmitted ? (
            <div className="space-y-4">
              <div>
                <h4 className="text-sm font-medium mb-2">
                  {t("generalMemoFeedback") || "Overall Feedback on the Generated Memo"}
                </h4>
                <Textarea
                  placeholder={
                    t("generalFeedbackPlaceholder") ||
                    "Was the memo legally sound and clearly reasoned? What could be improved?"
                  }
                  value={generalComment}
                  onChange={(e) => setGeneralComment(e.target.value)}
                  className="min-h-[120px] w-full"
                />
              </div>

              <div className="flex justify-end">
                <Button 
                  onClick={handleSubmitFeedback} 
                  disabled={feedbackSubmitted}
                >
                  {t("submitFeedback")}
                </Button>
              </div>
            </div>
          ) : (
            <div className="bg-green-50 border border-green-100 rounded-md p-4 text-center">
              <p className="text-green-800">{t("feedbackThanks")}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
