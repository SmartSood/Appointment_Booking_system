import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth";
import { ProfileAddon } from "@/addons/profile/ProfileAddon";

const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8000";

export default async function ProfilePage() {
  const session = await getServerSession(authOptions);
  const userId = (session?.user as { id?: string })?.id;
  const token = (session as { accessToken?: string })?.accessToken;

  if (!userId || !token) return null;

  let user: {
    id: string;
    name: string;
    email: string;
    role: string;
    specialization: string | null;
  } | null = null;

  try {
    const res = await fetch(`${BACKEND_URL}/api/profile`, {
      headers: { Authorization: `Bearer ${token}` },
      cache: "no-store",
    });
    if (res.ok) {
      user = await res.json();
    }
  } catch {
    // leave user null
  }

  if (!user) return null;

  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-bold text-slate-800">Profile</h1>
      <ProfileAddon
        user={{
          id: user.id,
          name: user.name,
          email: user.email,
          role: user.role,
          specialization: user.specialization ?? null,
        }}
      />
    </div>
  );
}
