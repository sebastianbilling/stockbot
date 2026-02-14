"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { BriefcaseBusiness, Lightbulb, Plus, TrendingDown, TrendingUp } from "lucide-react";
import { useAuth } from "@/hooks/use-auth";
import { api } from "@/lib/api-client";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertDescription } from "@/components/ui/alert";
import type { PortfolioListItem, Recommendation } from "@/types";

export default function DashboardPage() {
  const { token, user } = useAuth();

  const { data: portfolios, isLoading: portfoliosLoading } = useQuery({
    queryKey: ["portfolios"],
    queryFn: () => api.listPortfolios(token!) as Promise<PortfolioListItem[]>,
    enabled: !!token,
  });

  const { data: recommendations, isLoading: recsLoading } = useQuery({
    queryKey: ["recommendations"],
    queryFn: () => api.listRecommendations(token!) as Promise<Recommendation[]>,
    enabled: !!token,
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">
          Welcome back{user?.name ? `, ${user.name.split(" ")[0]}` : ""}
        </h1>
        <p className="text-muted-foreground">
          Here&apos;s your investment overview
        </p>
      </div>

      <Alert>
        <AlertDescription>
          Stockbot provides AI-powered advisory recommendations only. This is not financial advice.
          Always do your own research before making investment decisions.
        </AlertDescription>
      </Alert>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Portfolios
            </CardTitle>
            <BriefcaseBusiness className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            {portfoliosLoading ? (
              <Skeleton className="h-8 w-16" />
            ) : (
              <div className="text-2xl font-bold">{portfolios?.length ?? 0}</div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Total Holdings
            </CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            {portfoliosLoading ? (
              <Skeleton className="h-8 w-16" />
            ) : (
              <div className="text-2xl font-bold">
                {portfolios?.reduce((sum, p) => sum + p.holdings_count, 0) ?? 0}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              AI Recommendations
            </CardTitle>
            <Lightbulb className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            {recsLoading ? (
              <Skeleton className="h-8 w-16" />
            ) : (
              <div className="text-2xl font-bold">{recommendations?.length ?? 0}</div>
            )}
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>Your Portfolios</CardTitle>
            <Link href="/portfolios">
              <Button size="sm" variant="outline">
                <Plus className="mr-1 h-4 w-4" />
                New
              </Button>
            </Link>
          </CardHeader>
          <CardContent>
            {portfoliosLoading ? (
              <div className="space-y-3">
                {[1, 2].map((i) => (
                  <Skeleton key={i} className="h-12 w-full" />
                ))}
              </div>
            ) : portfolios?.length === 0 ? (
              <p className="text-sm text-muted-foreground">
                No portfolios yet.{" "}
                <Link href="/portfolios" className="text-primary hover:underline">
                  Create one
                </Link>{" "}
                to get started.
              </p>
            ) : (
              <div className="space-y-3">
                {portfolios?.slice(0, 5).map((p) => (
                  <Link
                    key={p.id}
                    href={`/portfolios/${p.id}`}
                    className="flex items-center justify-between rounded-md border p-3 transition-colors hover:bg-accent"
                  >
                    <div>
                      <p className="font-medium">{p.name}</p>
                      <p className="text-sm text-muted-foreground">
                        {p.holdings_count} holding{p.holdings_count !== 1 ? "s" : ""}
                      </p>
                    </div>
                    <BriefcaseBusiness className="h-4 w-4 text-muted-foreground" />
                  </Link>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>Recent Recommendations</CardTitle>
            <Link href="/recommendations">
              <Button size="sm" variant="outline">View All</Button>
            </Link>
          </CardHeader>
          <CardContent>
            {recsLoading ? (
              <div className="space-y-3">
                {[1, 2].map((i) => (
                  <Skeleton key={i} className="h-12 w-full" />
                ))}
              </div>
            ) : recommendations?.length === 0 ? (
              <p className="text-sm text-muted-foreground">
                No recommendations yet. Analyze a stock to get AI insights.
              </p>
            ) : (
              <div className="space-y-3">
                {recommendations?.slice(0, 5).map((r) => (
                  <Link
                    key={r.id}
                    href={`/recommendations/${r.id}`}
                    className="flex items-center justify-between rounded-md border p-3 transition-colors hover:bg-accent"
                  >
                    <div className="flex items-center gap-3">
                      {r.action === "BUY" ? (
                        <TrendingUp className="h-4 w-4 text-green-500" />
                      ) : r.action === "SELL" ? (
                        <TrendingDown className="h-4 w-4 text-red-500" />
                      ) : (
                        <div className="h-4 w-4 rounded-full bg-yellow-500/20" />
                      )}
                      <div>
                        <p className="font-medium">{r.stock.symbol}</p>
                        <p className="text-sm text-muted-foreground">{r.summary}</p>
                      </div>
                    </div>
                    <span
                      className={`rounded px-2 py-1 text-xs font-semibold ${
                        r.action === "BUY"
                          ? "bg-green-500/10 text-green-500"
                          : r.action === "SELL"
                          ? "bg-red-500/10 text-red-500"
                          : "bg-yellow-500/10 text-yellow-500"
                      }`}
                    >
                      {r.action}
                    </span>
                  </Link>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
