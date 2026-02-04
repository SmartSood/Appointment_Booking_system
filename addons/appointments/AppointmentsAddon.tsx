"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";

type Appointment = {
  id: string;
  dateTime: string;
  status: string;
  notes: string | null;
  patient: { id: string; name: string; email: string };
  doctor: { id: string; name: string; email: string };
};

type Doctor = { id: string; name: string };

interface AppointmentsAddonProps {
  role: "PATIENT" | "DOCTOR";
  userId: string;
  initialAppointments: Appointment[];
  doctors: Doctor[];
}

export function AppointmentsAddon({
  role,
  userId,
  initialAppointments,
  doctors,
}: AppointmentsAddonProps) {
  const router = useRouter();
  const [appointments, setAppointments] = useState(initialAppointments);
  useEffect(() => {
    setAppointments(initialAppointments);
  }, [initialAppointments]);
  const [loading, setLoading] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [doctorId, setDoctorId] = useState(doctors[0]?.id ?? "");
  const [dateTime, setDateTime] = useState("");
  const [notes, setNotes] = useState("");

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!doctorId || !dateTime) return;
    setLoading(true);
    try {
      const res = await fetch("/api/appointments", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          doctorId,
          dateTime: new Date(dateTime).toISOString(),
          notes: notes || undefined,
        }),
      });
      if (res.ok) {
        router.refresh();
        setShowForm(false);
        setDateTime("");
        setNotes("");
      }
    } finally {
      setLoading(false);
    }
  }

  async function handleCancel(id: string) {
    if (!confirm("Cancel this appointment?")) return;
    setLoading(true);
    try {
      await fetch(`/api/appointments/${id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: "CANCELLED" }),
      });
      router.refresh();
    } finally {
      setLoading(false);
    }
  }

  // Fixed locale so server and client render the same (avoids hydration mismatch)
  const formatDate = (d: string) =>
    new Date(d).toLocaleString("en-US", {
      dateStyle: "medium",
      timeStyle: "short",
    });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-4">
        <span className="text-slate-600 text-sm">
          {appointments.length} appointment{appointments.length !== 1 ? "s" : ""}
        </span>
        <button
          type="button"
          onClick={() => router.refresh()}
          className="text-sm text-primary-600 hover:underline"
        >
          Refresh list
        </button>
      </div>
      {role === "PATIENT" && doctors.length > 0 && (
        <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
          {!showForm ? (
            <button
              type="button"
              onClick={() => setShowForm(true)}
              className="px-4 py-2 bg-primary-600 text-white rounded-lg font-medium hover:bg-primary-700 transition"
            >
              Book appointment
            </button>
          ) : (
            <form onSubmit={handleCreate} className="space-y-4 max-w-md">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Doctor
                </label>
                <select
                  value={doctorId}
                  onChange={(e) => setDoctorId(e.target.value)}
                  required
                  className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                >
                  {doctors.map((d) => (
                    <option key={d.id} value={d.id}>
                      {d.name}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Date & time
                </label>
                <input
                  type="datetime-local"
                  value={dateTime}
                  onChange={(e) => setDateTime(e.target.value)}
                  required
                  className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Notes (optional)
                </label>
                <textarea
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  rows={2}
                  className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                />
              </div>
              <div className="flex gap-2">
                <button
                  type="submit"
                  disabled={loading}
                  className="px-4 py-2 bg-primary-600 text-white rounded-lg font-medium hover:bg-primary-700 disabled:opacity-50"
                >
                  {loading ? "Booking…" : "Book"}
                </button>
                <button
                  type="button"
                  onClick={() => setShowForm(false)}
                  className="px-4 py-2 border border-slate-300 rounded-lg font-medium text-slate-700 hover:bg-slate-50"
                >
                  Cancel
                </button>
              </div>
            </form>
          )}
        </div>
      )}

      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-sm">
        <table className="w-full text-left">
          <thead className="bg-slate-50 border-b border-slate-200">
            <tr>
              <th className="px-6 py-3 text-sm font-semibold text-slate-700">Date & time</th>
              {role === "PATIENT" && (
                <th className="px-6 py-3 text-sm font-semibold text-slate-700">Doctor</th>
              )}
              {role === "DOCTOR" && (
                <th className="px-6 py-3 text-sm font-semibold text-slate-700">Patient</th>
              )}
              <th className="px-6 py-3 text-sm font-semibold text-slate-700">Status</th>
              <th className="px-6 py-3 text-sm font-semibold text-slate-700">Actions</th>
            </tr>
          </thead>
          <tbody>
            {appointments.length === 0 ? (
              <tr>
                <td colSpan={4} className="px-6 py-8 text-center text-slate-500">
                  No appointments yet.
                </td>
              </tr>
            ) : (
              appointments.map((apt) => (
                <tr key={apt.id} className="border-b border-slate-100 last:border-0">
                  <td className="px-6 py-4 text-slate-800">{formatDate(apt.dateTime)}</td>
                  {role === "PATIENT" && (
                    <td className="px-6 py-4 text-slate-700">{apt.doctor.name}</td>
                  )}
                  {role === "DOCTOR" && (
                    <td className="px-6 py-4 text-slate-700">{apt.patient.name}</td>
                  )}
                  <td className="px-6 py-4">
                    <span
                      className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
                        apt.status === "SCHEDULED"
                          ? "bg-primary-100 text-primary-700"
                          : apt.status === "COMPLETED"
                            ? "bg-emerald-100 text-emerald-700"
                            : "bg-slate-100 text-slate-600"
                      }`}
                    >
                      {apt.status}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    {apt.status === "SCHEDULED" && (
                      <button
                        type="button"
                        onClick={() => handleCancel(apt.id)}
                        disabled={loading}
                        className="text-sm text-red-600 hover:underline disabled:opacity-50"
                      >
                        Cancel
                      </button>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
