"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { ArrowLeft, Plus, Trash2 } from "lucide-react";
import Decimal from "decimal.js";
import { useAuth } from "@/hooks/use-auth";
import { api } from "@/lib/api-client";
import { formatCurrency } from "@/lib/decimal";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Skeleton } from "@/components/ui/skeleton";
import { StockSearch } from "@/components/stock-search";
import { toast } from "sonner";
import type { Portfolio, StockSearchResult } from "@/types";

export default function PortfolioDetailPage() {
  const params = useParams();
  const router = useRouter();
  const { token } = useAuth();
  const queryClient = useQueryClient();
  const portfolioId = params.id as string;

  const [addOpen, setAddOpen] = useState(false);
  const [selectedStock, setSelectedStock] = useState<StockSearchResult | null>(null);
  const [quantity, setQuantity] = useState("");
  const [costBasis, setCostBasis] = useState("");

  const { data: portfolio, isLoading } = useQuery({
    queryKey: ["portfolio", portfolioId],
    queryFn: () => api.getPortfolio(token!, portfolioId) as Promise<Portfolio>,
    enabled: !!token,
  });

  const addHoldingMutation = useMutation({
    mutationFn: () =>
      api.addHolding(token!, portfolioId, {
        symbol: selectedStock!.symbol,
        quantity,
        avg_cost_basis: costBasis,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["portfolio", portfolioId] });
      queryClient.invalidateQueries({ queryKey: ["portfolios"] });
      setAddOpen(false);
      setSelectedStock(null);
      setQuantity("");
      setCostBasis("");
      toast.success("Holding added");
    },
    onError: (err: Error) => toast.error(err.message),
  });

  const deleteHoldingMutation = useMutation({
    mutationFn: (holdingId: string) => api.deleteHolding(token!, portfolioId, holdingId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["portfolio", portfolioId] });
      queryClient.invalidateQueries({ queryKey: ["portfolios"] });
      toast.success("Holding removed");
    },
    onError: (err: Error) => toast.error(err.message),
  });

  const deletePortfolioMutation = useMutation({
    mutationFn: () => api.deletePortfolio(token!, portfolioId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["portfolios"] });
      router.push("/portfolios");
      toast.success("Portfolio deleted");
    },
    onError: (err: Error) => toast.error(err.message),
  });

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (!portfolio) {
    return <p className="text-muted-foreground">Portfolio not found.</p>;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link href="/portfolios">
            <Button variant="ghost" size="icon">
              <ArrowLeft className="h-4 w-4" />
            </Button>
          </Link>
          <div>
            <h1 className="text-3xl font-bold">{portfolio.name}</h1>
            {portfolio.description && (
              <p className="text-muted-foreground">{portfolio.description}</p>
            )}
          </div>
        </div>
        <div className="flex gap-2">
          <Dialog open={addOpen} onOpenChange={setAddOpen}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="mr-1 h-4 w-4" />
                Add Stock
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Add Stock to Portfolio</DialogTitle>
              </DialogHeader>
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  if (selectedStock) addHoldingMutation.mutate();
                }}
                className="space-y-4"
              >
                <div className="space-y-2">
                  <Label>Stock</Label>
                  {selectedStock ? (
                    <div className="flex items-center justify-between rounded-md border p-3">
                      <div>
                        <span className="font-medium">{selectedStock.symbol}</span>
                        <span className="ml-2 text-sm text-muted-foreground">{selectedStock.name}</span>
                      </div>
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        onClick={() => setSelectedStock(null)}
                      >
                        Change
                      </Button>
                    </div>
                  ) : (
                    <StockSearch onSelect={setSelectedStock} />
                  )}
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="quantity">Shares</Label>
                    <Input
                      id="quantity"
                      type="number"
                      step="any"
                      placeholder="10"
                      value={quantity}
                      onChange={(e) => setQuantity(e.target.value)}
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="cost-basis">Avg Cost ($)</Label>
                    <Input
                      id="cost-basis"
                      type="number"
                      step="any"
                      placeholder="150.00"
                      value={costBasis}
                      onChange={(e) => setCostBasis(e.target.value)}
                      required
                    />
                  </div>
                </div>
                {selectedStock && quantity && costBasis && (
                  <p className="text-sm text-muted-foreground">
                    Total cost basis: ${formatCurrency(new Decimal(quantity).mul(costBasis).toString())}
                  </p>
                )}
                <Button
                  type="submit"
                  className="w-full"
                  disabled={!selectedStock || addHoldingMutation.isPending}
                >
                  {addHoldingMutation.isPending ? "Adding..." : "Add Holding"}
                </Button>
              </form>
            </DialogContent>
          </Dialog>
          <Button
            variant="destructive"
            size="icon"
            onClick={() => {
              if (confirm("Delete this portfolio?")) {
                deletePortfolioMutation.mutate();
              }
            }}
          >
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Holdings</CardTitle>
        </CardHeader>
        <CardContent>
          {portfolio.holdings.length === 0 ? (
            <p className="text-center text-muted-foreground py-8">
              No holdings yet. Add a stock to get started.
            </p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Symbol</TableHead>
                  <TableHead>Name</TableHead>
                  <TableHead className="text-right">Shares</TableHead>
                  <TableHead className="text-right">Avg Cost</TableHead>
                  <TableHead className="text-right">Total Cost</TableHead>
                  <TableHead></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {portfolio.holdings.map((h) => {
                  const totalCost = new Decimal(h.quantity).mul(h.avg_cost_basis);
                  return (
                    <TableRow key={h.id}>
                      <TableCell>
                        <Link
                          href={`/stocks/${h.stock.symbol}`}
                          className="font-medium text-primary hover:underline"
                        >
                          {h.stock.symbol}
                        </Link>
                      </TableCell>
                      <TableCell className="text-muted-foreground">{h.stock.name}</TableCell>
                      <TableCell className="text-right">{formatCurrency(h.quantity)}</TableCell>
                      <TableCell className="text-right">${formatCurrency(h.avg_cost_basis)}</TableCell>
                      <TableCell className="text-right">${formatCurrency(totalCost.toString())}</TableCell>
                      <TableCell className="text-right">
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => {
                            if (confirm(`Remove ${h.stock.symbol}?`)) {
                              deleteHoldingMutation.mutate(h.id);
                            }
                          }}
                        >
                          <Trash2 className="h-4 w-4 text-muted-foreground" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
