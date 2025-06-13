
import { Loader2 } from "lucide-react";
import { useEffect, useState } from "react";
import { useLanguage } from "@/contexts/LanguageContext";

interface LoadingSpinnerProps {
  startTime?: number;
  showElapsedTime?: boolean;
}

export const LoadingSpinner = ({ startTime, showElapsedTime = true }: LoadingSpinnerProps) => {
  const { t } = useLanguage();
  const [elapsedTime, setElapsedTime] = useState(0);
  
  useEffect(() => {
    if (!showElapsedTime || !startTime) return;
    
    const timer = setInterval(() => {
      const currentTime = Date.now();
      const elapsed = Math.floor((currentTime - startTime) / 1000);
      setElapsedTime(elapsed);
    }, 1000);
    
    return () => clearInterval(timer);
  }, [startTime, showElapsedTime]);

  return (
    <div className="flex flex-col items-center justify-center p-8 text-center">
      <Loader2 className="h-12 w-12 animate-spin text-primary mb-4" />
      <h3 className="text-lg font-medium">{t("loadingSpinnerTitle")}</h3>
      <p className="text-muted-foreground mt-2">{t("loadingSpinnerDesc")}</p>
      {showElapsedTime && startTime && (
        <p className="text-sm text-muted-foreground mt-4">
          {t("elapsedTime")}: {elapsedTime} {t("seconds")}
        </p>
      )}
    </div>
  );
};
