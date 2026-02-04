import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth";

const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8000";

export default async function DashboardPage() {
  const session = await getServerSession(authOptions);
  const role = session?.user?.role ?? "PATIENT";
  const token = (session as { accessToken?: string })?.accessToken;

  let stats = { appointments: 0, upcoming: 0 };
  if (token) {
    try {
      const res = await fetch(`${BACKEND_URL}/api/appointments`, {
        headers: { Authorization: `Bearer ${token}` },
        cache: "no-store",
      });
      if (res.ok) {
        const appointments = await res.json();
        stats.appointments = appointments.length;
        stats.upcoming = appointments.filter(
          (a: { status: string; dateTime: string }) =>
            a.status === "SCHEDULED" && new Date(a.dateTime) >= new Date()
        ).length;
      }
    } catch {
      // leave stats at 0
    }
  }

  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-bold text-slate-800">
        {role === "DOCTOR" ? "Doctor" : "Patient"} Dashboard
      </h1>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
          <p className="text-slate-600 text-sm font-medium">Total appointments</p>
          <p className="text-3xl font-bold text-slate-800 mt-1">{stats.appointments}</p>
        </div>
        <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
          <p className="text-slate-600 text-sm font-medium">Upcoming</p>
          <p className="text-3xl font-bold text-primary-600 mt-1">{stats.upcoming}</p>
        </div>
      </div>
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-slate-800 mb-4">Quick actions</h2>
        <ul className="space-y-2 text-slate-600">
          <li>
            <a href="/dashboard/appointments" className="text-primary-600 hover:underline">
              → View & manage appointments
            </a>
          </li>
          <li>
            <a href="/dashboard/profile" className="text-primary-600 hover:underline">
              → Edit your profile
            </a>
          </li>
        </ul>
      </div>
    </div>
  );
}
