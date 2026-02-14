"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import { useQuery, useMutation } from "@tanstack/react-query";
import { ArrowDown, ArrowUp, Loader2, Sparkles } from "lucide-react";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";
import { useAuth } from "@/hooks/use-auth";
import { api } from "@/lib/api-client";
import { formatCurrency, formatPercent } from "@/lib/decimal";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";
import type { LatestPrice, PriceHistoryPoint, NewsArticle, Recommendation } from "@/types";

const periods = ["1W", "1M", "3M", "6M", "1Y"] as const;

export default function StockDetailPage() {
  const params = useParams();
  const symbol = (params.symbol as string).toUpperCase();
  const { token } = useAuth();
  const [period, setPeriod] = useState<string>("1M");

  const { data: price, isLoading: priceLoading } = useQuery({
    queryKey: ["price", symbol],
    queryFn: () => api.getPrice(token!, symbol) as Promise<LatestPrice>,
    enabled: !!token,
  });

  const { data: history, isLoading: historyLoading } = useQuery({
    queryKey: ["history", symbol, period],
    queryFn: () => api.getPriceHistory(token!, symbol, period) as Promise<PriceHistoryPoint[]>,
    enabled: !!token,
  });

  const { data: news } = useQuery({
    queryKey: ["news", symbol],
    queryFn: () => api.getNews(token!, symbol) as Promise<NewsArticle[]>,
    enabled: !!token,
  });

  const analyzeMutation = useMutation({
    mutationFn: () => api.analyzeStock(token!, symbol) as Promise<Recommendation>,
    onSuccess: (data) => {
      toast.success(`AI recommends: ${(data as Recommendation).action}`);
    },
    onError: (err: Error) => toast.error(err.message),
  });

  const changePercent = price?.change_percent;
  const isPositive = changePercent ? parseFloat(changePercent) >= 0 : true;

  const chartData = history?.map((p) => ({
    date: p.date,
    close: parseFloat(p.close),
  }));

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          {priceLoading ? (
            <>
              <Skeleton className="h-10 w-32 mb-2" />
              <Skeleton className="h-6 w-48" />
            </>
          ) : (
            <>
              <div className="flex items-center gap-3">
                <h1 className="text-3xl font-bold">{symbol}</h1>
                <span className="text-lg text-muted-foreground">{price?.name}</span>
              </div>
              <div className="flex items-center gap-2 mt-1">
                <span className="text-3xl font-bold">
                  ${price ? formatCurrency(price.price) : "—"}
                </span>
                {changePercent && (
                  <Badge variant={isPositive ? "default" : "destructive"} className="text-sm">
                    {isPositive ? <ArrowUp className="mr-1 h-3 w-3" /> : <ArrowDown className="mr-1 h-3 w-3" />}
                    {formatPercent(changePercent)}
                  </Badge>
                )}
              </div>
            </>
          )}
        </div>
        <Button onClick={() => analyzeMutation.mutate()} disabled={analyzeMutation.isPending}>
          {analyzeMutation.isPending ? (
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          ) : (
            <Sparkles className="mr-2 h-4 w-4" />
          )}
          AI Analysis
        </Button>
      </div>

      {analyzeMutation.data && (
        <Card className="border-primary">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              AI Recommendation
              <Badge
                variant={
                  (analyzeMutation.data as Recommendation).action === "BUY"
                    ? "default"
                    : (analyzeMutation.data as Recommendation).action === "SELL"
                    ? "destructive"
                    : "secondary"
                }
              >
                {(analyzeMutation.data as Recommendation).action}
              </Badge>
              <span className="text-sm font-normal text-muted-foreground">
                Confidence: {(analyzeMutation.data as Recommendation).confidence}%
              </span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="mb-2 font-medium">{(analyzeMutation.data as Recommendation).summary}</p>
            <p className="text-sm text-muted-foreground whitespace-pre-line">
              {(analyzeMutation.data as Recommendation).reasoning}
            </p>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Price History</CardTitle>
          <Tabs value={period} onValueChange={setPeriod}>
            <TabsList>
              {periods.map((p) => (
                <TabsTrigger key={p} value={p}>{p}</TabsTrigger>
              ))}
            </TabsList>
          </Tabs>
        </CardHeader>
        <CardContent>
          {historyLoading ? (
            <Skeleton className="h-64 w-full" />
          ) : chartData && chartData.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                <XAxis
                  dataKey="date"
                  tick={{ fontSize: 12 }}
                  className="text-muted-foreground"
                />
                <YAxis
                  domain={["auto", "auto"]}
                  tick={{ fontSize: 12 }}
                  className="text-muted-foreground"
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "hsl(var(--card))",
                    border: "1px solid hsl(var(--border))",
                    borderRadius: "8px",
                  }}
                  labelStyle={{ color: "hsl(var(--foreground))" }}
                />
                <Line
                  type="monotone"
                  dataKey="close"
                  stroke="hsl(var(--primary))"
                  strokeWidth={2}
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-center text-muted-foreground py-8">No price data available</p>
          )}
        </CardContent>
      </Card>

      {news && news.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Recent News</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {news.slice(0, 10).map((article) => (
              <div key={article.id} className="border-b pb-3 last:border-0 last:pb-0">
                {article.url ? (
                  <a
                    href={article.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="font-medium hover:text-primary hover:underline"
                  >
                    {article.headline}
                  </a>
                ) : (
                  <p className="font-medium">{article.headline}</p>
                )}
                {article.summary && (
                  <p className="mt-1 text-sm text-muted-foreground line-clamp-2">{article.summary}</p>
                )}
                <div className="mt-1 flex gap-2 text-xs text-muted-foreground">
                  {article.source && <span>{article.source}</span>}
                  <span>{new Date(article.published_at).toLocaleDateString()}</span>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
