const BASE = process.env.NEXT_PUBLIC_BACKEND_URL!;

function backendBaseUrl() {
  if (!BASE) {
    throw new Error(
      "Backend is not configured. Set NEXT_PUBLIC_BACKEND_URL in Butterbase and redeploy."
    );
  }

  const isRemoteBrowser =
    typeof window !== "undefined" &&
    !["localhost", "127.0.0.1"].includes(window.location.hostname);
  const pointsToLocalhost = /^https?:\/\/(localhost|127\.0\.0\.1)(?::|\/|$)/.test(
    BASE
  );

  if (isRemoteBrowser && pointsToLocalhost) {
    throw new Error(
      "This deployment still points to a localhost backend. Set NEXT_PUBLIC_BACKEND_URL to the public HTTPS backend URL and redeploy."
    );
  }

  return BASE.replace(/\/$/, "");
}

export async function uploadPdf(file: File) {
  const fd = new FormData();
  fd.append("file", file);
  const r = await fetch(`${backendBaseUrl()}/api/upload`, {
    method: "POST",
    body: fd,
  });
  if (!r.ok) throw new Error(await r.text());
  return r.json() as Promise<{
    upload_id: string;
    extracted_text_preview: string;
    char_count: number;
  }>;
}

export async function generatePlan(uploadId: string, learnerId: string) {
  const r = await fetch(`${backendBaseUrl()}/api/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ upload_id: uploadId, learner_id: learnerId }),
  });
  if (!r.ok) throw new Error(await r.text());
  return r.json() as Promise<{ plan_id: string; plan: unknown }>;
}
