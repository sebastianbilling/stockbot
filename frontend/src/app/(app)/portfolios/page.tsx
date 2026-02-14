"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { Plus } from "lucide-react";
import { useAuth } from "@/hooks/use-auth";
import { api } from "@/lib/api-client";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { toast } from "sonner";
import type { PortfolioListItem } from "@/types";

export default function PortfoliosPage() {
  const { token } = useAuth();
  const queryClient = useQueryClient();
  const [open, setOpen] = useState(false);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");

  const { data: portfolios, isLoading } = useQuery({
    queryKey: ["portfolios"],
    queryFn: () => api.listPortfolios(token!) as Promise<PortfolioListItem[]>,
    enabled: !!token,
  });

  const createMutation = useMutation({
    mutationFn: () => api.createPortfolio(token!, { name, description: description || undefined }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["portfolios"] });
      setOpen(false);
      setName("");
      setDescription("");
      toast.success("Portfolio created");
    },
    onError: (err: Error) => toast.error(err.message),
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Portfolios</h1>
          <p className="text-muted-foreground">Manage your investment portfolios</p>
        </div>
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="mr-1 h-4 w-4" />
              New Portfolio
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Create Portfolio</DialogTitle>
            </DialogHeader>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                createMutation.mutate();
              }}
              className="space-y-4"
            >
              <div className="space-y-2">
                <Label htmlFor="portfolio-name">Name</Label>
                <Input
                  id="portfolio-name"
                  placeholder="My Portfolio"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="portfolio-desc">Description (optional)</Label>
                <Input
                  id="portfolio-desc"
                  placeholder="Long-term growth stocks"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                />
              </div>
              <Button type="submit" className="w-full" disabled={createMutation.isPending}>
                {createMutation.isPending ? "Creating..." : "Create Portfolio"}
              </Button>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {isLoading ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-32" />
          ))}
        </div>
      ) : portfolios?.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <p className="text-muted-foreground mb-4">No portfolios yet</p>
            <Button onClick={() => setOpen(true)}>
              <Plus className="mr-1 h-4 w-4" />
              Create your first portfolio
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {portfolios?.map((p) => (
            <Link key={p.id} href={`/portfolios/${p.id}`}>
              <Card className="transition-colors hover:bg-accent/50 cursor-pointer h-full">
                <CardHeader>
                  <CardTitle>{p.name}</CardTitle>
                </CardHeader>
                <CardContent>
                  {p.description && (
                    <p className="text-sm text-muted-foreground mb-2">{p.description}</p>
                  )}
                  <p className="text-sm text-muted-foreground">
                    {p.holdings_count} holding{p.holdings_count !== 1 ? "s" : ""}
                  </p>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
