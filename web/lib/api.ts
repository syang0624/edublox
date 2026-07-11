const BASE = process.env.NEXT_PUBLIC_BACKEND_URL!;

export async function uploadPdf(file: File) {
  const fd = new FormData();
  fd.append("file", file);
  const r = await fetch(`${BASE}/api/upload`, { method: "POST", body: fd });
  if (!r.ok) throw new Error(await r.text());
  return r.json() as Promise<{
    upload_id: string;
    extracted_text_preview: string;
    char_count: number;
  }>;
}

export async function generatePlan(uploadId: string, learnerId: string) {
  const r = await fetch(`${BASE}/api/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ upload_id: uploadId, learner_id: learnerId }),
  });
  if (!r.ok) throw new Error(await r.text());
  return r.json() as Promise<{ plan_id: string; plan: any }>;
}
