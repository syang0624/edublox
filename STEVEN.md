# Steven — Frontend (Next.js Web App)

## Ownership

Everything under `web/`. The user-facing upload flow, mission plan preview, and Roblox launch link.

## Files You Own

```
web/
├── app/
│   ├── page.tsx                        # Upload page
│   ├── preview/[planId]/page.tsx       # Mission Plan preview + launch button
│   └── api/proxy/[...path]/route.ts    # Optional CORS proxy to backend
├── components/
│   ├── UploadDropzone.tsx
│   ├── GenerationProgress.tsx
│   └── MissionPlanPreview.tsx
├── lib/
│   └── api.ts                          # fetch wrappers (uploadPdf, generatePlan)
├── package.json
├── .env.local
└── tailwind / tsconfig / next.config
```

## Task Checklist

### Setup
- [ ] Initialize Next.js project in `web/` with TypeScript + Tailwind CSS
- [ ] Install dependencies: `next`, `react`, `react-dom`, `typescript`, `tailwindcss`, `@cloudflare/next-on-pages`
- [ ] Create `.env.local` with `NEXT_PUBLIC_BACKEND_URL` and `NEXT_PUBLIC_ROBLOX_PLACE_ID`

### Core Pages
- [ ] **Upload page** (`app/page.tsx`) — PRD 5.2
  - Drag-and-drop or click-to-browse PDF upload
  - States: idle, uploading, generating, error
  - On success, redirect to `/preview/[planId]`
  - Generate a stable `learner_id` via `crypto.randomUUID()` stored in `localStorage`
- [ ] **Preview page** (`app/preview/[planId]/page.tsx`) — PRD 5.3
  - Fetch plan from `GET /api/config?plan_id=...`
  - Display: title, topic, 3 objectives, 3 mission cards (type, description, location)
  - "Launch in Roblox" button with deep link: `https://www.roblox.com/games/start?placeId=...&launchData={"plan_id":"..."}`

### API Wrappers
- [ ] **`lib/api.ts`** — PRD 5.1
  - `uploadPdf(file: File)` → POST `/api/upload` with FormData
  - `generatePlan(uploadId: string, learnerId: string)` → POST `/api/generate` with JSON body
- [ ] Optional: CORS proxy route at `api/proxy/[...path]/route.ts` if direct backend calls have CORS issues

### Styling & UX
- [ ] Dark space theme: `bg-slate-950`, `text-slate-100`, indigo/cyan accents
- [ ] Animated pulse loading states during upload and generation
- [ ] Error state with "Try again" button
- [ ] Responsive layout, centered content, max-width containers

### Deployment
- [ ] Deploy via Butterbase Edge SSR: `butterbase deploy:edge-ssr --from-source --from web`
- [ ] Build command: `npx @cloudflare/next-on-pages`
- [ ] Must use Edge SSR (not static export) because `/preview/[planId]` needs runtime routing

## Integration Points

| What | Who to coordinate with |
|------|----------------------|
| Backend API endpoints (`/api/upload`, `/api/generate`, `/api/config`) | **Nori** — agree on request/response shapes (PRD section 3) |
| `NEXT_PUBLIC_ROBLOX_PLACE_ID` | **Madi** — get the Place ID after Roblox place is published |
| Roblox deep link format (`launchData` JSON) | **Madi** — must match what `MissionRouter.server.lua` parses |

## Acceptance Criteria

1. Upload page accepts a PDF (max 25 MB), shows progress, and redirects to preview on success
2. Preview page renders all plan fields (title, topic, objectives, 3 missions with type/location)
3. "Launch in Roblox" button generates a correct deep link with `plan_id` in `launchData`
4. Error states are handled gracefully with clear messages and retry option
5. Works with any subject PDF — no solar-system-specific UI code
6. `learner_id` persists in `localStorage` across sessions
