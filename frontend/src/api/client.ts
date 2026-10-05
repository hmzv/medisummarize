export const PROTOTYPE_DISCLAIMER =
  "Research prototype for clinical-document summarization only. Not for diagnosis, prescribing, treatment recommendations, or autonomous clinical decision-making. Verify all generated information against the original records.";

export const TOKEN_STORAGE_KEY = "medisummarize.accessToken";

export function apiBaseUrl(): string {
  const configured = import.meta.env.VITE_API_BASE_URL;
  if (configured === undefined || configured === "") {
    return "";
  }
  return configured.replace(/\/$/, "");
}

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
    this.name = "ApiError";
  }
}

function detailFromResponse(data: unknown, status: number): string {
  if (typeof data !== "object" || data === null || !("detail" in data)) {
    return `Request failed with status ${status}`;
  }
  const detail = data.detail;
  if (typeof detail === "string") {
    return detail;
  }
  if (Array.isArray(detail) && detail.length > 0) {
    const first = detail[0];
    if (typeof first === "object" && first !== null && "msg" in first && typeof first.msg === "string") {
      return first.msg;
    }
  }
  return `Request failed with status ${status}`;
}

export function readStoredToken(): string | null {
  return window.sessionStorage.getItem(TOKEN_STORAGE_KEY);
}

export function storeToken(token: string): void {
  window.sessionStorage.setItem(TOKEN_STORAGE_KEY, token);
}

export function clearToken(): void {
  window.sessionStorage.removeItem(TOKEN_STORAGE_KEY);
}

type FetchOptions = {
  method?: string;
  body?: unknown;
  token?: string | null;
  timeoutMs?: number;
};

export async function fetchJson<T>(path: string, options: FetchOptions = {}): Promise<T> {
  const controller = new AbortController();
  const timer = window.setTimeout(() => controller.abort(), options.timeoutMs ?? 8000);
  const headers: Record<string, string> = { Accept: "application/json" };
  if (options.body !== undefined) {
    headers["Content-Type"] = "application/json";
  }
  const token = options.token === undefined ? readStoredToken() : options.token;
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  try {
    const response = await fetch(`${apiBaseUrl()}${path}`, {
      method: options.method ?? "GET",
      headers,
      body: options.body === undefined ? undefined : JSON.stringify(options.body),
      signal: controller.signal,
    });
    if (response.status === 204) {
      return undefined as T;
    }
    const data: unknown = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new ApiError(response.status, detailFromResponse(data, response.status));
    }
    return data as T;
  } finally {
    window.clearTimeout(timer);
  }
}

export type HealthResponse = {
  status: string;
  service: string;
  environment: string;
};

export type ReadyResponse = {
  status: string;
  database: string;
};

export type BackendConnection =
  | { state: "checking" }
  | { state: "connected"; health: HealthResponse; ready: ReadyResponse | null }
  | { state: "disconnected"; message: string };

export async function checkBackendConnection(): Promise<BackendConnection> {
  try {
    const health = await fetchJson<HealthResponse>("/api/v1/health", { token: null });
    let ready: ReadyResponse | null = null;
    try {
      ready = await fetchJson<ReadyResponse>("/api/v1/health/ready", { token: null });
    } catch {
      ready = null;
    }
    return { state: "connected", health, ready };
  } catch (error) {
    const message =
      error instanceof Error ? error.message : "Backend is not reachable.";
    return { state: "disconnected", message };
  }
}

export type UserPublic = {
  id: string;
  email: string;
  created_at: string;
};

export type AuthResponse = {
  access_token: string;
  token_type: string;
  user: UserPublic;
};

export type RecordResponse = {
  id: string;
  display_label: string;
  created_at: string;
  updated_at: string;
  synthetic_notice: string;
};

export async function registerAccount(email: string, password: string): Promise<AuthResponse> {
  return fetchJson<AuthResponse>("/api/v1/auth/register", {
    method: "POST",
    body: { email, password },
    token: null,
  });
}

export async function loginAccount(email: string, password: string): Promise<AuthResponse> {
  return fetchJson<AuthResponse>("/api/v1/auth/login", {
    method: "POST",
    body: { email, password },
    token: null,
  });
}

export async function fetchCurrentUser(token: string): Promise<UserPublic> {
  return fetchJson<UserPublic>("/api/v1/auth/me", { token });
}

export async function listRecords(): Promise<RecordResponse[]> {
  const body = await fetchJson<{ items: RecordResponse[] }>("/api/v1/records");
  return body.items;
}

export async function createRecord(displayLabel: string): Promise<RecordResponse> {
  return fetchJson<RecordResponse>("/api/v1/records", {
    method: "POST",
    body: { display_label: displayLabel },
  });
}

export async function getRecord(recordId: string): Promise<RecordResponse> {
  return fetchJson<RecordResponse>(`/api/v1/records/${recordId}`);
}

