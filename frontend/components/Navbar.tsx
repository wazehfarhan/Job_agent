"use client";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { clearToken, getToken } from "@/lib/auth";
import type { UserOut } from "@/types/api";

const LINKS = [
  { href: "/", label: "Dashboard" },
  { href: "/jobs", label: "Jobs" },
  { href: "/applications", label: "Applications" },
  { href: "/resumes", label: "Resumes" },
  { href: "/profile", label: "Profile" },
  { href: "/settings", label: "Settings" },
];

export default function Navbar() {
  const pathname = usePathname();
  const router = useRouter();
  const [user, setUser] = useState<UserOut | null>(null);

  useEffect(() => {
    if (getToken()) {
      api
        .me()
        .then(setUser)
        .catch(() => setUser(null));
    } else {
      setUser(null);
    }
  }, [pathname]);

  function logout() {
    clearToken();
    setUser(null);
    router.push("/login");
  }

  return (
    <nav className="border-b border-slate-800 bg-slate-900">
      <div className="mx-auto flex max-w-5xl flex-wrap items-center gap-x-4 gap-y-2 px-4 py-3">
        <Link href="/" className="font-semibold text-sky-400">
          Job Agent
        </Link>
        <div className="flex flex-wrap gap-1">
          {LINKS.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className={`rounded-md px-2.5 py-1.5 text-sm ${
                pathname === link.href
                  ? "bg-slate-800 text-sky-300"
                  : "text-slate-300 hover:bg-slate-800 hover:text-slate-100"
              }`}
            >
              {link.label}
            </Link>
          ))}
        </div>
        <div className="ml-auto flex items-center gap-2 text-sm">
          {user ? (
            <>
              <span className="text-slate-400">{user.email}</span>
              <button className="btn-secondary" onClick={logout}>
                Log out
              </button>
            </>
          ) : (
            <Link href="/login" className="btn">
              Log in
            </Link>
          )}
        </div>
      </div>
    </nav>
  );
}