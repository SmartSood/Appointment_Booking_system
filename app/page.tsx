import Link from "next/link";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth";

export default async function HomePage() {
  const session = await getServerSession(authOptions);

  if (session?.user) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-slate-50">
        <div className="text-center space-y-4">
          <h1 className="text-3xl font-bold text-slate-800">
            Welcome, {session.user.name}
          </h1>
          <p className="text-slate-600">You are logged in as {session.user.role}</p>
          <Link
            href="/dashboard"
            className="inline-block px-6 py-3 bg-primary-600 text-white rounded-lg font-medium hover:bg-primary-700 transition"
          >
            Go to Dashboard
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gradient-to-br from-slate-50 to-primary-50">
      <div className="text-center max-w-md mx-auto px-4 space-y-8">
        <h1 className="text-4xl font-bold text-slate-800">Dobble</h1>
        <p className="text-slate-600">
          Healthcare platform for patients and doctors. Sign in or register to continue.
        </p>
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Link
            href="/login"
            className="px-6 py-3 bg-primary-600 text-white rounded-lg font-medium hover:bg-primary-700 transition"
          >
            Log in
          </Link>
          <Link
            href="/signup"
            className="px-6 py-3 border-2 border-primary-600 text-primary-700 rounded-lg font-medium hover:bg-primary-50 transition"
          >
            Sign up
          </Link>
        </div>
      </div>
    </div>
  );
}
