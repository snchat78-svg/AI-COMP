import { handleRequest } from "./index.ts";

function assertEquals<T>(actual: T, expected: T, message = "values differ") {
  if (JSON.stringify(actual) !== JSON.stringify(expected)) {
    throw new Error(`${message}: expected ${JSON.stringify(expected)}, got ${JSON.stringify(actual)}`);
  }
}

function assert(condition: unknown, message: string) {
  if (!condition) throw new Error(message);
}

function post(body: unknown) {
  return new Request("https://function.test/official-source-health", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(body),
  });
}

Deno.test("all probes only the two fixed official robots.txt paths", async () => {
  const calls: Array<{ url: string; init?: RequestInit }> = [];
  const fakeFetch = async (input: string | URL | Request, init?: RequestInit) => {
    const url = String(input);
    calls.push({ url, init });
    return new Response("not read", {
      status: url.includes("rssb.rajasthan.gov.in") ? 200 : 403,
      headers: { "content-type": "text/plain; charset=utf-8" },
    });
  };

  const response = await handleRequest(post({ source_id: "all" }), {
    fetchImpl: fakeFetch,
    executionRegion: "ap-south-1",
  });
  const data = await response.json();

  assertEquals(response.status, 200);
  assertEquals(data.phase, "2.6-regional-source-probe");
  assertEquals(data.execution_region, "ap-south-1");
  assertEquals(data.sources_probed, 2);
  assertEquals(data.content_downloaded, false);
  assertEquals(data.database_modified, false);
  assertEquals(data.results[0].http_status, 200);
  assertEquals(data.results[1].http_status, 403);
  assertEquals(data.results[0].network_status, "HTTP_RESPONSE");
  assertEquals(data.results[1].network_status, "HTTP_RESPONSE");
  assertEquals(calls.map((call) => call.url), [
    "https://rssb.rajasthan.gov.in/robots.txt",
    "https://rpsc.rajasthan.gov.in/robots.txt",
  ]);
  assert(calls.every((call) => call.init?.redirect === "manual"), "redirects must not be followed");
  assert(calls.every((call) => (call.init?.signal as AbortSignal | undefined) !== undefined), "probes must be time-bound");
  assertEquals(response.headers.get("cache-control"), "no-store");
  assertEquals(response.headers.get("x-content-type-options"), "nosniff");
});

Deno.test("source selection accepts a registered ID and never a caller-supplied URL", async () => {
  const calls: string[] = [];
  const fakeFetch = async (input: string | URL | Request) => {
    calls.push(String(input));
    return new Response(null, { status: 200 });
  };

  const one = await handleRequest(post({ source_id: "RPSC_OFFICIAL" }), {
    fetchImpl: fakeFetch,
    executionRegion: "ap-south-1",
  });
  const oneData = await one.json();
  assertEquals(oneData.sources_probed, 1);
  assertEquals(calls, ["https://rpsc.rajasthan.gov.in/robots.txt"]);

  calls.length = 0;
  const arbitrary = await handleRequest(post({
    source_id: "all",
    url: "https://untrusted.example/robots.txt",
  }), { fetchImpl: fakeFetch });
  assertEquals(arbitrary.status, 400);
  assertEquals(calls, []);
  assert(!(await arbitrary.text()).includes("untrusted.example"), "do not echo arbitrary URLs");
});

Deno.test("unknown sources and methods are rejected without network calls", async () => {
  let calls = 0;
  const fakeFetch = async () => {
    calls += 1;
    return new Response(null, { status: 200 });
  };

  const unknown = await handleRequest(post({ source_id: "OTHER_SOURCE" }), {
    fetchImpl: fakeFetch,
  });
  assertEquals(unknown.status, 400);

  const method = await handleRequest(new Request("https://function.test/", { method: "GET" }), {
    fetchImpl: fakeFetch,
  });
  assertEquals(method.status, 405);
  assertEquals(calls, 0);
});

Deno.test("HTTP redirects are reported but never followed", async () => {
  const calls: string[] = [];
  const fakeFetch = async (input: string | URL | Request) => {
    calls.push(String(input));
    return new Response(null, {
      status: 302,
      headers: { location: "https://untrusted.example/robots.txt" },
    });
  };

  const response = await handleRequest(post({ source_id: "RSSB_OFFICIAL" }), {
    fetchImpl: fakeFetch,
  });
  const data = await response.json();

  assertEquals(data.results[0].http_status, 302);
  assertEquals(data.results[0].redirect_not_followed, true);
  assertEquals(calls, ["https://rssb.rajasthan.gov.in/robots.txt"]);
});

Deno.test("network errors return safe error classes without exception text", async () => {
  const fakeFetch = async () => {
    throw new DOMException("private network diagnostic", "TimeoutError");
  };
  const response = await handleRequest(post({ source_id: "RSSB_OFFICIAL" }), {
    fetchImpl: fakeFetch,
  });
  const body = await response.text();

  assertEquals(response.status, 200);
  assert(body.includes('"network_status":"TIMEOUT"'), "timeout category should be reported");
  assert(body.includes('"error_type":"TimeoutError"'), "error type should be reported");
  assert(!body.includes("private network diagnostic"), "exception messages must not be exposed");
});
