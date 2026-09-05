export interface ApiErrorBody {
  error: {
    code: string;
    message: string;
    details?: Record<string, unknown>;
  };
}

export type AttentionLevel = "none" | "low" | "moderate" | "high";

export interface AttentionResponse {
  symbol: string;
  score: number;
  level: AttentionLevel;
  isNew: boolean;
  latestRelevantAt: string;
  reasons: string[];
  evidence: {
    priceScore: number;
    volumeScore: number;
    relativeScore: number;
    volatilityScore: number;
    eventScore: number;
    relevanceScore: number;
  };
}

export interface DemoScenario {
  scenario: string;
  title: string;
  description: string;
  source: string;
}

export interface LastSeenResponse {
  lastSeenAt: string | null;
}

export interface MarketQuote {
  symbol: string;
  price: number;
  previousClose: number;
  absoluteChange: number;
  percentageChange: number;
  volume: number;
  averageVolume: number;
  timestamp: string;
  dataStatus: string;
  source: string;
  dayHigh: number;
  dayLow: number;
  open: number;
}

export class ApiClientError extends Error {
  constructor(
    public readonly status: number,
    public readonly code: string,
    message: string,
    public readonly details?: Record<string, unknown>,
  ) {
    super(message);
    this.name = "ApiClientError";
  }
}

const baseUrl =
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1";

export async function apiRequest<T>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const response = await fetch(`${baseUrl}${path}`, {
    ...init,
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
      ...init.headers,
    },
  });

  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as ApiErrorBody | null;

    throw new ApiClientError(
      response.status,
      body?.error.code ?? "network_error",
      body?.error.message ?? "The request failed.",
      body?.error.details,
    );
  }

  if (response.status === 204) return undefined as T;

  return (await response.json()) as T;
}

export async function apiGet<T>(path: string): Promise<T> {
  return apiRequest<T>(path);
}

export async function getAttention(
  symbols: string[],
): Promise<AttentionResponse[]> {
  return apiGet<AttentionResponse[]>(
    `/market/attention?symbols=${encodeURIComponent(symbols.join(","))}`,
  );
}

export async function getQuotes(symbols: string[]): Promise<MarketQuote[]> {
  return apiGet<MarketQuote[]>(
    `/market/quotes?symbols=${encodeURIComponent(symbols.join(","))}`,
  );
}

export async function getScenarios(): Promise<DemoScenario[]> {
  return apiGet<DemoScenario[]>("/demo/scenarios");
}

export async function selectScenario(scenario: string): Promise<DemoScenario> {
  return apiRequest<DemoScenario>("/demo/scenario", {
    method: "POST",
    body: JSON.stringify({ scenario }),
  });
}

export async function getLastSeen(): Promise<LastSeenResponse> {
  return apiGet<LastSeenResponse>("/market/last-seen");
}

export async function markChecked(): Promise<LastSeenResponse> {
  return apiRequest<LastSeenResponse>("/market/mark-checked", { method: "POST" });
}
