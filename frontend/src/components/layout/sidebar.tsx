"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  BarChart3,
  Bell,
  BriefcaseBusiness,
  LayoutDashboard,
  Lightbulb,
  LogOut,
} from "lucide-react";
import { signOut } from "next-auth/react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { ThemeToggle } from "./theme-toggle";

const navItems = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/portfolios", label: "Portfolios", icon: BriefcaseBusiness },
  { href: "/recommendations", label: "AI Insights", icon: Lightbulb },
  { href: "/notifications", label: "Notifications", icon: Bell },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="flex h-screen w-64 flex-col border-r bg-card">
      <div className="flex h-14 items-center gap-2 border-b px-4">
        <BarChart3 className="h-6 w-6 text-primary" />
        <span className="text-lg font-bold">Stockbot</span>
      </div>

      <nav className="flex-1 space-y-1 p-3">
        {navItems.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={cn(
              "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors hover:bg-accent hover:text-accent-foreground",
              pathname.startsWith(item.href)
                ? "bg-accent text-accent-foreground"
                : "text-muted-foreground"
            )}
          >
            <item.icon className="h-4 w-4" />
            {item.label}
          </Link>
        ))}
      </nav>

      <div className="border-t p-3 space-y-1">
        <div className="flex items-center justify-between px-3">
          <span className="text-xs text-muted-foreground">Theme</span>
          <ThemeToggle />
        </div>
        <Button
          variant="ghost"
          className="w-full justify-start gap-3 text-muted-foreground"
          onClick={() => signOut({ callbackUrl: "/login" })}
        >
          <LogOut className="h-4 w-4" />
          Sign Out
        </Button>
      </div>
    </aside>
  );
}
