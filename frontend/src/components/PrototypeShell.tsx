import type { ReactNode } from "react";
import { AppHeader } from "./AppHeader";
import { DisclaimerBanner } from "./DisclaimerBanner";
import { GenerationModeBanner } from "./GenerationModeBanner";

type PrototypeShellProps = {
  children: ReactNode;
};

export function PrototypeShell({ children }: PrototypeShellProps) {
  return (
    <div className="min-h-screen">
      <DisclaimerBanner />
      <GenerationModeBanner />
      <AppHeader />
      {children}
    </div>
  );
}
