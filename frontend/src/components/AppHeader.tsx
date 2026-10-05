import { Link } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

export function AppHeader() {
  const { user, logout } = useAuth();
  return (
    <header className="border-b border-line bg-card">
      <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-accent">
            FYP-I research prototype
          </p>
          <Link to={user ? "/records" : "/login"} className="text-xl font-semibold text-ink">
            MediSummarize AI
          </Link>
        </div>
        {user ? (
          <div className="flex items-center gap-4 text-sm">
            <span className="hidden text-muted sm:inline">{user.email}</span>
            <button
              type="button"
              onClick={logout}
              className="rounded border border-line px-3 py-1.5 text-ink hover:bg-paper"
            >
              Sign out
            </button>
          </div>
        ) : (
          <nav className="flex gap-3 text-sm">
            <Link to="/login" className="text-accent-dark hover:underline">
              Sign in
            </Link>
            <Link to="/register" className="text-accent-dark hover:underline">
              Register
            </Link>
          </nav>
        )}
      </div>
    </header>
  );
}
