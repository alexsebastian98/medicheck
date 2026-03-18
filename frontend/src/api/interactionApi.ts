import { apiClient } from "./client";
import type { CheckInteractionsRequest, CheckInteractionsResponse } from "../types/api";

export async function checkInteractions(
  payload: CheckInteractionsRequest,
): Promise<CheckInteractionsResponse> {
  const { data } = await apiClient.post<CheckInteractionsResponse>("/check-interactions", payload);
  return data;
}
