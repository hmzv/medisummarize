import { type FormEvent, useState } from "react";
import { Link, Navigate } from "react-router-dom";
import { ApiError } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import { BackendStatus } from "../components/BackendStatus";
import { PrototypeShell } from "../components/PrototypeShell";

export function LoginPage() {
  const { user, login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  if (user) {
    return <Navigate to="/records" replace />;
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setPending(true);
    try {
      await login(email, password);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Unable to sign in.");
    } finally {
      setPending(false);
    }
  }

  return (
    <PrototypeShell>
      <main className="mx-auto grid max-w-5xl gap-8 px-4 py-8 lg:grid-cols-2">
        <section>
          <h1 className="text-2xl font-semibold">Sign in</h1>
          <p className="mt-2 text-sm text-muted">
            Prototype accounts are for synthetic demonstration records only. The
            access token is stored in <code>sessionStorage</code> and sent as an
            Authorization header, never in the URL.
          </p>
          <form className="mt-6 space-y-4" onSubmit={onSubmit}>
            <label className="block text-sm">
              Email
              <input
                className="mt-1 w-full rounded border border-line bg-card px-3 py-2"
                type="email"
                autoComplete="username"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                required
              />
            </label>
            <label className="block text-sm">
              Password
              <input
                className="mt-1 w-full rounded border border-line bg-card px-3 py-2"
                type="password"
                autoComplete="current-password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                required
                minLength={10}
              />
            </label>
            {error ? <p className="text-sm text-red-800">{error}</p> : null}
            <button
              type="submit"
              disabled={pending}
              className="rounded bg-accent px-4 py-2 text-sm font-medium text-white hover:bg-accent-dark disabled:opacity-60"
            >
              {pending ? "Signing in…" : "Sign in"}
            </button>
          </form>
          <p className="mt-4 text-sm text-muted">
            Need an account?{" "}
            <Link to="/register" className="text-accent-dark hover:underline">
              Register
            </Link>
          </p>
        </section>
        <BackendStatus />
      </main>
    </PrototypeShell>
  );
}
