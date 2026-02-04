import { redirect } from "next/navigation";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth";
import { getAddonsForRole } from "@/lib/addons/registry";
import { DashboardNav } from "@/components/DashboardNav";
import { SignOutButton } from "@/components/SignOutButton";

export default async function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const session = await getServerSession(authOptions);
  if (!session?.user) redirect("/login?callbackUrl=/dashboard");

  const role = session.user.role as "PATIENT" | "DOCTOR";
  const addons = getAddonsForRole(role);

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-white border-b border-slate-200 sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 flex items-center justify-between h-14">
          <div className="flex items-center gap-6">
            <a href="/dashboard" className="font-bold text-slate-800">
              Dobble
            </a>
            <DashboardNav addons={addons} />
          </div>
          <div className="flex items-center gap-4">
            <span className="text-sm text-slate-600">
              {session.user.name} <span className="text-slate-400">({role})</span>
            </span>
            <SignOutButton />
          </div>
        </div>
      </header>
      <main className="max-w-6xl mx-auto px-4 sm:px-6 py-8">{children}</main>
    </div>
  );
}
