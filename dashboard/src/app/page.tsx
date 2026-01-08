type QuietEyeEvent = {
  id: number;
  event_type: string;
  timestamp: string;
  site_id: string;
  device_id: string;
  camera_id: string;
  zone?: string | null;
  confidence: number;
  snapshot_ref?: string | null;
  extra: Record<string, any>;
};

async function fetchEvents(): Promise<QuietEyeEvent[]> {
  const base =
    process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";

  const res = await fetch(`${base}/v1/events?limit=50`, {
    cache: "no-store",
  });

  if (!res.ok) {
    throw new Error(`Failed to fetch events (${res.status})`);
  }

  return res.json();
}

export default async function Home() {
  const events = await fetchEvents();

  return (
    <main className="min-h-screen bg-neutral-50 p-6">
      <div className="mx-auto max-w-6xl">
        <h1 className="text-3xl font-semibold tracking-tight">
          QuietEye Dashboard
        </h1>
        <p className="mt-2 text-sm text-neutral-600">
          Live security & safety events
        </p>

        <div className="mt-6 overflow-hidden rounded-xl border bg-white shadow-sm">
          <div className="grid grid-cols-6 gap-3 border-b bg-neutral-100 px-4 py-3 text-xs font-semibold uppercase text-neutral-600">
            <div>ID</div>
            <div className="col-span-2">Event</div>
            <div>Zone</div>
            <div>Confidence</div>
            <div>Time (UTC)</div>
          </div>

          {events.length === 0 ? (
            <div className="p-4 text-sm text-neutral-500">
              No events yet.
            </div>
          ) : (
            events.map((e) => (
              <div
                key={e.id}
                className="grid grid-cols-6 gap-3 border-b px-4 py-3 text-sm hover:bg-neutral-50"
              >
                <div className="font-mono text-xs">{e.id}</div>
                <div className="col-span-2 font-medium">
                  {e.event_type}
                </div>
                <div>{e.zone ?? "-"}</div>
                <div>{Math.round(e.confidence * 100)}%</div>
                <div className="font-mono text-xs">
                  {new Date(e.timestamp).toISOString()}
                </div>
              </div>
            ))
          )}
        </div>

        <div className="mt-6 rounded-xl border bg-white p-4 text-sm">
          <div className="font-semibold">Roadmap</div>
          <ul className="mt-2 list-disc pl-5 text-neutral-600">
            <li>Event detail view + snapshots</li>
            <li>Filters (type, zone, camera)</li>
            <li>Realtime updates (WebSocket)</li>
            <li>User auth + roles</li>
          </ul>
        </div>
      </div>
    </main>
  );
}
