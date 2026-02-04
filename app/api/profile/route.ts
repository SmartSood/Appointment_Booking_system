import { NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth";
import { z } from "zod";

const updateSchema = z.object({
  name: z.string().min(1).optional(),
  specialization: z.string().nullable().optional(),
});

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
    const res = await fetch(`${BACKEND_URL}/api/profile`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) {
      return NextResponse.json({ message: "Failed to fetch profile" }, { status: res.status });
    }
    const data = await res.json();
    return NextResponse.json(data);
  } catch (e) {
    console.error("Profile fetch error:", e);
    return NextResponse.json({ message: "Failed to fetch profile" }, { status: 500 });
  }
}

export async function PATCH(req: Request) {
  const session = await getServerSession(authOptions);
  if (!session?.user) {
    return NextResponse.json({ message: "Unauthorized" }, { status: 401 });
  }
  const token = getToken(session);
  if (!token) {
    return NextResponse.json({ message: "Not authenticated" }, { status: 401 });
  }
  try {
    const body = await req.json();
    const parsed = updateSchema.safeParse(body);
    if (!parsed.success) {
      return NextResponse.json({ message: "Invalid input" }, { status: 400 });
    }
    const res = await fetch(`${BACKEND_URL}/api/profile`, {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(parsed.data),
    });
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      return NextResponse.json(
        { message: (data.detail as string) ?? "Failed to update profile" },
        { status: res.status }
      );
    }
    return NextResponse.json({ ok: true });
  } catch (e) {
    console.error("Profile update error:", e);
    return NextResponse.json(
      { message: "Failed to update profile" },
      { status: 500 }
    );
  }
}
