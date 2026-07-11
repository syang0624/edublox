"use client";
import { useEffect, useState } from "react";
import demoNewtonPlan from "@/lib/demo_newton_laws_plan.json";

type SimulationBox = {
  label: string;
  mass_kg: number;
};

type Mission = {
  mission_id: string;
  type: "dialogue" | "puzzle" | "exploration" | "simulation";
  location: string;
  prompt?: string;
  npc_name?: string;
  boxes?: SimulationBox[];
};

type MissionPlan = {
  title: string;
  topic: string;
  objectives: string[];
  missions: Mission[];
};

type ConfigResponse = {
  plan: MissionPlan;
  learner_id?: string;
};

type MemoryResponse = {
  memory: Record<string, string>;
};

// Pre-baked demo plans render instantly with no backend round-trip —
// presentation-proof even if the backend is cold. Keep the JSON in sync
// with backend/app/demo/ (source of truth); learner must match
// DEMO_PLANS in backend/app/main.py.
const PREBAKED_PLANS: Record<string, { plan: MissionPlan; learnerId: string }> = {
  demo_newton_laws: {
    plan: demoNewtonPlan as MissionPlan,
    learnerId: "kai_tanaka",
  },
};

// Short staged reveal for pre-baked demo plans: the plan is already in the
// bundle, but the demo reads better with a beat of "generation" while the
// live EverOS memory fetch runs in parallel.
const GENERATING_STEPS = [
  "Reading the learner's memory…",
  "Personalizing missions to what they've mastered…",
  "Designing the world…",
];
const STEP_MS = 850;

// Staged beat between clicking "Launch" and the Roblox redirect, so the
// hand-off reads as deliberate instead of an abrupt page jump.
const LAUNCHING_STEPS = [
  "Packaging your mission plan…",
  "Sending it to Roblox…",
  "Launching your world…",
];

