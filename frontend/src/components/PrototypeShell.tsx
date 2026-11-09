import type { ReactNode } from "react";
import { AppHeader } from "./AppHeader";
import { DisclaimerBanner } from "./DisclaimerBanner";
import { GenerationModeBanner } from "./GenerationModeBanner";
import { NavLink, useLocation } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { Icon } from "./Icon";

type PrototypeShellProps = {
  children: ReactNode;
};

export function PrototypeShell({ children }: PrototypeShellProps) {
  const { user, logout } = useAuth();
  const { pathname } = useLocation();
  const section = pathname.startsWith("/experiments") ? "Experiments" : pathname.startsWith("/guide") ? "Demo guide" : pathname.startsWith("/system") ? "System" : "Records";
  return (
    <div className={user ? "app-layout" : "auth-layout"}>
      <a className="skip-link" href="#main-content">Skip to content</a>
      {user ? <aside className="sidebar">
        <NavLink className="brand" to="/records"><span className="brand-symbol"><Icon name="logo" size={29} /></span><span>MediSummarize AI</span></NavLink>
        <nav aria-label="Workspace"><NavLink to="/records"><Icon name="records" />Records</NavLink><NavLink to="/experiments"><Icon name="experiments" />Experiments</NavLink><NavLink to="/guide"><Icon name="book" />Demo guide</NavLink><NavLink to="/system"><Icon name="activity" />System</NavLink></nav>
        <div className="sidebar-bottom"><p className="prototype-tag">FYP I · Fall 2026</p><p>Synthetic records only.<br />Verify every summary at its source.</p><div className="account"><span className="avatar">{user.email.charAt(0).toUpperCase()}</span><span className="account-email" title={user.email}>{user.email}</span><button className="icon-button" onClick={logout} aria-label="Sign out"><Icon name="logout" /></button></div></div>
      </aside> : <AppHeader />}
      <div className="app-body">{user && <header className="workspace-bar"><span className="breadcrumb"><NavLink to={section === "Records" ? "/records" : pathname}>{section}</NavLink>{/^\/records\/.+/.test(pathname) && <><Icon name="arrow" size={14} /><span>Record review</span></>}</span><span className="workspace-account"><Icon name="user" size={18} />Research workspace</span></header>}<GenerationModeBanner /><div id="main-content">{children}</div><DisclaimerBanner /></div>
    </div>
  );
}
