import { cn } from "@/lib/utils";
import { motion } from "framer-motion";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

interface StatCardProps {
  title: string;
  value: string | number;
  description?: string;
  icon?: React.ReactNode;
  trend?: string;
  change?: {
    value: number;
    positive?: boolean;
  };
  className?: string;
  bgGradient?: string;
  delay?: number;
  sparkline?: React.ReactNode;
}

const StatCard = ({
  title,
  value,
  description,
  icon,
  trend,
  change,
  className,
  bgGradient,
  delay = 0,
  sparkline,
}: StatCardProps) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: delay * 0.1 }}
      whileHover={{ scale: 1.02, transition: { duration: 0.2 } }}
    >
      <Card
        className={cn(
          "overflow-hidden transition-all duration-300 hover:shadow-lg border-opacity-70 h-full",
          className
        )}
        style={
          bgGradient
            ? {
                background: bgGradient,
                boxShadow: "0 4px 12px rgba(0, 0, 0, 0.05)",
              }
            : undefined
        }
      >
        <CardHeader className="flex flex-row items-center justify-between space-y-0 p-3">
          <CardTitle
            className={cn(
              "text-xs font-medium",
              bgGradient && "text-white/90"
            )}
          >
            {icon && (
              <span className="mr-2 inline-flex items-center justify-center">
                {icon}
              </span>
            )}
            {title}
          </CardTitle>
        </CardHeader>
        <CardContent className="p-3 pt-0">
          <div className="space-y-1">
            <div
              className={cn(
                "text-lg md:text-xl font-bold",
                bgGradient && "text-white"
              )}
            >
              {value}
            </div>
            {(description || change) && (
              <div className="flex items-center space-x-2">
                {change && (
                  <span
                    className={cn(
                      "text-xs font-medium flex items-center",
                      bgGradient ? "text-white" : "text-muted-foreground"
                    )}
                  >
                    {Math.abs(change.value)}%
                  </span>
                )}
                {description && (
                  <p
                    className={cn(
                      "text-[0.65rem] truncate",
                      bgGradient
                        ? "text-white/80"
                        : "text-muted-foreground"
                    )}
                  >
                    {description}
                  </p>
                )}
              </div>
            )}
            {sparkline && (
              <div className="pt-1">
                {sparkline}
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
};

export default StatCard;
