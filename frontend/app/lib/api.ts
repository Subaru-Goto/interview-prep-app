export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL as string;

/** A non-ok API response with a backend-provided detail message. */
export class ApiError extends Error { }

export async function apiCall<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`, init);
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new ApiError(err.detail ?? "Something went wrong.");
  }
  return res.json();
}

export function apiErrorMessage(error: unknown, fallback: string): string {
  return "✗ " + (error instanceof ApiError ? error.message : fallback);
}
