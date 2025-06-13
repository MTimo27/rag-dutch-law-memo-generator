
import { useEffect, useState } from "react";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { MemoQuestion } from "./MemoQuestion";
import { useToast } from "@/components/ui/use-toast";
import { useLanguage } from "@/contexts/LanguageContext";
import { MemoFormData, PredefinedCase } from "@/types/memoTypes";
import { AlertDialog, AlertDialogContent, AlertDialogDescription, AlertDialogHeader, AlertDialogTitle } from "@/components/ui/alert-dialog";
import { Loader2 } from "lucide-react";
import { 
  FileText, 
  Target, 
  Info,
  AlertTriangle, 
  Users 
} from "lucide-react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { PredefinedCaseSelect } from "./PredefinedCaseSelect";

interface MemoFormProps {
  onGenerateMemo: (formData: MemoFormData, memoId: string) => void;
  onContentChange: (content: string) => void;
}

export const MemoForm = ({ onGenerateMemo, onContentChange }: MemoFormProps) => {
  const { toast } = useToast();
  const { t } = useLanguage();
  const [showDisclaimer, setShowDisclaimer] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [memoId] = useState(() => `memo-${Date.now()}`);
  const [formData, setFormData] = useState<MemoFormData>({
    disputedDecision: "",
    desiredOutcome: "",
    criticalFacts: "",
    applicableLaw: "wia",
    recipients: "lawyer"
  });

  const handleSelectPredefinedCase = (caseData: PredefinedCase | null) => {
    if (caseData) {
      setFormData(caseData.formData);
      sessionStorage.setItem("memoFormData", JSON.stringify(caseData.formData));
    } else {
      toast({
        title: t("selectCaseRequired"),
        description: t("pleaseChooseFromList"),
        variant: "destructive"
      });
    }
  };

  const handleGenerateMemo = () => {
    if (!formData.disputedDecision || !formData.desiredOutcome) {
      toast({
        title: t("missingInfo"),
        description: t("missingInfoDesc"),
        variant: "destructive"
      });
      return;
    }
    setShowDisclaimer(true);
  };

  const confirmGeneration = () => {
    setIsSubmitting(true);
    
    // Close disclaimer
    setShowDisclaimer(false);
    
    // Pass the form data to parent component to handle API call
    onGenerateMemo(formData, memoId);
    
    // Reset submission state
    setIsSubmitting(false);
  };

  useEffect(() => {
  const storedData = sessionStorage.getItem("memoFormData");
    if (storedData) {
      try {
        const parsed = JSON.parse(storedData);
        setFormData(parsed);
      } catch (e) {
        console.error("Failed to parse stored form data:", e);
      }
    }
  }, []);

  return (
    <>
      <div className="space-y-6 p-6 bg-white rounded-lg shadow-sm">
        <PredefinedCaseSelect onSelectCase={handleSelectPredefinedCase} />

        <MemoQuestion 
          number={1} 
          icon={<FileText className="text-primary" />}
          question={t("disputedDecisionQuestion")}
        >
          <Input
            placeholder={t("disputedDecisionPlaceholder")}
            value={formData.disputedDecision}
            disabled
            className="bg-gray-100 cursor-not-allowed"
          />
        </MemoQuestion>

        <MemoQuestion number={2} icon={<Target className="text-primary" />} question={t("desiredOutcomeQuestion")}>
          <Input
            placeholder={t("desiredOutcomePlaceholder")}
            value={formData.desiredOutcome}
            disabled
            className="bg-gray-100 cursor-not-allowed"
          />
        </MemoQuestion>

        <MemoQuestion number={3} icon={<Info className="text-primary" />} question={t("factsQuestion")}>
          <Textarea
            placeholder={t("factsPlaceholder")}
            value={formData.criticalFacts}
            disabled
            className="textarea-autosize bg-gray-100 cursor-not-allowed"
          />
        </MemoQuestion>

        <MemoQuestion number={4} icon={<AlertTriangle className="text-primary" />} question={t("applicableLawQuestion")}>
          <Select value={formData.applicableLaw} disabled>
            <SelectTrigger className="w-full bg-gray-100 cursor-not-allowed">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="wia">{t("wia")}</SelectItem>
              <SelectItem value="ww">{t("ww")}</SelectItem>
              <SelectItem value="aow">{t("aow")}</SelectItem>
              <SelectItem value="participatiewet">{t("participatiewet")}</SelectItem>
              <SelectItem value="toeslagenwet">{t("toeslagenwet")}</SelectItem>
              <SelectItem value="other">{t("otherLaw")}</SelectItem>
            </SelectContent>
          </Select>
        </MemoQuestion>

        <MemoQuestion number={5} icon={<Users className="text-primary" />} question={t("recipientsQuestion")}>
          <Select value={formData.recipients} disabled>
            <SelectTrigger className="w-full bg-gray-100 cursor-not-allowed">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="lawyer">{t("lawyer")}</SelectItem>
              <SelectItem value="client">{t("client")}</SelectItem>
              <SelectItem value="judge">{t("judge")}</SelectItem>
              <SelectItem value="legalStaff">{t("legalStaff")}</SelectItem>
              <SelectItem value="caseworker">{t("caseworker")}</SelectItem>
            </SelectContent>
          </Select>
        </MemoQuestion>

        <div className="flex justify-center mt-8">
          <Button 
            onClick={handleGenerateMemo} 
            className="w-full max-w-md py-6"
          >
            {t("createMemo")}
          </Button>
        </div>
      </div>

      <AlertDialog open={showDisclaimer} onOpenChange={setShowDisclaimer}>
        <AlertDialogContent className="max-w-lg">
          <AlertDialogHeader>
            <AlertDialogTitle>❗{t("disclaimerTitle")}</AlertDialogTitle>
            <AlertDialogDescription className="space-y-4">
              <p>{t("disclaimerText1")}</p>
              <p>{t("disclaimerText2")}</p>
              <p>{t("disclaimerText3")}</p>
              <p className='font-bold'>{t("disclaimerText4")}</p>
            </AlertDialogDescription>
          </AlertDialogHeader>
          <div className="flex justify-end gap-3 mt-4">
            <Button variant="outline" onClick={() => setShowDisclaimer(false)} disabled={isSubmitting}>
              {t("cancel")}
            </Button>
            <Button onClick={confirmGeneration} disabled={isSubmitting}>
              {isSubmitting ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  {t("generating")}
                </>
              ) : (
                t("understand")
              )}
            </Button>
          </div>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
};
