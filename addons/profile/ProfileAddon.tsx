"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

interface ProfileAddonProps {
  user: {
    id: string;
    name: string;
    email: string;
    role: string;
    specialization: string | null;
  };
}

export function ProfileAddon({ user }: ProfileAddonProps) {
  const router = useRouter();
  const [name, setName] = useState(user.name);
  const [specialization, setSpecialization] = useState(user.specialization ?? "");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setMessage(null);
    try {
      const res = await fetch("/api/profile", {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name,
          ...(user.role === "DOCTOR" && { specialization: specialization || null }),
        }),
      });
      if (res.ok) {
        setMessage({ type: "success", text: "Profile updated." });
        router.refresh();
      } else {
        setMessage({ type: "error", text: "Update failed. Try again." });
      }
    } catch {
      setMessage({ type: "error", text: "Something went wrong." });
    }
    setLoading(false);
  }

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm max-w-md">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Email</label>
          <input
            type="email"
            value={user.email}
            disabled
            className="w-full px-4 py-2 border border-slate-200 rounded-lg bg-slate-50 text-slate-500"
          />
          <p className="text-xs text-slate-500 mt-1">Email cannot be changed.</p>
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Full name</label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
            className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
          />
        </div>
        {user.role === "DOCTOR" && (
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              Specialization
            </label>
            <input
              type="text"
              value={specialization}
              onChange={(e) => setSpecialization(e.target.value)}
              className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              placeholder="e.g. General Practice"
            />
          </div>
        )}
        {message && (
          <p
            className={`text-sm ${
              message.type === "success" ? "text-emerald-600" : "text-red-600"
            }`}
          >
            {message.text}
          </p>
        )}
        <button
          type="submit"
          disabled={loading}
          className="px-4 py-2 bg-primary-600 text-white rounded-lg font-medium hover:bg-primary-700 disabled:opacity-50 transition"
        >
          {loading ? "Saving…" : "Save changes"}
        </button>
      </form>
    </div>
  );
}
