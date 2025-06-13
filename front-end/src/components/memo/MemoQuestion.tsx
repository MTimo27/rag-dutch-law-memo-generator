
import React from "react";
import { cn } from "@/lib/utils";
import { LucideIcon } from "lucide-react";

interface MemoQuestionProps {
  number: number;
  question: string;
  icon?: React.ReactElement;
  children: React.ReactNode;
  className?: string;
}

export const MemoQuestion: React.FC<MemoQuestionProps> = ({
  number,
  question,
  icon,
  children,
  className,
}) => {
  return (
    <div className={cn("space-y-3", className)}>
      <div className="flex items-start gap-3">
        <div className="flex-shrink-0 w-7 h-7 bg-slate-100 rounded-full flex items-center justify-center text-primary font-semibold">
          {number}
        </div>
        <div className="flex gap-2 items-center">
          {icon && <span className="text-primary">{icon}</span>}
          <h3 className="font-medium text-gray-800 text-sm sm:text-base">{question}</h3>
        </div>
      </div>
      <div className="pl-10">
        {children}
      </div>
    </div>
  );
};
