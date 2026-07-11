import { Suspense } from "react";
import QueryPreviewClient from "./query-preview-client";

export default function PreviewPage() {
  return (
    <Suspense
      fallback={
        <main className="min-h-screen flex items-center justify-center">
          <div className="animate-pulse text-xl">Loading mission plan...</div>
        </main>
      }
    >
      <QueryPreviewClient />
    </Suspense>
  );
}
