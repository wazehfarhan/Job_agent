// Token storage. localStorage is the honest, simple choice for a single-user
// local tool; it is XSS-exposed by design — noted in FutureUpdate.md (v1.0
// auth hardening would move to httpOnly cookies).
const TOKEN_KEY = "job_agent_token";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
  localStorage.removeItem(TOKEN_KEY);
}

export function isLoggedIn(): boolean {
  return getToken() !== null;
}