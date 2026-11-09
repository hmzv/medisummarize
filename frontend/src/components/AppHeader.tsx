import { Link } from "react-router-dom";
import { Icon } from "./Icon";
export function AppHeader() {
  return <header className="public-header"><Link className="brand" to="/login"><span className="brand-symbol"><Icon name="logo" size={25} /></span><span>MediSummarize<span className="brand-sub">AI research workspace</span></span></Link><span className="prototype-tag">FYP I · Fall 2026</span></header>;
}
