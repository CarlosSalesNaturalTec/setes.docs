import { NextResponse } from "next/server";

// Health check do serviço `web` (task 1.3, spec plataforma-gcp — health 200).
export const dynamic = "force-dynamic";

export function GET() {
  return NextResponse.json({ status: "ok", service: "web" });
}
