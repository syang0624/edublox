"use client";
import { useEffect, useState, use } from "react";

export default function Preview({
  params,
}: {
  params: Promise<{ planId: string }>;
}) {
  const { planId } = use(params);
  const [plan, setPlan] = useState<any>(null);
  const placeId = process.env.NEXT_PUBLIC_ROBLOX_PLACE_ID;

  useEffect(() => {
    fetch(
      `${process.env.NEXT_PUBLIC_BACKEND_URL}/api/config?plan_id=${planId}`
    )
      .then((r) => r.json())
      .then((d) => setPlan(d.plan));
  }, [planId]);

  if (!plan) {
    return (
      <main className="min-h-screen flex items-center justify-center">
        <div className="animate-pulse text-xl">Loading mission plan...</div>
      </main>
    );
  }

  const launchData = encodeURIComponent(
    JSON.stringify({ plan_id: planId })
  );
  const launchUrl = `https://www.roblox.com/games/start?placeId=${placeId}&launchData=${launchData}`;

  return (
    <main className="min-h-screen p-8">
      <div className="max-w-2xl mx-auto">
        <h1 className="text-3xl font-bold">{plan.title}</h1>
        <p className="text-slate-300 mt-1">{plan.topic}</p>

        <section className="mt-8">
          <h2 className="text-xl font-semibold mb-2">You will learn to:</h2>
          <ul className="list-disc pl-6 space-y-1">
            {plan.objectives.map((o: string, i: number) => (
              <li key={i}>{o}</li>
            ))}
          </ul>
        </section>

        <section className="mt-8">
          <h2 className="text-xl font-semibold mb-2">Missions:</h2>
          <ol className="space-y-3">
            {plan.missions.map((m: any) => (
              <li
                key={m.mission_id}
                className="p-4 bg-slate-900 border border-indigo-900 rounded-lg shadow-sm"
              >
                <div className="text-sm uppercase text-cyan-300">
                  {m.type}
                </div>
                <div className="font-medium">
                  {m.type === "dialogue" && `Speak with ${m.npc_name}`}
                  {m.type === "puzzle" && m.prompt}
                  {m.type === "exploration" && m.prompt}
                </div>
                <div className="text-sm text-slate-400">
                  Location: {m.location.replaceAll("_", " ")}
                </div>
              </li>
            ))}
          </ol>
        </section>

        <a
          href={launchUrl}
          className="mt-8 block text-center bg-indigo-600 hover:bg-indigo-500 text-white text-xl font-semibold py-4 rounded-xl transition"
        >
          Launch in Roblox
        </a>
      </div>
    </main>
  );
}
