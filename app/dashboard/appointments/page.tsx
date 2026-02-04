import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth";
import { AppointmentsAddon } from "@/addons/appointments/AppointmentsAddon";

const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8000";

export default async function AppointmentsPage() {
  const session = await getServerSession(authOptions);
  const role = session?.user?.role ?? "PATIENT";
  const userId = (session?.user as { id?: string })?.id;
  const token = (session as { accessToken?: string })?.accessToken;

  let appointments: Array<{
    id: string;
    dateTime: string;
    status: string;
    notes: string | null;
    patient: { id: string; name: string; email: string };
    doctor: { id: string; name: string; email: string };
  }> = [];
  let doctors: Array<{ id: string; name: string }> = [];

  if (token) {
    try {
      const apptRes = await fetch(`${BACKEND_URL}/api/appointments`, {
        headers: { Authorization: `Bearer ${token}` },
        cache: "no-store",
      });
      if (apptRes.ok) {
        appointments = await apptRes.json();
      }
      if (role === "PATIENT") {
        const docRes = await fetch(`${BACKEND_URL}/api/doctors`, {
          headers: { Authorization: `Bearer ${token}` },
          cache: "no-store",
        });
        if (docRes.ok) {
          doctors = await docRes.json();
        }
      }
    } catch {
      // leave empty
    }
  }

  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-bold text-slate-800">Appointments</h1>
      <AppointmentsAddon
        role={role as "PATIENT" | "DOCTOR"}
        userId={userId ?? ""}
        initialAppointments={appointments}
        doctors={doctors}
      />
    </div>
  );
}