export async function deleteRecord(recordId: string): Promise<void> {
  await fetchJson<void>(`/api/v1/records/${recordId}`, { method: "DELETE" });
}

export type DocumentResponse = {
  id: string;
  record_id: string;
  original_filename: string;
  file_kind: string;
  detected_media_type: string;
  size_bytes: number;
  sha256: string;
  status: string;
  page_count: number | null;
  image_width: number | null;
  image_height: number | null;
  public_error: string | null;
  created_at: string;
};

export async function listDocuments(recordId: string): Promise<DocumentResponse[]> {
  const body = await fetchJson<{ items: DocumentResponse[] }>(
    `/api/v1/records/${recordId}/documents`,
  );
  return body.items;
}

export async function uploadDocument(recordId: string, file: File): Promise<DocumentResponse> {
  const controller = new AbortController();
  const timer = window.setTimeout(() => controller.abort(), 30000);
  const headers: Record<string, string> = { Accept: "application/json" };
  const token = readStoredToken();
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  const form = new FormData();
  form.append("file", file);
  try {
    const response = await fetch(`${apiBaseUrl()}/api/v1/records/${recordId}/documents`, {
      method: "POST",
      headers,
      body: form,
      signal: controller.signal,
    });
    const data: unknown = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new ApiError(response.status, detailFromResponse(data, response.status));
    }
    return data as DocumentResponse;
  } finally {
    window.clearTimeout(timer);
  }
}

export async function deleteDocument(recordId: string, documentId: string): Promise<void> {
  await fetchJson<void>(`/api/v1/records/${recordId}/documents/${documentId}`, {
    method: "DELETE",
  });
}

export async function downloadDocument(recordId: string, doc: DocumentResponse): Promise<void> {
  const token = readStoredToken();
  const response = await fetch(
    `${apiBaseUrl()}/api/v1/records/${recordId}/documents/${doc.id}/file`,
    {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    },
  );
  if (!response.ok) {
    throw new ApiError(response.status, "Unable to download the original file.");
  }
  const blob = await response.blob();
  const objectUrl = URL.createObjectURL(blob);
  const anchor = window.document.createElement("a");
  anchor.href = objectUrl;
  anchor.download = doc.original_filename;
  anchor.click();
  URL.revokeObjectURL(objectUrl);
}

export type ExtractedPageResponse = {
  id: string;
  document_id: string;
  page_number: number;
  text: string;
  extraction_method: string;
  ocr_confidence: number | null;
  warnings: string[];
  created_at: string;
};

export type ExtractedPageListResponse = {
  document_id: string;
  status: string;
  public_error: string | null;
  items: ExtractedPageResponse[];
};

export async function extractDocument(
  recordId: string,
  documentId: string,
): Promise<ExtractedPageListResponse> {
  return fetchJson<ExtractedPageListResponse>(
    `/api/v1/records/${recordId}/documents/${documentId}/extract`,
    { method: "POST", timeoutMs: 60000 },
  );
}

export async function fetchExtractedText(
  recordId: string,
  documentId: string,
): Promise<ExtractedPageListResponse> {
  return fetchJson<ExtractedPageListResponse>(
    `/api/v1/records/${recordId}/documents/${documentId}/extracted`,
  );
}

export type Claim = {
  text: string;
  source_ids: string[];
  evidence_status: string;
};

export type StructuredSummary = {
  key_history: Claim[];
  current_documented_findings: Claim[];
  medications: Claim[];
  allergies: Claim[];
  laboratory_findings: Claim[];
  unresolved_or_unavailable: string[];
  processing_limitations: string[];
  disclaimer: string;
};

export type EvidencePassage = {
  id: string;
  document_id: string;
  original_filename: string;
  page: number;
  method: string;
  text: string;
};

export type SummaryResponse = {
  id: string;
  record_id: string;
  summary: StructuredSummary;
  evidence: EvidencePassage[];
  prompt_version: string;
  generation_provider: string;
  generation_model: string;
  embedding_model: string;
  is_mock: boolean;
  validation_warnings: string[];
  created_at: string;
};

export type GenerationHealthResponse = {
  status: string;
  provider: string;
  is_mock: boolean;
  warning: string | null;
};

export async function fetchGenerationHealth(): Promise<GenerationHealthResponse> {
  return fetchJson<GenerationHealthResponse>("/api/v1/health/generation", {
    token: null,
  });
}

export async function generateSummary(recordId: string): Promise<SummaryResponse> {
  return fetchJson<SummaryResponse>(`/api/v1/records/${recordId}/summary`, {
    method: "POST",
    timeoutMs: 120000,
  });
}

export async function fetchSummary(recordId: string): Promise<SummaryResponse> {
  return fetchJson<SummaryResponse>(`/api/v1/records/${recordId}/summary`);
}
