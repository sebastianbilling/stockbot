"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { formatDistanceToNow } from "date-fns";
import { TrendingDown, TrendingUp, Minus } from "lucide-react";
import { useAuth } from "@/hooks/use-auth";
import { api } from "@/lib/api-client";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import type { Recommendation } from "@/types";

const actionFilters = [
  { value: "", label: "All" },
  { value: "BUY", label: "Buy" },
  { value: "SELL", label: "Sell" },
  { value: "HOLD", label: "Hold" },
];

export default function RecommendationsPage() {
  const { token } = useAuth();
  const [filter, setFilter] = useState("");

  const { data: recommendations, isLoading } = useQuery({
    queryKey: ["recommendations", filter],
    queryFn: () =>
      api.listRecommendations(token!, filter || undefined) as Promise<Recommendation[]>,
    enabled: !!token,
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">AI Recommendations</h1>
        <p className="text-muted-foreground">AI-powered analysis of your stocks</p>
      </div>

      <Tabs value={filter} onValueChange={setFilter}>
        <TabsList>
          {actionFilters.map((f) => (
            <TabsTrigger key={f.value} value={f.value}>
              {f.label}
            </TabsTrigger>
          ))}
        </TabsList>
      </Tabs>

      {isLoading ? (
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-24" />
          ))}
        </div>
      ) : recommendations?.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center text-muted-foreground">
            No recommendations yet. Go to a stock page and click &quot;AI Analysis&quot; to get started.
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {recommendations?.map((rec) => (
            <Link key={rec.id} href={`/recommendations/${rec.id}`}>
              <Card className="transition-colors hover:bg-accent/50 cursor-pointer mb-4">
                <CardContent className="flex items-center justify-between p-4">
                  <div className="flex items-center gap-4">
                    <div className="flex h-10 w-10 items-center justify-center rounded-full bg-muted">
                      {rec.action === "BUY" ? (
                        <TrendingUp className="h-5 w-5 text-green-500" />
                      ) : rec.action === "SELL" ? (
                        <TrendingDown className="h-5 w-5 text-red-500" />
                      ) : (
                        <Minus className="h-5 w-5 text-yellow-500" />
                      )}
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-bold">{rec.stock.symbol}</span>
                        <Badge
                          variant={
                            rec.action === "BUY"
                              ? "default"
                              : rec.action === "SELL"
                              ? "destructive"
                              : "secondary"
                          }
                        >
                          {rec.action}
                        </Badge>
                        <span className="text-sm text-muted-foreground">
                          {rec.confidence}% confidence
                        </span>
                      </div>
                      <p className="mt-1 text-sm text-muted-foreground line-clamp-1">
                        {rec.summary}
                      </p>
                    </div>
                  </div>
                  <span className="text-sm text-muted-foreground whitespace-nowrap">
                    {formatDistanceToNow(new Date(rec.created_at), { addSuffix: true })}
                  </span>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
