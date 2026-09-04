import { apiRequest } from "./client";

export interface HealthResponse {
  status: "ok";
  version: string;
}

export function getHealth(): Promise<HealthResponse> {
  return apiRequest<HealthResponse>("/health");
}
