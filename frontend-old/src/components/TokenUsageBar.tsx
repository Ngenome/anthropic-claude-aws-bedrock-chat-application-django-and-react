import React from "react";
import { Progress } from "@/components/ui/progress";
import { cn } from "@/lib/utils";

interface TokenUsageBarProps {
  current: number;
  max: number;
  label?: string;
  className?: string;
}

export function TokenUsageBar({
  current,
  max,
  label,
  className,
}: TokenUsageBarProps) {
  const percentage = (current / max) * 100;
  const getColor = () => {
    if (percentage > 90) return "bg-red-500";
    if (percentage > 70) return "bg-yellow-500";
    return "bg-green-500";
  };

  return (
    <div className={cn("space-y-2", className)}>
      {label && (
        <div className="flex justify-between text-sm">
          <span>{label}</span>
          <span>
            {current.toLocaleString()} / {max.toLocaleString()} (
            {percentage.toFixed(1)}%)
          </span>
        </div>
      )}
      <Progress value={percentage} className={cn("h-2", getColor())} />
    </div>
  );
}
