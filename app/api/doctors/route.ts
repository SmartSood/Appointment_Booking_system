import { NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth";

const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8000";

function getToken(session: unknown): string | null {
  return (session as { accessToken?: string })?.accessToken ?? null;
}

export async function GET() {
  const session = await getServerSession(authOptions);
  if (!session?.user) {
    return NextResponse.json({ message: "Unauthorized" }, { status: 401 });
  }
  const token = getToken(session);
  if (!token) {
    return NextResponse.json({ message: "Not authenticated" }, { status: 401 });
  }
  try {
    const res = await fetch(`${BACKEND_URL}/api/doctors`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) {
      return NextResponse.json({ message: "Failed to fetch doctors" }, { status: res.status });
    }
    const data = await res.json();
    return NextResponse.json(data);
  } catch (e) {
    console.error("Doctors fetch error:", e);
    return NextResponse.json({ message: "Failed to fetch doctors" }, { status: 500 });
  }
}
