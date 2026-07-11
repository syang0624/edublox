"use client";

import { useSearchParams } from "next/navigation";
import PreviewClient from "./[planId]/preview-client";

export default function QueryPreviewClient() {
  const searchParams = useSearchParams();
  const planId = searchParams.get("plan_id");

  if (!planId) {
    return (
      <main className="min-h-screen flex items-center justify-center p-8">
        <div className="text-center">
          <h1 className="text-2xl font-semibold">Mission plan not specified</h1>
          {/* eslint-disable-next-line @next/next/no-html-link-for-pages */}
          <a className="inline-block mt-4 text-cyan-300 underline" href="/">
            Return to Edublox
          </a>
        </div>
      </main>
    );
  }

  return <PreviewClient planId={planId} />;
}
