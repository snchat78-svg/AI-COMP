/// <reference lib="deno.ns" />

/**
 * Fixed-host regional connectivity probe for official-source robots.txt.
 *
 * This function is diagnostic only. It does not crawl pages, read robots.txt
 * content, download papers, follow redirects, accept arbitrary URLs, or write
 * to the database. Supabase's JWT verification remains enabled by config.toml.
 */

type OfficialSource = {
  source_id: "RSSB_OFFICIAL" | "RPSC_OFFICIAL";
  base_url: string;
};

type ProbeFetch = (input: string | URL | Request, init?: RequestInit) => Promise<Response>;

type ProbeOptions = {
  fetchImpl?: ProbeFetch;
  executionRegion?: string;
};

const OFFICIAL_SOURCES: readonly OfficialSource[] = [
  {
    source_id: "RSSB_OFFICIAL",
    base_url: "https://rssb.rajasthan.gov.in/",
  },
  {
    source_id: "RPSC_OFFICIAL",
    base_url: "https://rpsc.rajasthan.gov.in/",
  },
];

const SOURCE_BY_ID = new Map(
  OFFICIAL_SOURCES.map((source) => [source.source_id, source]),
);
const REQUEST_TIMEOUT_MS = 3_000;
const USER_AGENT = "AI-COMP/phase2";
const RESPONSE_HEADERS = {
  "content-type": "application/json; charset=utf-8",
  "cache-control": "no-store",
  "x-content-type-options": "nosniff",
};

function jsonResponse(status: number, payload: Record<string, unknown>): Response {
  return new Response(JSON.stringify(payload), {
    status,
    headers: RESPONSE_HEADERS,
  });
}

async function probeRobots(source: OfficialSource, fetchImpl: ProbeFetch) {
  const target = new URL("robots.txt", source.base_url);
  const started = performance.now();

  try {
    const response = await fetchImpl(target, {
      method: "GET",
      headers: {
        "user-agent": USER_AGENT,
        "accept": "text/plain, */*;q=0.5",
      },
      // Never follow redirects here. The probe is limited to the registered host.
      redirect: "manual",
      signal: AbortSignal.timeout(REQUEST_TIMEOUT_MS),
    });

    const status = response.status;
    const contentType = response.headers.get("content-type")?.split(";")[0] ?? null;
    const redirectNotFollowed = status >= 300 && status < 400;

    try {
      await response.body?.cancel();
    } catch {
      // The status and headers already prove a response was received; no body is needed.
    }

    return {
      source_id: source.source_id,
      host: target.hostname,
      network_status: "HTTP_RESPONSE",
      http_status: status,
      redirect_not_followed: redirectNotFollowed,
      content_type: contentType,
      duration_ms: Math.max(0, Math.round(performance.now() - started)),
    };
  } catch (error) {
    const errorType = error instanceof Error ? error.name : "UnknownError";
    return {
      source_id: source.source_id,
      host: target.hostname,
      network_status: errorType === "TimeoutError" || errorType === "AbortError"
        ? "TIMEOUT"
        : "FAILED",
      error_type: errorType,
      duration_ms: Math.max(0, Math.round(performance.now() - started)),
    };
  }
}

export async function handleRequest(
  request: Request,
  options: ProbeOptions = {},
): Promise<Response> {
  if (request.method !== "POST") {
    return jsonResponse(405, {
      error: { code: "METHOD_NOT_ALLOWED", message: "Use POST for this diagnostic." },
    });
  }

  const contentLength = Number(request.headers.get("content-length") ?? "0");
  if (Number.isFinite(contentLength) && contentLength > 1024) {
    return jsonResponse(413, {
      error: { code: "REQUEST_TOO_LARGE", message: "Diagnostic request must be at most 1 KiB." },
    });
  }

  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return jsonResponse(400, {
      error: { code: "INVALID_JSON", message: "Request body must be JSON." },
    });
  }

  if (
    body === null ||
    typeof body !== "object" ||
    Array.isArray(body) ||
    Object.keys(body).some((key) => key !== "source_id")
  ) {
    return jsonResponse(400, {
      error: { code: "INVALID_REQUEST", message: "Only the optional source_id field is accepted." },
    });
  }

  const sourceId = (body as { source_id?: unknown }).source_id ?? "all";
  if (
    typeof sourceId !== "string" ||
    (sourceId !== "all" && !SOURCE_BY_ID.has(sourceId as OfficialSource["source_id"]))
  ) {
    return jsonResponse(400, {
      error: { code: "UNKNOWN_SOURCE", message: "Only registered official source IDs or all are accepted." },
    });
  }

  const sources = sourceId === "all"
    ? OFFICIAL_SOURCES
    : [SOURCE_BY_ID.get(sourceId as OfficialSource["source_id"])!];
  const fetchImpl = options.fetchImpl ?? fetch;
  const executionRegion = options.executionRegion ?? Deno.env.get("SB_REGION") ?? "unknown";
  const results = [];

  // Keep the run deterministic and low-volume: one robots.txt request per source.
  for (const source of sources) {
    results.push(await probeRobots(source, fetchImpl));
  }

  return jsonResponse(200, {
    phase: "2.6-regional-source-probe",
    execution_region: executionRegion,
    sources_probed: results.length,
    diagnostic_only: true,
    content_downloaded: false,
    database_modified: false,
    results,
  });
}

if (import.meta.main) {
  Deno.serve((request) => handleRequest(request));
}