export default function PreviewClient({ planId }: { planId: string }) {
  const [plan, setPlan] = useState<MissionPlan | null>(null);
  const [memory, setMemory] = useState<Record<string, string> | null>(null);
  const [genStep, setGenStep] = useState(0);
  const [launchStep, setLaunchStep] = useState<number | null>(null);
  const [launchError, setLaunchError] = useState("");
  const [loadError, setLoadError] = useState("");
  const placeId = process.env.NEXT_PUBLIC_ROBLOX_PLACE_ID;
  const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL;
  const isDemo = planId in PREBAKED_PLANS;
  const backendConfigurationError =
    !isDemo && !backendUrl
      ? "Backend is not configured. Set NEXT_PUBLIC_BACKEND_URL in Butterbase and redeploy."
      : "";

  useEffect(() => {
    // Memory reveal: show what EverOS actually remembers about this
    // learner — the same context the plan generator was given.
    const fetchMemory = async (learnerId: string) => {
      if (!backendUrl) return;
      try {
        const response = await fetch(
          `${backendUrl.replace(/\/$/, "")}/api/memory/${learnerId}`
        );
        if (!response.ok) {
          throw new Error(`Memory request failed (${response.status})`);
        }
        const data = (await response.json()) as MemoryResponse;
        setMemory(data.memory);
      } catch {
        // Memory is an enhancement; the pre-baked demo remains usable when
        // EverOS or the backend is unavailable.
      }
    };

    const prebaked = PREBAKED_PLANS[planId];
    if (prebaked) {
      fetchMemory(prebaked.learnerId);
      const timers = GENERATING_STEPS.map((_, i) =>
        setTimeout(() => setGenStep(i), i * STEP_MS)
      );
      timers.push(
        setTimeout(
          () => setPlan(prebaked.plan),
          GENERATING_STEPS.length * STEP_MS
        )
      );
      return () => timers.forEach(clearTimeout);
    }
    if (!backendUrl) {
      return;
    }
    fetch(
      `${backendUrl.replace(/\/$/, "")}/api/config?plan_id=${encodeURIComponent(planId)}`
    )
      .then((r) => {
        if (!r.ok) throw new Error(`Mission plan request failed (${r.status})`);
        return r.json();
      })
      .then((d: ConfigResponse) => {
        setPlan(d.plan);
        if (d.learner_id) fetchMemory(d.learner_id);
      })
      .catch((error: unknown) =>
        setLoadError(
          error instanceof Error ? error.message : "Could not load mission plan"
        )
      );
  }, [backendUrl, planId]);

  if (loadError || backendConfigurationError) {
    return (
      <main className="min-h-screen flex items-center justify-center p-8">
        <div className="max-w-lg text-center">
          <h1 className="text-2xl font-semibold">Could not load mission plan</h1>
          <p className="mt-3 text-red-400">
            {loadError || backendConfigurationError}
          </p>
          {/* eslint-disable-next-line @next/next/no-html-link-for-pages */}
          <a className="inline-block mt-5 text-cyan-300 underline" href="/">
            Return to Edublox
          </a>
        </div>
      </main>
    );
  }

  if (!plan) {
    return (
      <main className="min-h-screen flex items-center justify-center">
        {isDemo ? (
          <div className="text-center w-full max-w-sm px-8">
            <div className="animate-pulse text-xl">
              {GENERATING_STEPS[genStep]}
            </div>
            <div className="mt-6 h-1.5 bg-slate-800 rounded-full overflow-hidden">
              <div
                className="h-full bg-cyan-400 rounded-full transition-all duration-700 ease-out"
                style={{
                  width: `${((genStep + 1) / GENERATING_STEPS.length) * 100}%`,
                }}
              />
            </div>
            <div className="text-sm text-slate-400 mt-3">
              Powered by EverOS memory
            </div>
          </div>
        ) : (
          <div className="animate-pulse text-xl">Loading mission plan...</div>
        )}
      </main>
    );
  }

  const launchData = encodeURIComponent(
    JSON.stringify({ plan_id: planId })
  );
  const launchUrl = `https://www.roblox.com/games/start?placeId=${placeId}&launchData=${launchData}`;

  const startLaunch = () => {
    if (launchStep !== null) return;
    if (!placeId || !/^\d+$/.test(placeId)) {
      setLaunchError(
        "Roblox launch is not configured. Set NEXT_PUBLIC_ROBLOX_PLACE_ID in the Butterbase deployment and redeploy."
      );
      return;
    }
    setLaunchStep(0);
    LAUNCHING_STEPS.forEach((_, i) => {
      if (i > 0) setTimeout(() => setLaunchStep(i), i * STEP_MS);
    });
    setTimeout(() => {
      window.location.href = launchUrl;
    }, LAUNCHING_STEPS.length * STEP_MS);
  };

  if (launchStep !== null) {
    return (
      <main className="min-h-screen flex items-center justify-center">
        <div className="text-center w-full max-w-sm px-8">
          <div className="animate-pulse text-xl">
            {LAUNCHING_STEPS[launchStep]}
          </div>
          <div className="mt-6 h-1.5 bg-slate-800 rounded-full overflow-hidden">
            <div
              className="h-full bg-indigo-400 rounded-full transition-all duration-700 ease-out"
              style={{
                width: `${((launchStep + 1) / LAUNCHING_STEPS.length) * 100}%`,
              }}
            />
          </div>
          <div className="text-sm text-slate-400 mt-3">
            Opening Roblox — choose “Open” if your browser asks
          </div>
        </div>
      </main>
    );
  }

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
            {plan.missions.map((m) => (
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
                  {m.type === "simulation" && m.prompt}
                </div>
                {m.type === "simulation" && (
                  <div className="text-sm text-slate-400 mt-1">
                    Push:{" "}
                    {m.boxes
                      ?.map((b) => `${b.label} (${b.mass_kg} kg)`)
                      .join(" · ")}{" "}
                    — ends with a 1-question quiz
                  </div>
                )}
                <div className="text-sm text-slate-400">
                  Location: {m.location.replaceAll("_", " ")}
                </div>
              </li>
            ))}
          </ol>
        </section>

        {memory && Object.values(memory).some((v) => v && v.trim()) && (
          <section className="mt-8">
            <h2 className="text-xl font-semibold mb-2">
              🧠 What the tutor remembers
            </h2>
            <p className="text-sm text-slate-400 mb-3">
              Recalled from EverOS memory and used to personalize this plan.
            </p>
            <div className="space-y-3">
              {(
                [
                  ["mastered", "Already mastered"],
                  ["struggles", "Still working on"],
                  ["profile", "How they learn"],
                ] as const
              ).map(
                ([key, label]) =>
                  memory[key]?.trim() && (
                    <div
                      key={key}
                      className="p-4 bg-slate-900 border border-emerald-900 rounded-lg"
                    >
                      <div className="text-sm uppercase text-emerald-300">
                        {label}
                      </div>
                      <p className="text-sm text-slate-300 whitespace-pre-line mt-1">
                        {memory[key]}
                      </p>
                    </div>
                  )
              )}
            </div>
          </section>
        )}

        <button
          onClick={startLaunch}
          className="mt-8 block w-full text-center bg-indigo-600 hover:bg-indigo-500 text-white text-xl font-semibold py-4 rounded-xl transition"
        >
          Launch in Roblox
        </button>
        {launchError && (
          <p className="mt-3 text-center text-sm text-red-400" role="alert">
            {launchError}
          </p>
        )}
      </div>
    </main>
  );
}
