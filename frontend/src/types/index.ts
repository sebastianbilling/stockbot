export interface User {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface Portfolio {
  id: string;
  name: string;
  description: string | null;
  holdings: Holding[];
  created_at: string;
  updated_at: string;
}

export interface PortfolioListItem {
  id: string;
  name: string;
  description: string | null;
  holdings_count: number;
  created_at: string;
}

export interface Holding {
  id: string;
  stock: StockInHolding;
  quantity: string;
  avg_cost_basis: string;
  created_at: string;
}

export interface StockInHolding {
  id: string;
  symbol: string;
  name: string;
}

export interface StockSearchResult {
  symbol: string;
  name: string;
  exchange: string | null;
  asset_type: string;
}

export interface LatestPrice {
  symbol: string;
  name: string;
  price: string;
  previous_close: string | null;
  change_percent: string | null;
  fetched_at: string;
}

export interface PriceHistoryPoint {
  date: string;
  open: string;
  high: string;
  low: string;
  close: string;
  volume: number;
  vwap: string | null;
}

export interface Recommendation {
  id: string;
  stock: {
    id: string;
    symbol: string;
    name: string;
    exchange: string | null;
    asset_type: string;
  };
  action: "BUY" | "SELL" | "HOLD";
  confidence: string;
  summary: string;
  reasoning?: string;
  model_version?: string;
  created_at: string;
}

export interface NewsArticle {
  id: string;
  headline: string;
  summary: string | null;
  url: string | null;
  source: string | null;
  published_at: string;
}

export interface Notification {
  id: string;
  type: string;
  title: string;
  message: string;
  reference_id: string | null;
  is_read: boolean;
  created_at: string;
}
