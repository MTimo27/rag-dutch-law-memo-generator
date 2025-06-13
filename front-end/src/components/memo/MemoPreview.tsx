import { useEffect, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { MemoFormData, FeedbackData } from "@/types/memoTypes";
import { Copy, Download, CheckCircle, RefreshCcw } from "lucide-react";
import { useToast } from "@/components/ui/use-toast";
import { useLanguage } from "@/contexts/LanguageContext";
import { JurisprudenceChunk, EvaluationResult } from "@/types/memoTypes";
import { JurisprudenceChunks } from "./JurisprudenceChunks";
import { MemoEvaluation } from "./MemoEvaluation";
import { Loader2 } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { saveMemoWithFeedback } from "@/services/memoService";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";

import { Crepe } from "@milkdown/crepe";
import { getMarkdown } from "@milkdown/utils";
import { EditorStatus } from "@milkdown/core";
import "@milkdown/crepe/theme/common/style.css";
import "@milkdown/crepe/theme/frame.css";

interface MemoPreviewProps {
  formData: MemoFormData;
  content: string;
  chunks?: JurisprudenceChunk[];
  evaluation?: EvaluationResult;
  onContentChange: (content: string) => void;
  onEvaluate: (similarityMetric: "cosine" | "dot" | "euclidean", thresholdMetric: number) => void;
  memoId: string;
}

export const MemoPreview = ({
  formData,
  content,
  chunks = [],
  evaluation,
  onContentChange,
  onEvaluate,
  memoId
}: MemoPreviewProps) => {
  const { toast } = useToast();
  const { t, language } = useLanguage();
  const [editableContent, setEditableContent] = useState(content);
  const [copySuccess, setCopySuccess] = useState(false);
  const [showPreviewDialog, setShowPreviewDialog] = useState(false);
  const [feedbackSubmitted, setFeedbackSubmitted] = useState(false);
  const [submittingFeedback, setSubmittingFeedback] = useState(false);
  const [isEvaluating, setIsEvaluating] = useState(false);
  const [similarityMetric, setSimilarityMetric] = useState<"cosine" | "dot" | "euclidean">("cosine");
  const [thresholdMetric, setThresholdMetric] = useState<number>(0.7);

  const editorRef = useRef<HTMLDivElement | null>(null);
  const editorInstance = useRef<Crepe | null>(null);

  const currentDate = new Date().toLocaleDateString(
    language === 'nl' ? 'nl-NL' : 'en-US',
    { year: 'numeric', month: 'long', day: 'numeric' }
  );

  useEffect(() => {
    if (!editorRef.current) return;

    const crepe = new Crepe({
      root: editorRef.current,
      defaultValue: editableContent,
    });

    crepe.create().then(() => {
      const interval = setInterval(async () => {
        if (crepe.editor?.status === EditorStatus.Created) {
          // Get the content as markdown
          const md = await crepe.editor.action(getMarkdown());
          setEditableContent(md);
          onContentChange(md);
        }
      }, 500);

      editorInstance.current = crepe;

      return () => {
        clearInterval(interval);
        crepe.destroy();
      };
    });
  }, []);

  const handleEvaluate = async () => {
    setIsEvaluating(true);
    try {
      await onEvaluate(similarityMetric, thresholdMetric);
    } finally {
      setIsEvaluating(false);
    }
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(editableContent);
    setCopySuccess(true);
    setTimeout(() => setCopySuccess(false), 2000);
    toast({ title: t("copied"), description: t("copiedDesc") });
  };

  const handleDownload = () => {
    const blob = new Blob([editableContent], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = language === 'nl' ? 'juridisch-memo.md' : 'legal-memo.md';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    toast({ title: t("downloaded"), description: t("downloadedDesc") });
  };

  const handleFeedbackSubmit = async (feedback: FeedbackData) => {
    try {
      setSubmittingFeedback(true);

      const result = await saveMemoWithFeedback({
        id: memoId,
        content: editableContent,
        formData,
        chunks,
        createdAt: new Date().toISOString(),
        feedback,
      });

      if (result.id === memoId) {
        setFeedbackSubmitted(true);
        toast({
          title: t("feedbackSubmitted"),
          description: t("feedbackSubmittedDesc"),
        });
      }
    } catch (error) {
      console.error("Error saving feedback:", error);
      toast({
        title: t("errorSubmittingFeedback"),
        description: t("errorSubmittingFeedbackDesc"),
        variant: "destructive",
      });
    } finally {
      setSubmittingFeedback(false);
    }
  };

  // Handle threshold change from slider
  const handleSliderChange = (value: number[]) => {
    setThresholdMetric(value[0]);
  };

  // Handle threshold change from input field
  const handleInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const value = parseFloat(event.target.value);
    if (!isNaN(value) && value >= 0 && value <= 1) {
      setThresholdMetric(value);
    }
  };

  return (
    <div className="p-4 bg-white rounded-md shadow-sm relative">
      <div className="absolute top-4 right-4 flex gap-2">
        <Button variant="outline" size="icon" onClick={handleCopy} className="h-8 w-8">
          {copySuccess ? <CheckCircle className="h-4 w-4 text-green-500" /> : <Copy className="h-4 w-4" />}
        </Button>
        <Button variant="outline" size="icon" onClick={handleDownload} className="h-8 w-8">
          <Download className="h-4 w-4" />
        </Button>
      </div>

      <div className="space-y-4 pt-4">
        <div className="text-center mb-4">
          <h2 className="text-lg font-semibold">{t("legalMemoTitle")}</h2>
          <p className="text-gray-500 text-sm">{currentDate}</p>
          <p className="mt-2 text-red-500 text-xs italic">{t("llmDisclaimer")}</p>
        </div>

        <div ref={editorRef} className="min-h-[400px] border border-gray-200 rounded-md p-3 bg-white" />

        {!evaluation && (
          <div className="flex flex-col sm:flex-row justify-center items-center gap-4 mt-6">
            <div className="w-full max-w-xs space-y-4">
              <div className="space-y-2">
                <Label htmlFor="similarity-metric">{t("selectSimilarityMetric") || "Similarity Metric"}</Label>
                <Select
                  value={similarityMetric}
                  onValueChange={(value) => setSimilarityMetric(value as "cosine" | "dot" | "euclidean")}
                >
                  <SelectTrigger id="similarity-metric" className="w-full">
                    <SelectValue placeholder={t("selectSimilarityMetric") || "Select similarity metric"} />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="cosine">Cosine Similarity</SelectItem>
                    <SelectItem value="dot">Dot Product</SelectItem>
                    <SelectItem value="euclidean">Euclidean Distance</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              
              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <Label htmlFor="threshold-metric">{t("thresholdValue") || "Threshold Value"}</Label>
                  <span className="text-sm text-gray-500">{thresholdMetric.toFixed(2)}</span>
                </div>
                <Slider
                  id="threshold-slider"
                  min={0}
                  max={1}
                  step={0.01}
                  value={[thresholdMetric]}
                  onValueChange={handleSliderChange}
                  className="mb-2"
                />
                <Input
                  id="threshold-metric"
                  type="number"
                  min={0}
                  max={1}
                  step={0.01}
                  value={thresholdMetric}
                  onChange={handleInputChange}
                  className="w-full"
                />
              </div>
            </div>
            <Button onClick={handleEvaluate} disabled={isEvaluating} className="inline-flex gap-2">
              {isEvaluating ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <RefreshCcw className="h-4 w-4" />
              )}
              {t("evaluateMemo")}
            </Button>
          </div>
        )}

        {evaluation && (
          <div className="space-y-4">
            <div className="flex flex-col sm:flex-row justify-between items-center gap-4 border-t pt-4">
              <div className="w-full max-w-xs space-y-2">
                <Label htmlFor="similarity-metric-evaluation">{t("selectSimilarityMetric") || "Similarity Metric"}</Label>
                <Select
                  value={similarityMetric}
                  onValueChange={(value) => setSimilarityMetric(value as "cosine" | "dot" | "euclidean")}
                >
                  <SelectTrigger id="similarity-metric-evaluation" className="w-full">
                    <SelectValue placeholder={t("selectSimilarityMetric")} />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="cosine">Cosine Similarity</SelectItem>
                    <SelectItem value="dot">Dot Product</SelectItem>
                    <SelectItem value="euclidean">Euclidean Distance</SelectItem>
                  </SelectContent>
                </Select>
                
                <div className="flex justify-between items-center mt-2">
                  <Label htmlFor="threshold-metric-evaluation">{t("thresholdValue") || "Threshold Value"}</Label>
                  <span className="text-sm text-gray-500">{thresholdMetric.toFixed(2)}</span>
                </div>
                <Slider
                  id="threshold-slider-evaluation"
                  min={0}
                  max={1}
                  step={0.01}
                  value={[thresholdMetric]}
                  onValueChange={handleSliderChange}
                  className="mb-2"
                />
                <Input
                  id="threshold-metric-evaluation"
                  type="number"
                  min={0}
                  max={1}
                  step={0.01}
                  value={thresholdMetric}
                  onChange={handleInputChange}
                  className="w-full"
                />
              </div>
              <Button onClick={handleEvaluate} disabled={isEvaluating} className="inline-flex gap-2">
                {isEvaluating ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <RefreshCcw className="h-4 w-4" />
                )}
                {t("reevaluateMemo")}
              </Button>
            </div>
            <MemoEvaluation evaluation={evaluation} />
          </div>
        )}

        {chunks && chunks.length > 0 && (
          <JurisprudenceChunks
            chunks={chunks}
            showEvaluation={true}
            memoId={memoId}
            onFeedbackSubmit={handleFeedbackSubmit}
          />
        )}
      </div>

      <Dialog open={showPreviewDialog} onOpenChange={setShowPreviewDialog}>
        <DialogContent className="max-w-3xl max-h-[80vh] overflow-auto">
          <DialogHeader>
            <DialogTitle>{t("rawMarkdown")}</DialogTitle>
            <DialogDescription>{t("rawMarkdownDesc")}</DialogDescription>
          </DialogHeader>
          <pre className="bg-gray-100 p-4 rounded-md overflow-x-auto text-sm">
            {editableContent}
          </pre>
        </DialogContent>
      </Dialog>
    </div>
  );
};
