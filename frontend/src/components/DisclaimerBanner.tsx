import { PROTOTYPE_DISCLAIMER } from "../api/client";

export function DisclaimerBanner() {
  return (
    <div
      role="note"
      className="bg-banner px-4 py-3 text-sm leading-relaxed text-white"
    >
      <p className="mx-auto max-w-5xl font-medium">{PROTOTYPE_DISCLAIMER}</p>
    </div>
  );
}
