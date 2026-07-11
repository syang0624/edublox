"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { uploadPdf, generatePlan } from "@/lib/api";

export default function Home() {
  const router = useRouter();
  const [status, setStatus] = useState<
    "idle" | "uploading" | "generating" | "error"
  >("idle");
  const [error, setError] = useState("");

  async function handleFile(file: File) {
    try {
      let learnerId = localStorage.getItem("learner_id");
      if (!learnerId) {
        learnerId = crypto.randomUUID();
        localStorage.setItem("learner_id", learnerId);
      }
      setStatus("uploading");
      const { upload_id } = await uploadPdf(file);
      setStatus("generating");
      const { plan_id } = await generatePlan(upload_id, learnerId);
      router.push(`/preview/${plan_id}`);
    } catch (e: unknown) {
      setStatus("error");
      setError(e instanceof Error ? e.message : "Something went wrong");
    }
  }

  return (
    <main className="min-h-screen flex items-center justify-center p-8">
      <div className="max-w-xl w-full text-center">
        <h1 className="text-4xl font-bold mb-2">Edublox</h1>
        <p className="text-slate-300 mb-8">
          Upload any study PDF and we&apos;ll turn it into a playable Roblox
          mission.
        </p>

        {status === "idle" && (
          <>
            <label className="block border-2 border-dashed border-indigo-400 rounded-xl p-12 cursor-pointer hover:bg-indigo-950 transition">
              <input
                type="file"
                accept="application/pdf"
                className="hidden"
                onChange={(e) =>
                  e.target.files?.[0] && handleFile(e.target.files[0])
                }
              />
              <div className="text-lg">
                Drop your PDF here, or click to browse
              </div>
              <div className="text-sm text-slate-400 mt-2">
                Max 25 MB &middot; Any school subject &middot; Learn by
                playing
              </div>
            </label>

            <Link
              href="/preview/demo_newton_laws"
              prefetch
              className="mt-6 block w-full bg-slate-800 border border-cyan-700 hover:bg-slate-700 text-cyan-200 font-semibold py-3 rounded-xl transition"
            >
              ▶ Demo: Newton&apos;s Laws of Motion
            </Link>
            <div className="text-xs text-slate-500 mt-2">
              Personalized mission plan for Kai (11) — no upload needed
            </div>
          </>
        )}

        {status === "uploading" && (
          <Progress label="Reading your material..." />
        )}
        {status === "generating" && (
          <Progress label="Designing your world..." />
        )}
        {status === "error" && (
          <div className="text-red-400">
            {error}
            <button
              className="block mx-auto mt-4 underline"
              onClick={() => setStatus("idle")}
            >
              Try again
            </button>
          </div>
        )}
      </div>
    </main>
  );
}

function Progress({ label }: { label: string }) {
  return (
    <div className="p-8">
      <div className="animate-pulse text-xl">{label}</div>
      <div className="text-sm text-slate-400 mt-2">
        This can take up to 90 seconds
      </div>
    </div>
  );
}
