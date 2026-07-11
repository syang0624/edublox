import PreviewClient from "./preview-client";

// Static export only pre-renders the pre-baked demo plan; other plan IDs
// are created at runtime by the backend and fall back to the SPA redirect.
export function generateStaticParams() {
  return [{ planId: "demo_newton_laws" }];
}

export default async function Page({
  params,
}: {
  params: Promise<{ planId: string }>;
}) {
  const { planId } = await params;
  return <PreviewClient planId={planId} />;
}
