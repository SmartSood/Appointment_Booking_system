import { NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth";
import { z } from "zod";

const createSchema = z.object({
  doctorId: z.string().min(1),
  dateTime: z.string().datetime(),
  notes: z.string().optional(),
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
    const res = await fetch(`${BACKEND_URL}/api/appointments`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) {
      return NextResponse.json({ message: "Failed to fetch appointments" }, { status: res.status });
    }
    const data = await res.json();
    return NextResponse.json(data);
  } catch (e) {
    console.error("Appointments fetch error:", e);
    return NextResponse.json({ message: "Failed to fetch appointments" }, { status: 500 });
  }
}

export async function POST(req: Request) {
  const session = await getServerSession(authOptions);
  if (!session?.user) {
    return NextResponse.json({ message: "Unauthorized" }, { status: 401 });
  }
  const user = session.user as { role: string };
  if (user.role !== "PATIENT") {
    return NextResponse.json({ message: "Only patients can book appointments" }, { status: 403 });
  }
  const token = getToken(session);
  if (!token) {
    return NextResponse.json({ message: "Not authenticated" }, { status: 401 });
  }
  try {
    const body = await req.json();
    const parsed = createSchema.safeParse(body);
    if (!parsed.success) {
      return NextResponse.json({ message: "Invalid input" }, { status: 400 });
    }
    const res = await fetch(`${BACKEND_URL}/api/appointments`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(parsed.data),
    });
    const data = await res.json();
    if (!res.ok) {
      return NextResponse.json(
        { message: (data.detail as string) ?? "Failed to create appointment" },
        { status: res.status }
      );
    }
    return NextResponse.json(data);
  } catch (e) {
    console.error("Create appointment error:", e);
    return NextResponse.json({ message: "Failed to create appointment" }, { status: 500 });
  }
}
