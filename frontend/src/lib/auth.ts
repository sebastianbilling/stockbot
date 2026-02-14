import NextAuth from "next-auth";
import Credentials from "next-auth/providers/credentials";
import type { TokenResponse } from "@/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const { handlers, signIn, signOut, auth } = NextAuth({
  providers: [
    Credentials({
      credentials: {
        email: {},
        password: {},
      },
      async authorize(credentials) {
        const res = await fetch(`${API_URL}/api/auth/login`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            email: credentials.email,
            password: credentials.password,
          }),
        });

        if (!res.ok) return null;

        const data: TokenResponse = await res.json();
        return {
          id: data.user.id,
          email: data.user.email,
          name: data.user.full_name,
          accessToken: data.access_token,
        };
      },
    }),
  ],
  callbacks: {
    async jwt({ token, user }) {
      if (user) {
        token.accessToken = (user as Record<string, unknown>).accessToken;
        token.userId = user.id;
      }
      return token;
    },
    async session({ session, token }) {
      session.accessToken = token.accessToken as string;
      session.user.id = token.userId as string;
      return session;
    },
  },
  pages: {
    signIn: "/login",
  },
});
