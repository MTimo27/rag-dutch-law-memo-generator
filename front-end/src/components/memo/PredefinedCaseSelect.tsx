
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useLanguage } from "@/contexts/LanguageContext";
import { PredefinedCase } from "@/types/memoTypes";
import { useState } from "react";

interface PredefinedCaseSelectProps {
  onSelectCase: (caseData: PredefinedCase | null) => void;
}

export const PredefinedCaseSelect = ({ onSelectCase }: PredefinedCaseSelectProps) => {
  const { t } = useLanguage();
  const [selectedCase, setSelectedCase] = useState<string | null>(() => {
    return sessionStorage.getItem("selectedCaseId") || "";
  });

  // Predefined test cases
  const predefinedCases: PredefinedCase[] = [
    {
      id: "test-case-1",
      name: t("testCase1"),
      formData: {
        disputedDecision: "Afwijzing van een WW-uitkering door het UWV",
        desiredOutcome: "Toekenning van WW-uitkering met terugwerkende kracht",
        criticalFacts: "Cliënt heeft 26 weken gewerkt, maar UWV telt 3 weken niet mee vanwege ziekte. Werkgever bevestigt echter dat cliënt deze weken gewoon heeft doorgewerkt.",
        applicableLaw: "ww",
        recipients: "lawyer",
        isPredefinedCase: true
      }
    },
    {
      id: "test-case-2",
      name: t("testCase2"),
      formData: {
        disputedDecision: "Terugvordering van bijstand door de gemeente",
        desiredOutcome: "Intrekking van de terugvordering",
        criticalFacts: "Cliënt heeft samenwoning niet gemeld, maar woonde feitelijk apart van huisgenoot met eigen huurcontract en gescheiden financiën.",
        applicableLaw: "participatiewet",
        recipients: "judge",
        isPredefinedCase: true
      }
    },
    {
      id: "test-case-3",
      name: t("testCase3"),
      formData: {
        disputedDecision: "Afwijzing aanvraag huurtoeslag",
        desiredOutcome: "Toekenning huurtoeslag",
        criticalFacts: "Belastingdienst stelt dat cliënt te hoog inkomen had, maar heeft buitengewone zorgkosten niet meegenomen in de berekening.",
        applicableLaw: "toeslagenwet",
        recipients: "caseworker",
        isPredefinedCase: true
      }
    },
    {
      id: "test-case-4",
      name: t("testCase4"),
      formData: {
        disputedDecision: "Beëindiging van de WIA-uitkering door het UWV wegens vermeende herstel",
        desiredOutcome: "Voortzetting van de WIA-uitkering",
        criticalFacts: "Cliënt is door een onafhankelijke arts nog volledig arbeidsongeschikt bevonden. UWV heeft slechts éénzijdig medisch dossier gebruikt.",
        applicableLaw: "wia",
        recipients: "lawyer",
        isPredefinedCase: true
      }
    },
    {
      id: "test-case-5",
      name: t("testCase5"),
      formData: {
        disputedDecision: "Afwijzing AOW-aanvraag wegens onvoldoende opbouwjaren",
        desiredOutcome: "Toekenning volledige AOW",
        criticalFacts: "SVB heeft buitenlandperiodes niet meegeteld, terwijl cliënt in die periode wel in Nederland verzekerd was via detachering en premies heeft betaald.",
        applicableLaw: "aow",
        recipients: "client",
        isPredefinedCase: true
      }
    }
  ];

  const handleSelectCase = (value: string) => {
    setSelectedCase(value);
    sessionStorage.setItem("selectedCaseId", value);

    if (value === "custom") {
      onSelectCase(null);
      return;
    }

    const selectedPredefinedCase = predefinedCases.find(c => c.id === value);
    if (selectedPredefinedCase) {
      onSelectCase(selectedPredefinedCase);
    }
  };

  return (
    <div className="mb-8 p-4 bg-blue-50 rounded-lg border border-blue-100">
      <h3 className="font-medium text-blue-800 mb-2">{t("selectTestCase")}</h3>
      <Select value={selectedCase || ""} onValueChange={handleSelectCase}>
        <SelectTrigger className="w-full">
          <SelectValue placeholder={t("selectTestCasePlaceholder")} />
        </SelectTrigger>
        <SelectContent>
          {predefinedCases.map((testCase) => (
            <SelectItem key={testCase.id} value={testCase.id}>
              {testCase.name}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      <p className="text-xs text-blue-600 mt-2">{t("testCaseDescription")}</p>
    </div>
  );
};
