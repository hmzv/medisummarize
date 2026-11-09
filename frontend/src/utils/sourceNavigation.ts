/** Scroll to a source without overriding a user's reduced-motion preference. */
export function scrollToSource(id: string) {
  const reducedMotion = window.matchMedia?.("(prefers-reduced-motion: reduce)").matches ?? false;
  document.getElementById(id)?.scrollIntoView({
    behavior: reducedMotion ? "auto" : "smooth",
    block: "center",
  });
}
