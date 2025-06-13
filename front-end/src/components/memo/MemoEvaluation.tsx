
import React, { useMemo } from "react";
import { useLanguage } from "@/contexts/LanguageContext";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Check, X, FileText, FileX, MessageSquareX, EyeOff, Info } from "lucide-react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { EvaluationResult } from '@/types/memoTypes';

interface MemoEvaluationProps {
  evaluation: EvaluationResult;
}

export const MemoEvaluation = ({ evaluation }: MemoEvaluationProps) => {
  const { t } = useLanguage();

  const citationPrecisionPercentage = Math.round(evaluation.citation_precision * 100);
  const citationRecallPercentage = Math.round(evaluation.citation_recall * 100);

  const matchedEclis = useMemo(() => {
    const predictedSet = new Set(evaluation.predicted_eclis);
    const referenceSet = new Set(evaluation.reference_eclis);
    const map = new Map<string, boolean>();

    evaluation.predicted_eclis.forEach(ecli => {
      map.set(ecli, referenceSet.has(ecli));
    });

    evaluation.reference_eclis.forEach(ecli => {
      if (!map.has(ecli)) {
        map.set(ecli, predictedSet.has(ecli));
      }
    });

    return map;
  }, [evaluation.predicted_eclis, evaluation.reference_eclis]);

  const sortedPredictedEclis = useMemo(() => {
    const intersection = evaluation.predicted_eclis.filter(ecli =>
      evaluation.reference_eclis.includes(ecli)
    );
    const nonMatching = evaluation.predicted_eclis.filter(ecli =>
      !evaluation.reference_eclis.includes(ecli)
    );
    return [...intersection, ...nonMatching];
  }, [evaluation.predicted_eclis, evaluation.reference_eclis]);

  const sortedReferenceEclis = useMemo(() => {
    const intersection = evaluation.predicted_eclis.filter(ecli =>
      evaluation.reference_eclis.includes(ecli)
    );
    const nonMatching = evaluation.reference_eclis.filter(ecli =>
      !evaluation.predicted_eclis.includes(ecli)
    );
    return [...intersection, ...nonMatching];
  }, [evaluation.predicted_eclis, evaluation.reference_eclis]);

  return (
    <Card className="mb-6">
      <CardHeader className="pb-2">
        <CardTitle className="text-lg flex items-center gap-2">
          {t("evaluationResults")}
          <Badge 
            variant={evaluation.hallucinated ? "destructive" : "default"} 
            className="ml-2"
          >
            {evaluation.hallucinated ? t("unreliable") : t("reliable")}
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          
          {/* Citation Precision */}
          <div>
            <div className="flex items-center justify-between mb-1">
              <div className="text-sm font-medium flex items-center gap-1">
                {citationPrecisionPercentage >= 70 ? 
                  <Check className="h-4 w-4 text-green-500" /> : 
                  <X className="h-4 w-4 text-red-500" />
                }
                {t("citationPrecision")}
              </div>
              <span className="text-sm font-semibold">
                {citationPrecisionPercentage}%
              </span>
            </div>
            <Progress 
              value={citationPrecisionPercentage} 
              className={`h-2 ${
                citationPrecisionPercentage >= 70 ? 'bg-green-100' : 'bg-red-100'
              }`}
            />
          </div>

          {/* Citation Recall */}
          <div>
            <div className="flex items-center justify-between mb-1">
              <div className="text-sm font-medium flex items-center gap-1">
                <Info className="h-4 w-4 text-blue-500" />
                {t("citationRecall")}
              </div>
              <span className="text-sm font-semibold">
                {citationRecallPercentage}%
              </span>
            </div>
            <Progress 
              value={citationRecallPercentage} 
              className="h-2 bg-blue-100"
            />
          </div>

          {/* Issues Summary */}
          <div className="grid grid-cols-2 gap-2 md:grid-cols-3 mb-4">
            <div className="bg-slate-50 p-3 rounded-md border border-slate-200 flex flex-col items-center">
              <FileX className="h-5 w-5 text-red-500 mb-1" />
              <div className="text-center">
                <p className="text-xs text-gray-500">{t("fabricatedCitations")}</p>
                <p className="text-lg font-semibold">{evaluation.fabricated_eclis}</p>
              </div>
            </div>
            <div className="bg-slate-50 p-3 rounded-md border border-slate-200 flex flex-col items-center">
              <MessageSquareX className="h-5 w-5 text-amber-500 mb-1" />
              <div className="text-center">
                <p className="text-xs text-gray-500">{t("ungroundedStatements")}</p>
                <p className="text-lg font-semibold">{evaluation.ungrounded_statements}</p>
              </div>
            </div>
            <div className="bg-slate-50 p-3 rounded-md border border-slate-200 flex flex-col items-center md:col-span-1 col-span-2">
              <EyeOff className="h-5 w-5 text-gray-500 mb-1" />
              <div className="text-center">
                <p className="text-xs text-gray-500">{t("hallucinated")}</p>
                <p className="text-lg font-semibold">{evaluation.hallucinated ? t("yes") : t("no")}</p>
              </div>
            </div>
          </div>

          {/* ECLI Tables */}
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <h3 className="text-sm font-medium mb-2 flex items-center gap-1">
                <FileText className="h-4 w-4 text-primary" />
                {t("citedSources")} ({sortedPredictedEclis.length})
              </h3>
              <div className="max-h-[200px] overflow-auto border rounded-md">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="w-12">#</TableHead>
                      <TableHead>{t("ecli")}</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {sortedPredictedEclis.length > 0 ? (
                      sortedPredictedEclis.map((ecli, index) => (
                        <TableRow key={`cited-${index}`}>
                          <TableCell className="font-medium">{index + 1}</TableCell>
                          <TableCell className={matchedEclis.get(ecli) ? "text-green-600 font-medium" : "text-red-500"}>
                            {ecli}
                          </TableCell>
                        </TableRow>
                      ))
                    ) : (
                      <TableRow>
                        <TableCell colSpan={2} className="text-center text-muted-foreground h-24">
                          {t("noSourcesCited")}
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </div>
            </div>

            <div>
              <h3 className="text-sm font-medium mb-2 flex items-center gap-1">
                <FileText className="h-4 w-4 text-primary" />
                {t("retrievedSources")} ({sortedReferenceEclis.length})
              </h3>
              <div className="max-h-[200px] overflow-auto border rounded-md">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="w-12">#</TableHead>
                      <TableHead>{t("ecli")}</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {sortedReferenceEclis.length > 0 ? (
                      sortedReferenceEclis.map((ecli, index) => (
                        <TableRow key={`retrieved-${index}`}>
                          <TableCell className="font-medium">{index + 1}</TableCell>
                          <TableCell className={matchedEclis.get(ecli) ? "text-green-600 font-medium" : "text-red-500"}>
                            {ecli}
                          </TableCell>
                        </TableRow>
                      ))
                    ) : (
                      <TableRow>
                        <TableCell colSpan={2} className="text-center text-muted-foreground h-24">
                          {t("noSourcesRetrieved")}
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};
