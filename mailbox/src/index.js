const SNAPSHOT_KEY = "snapshot";
const MAX_BYTES = 256 * 1024;
const SCHEMA = "aindle.snapshot.v2";

function bearerOk(request, token) {
  if (!token) {
    return false;
  }
  const auth = request.headers.get("Authorization") || "";
  return auth === "Bearer " + token;
}

export default {
  async fetch(request, env) {
    const token = env.MAILBOX_TOKEN;
    if (!token) {
      return new Response("mailbox token missing\n", { status: 503 });
    }
    if (!bearerOk(request, token)) {
      return new Response("unauthorized\n", { status: 401 });
    }

    const url = new URL(request.url);
    const path = url.pathname.replace(/\/+$/, "") || "/";
    if (path !== "/snapshot.json") {
      return new Response("not found\n", { status: 404 });
    }

    if (request.method === "GET") {
      const body = await env.BOX.get(SNAPSHOT_KEY);
      if (!body) {
        return new Response("empty\n", { status: 404 });
      }
      return new Response(body, {
        headers: {
          "content-type": "application/json; charset=utf-8",
          "cache-control": "no-store",
        },
      });
    }

    if (request.method === "PUT") {
      const declared = Number(request.headers.get("content-length") || "0");
      if (declared > MAX_BYTES) {
        return new Response("too large\n", { status: 413 });
      }
      const buf = await request.arrayBuffer();
      if (buf.byteLength === 0 || buf.byteLength > MAX_BYTES) {
        return new Response("bad size\n", { status: 400 });
      }
      let parsed;
      try {
        parsed = JSON.parse(new TextDecoder().decode(buf));
      } catch (err) {
        return new Response("bad json\n", { status: 400 });
      }
      if (!parsed || parsed.schema !== SCHEMA) {
        return new Response("bad schema\n", { status: 400 });
      }
      await env.BOX.put(SNAPSHOT_KEY, JSON.stringify(parsed));
      return new Response("ok\n", { status: 200 });
    }

    return new Response("method\n", { status: 405, headers: { allow: "GET, PUT" } });
  },
};
