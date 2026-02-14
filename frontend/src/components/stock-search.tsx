"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Search } from "lucide-react";
import { useAuth } from "@/hooks/use-auth";
import { api } from "@/lib/api-client";
import { Input } from "@/components/ui/input";
import type { StockSearchResult } from "@/types";

interface StockSearchProps {
  onSelect: (stock: StockSearchResult) => void;
}

export function StockSearch({ onSelect }: StockSearchProps) {
  const { token } = useAuth();
  const [query, setQuery] = useState("");

  const { data: results } = useQuery({
    queryKey: ["stock-search", query],
    queryFn: () => api.searchStocks(token!, query) as Promise<StockSearchResult[]>,
    enabled: !!token && query.length >= 1,
    staleTime: 30000,
  });

  return (
    <div className="relative">
      <div className="relative">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          placeholder="Search stocks (e.g. AAPL, Tesla)"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="pl-9"
        />
      </div>
      {results && results.length > 0 && query.length >= 1 && (
        <div className="absolute z-50 mt-1 w-full rounded-md border bg-popover p-1 shadow-md max-h-60 overflow-auto">
          {results.map((stock) => (
            <button
              key={stock.symbol}
              className="flex w-full items-center justify-between rounded-sm px-3 py-2 text-sm hover:bg-accent"
              onClick={() => {
                onSelect(stock);
                setQuery("");
              }}
            >
              <div>
                <span className="font-medium">{stock.symbol}</span>
                <span className="ml-2 text-muted-foreground">{stock.name}</span>
              </div>
              {stock.exchange && (
                <span className="text-xs text-muted-foreground">{stock.exchange}</span>
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
