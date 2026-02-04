"use client";

import { useState } from "react";
import { useSession } from "next-auth/react";

const API_BASE = "/api/agent";

export default function AssistantPage() {
  const { data: session, status } = useSession();

  if (status === "loading") {
    return (
      <div className="max-w-2xl mx-auto">
        <p className="text-slate-600">Loading…</p>
      </div>
    );
  }

  if (!session?.user) {
    return (
      <div className="max-w-2xl mx-auto space-y-4">
        <h1 className="text-2xl font-bold text-slate-800">Assistant</h1>
        <p className="text-slate-600">Please sign in to use the assistant (patient booking or doctor reports).</p>
      </div>
    );
  }

  const role = (session.user as { role?: string }).role ?? "";

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold text-slate-800">Assistant</h1>
      {role === "PATIENT" && (
        <>
          <p className="text-slate-600 text-sm">
            Book appointments in plain language. Ask for available doctors or check a doctor&apos;s availability and book a slot.
          </p>
          <PatientChat
            patientName={session.user.name ?? undefined}
            patientEmail={session.user.email ?? undefined}
          />
        </>
      )}
      {role === "DOCTOR" && (
        <>
          <p className="text-slate-600 text-sm">
            Get summary reports in plain language: visits, appointments today/tomorrow, or patients by condition.
          </p>
          <DoctorReport
            doctorName={session.user.name ?? undefined}
            doctorEmail={session.user.email ?? undefined}
          />
        </>
      )}
      {role !== "PATIENT" && role !== "DOCTOR" && (
        <p className="text-slate-600">Your account role is not set. Sign in as Patient or Doctor to use the assistant.</p>
      )}
    </div>
  );
}

function PatientChat({
  patientName,
  patientEmail,
}: {
  patientName?: string | null;
  patientEmail?: string | null;
}) {
  const [prompt, setPrompt] = useState("");
  const [messages, setMessages] = useState<{ role: string; content: string }[]>([]);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function send() {
    const p = prompt.trim();
    if (!p || loading) return;
    setPrompt("");
    setMessages((m) => [...m, { role: "user", content: p }]);
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          prompt: p,
          session_id: sessionId,
          role: "patient",
          ...(patientName && patientEmail && { patient_name: patientName, patient_email: patientEmail }),
        }),
      });
      const text = await res.text();
      if (!res.ok) {
        setMessages((m) => [...m, { role: "assistant", content: `Error (${res.status}): ${text || res.statusText}` }]);
        setLoading(false);
        return;
      }
      let data: { reply?: string; session_id?: string };
      try {
        data = JSON.parse(text);
      } catch {
        setMessages((m) => [...m, { role: "assistant", content: "Invalid response from server: " + text.slice(0, 200) }]);
        setLoading(false);
        return;
      }
      setSessionId(data.session_id ?? null);
      setMessages((m) => [...m, { role: "assistant", content: data.reply ?? "No reply." }]);
    } catch (e) {
      setMessages((m) => [
        ...m,
        { role: "assistant", content: "Error: " + (e instanceof Error ? e.message : String(e)) },
      ]);
    }
    setLoading(false);
  }

  return (
    <section className="space-y-4">
      <h2 className="text-lg font-semibold text-slate-800">Patient – Natural language booking</h2>
      <p className="text-slate-600 text-sm">
        Example: &quot;I want to book an appointment with Dr. Ahuja tomorrow morning&quot; then &quot;Book the 10:00 slot&quot; (multi-turn).
      </p>
      <div className="bg-white border border-slate-200 rounded-xl p-4 min-h-[200px] max-h-[320px] overflow-y-auto">
        {messages.length === 0 ? (
          <span className="text-slate-400">Send a message to start…</span>
        ) : (
          <ul className="space-y-3">
            {messages.map((msg, i) => (
              <li key={i}>
                <span className={`font-semibold ${msg.role === "user" ? "text-primary-600" : "text-slate-500"}`}>
                  {msg.role === "user" ? "You" : "Assistant"}:
                </span>{" "}
                {msg.content}
              </li>
            ))}
          </ul>
        )}
      </div>
      <div className="flex gap-2">
        <input
          type="text"
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && send()}
          placeholder="Type your request (e.g. book with Dr. Ahuja tomorrow at 10:00)"
          className="flex-1 px-4 py-2.5 border border-slate-300 rounded-lg text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          aria-label="Your message"
        />
        <button
          type="button"
          onClick={send}
          disabled={loading}
          className="px-5 py-2.5 bg-primary-600 text-white font-medium rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? "…" : "Send"}
        </button>
      </div>
    </section>
  );
}

function DoctorReport({
  doctorName,
  doctorEmail,
}: {
  doctorName?: string | null;
  doctorEmail?: string | null;
}) {
  const [prompt, setPrompt] = useState("");
  const [reply, setReply] = useState("");
  const [loading, setLoading] = useState(false);

  async function send() {
    if (!prompt.trim() || loading) return;
    setLoading(true);
    setReply("");
    try {
      const res = await fetch(`${API_BASE}/doctor-report`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          prompt,
          ...(doctorName && doctorEmail && { doctor_name: doctorName, doctor_email: doctorEmail }),
        }),
      });
      const text = await res.text();
      if (!res.ok) {
        setReply(`Error (${res.status}): ${text || res.statusText}`);
        setLoading(false);
        return;
      }
      let data: { reply?: string };
      try {
        data = JSON.parse(text);
      } catch {
        setReply("Invalid response from server: " + text.slice(0, 200));
        setLoading(false);
        return;
      }
      setReply(data.reply ?? "No reply.");
    } catch (e) {
      setReply("Error: " + (e instanceof Error ? e.message : String(e)));
    }
    setLoading(false);
  }

  return (
    <section className="space-y-4">
      <h2 className="text-lg font-semibold text-slate-800">Doctor – Summary report & notification</h2>
      <p className="text-slate-600 text-sm">
        Example: &quot;How many patients visited yesterday?&quot; or &quot;How many appointments do I have today?&quot;
      </p>
      <div className="flex gap-2">
        <input
          type="text"
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && send()}
          placeholder="Ask for summary (e.g. how many patients yesterday?)"
          className="flex-1 px-4 py-2.5 border border-slate-300 rounded-lg text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          aria-label="Your question"
        />
        <button
          type="button"
          onClick={send}
          disabled={loading}
          className="px-5 py-2.5 bg-primary-600 text-white font-medium rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? "…" : "Get report"}
        </button>
      </div>
      <div className="bg-white border border-slate-200 rounded-xl p-4 min-h-[120px]">
        {reply ? (
          <pre className="whitespace-pre-wrap font-sans text-slate-700 m-0">{reply}</pre>
        ) : (
          <span className="text-slate-400">Reply will appear here.</span>
        )}
      </div>
    </section>
  );
}
