// snap.easychamp.com: a thin edge in front of the Snap to League app.
// The app runs on the organizer's machine behind a Cloudflare Tunnel (ORIGIN); this Worker
// keeps a stable EasyChamp address, passes the visitor's IP for rate limits, and shows a
// friendly page when the app is offline.
export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const origin = new URL(env.ORIGIN);
    const target = new URL(url.pathname + url.search, origin);
    const headers = new Headers(request.headers);
    // the tunnel replaces cf-connecting-ip with the Worker's own address, so pass the visitor's separately
    headers.set("x-snap-visitor", request.headers.get("cf-connecting-ip") || "");
    headers.set("x-forwarded-host", url.host);
    try {
      const resp = await fetch(target, {
        method: request.method,
        headers,
        body: ["GET", "HEAD"].includes(request.method) ? undefined : request.body,
        redirect: "manual",
      });
      if (resp.status >= 520 && resp.status <= 530) return offline();
      return resp;
    } catch (e) {
      return offline();
    }
  },
};

function offline() {
  return new Response(
    `<!doctype html><meta name="viewport" content="width=device-width,initial-scale=1"><title>Snap to League</title>
     <body style="font-family:system-ui;background:#fafafa;color:#22263b;display:grid;place-items:center;min-height:100vh;margin:0;padding:16px">
     <div style="max-width:420px"><h1 style="font-size:28px">Snap to League is taking a break</h1>
     <p>The app is offline for a moment. Try again shortly, or visit <a href="https://easychamp.com">easychamp.com</a>.</p></div>`,
    { status: 503, headers: { "content-type": "text/html; charset=utf-8", "retry-after": "60" } },
  );
}
