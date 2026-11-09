const paths: Record<string, string> = {
  logo: "M4 4h6v6H4z M14 4h6v6h-6z M4 14h6v6H4z M14 14h6v6h-6z",
  records: "M4 5h6l2 2h8v13H4z M8 12h8 M8 16h5",
  arrow: "M5 12h14 M14 7l5 5-5 5", plus: "M12 5v14 M5 12h14",
  search: "M21 21l-5-5 M18 10a8 8 0 1 1-16 0 8 8 0 0 1 16 0",
  upload: "M12 16V3 M7 8l5-5 5 5 M4 15v5h16v-5",
  file: "M14 2H5v20h14V7z M14 2v6h5 M8 13h8 M8 17h5",
  check: "M5 12l4 4L19 6",
  book: "M12 5c-3-2-7-2-10 0v15c3-2 7-2 10 0 3-2 7-2 10 0V5c-3-2-7-2-10 0z M12 5v15",
  activity: "M2 12h5l3-8 4 16 3-8h5",
  experiments: "M9 3h6 M10 3v6L4 19a1 1 0 0 0 1 2h14a1 1 0 0 0 1-2L14 9V3 M8 14h8",
  user: "M16 7a4 4 0 1 1-8 0 4 4 0 0 1 8 0 M4 21v-3a8 8 0 0 1 16 0v3",
  logout: "M9 4H3v16h6 M9 12h12 M17 8l4 4-4 4",
  download: "M12 3v13 M7 11l5 5 5-5 M4 17v4h16v-4",
};
export function Icon({ name, size = 20 }: { name: string; size?: number }) {
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d={paths[name] ?? paths.file} /></svg>;
}
