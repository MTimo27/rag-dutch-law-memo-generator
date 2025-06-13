import React, { useState, useEffect, useMemo } from "react";
import { JurisprudenceChunk } from "@/types/memoTypes";
import { useLanguage } from "@/contexts/LanguageContext";
import { Calendar, ExternalLink, Search } from "lucide-react";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { LoadingSpinner } from "@/components/ui/LoadingSpinner";

interface UsedDataViewProps {
  chunks: JurisprudenceChunk[];
  dataRange?: { startDate: string; endDate: string } | null;
  isLoading?: boolean;
}

const PAGE_SIZE = 50;

export const UsedDataView = ({
  chunks,
  dataRange = null,
  isLoading = false,
}: UsedDataViewProps) => {
  const { t } = useLanguage();
  const [searchQuery, setSearchQuery] = useState("");
  const [currentPage, setCurrentPage] = useState(1);
  const [calculatedRange, setCalculatedRange] = useState<{
    startDate: string;
    endDate: string;
  } | null>(dataRange);

  const getRechtspraakUrl = (ecli: string) => {
    const ecliMatch = ecli.match(/ECLI:[A-Z]{2}:[A-Z]+:\d+:\d+/);
    const cleanEcli = ecliMatch ? ecliMatch[0] : ecli;
    return `https://uitspraken.rechtspraak.nl/details?id=${cleanEcli}`;
  };

  const computeRange = (): { startDate: string; endDate: string } | null => {
    const rawDates: string[] = chunks
      .map((chunk) => chunk.metadata.date)
      .filter((date): date is string => !!date);

    if (rawDates.length === 0) return null;

    const dates = rawDates
      .map((s) => {
        const parts = s.split("-").map((p) => parseInt(p, 10));
        if (parts.length === 3) {
          const [y, m, d] = parts;
          return new Date(y, m - 1, d);
        }
        return null;
      })
      .filter((d): d is Date => d instanceof Date && !isNaN(d.getTime()));

    if (dates.length === 0) return null;

    const minDate = new Date(Math.min(...dates.map((d) => d.getTime())));
    const maxDate = new Date(Math.max(...dates.map((d) => d.getTime())));

    const formatDate = (d: Date) =>
      `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(
        d.getDate()
      ).padStart(2, "0")}`;

    return {
      startDate: formatDate(minDate),
      endDate: formatDate(maxDate),
    };
  };

  useEffect(() => {
    setCalculatedRange(dataRange ?? computeRange());
  }, [chunks, dataRange]);

  const filteredChunks = useMemo(() => {
    if (!searchQuery.trim()) return chunks;
    const query = searchQuery.toLowerCase();
    return chunks.filter((chunk) =>
      [chunk.metadata.title, chunk.metadata.court, chunk.ecli]
        .some(field => field?.toLowerCase().includes(query))
    );
  }, [searchQuery, chunks]);

  const paginatedChunks = useMemo(() => {
    const start = (currentPage - 1) * PAGE_SIZE;
    return filteredChunks.slice(start, start + PAGE_SIZE);
  }, [filteredChunks, currentPage]);

  const totalPages = Math.ceil(filteredChunks.length / PAGE_SIZE);

  const handlePrevPage = () => setCurrentPage((p) => Math.max(p - 1, 1));
  const handleNextPage = () => setCurrentPage((p) => Math.min(p + 1, totalPages));

  useEffect(() => {
    setCurrentPage(1); // Reset to first page on new search
  }, [searchQuery]);

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg p-4 md:p-6 shadow-sm">
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>{t("availableDataTitle")}</CardTitle>
          <CardDescription>{t("availableDataDescription")}</CardDescription>
        </CardHeader>
        <CardContent>
          {calculatedRange && (
            <div className="flex items-center gap-2 mb-6 bg-slate-50 p-3 rounded-lg">
              <Calendar className="h-5 w-5 text-primary" />
              <div>
                <p className="text-sm font-medium">{t("dataDateRange")}</p>
                <p className="text-sm text-gray-500">
                  {calculatedRange.startDate} - {calculatedRange.endDate}
                </p>
              </div>
            </div>
          )}

          {/* Search Bar */}
          <div className="mb-6">
            <div className="relative w-full">
              <Search className="absolute left-3 top-2.5 h-4 w-4 text-gray-400" />
              <Input
                type="text"
                placeholder={t("searchCases") || "Search by title, court or ECLI..."}
                className="pl-9"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
          </div>

          <div>
            <h3 className="text-lg font-medium mb-3">{t("availableCases")}</h3>
            <Accordion type="single" collapsible className="w-full">
              {paginatedChunks.map((chunk, idx) => (
                <AccordionItem
                  key={`${chunk.ecli}-${idx}`}
                  value={`item-${idx}`}
                  className="border-b border-gray-200"
                >
                  <AccordionTrigger className="py-4 px-4 hover:bg-slate-50 rounded-md transition-colors">
                    <div className="flex flex-col md:flex-row md:items-center w-full gap-2 text-left">
                      <div className="flex-1">
                        <h4 className="font-medium text-primary text-base">{chunk.metadata.title || chunk.ecli}</h4>
                        <span className="text-sm text-muted-foreground">{chunk.metadata.court}</span>
                      </div>
                      <div className="flex gap-2 flex-wrap">
                        {chunk.metadata.date && (
                          <Badge variant="outline" className="flex items-center gap-1 whitespace-nowrap">
                            <Calendar className="h-3 w-3 text-muted-foreground" />
                            {chunk.metadata.date}
                          </Badge>
                        )}
                        <Badge variant="secondary" className="whitespace-nowrap">
                          {chunk.metadata.procedure?.replace("procedure#", "") || t("unknownProcedure")}
                        </Badge>
                      </div>
                    </div>
                  </AccordionTrigger>
                  <AccordionContent className="px-4 pb-4 pt-2">
                    <div className="space-y-4">
                      <div>
                        <h5 className="text-sm font-medium text-muted-foreground mb-1">{t("subject")}</h5>
                        <p className="text-sm">{chunk.metadata.subject?.replace("rechtsgebied#", "") || "-"}</p>
                      </div>
                      <div>
                        <h5 className="text-sm font-medium text-muted-foreground mb-1">{t("caseReference")}</h5>
                        <p className="text-sm">
                          <a 
                            href={getRechtspraakUrl(chunk.ecli)} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className="text-primary hover:underline flex items-center gap-1"
                          >
                            {chunk.ecli} <ExternalLink className="h-3 w-3 inline" />
                          </a>
                        </p>
                      </div>
                      <div>
                        <h5 className="text-sm font-medium text-muted-foreground mb-1">{t("relevantText")}</h5>
                        <div className="text-sm bg-slate-50 p-3 rounded-md border border-slate-200 whitespace-pre-wrap">{chunk.text}</div>
                      </div>
                    </div>
                  </AccordionContent>
                </AccordionItem>
              ))}
            </Accordion>

            {filteredChunks.length === 0 && (
              <div className="text-center p-8 bg-slate-50 rounded-lg">
                <p className="text-muted-foreground">{t("noDataAvailable")}</p>
              </div>
            )}

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex justify-center items-center mt-6 gap-4">
                <button
                  onClick={handlePrevPage}
                  disabled={currentPage === 1}
                  className="px-4 py-1 border rounded text-sm disabled:opacity-50"
                >
                  {t("prev") || "Previous"}
                </button>
                <span className="text-sm">
                  {t("page")} {currentPage} / {totalPages}
                </span>
                <button
                  onClick={handleNextPage}
                  disabled={currentPage === totalPages}
                  className="px-4 py-1 border rounded text-sm disabled:opacity-50"
                >
                  {t("next") || "Next"}
                </button>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
