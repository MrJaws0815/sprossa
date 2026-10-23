export const TOKEN_KEY = "sprossa_token";

export function authHeaders(): Record<string, string> {
  return {}; // httpOnly-Cookie wird automatisch vom Browser gesendet
}

export function getApiBase(): string {
  return process.env.NEXT_PUBLIC_API_URL || "/api/v1";
}
