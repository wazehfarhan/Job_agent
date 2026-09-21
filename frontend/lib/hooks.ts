"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getToken } from "./auth";
import { api } from "./api";

/**
 * Guard for protected pages: redirects to /login when there is no token,
 * validates the token against /auth/me otherwise. Returns `ready` — render
 * nothing (a loading state) until it flips true.
 */
export function useRequireAuth(): boolean {
  const router = useRouter();
  const [ready, setReady] = useState(false);

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    api
      .me()
      .then(() => setReady(true))
      .catch(() => setReady(false)); // 401 already redirected via apiFetch
  }, [router]);

  return ready;
}