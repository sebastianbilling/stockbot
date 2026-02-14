const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(
  path: string,
  options: RequestInit = {},
  token?: string | null
): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    headers,
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new ApiError(res.status, body.detail || res.statusText);
  }

  if (res.status === 204) return undefined as T;
  return res.json();
}

export const api = {
  // Auth
  register(data: { email: string; password: string; full_name: string }) {
    return request("/api/auth/register", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },
  login(data: { email: string; password: string }) {
    return request("/api/auth/login", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },
  me(token: string) {
    return request("/api/auth/me", {}, token);
  },

  // Portfolios
  listPortfolios(token: string) {
    return request("/api/portfolios", {}, token);
  },
  getPortfolio(token: string, id: string) {
    return request(`/api/portfolios/${id}`, {}, token);
  },
  createPortfolio(token: string, data: { name: string; description?: string }) {
    return request("/api/portfolios", {
      method: "POST",
      body: JSON.stringify(data),
    }, token);
  },
  updatePortfolio(token: string, id: string, data: { name?: string; description?: string }) {
    return request(`/api/portfolios/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }, token);
  },
  deletePortfolio(token: string, id: string) {
    return request(`/api/portfolios/${id}`, { method: "DELETE" }, token);
  },

  // Holdings
  addHolding(token: string, portfolioId: string, data: { symbol: string; quantity: string; avg_cost_basis: string }) {
    return request(`/api/portfolios/${portfolioId}/holdings`, {
      method: "POST",
      body: JSON.stringify(data),
    }, token);
  },
  updateHolding(token: string, portfolioId: string, holdingId: string, data: { quantity?: string; avg_cost_basis?: string }) {
    return request(`/api/portfolios/${portfolioId}/holdings/${holdingId}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }, token);
  },
  deleteHolding(token: string, portfolioId: string, holdingId: string) {
    return request(`/api/portfolios/${portfolioId}/holdings/${holdingId}`, { method: "DELETE" }, token);
  },

  // Stocks
  searchStocks(token: string, query: string) {
    return request(`/api/stocks/search?q=${encodeURIComponent(query)}`, {}, token);
  },
  getPrice(token: string, symbol: string) {
    return request(`/api/stocks/${symbol}/price`, {}, token);
  },
  getPriceHistory(token: string, symbol: string, period = "1M") {
    return request(`/api/stocks/${symbol}/history?period=${period}`, {}, token);
  },
  getNews(token: string, symbol: string) {
    return request(`/api/stocks/${symbol}/news`, {}, token);
  },

  // Recommendations
  listRecommendations(token: string, action?: string) {
    const params = action ? `?action=${action}` : "";
    return request(`/api/recommendations${params}`, {}, token);
  },
  getRecommendation(token: string, id: string) {
    return request(`/api/recommendations/${id}`, {}, token);
  },
  analyzeStock(token: string, symbol: string) {
    return request(`/api/recommendations/analyze/${symbol}`, { method: "POST" }, token);
  },

  // Notifications
  listNotifications(token: string) {
    return request("/api/notifications", {}, token);
  },
  getUnreadCount(token: string) {
    return request<{ count: number }>("/api/notifications/unread-count", {}, token);
  },
  markRead(token: string, id: string) {
    return request(`/api/notifications/${id}/read`, { method: "PUT" }, token);
  },
  markAllRead(token: string) {
    return request("/api/notifications/read-all", { method: "PUT" }, token);
  },
};
