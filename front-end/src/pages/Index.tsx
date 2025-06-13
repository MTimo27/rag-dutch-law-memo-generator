import { useState, useEffect } from "react";
import { MemoForm } from "@/components/memo/MemoForm";
import { MemoPreview } from "@/components/memo/MemoPreview";
import { UsedDataView } from "@/components/memo/UsedDataView";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { EvaluationResult, JurisprudenceChunk, MemoFormData } from "@/types/memoTypes";
import { useLanguage } from "@/contexts/LanguageContext";
import { LanguageToggle } from "@/components/ui/language-toggle";
import { BookOpen, Database, Edit } from "lucide-react";
import { generateMemo, getAllChunks, evaluateMemo } from "@/services/memoService";
import { useToast } from "@/components/ui/use-toast";
import { useIsMobile } from "@/hooks/use-mobile";
import { LoadingSpinner } from "@/components/ui/LoadingSpinner";
import { useQuery } from "@tanstack/react-query";


// Session storage keys
const SESSION_MEMO_DATA = "memo_form_data";
const SESSION_MEMO_CONTENT = "memo_content";
const SESSION_MEMO_CHUNKS = "memo_chunks";
const SESSION_MEMO_ID = "memo_id";
const SESSION_MEMO_EVALUATION = "memo_evaluation";

