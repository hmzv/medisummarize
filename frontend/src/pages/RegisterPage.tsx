import { type FormEvent, useState } from "react";
import { Link, Navigate } from "react-router-dom";
import { ApiError } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import { PrototypeShell } from "../components/PrototypeShell";

export function RegisterPage() {
  const { user, register } = useAuth();
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
      await register(email, password);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Unable to register.");
    } finally {
      setPending(false);
    }
  }

  return (
    <PrototypeShell>
      <main className="mx-auto max-w-md px-4 py-8">
        <h1 className="text-2xl font-semibold">Create a prototype account</h1>
        <p className="mt-2 text-sm text-muted">
          Use a fictional email. Do not upload real patient information. Passwords
          must be at least 10 characters and are stored as bcrypt hashes.
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
              autoComplete="new-password"
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
            {pending ? "Creating account…" : "Register"}
          </button>
        </form>
        <p className="mt-4 text-sm text-muted">
          Already registered?{" "}
          <Link to="/login" className="text-accent-dark hover:underline">
            Sign in
          </Link>
        </p>
      </main>
    </PrototypeShell>
  );
}
