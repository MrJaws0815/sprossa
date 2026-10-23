export const TOKEN_KEY = "sprossa_token";

export function authHeaders(): Record<string, string> {
  const token = localStorage.getItem(TOKEN_KEY);
  if (!token) return {};
  return { Authorization: `Bearer ${token}` };
}

export function getApiBase(): string {
  return process.env.NEXT_PUBLIC_API_URL || "/api/v1";
}