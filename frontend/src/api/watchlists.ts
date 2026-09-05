import { apiRequest } from "./client";

export interface Instrument {
  id: string;
  symbol: string;
  companyName: string;
  exchange: string;
  sector: string;
  industry: string;
}

export interface WatchlistItem {
  id: string;
  position: number;
  createdAt: string;
  instrument: Instrument;
}

export interface WatchlistSummary {
  id: string;
  name: string;
  createdAt: string;
  updatedAt: string;
  itemCount: number;
}

export interface Watchlist extends Omit<WatchlistSummary, "itemCount"> {
  userId: string;
  items: WatchlistItem[];
}

export const listWatchlists = () => apiRequest<WatchlistSummary[]>("/watchlists");
export const getWatchlist = (id: string) => apiRequest<Watchlist>(`/watchlists/${id}`);
export const createWatchlist = (name: string) =>
  apiRequest<Watchlist>("/watchlists", { method: "POST", body: JSON.stringify({ name }) });
export const renameWatchlist = (id: string, name: string) =>
  apiRequest<Watchlist>(`/watchlists/${id}`, { method: "PATCH", body: JSON.stringify({ name }) });
export const deleteWatchlist = (id: string) => apiRequest<void>(`/watchlists/${id}`, { method: "DELETE" });
export const searchInstruments = (query: string) =>
  apiRequest<Instrument[]>(`/instruments?query=${encodeURIComponent(query)}`);
export const addItem = (watchlistId: string, symbol: string) =>
  apiRequest<WatchlistItem>(`/watchlists/${watchlistId}/items`, {
    method: "POST",
    body: JSON.stringify({ symbol }),
  });
export const removeItem = (watchlistId: string, symbol: string) =>
  apiRequest<void>(`/watchlists/${watchlistId}/items/${symbol}`, { method: "DELETE" });
export const reorderItems = (watchlistId: string, symbols: string[]) =>
  apiRequest<WatchlistItem[]>(`/watchlists/${watchlistId}/items/reorder`, {
    method: "PUT",
    body: JSON.stringify({ symbols }),
  });