const Index = () => {
  const { t } = useLanguage();
  const { toast } = useToast();
  const isMobile = useIsMobile();
  const [activeTab, setActiveTab] = useState("editor");
  
  const [memoData, setMemoData] = useState<MemoFormData>({
    disputedDecision: "",
    desiredOutcome: "",
    criticalFacts: "",
    applicableLaw: "other",
    recipients: "lawyer"
  });
  const [memoGenerated, setMemoGenerated] = useState(false);
  const [memoContent, setMemoContent] = useState<string>("");
  const [isGenerating, setIsGenerating] = useState(false);
  const [generationStartTime, setGenerationStartTime] = useState<number | null>(null);
  const [jurisprudenceChunks, setJurisprudenceChunks] = useState<JurisprudenceChunk[]>([]);
  const [dataRange, setDataRange] = useState<{ startDate: string; endDate: string } | null>(null);
  const [memoId, setMemoId] = useState<string>("");
  const [evaluation, setEvaluation] = useState<EvaluationResult | undefined>(undefined);
  const [similarityMetric, setSimilarityMetric] = useState<"cosine" | "dot" | "euclidean">("cosine");

  // Fetch all available chunks for the "used-data" tab
  const { data: databaseInfo, isLoading: isLoadingAllChunks } = useQuery({
    queryKey: ['allChunks'],
    queryFn: getAllChunks,
    enabled: activeTab === "used-data",
  });

  // Load data from session storage on initial render
  useEffect(() => {
    const savedMemoData = sessionStorage.getItem(SESSION_MEMO_DATA);
    const savedMemoContent = sessionStorage.getItem(SESSION_MEMO_CONTENT);
    const savedMemoChunks = sessionStorage.getItem(SESSION_MEMO_CHUNKS);
    const savedMemoId = sessionStorage.getItem(SESSION_MEMO_ID);
    const savedEvaluation = sessionStorage.getItem(SESSION_MEMO_EVALUATION);
    
    if (savedMemoData && savedMemoContent) {
      try {
        const parsedMemoData = JSON.parse(savedMemoData) as MemoFormData;
        const parsedMemoContent = JSON.parse(savedMemoContent) as string;
        const parsedMemoChunks = savedMemoChunks ? JSON.parse(savedMemoChunks) as JurisprudenceChunk[] : [];
        const parsedMemoId = savedMemoId || `memo-${Date.now()}`;
        const parsedEvaluation = savedEvaluation ? JSON.parse(savedEvaluation) as EvaluationResult : undefined;
        
        setMemoData(parsedMemoData);
        setMemoContent(parsedMemoContent);
        setJurisprudenceChunks(parsedMemoChunks);
        setMemoId(parsedMemoId);
        setEvaluation(parsedEvaluation);
        setMemoGenerated(true);
      } catch (error) {
        console.error("Failed to parse session storage data:", error);
      }
    }
  }, []);

  // Save data to session storage whenever it changes
  useEffect(() => {
    if (memoGenerated && memoContent) {
      sessionStorage.setItem(SESSION_MEMO_DATA, JSON.stringify(memoData));
      sessionStorage.setItem(SESSION_MEMO_CONTENT, JSON.stringify(memoContent));
      
      if (jurisprudenceChunks && jurisprudenceChunks.length > 0) {
        sessionStorage.setItem(SESSION_MEMO_CHUNKS, JSON.stringify(jurisprudenceChunks));
      }
      
      if (memoId) {
        sessionStorage.setItem(SESSION_MEMO_ID, memoId);
      }

      if (evaluation) {
        sessionStorage.setItem(SESSION_MEMO_EVALUATION, JSON.stringify(evaluation));
      }
    }
  }, [memoGenerated, memoContent, memoData, jurisprudenceChunks, memoId, evaluation]);

  const handleGenerateMemo = async (formData: MemoFormData) => {
    setIsGenerating(true);
    setGenerationStartTime(Date.now());
    setMemoData(formData);
  
    const newMemoId = `memo-${Date.now()}`;
    setMemoId(newMemoId);
    setActiveTab("preview");
  
    try {
      const response = await generateMemo(formData, newMemoId);
      setMemoContent(response.memo);
      setJurisprudenceChunks(response.chunks || []);
      setEvaluation(undefined); 
      setDataRange({
        startDate: "2015-01-01",
        endDate: new Date().toISOString().split('T')[0]
      });
  
      setMemoGenerated(true);
  
      toast({
        title: t("memoGenerated"),
        description: t("memoGeneratedDesc"),
      });
    } catch (error) {
      console.error("Failed to generate memo:", error);
      toast({
        title: t("memoGenerationFailed"),
        description: t("memoGenerationFailedDesc"),
        variant: "destructive"
      });
      setActiveTab("editor");
    } finally {
      setIsGenerating(false);
      setGenerationStartTime(null);
    }
  };

  const handleEvaluateMemo = async (metric: "cosine" | "dot" | "euclidean", thresholdMetric: number) => {
    try {
      const result = await evaluateMemo(memoContent, jurisprudenceChunks, metric, thresholdMetric);
      setEvaluation(result);
      sessionStorage.setItem(SESSION_MEMO_EVALUATION, JSON.stringify(result));
      toast({
        title: t("evaluationComplete"),
        description: t("evaluationCompleteDesc"),
      });
    } catch (error) {
      console.error("Memo evaluation failed:", error);
      toast({
        title: t("evaluationFailed"),
        description: t("evaluationFailedDesc"),
        variant: "destructive",
      });
    }
  };

  const handleMemoContentChange = (content: string) => {
    setMemoContent(content);
  };

  return (
    <div className="flex flex-col min-h-screen bg-slate-50">
      <header className="bg-white py-3 md:py-4 shadow-sm">
        <div className="container mx-auto px-4 flex flex-col sm:flex-row justify-between items-center gap-2 sm:gap-0">
          <div className="flex items-center gap-3 sm:gap-4">
                <img 
                  src="/logo.png" 
                  alt="Logo" 
                  className="w-12 h-12 sm:w-12 sm:h-12 rounded-full"
                />
                <div className="text-center sm:text-left">
                  <h1 className="text-xl sm:text-2xl font-bold text-gray-800">
                  {t("appTitle")}
                  </h1>
                  <p className="text-gray-500 text-xs sm:text-sm">
                  {t("appDescription")}
                  </p>
                </div>
                </div>
          <LanguageToggle />
        </div>
      </header>

      <main className="flex-grow container mx-auto px-4 py-4 md:py-8">
        <div className="p-2 md:p-6">
          <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
            <TabsList className="grid w-full max-w-md mx-auto grid-cols-3 mb-4 md:mb-6">
              <TabsTrigger value="editor" className="flex items-center gap-1 sm:gap-2 text-sm sm:text-base">
                <Edit className="h-3 w-3 sm:h-4 sm:w-4" />
                <span>{t("editor")}</span>
              </TabsTrigger>
              <TabsTrigger value="preview" className="flex items-center gap-1 sm:gap-2 text-sm sm:text-base">
                <BookOpen className="h-3 w-3 sm:h-4 sm:w-4" />
                <span>{t("preview")}</span>
              </TabsTrigger>
              <TabsTrigger value="used-data" className="flex items-center gap-1 sm:gap-2 text-sm sm:text-base">
                <Database className="h-3 w-3 sm:h-4 sm:w-4" />
                <span>{t("usedData")}</span>
              </TabsTrigger>
            </TabsList>
            
            <TabsContent value="editor" className="mt-0">
              <div className="max-w-4xl mx-auto">
                <p className="text-center text-gray-600 text-sm md:text-base mb-4 md:mb-6">
                  {t("editorDescription")}
                </p>
                <MemoForm 
                  onGenerateMemo={handleGenerateMemo}
                  onContentChange={handleMemoContentChange}
                />
              </div>
            </TabsContent>
            
            <TabsContent value="preview" className="mt-0">
              <div className="max-w-4xl mx-auto">
                {isGenerating ? (
                  <div className="bg-white rounded-lg p-4 md:p-6 shadow-sm">
                    <LoadingSpinner startTime={generationStartTime || undefined} />
                  </div>
                ) : memoGenerated ? (
                  <MemoPreview 
                    formData={memoData}
                    content={memoContent}
                    chunks={jurisprudenceChunks}
                    evaluation={evaluation}
                    onContentChange={handleMemoContentChange}
                    onEvaluate={handleEvaluateMemo}
                    memoId={memoId}
                  />
                ) : (
                  <div className="bg-white rounded-lg p-4 md:p-6 text-center shadow-sm">
                    <p className="text-gray-500 text-sm md:text-base">
                      {t("previewEmpty")}
                    </p>
                  </div>
                )}
              </div>
            </TabsContent>
            
            <TabsContent value="used-data" className="mt-0">
              <div className="max-w-4xl mx-auto">
                {isLoadingAllChunks ? (
                  <div className="bg-white rounded-lg p-4 md:p-6 shadow-sm">
                    <LoadingSpinner />
                  </div>
                ) : databaseInfo && databaseInfo.chunks.length > 0 ? (
                  <UsedDataView 
                    chunks={databaseInfo.chunks} 
                    isLoading={isLoadingAllChunks}
                  />
                ) : (
                  <div className="bg-white rounded-lg p-4 md:p-6 text-center shadow-sm">
                    <p className="text-gray-500 text-sm md:text-base">
                      {t("noDataAvailable")}
                    </p>
                  </div>
                )}
              </div>
            </TabsContent>
          </Tabs>
        </div>
      </main>

      <footer className="bg-white py-4 md:py-6 border-t mt-auto">
        <div className="container mx-auto px-4 text-center text-xs sm:text-sm text-gray-500">
          <p>{t("footer")}</p>
          <p className="mt-1">{t("footerDisclaimer")}</p>
        </div>
      </footer>
    </div>
  );
};

export default Index;
