"use client";

import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { formatDistanceToNow } from "date-fns";
import { ArrowLeft, TrendingDown, TrendingUp, Minus } from "lucide-react";
import { useAuth } from "@/hooks/use-auth";
import { api } from "@/lib/api-client";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import type { Recommendation } from "@/types";

export default function RecommendationDetailPage() {
  const params = useParams();
  const recId = params.id as string;
  const { token } = useAuth();

  const { data: rec, isLoading } = useQuery({
    queryKey: ["recommendation", recId],
    queryFn: () => api.getRecommendation(token!, recId) as Promise<Recommendation>,
    enabled: !!token,
  });

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (!rec) {
    return <p className="text-muted-foreground">Recommendation not found.</p>;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Link href="/recommendations">
          <Button variant="ghost" size="icon">
            <ArrowLeft className="h-4 w-4" />
          </Button>
        </Link>
        <div className="flex items-center gap-3">
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
            <h1 className="text-2xl font-bold">
              {rec.stock.symbol} — {rec.stock.name}
            </h1>
            <p className="text-sm text-muted-foreground">
              {formatDistanceToNow(new Date(rec.created_at), { addSuffix: true })}
              {rec.model_version && ` · Model: ${rec.model_version}`}
            </p>
          </div>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-muted-foreground">Action</CardTitle>
          </CardHeader>
          <CardContent>
            <Badge
              variant={
                rec.action === "BUY"
                  ? "default"
                  : rec.action === "SELL"
                  ? "destructive"
                  : "secondary"
              }
              className="text-lg px-4 py-1"
            >
              {rec.action}
            </Badge>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-muted-foreground">Confidence</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{rec.confidence}%</div>
            <div className="mt-2 h-2 rounded-full bg-muted overflow-hidden">
              <div
                className="h-full rounded-full bg-primary transition-all"
                style={{ width: `${rec.confidence}%` }}
              />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-muted-foreground">Stock</CardTitle>
          </CardHeader>
          <CardContent>
            <Link
              href={`/stocks/${rec.stock.symbol}`}
              className="text-lg font-bold text-primary hover:underline"
            >
              {rec.stock.symbol}
            </Link>
            <p className="text-sm text-muted-foreground">{rec.stock.name}</p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Summary</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-lg">{rec.summary}</p>
        </CardContent>
      </Card>

      {rec.reasoning && (
        <Card>
          <CardHeader>
            <CardTitle>Detailed Analysis</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="whitespace-pre-line text-muted-foreground leading-relaxed">
              {rec.reasoning}
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
