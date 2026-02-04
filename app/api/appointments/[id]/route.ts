import { NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth";
import { z } from "zod";

const updateSchema = z.object({ status: z.enum(["SCHEDULED", "COMPLETED", "CANCELLED"]) });

const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8000";

export async function PATCH(
  req: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const session = await getServerSession(authOptions);
  if (!session?.user) {
    return NextResponse.json({ message: "Unauthorized" }, { status: 401 });
  }
  const token = (session as { accessToken?: string }).accessToken;
  if (!token) {
    return NextResponse.json({ message: "Not authenticated" }, { status: 401 });
  }
  const { id } = await params;
  try {
    const body = await req.json();
    const parsed = updateSchema.safeParse(body);
    if (!parsed.success) {
      return NextResponse.json({ message: "Invalid input" }, { status: 400 });
    }
    const res = await fetch(`${BACKEND_URL}/api/appointments/${id}`, {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ status: parsed.data.status }),
    });
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      return NextResponse.json(
        { message: (data.detail as string) ?? "Failed to update appointment" },
        { status: res.status }
      );
    }
    return NextResponse.json({ ok: true });
  } catch (e) {
    console.error("Update appointment error:", e);
    return NextResponse.json({ message: "Failed to update appointment" }, { status: 500 });
  }
}
