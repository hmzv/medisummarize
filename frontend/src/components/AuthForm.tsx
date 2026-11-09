import { type FormEvent, useState } from "react";
import { Link, Navigate } from "react-router-dom";
import { ApiError } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import { PrototypeShell } from "./PrototypeShell";
import { Icon } from "./Icon";

export function AuthForm({ register = false }: { register?: boolean }) {
  const auth = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  if (auth.user) return <Navigate to="/records" replace />;
  async function submit(event: FormEvent) {
    event.preventDefault(); setError(null); setPending(true);
    try { await (register ? auth.register : auth.login)(email.trim(), password); }
    catch (err) { setError(err instanceof ApiError ? err.message : "Cannot reach the service. Check that the backend is running, then try again."); }
    finally { setPending(false); }
  }
  return <PrototypeShell><main className="auth-main"><section className="auth-story"><h1>Every summary.<br /><em>Back to its source.</em></h1><p>A focused workspace for reviewing fragmented clinical documents, with the evidence always close at hand.</p><ol className="auth-steps"><li><Icon name="upload" /><span>Add a fictional case<small>PDFs, scans, and text records</small></span></li><li><Icon name="file" /><span>Extract and review<small>Check the text before summarizing</small></span></li><li><Icon name="check" /><span>Follow the evidence<small>Read the source behind each claim</small></span></li></ol><p className="auth-footnote">MediSummarize AI · FAST NUCES, Karachi<br />FYP I research prototype</p></section><section className="auth-form-section"><h2>{register ? "Create your workspace" : "Welcome back"}</h2><p>{register ? "Use a fictional email for the prototype demonstration." : "Sign in to continue reviewing your records."}</p><form onSubmit={submit}><label htmlFor="email">Email address<input id="email" type="email" autoComplete="username" placeholder="you@example.test" required value={email} onChange={e => setEmail(e.target.value)} /></label><label htmlFor="password">Password<input id="password" type={showPassword ? "text" : "password"} autoComplete={register ? "new-password" : "current-password"} required minLength={register ? 10 : undefined} value={password} onChange={e => setPassword(e.target.value)} aria-describedby={register ? "password-help" : undefined} /></label>{register && <p id="password-help" className="field-help">At least 10 characters. Use a unique demonstration password.</p>}<label className="checkbox-label"><input type="checkbox" checked={showPassword} onChange={e => setShowPassword(e.target.checked)} />Show password</label>{error && <p className="error-message" role="alert">{error}</p>}<button className="button primary auth-submit" disabled={pending}>{pending ? (register ? "Creating account…" : "Signing in…") : (register ? "Create account" : "Sign in")}<Icon name="arrow" size={18} /></button></form><p className="auth-switch">{register ? "Already have an account?" : "New to MediSummarize?"} <Link className="text-link" to={register ? "/login" : "/register"}>{register ? "Sign in" : "Create an account"}</Link></p><p className="field-help">Use synthetic records only. Keep real patient information out of this research prototype.</p></section></main></PrototypeShell>;
}
