import type { NextAuthOptions } from "next-auth";
import CredentialsProvider from "next-auth/providers/credentials";

const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8000";

export const authOptions: NextAuthOptions = {
  session: {
    strategy: "jwt",
    maxAge: 30 * 24 * 60 * 60, // 30 days
  },
  pages: {
    signIn: "/login",
  },
  providers: [
    CredentialsProvider({
      name: "credentials",
      credentials: {
        email: { label: "Email", type: "email" },
        password: { label: "Password", type: "password" },
        role: { label: "Role", type: "text" },
        accessToken: { label: "Access Token", type: "text" },
      },
      async authorize(credentials) {
        if (!credentials?.email || !credentials?.role) return null;
        // If token from register, validate via /api/me
        if (credentials.accessToken) {
          const res = await fetch(`${BACKEND_URL}/api/me`, {
            headers: { Authorization: `Bearer ${credentials.accessToken}` },
          });
          if (!res.ok) return null;
          const user = await res.json();
          return { ...user, accessToken: credentials.accessToken };
        }
        if (!credentials?.password) return null;
        const res = await fetch(`${BACKEND_URL}/api/auth/login`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            email: credentials.email,
            password: credentials.password,
            role: credentials.role,
          }),
        });
        if (!res.ok) return null;
        const data = await res.json();
        const user = data.user;
        if (!user) return null;
        return { ...user, accessToken: data.access_token };
      },
    }),
  ],
  callbacks: {
    async jwt({ token, user }) {
      if (user) {
        token.id = user.id;
        token.role = user.role;
        token.email = (user as { email?: string }).email;
        token.name = (user as { name?: string }).name;
        token.accessToken = (user as { accessToken?: string }).accessToken;
      }
      return token;
    },
    async session({ session, token }) {
      if (session.user) {
        (session.user as { id: string }).id = token.id as string;
        (session.user as { role: string }).role = token.role as string;
        session.user.email = (token.email as string) ?? session.user.email ?? null;
        session.user.name = (token.name as string) ?? session.user.name ?? null;
        (session as { accessToken?: string }).accessToken = token.accessToken as string;
      }
      return session;
    },
  },
};
