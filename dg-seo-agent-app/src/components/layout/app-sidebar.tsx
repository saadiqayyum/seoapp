"use client";

import {
  LayoutDashboard,
  Search,
  Users,
  ListChecks,
  FileText,
  Globe,
  PlayCircle,
  History,
  LogOut,
} from "lucide-react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarFooter,
} from "@/components/ui/sidebar";
import { Separator } from "@/components/ui/separator";
import { DomainSwitcher } from "@/components/layout/domain-switcher";

const auditNav = [
  { title: "Overview", href: "/", icon: LayoutDashboard },
  { title: "Keywords", href: "/keywords", icon: Search },
  { title: "Competitors", href: "/competitors", icon: Users },
  { title: "Action Items", href: "/actions", icon: ListChecks },
  { title: "Full Report", href: "/report", icon: FileText },
];

const accountNav = [
  { title: "New Audit", href: "/audits/new", icon: PlayCircle },
  { title: "Audit History", href: "/audits", icon: History },
  { title: "Domains", href: "/domains", icon: Globe },
];

export function AppSidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const [email, setEmail] = useState<string | null>(null);

  useEffect(() => {
    fetch("/api/auth/me")
      .then((r) => r.json())
      .then((d) => setEmail(d.user?.email ?? null))
      .catch(() => {});
  }, []);

  async function handleLogout() {
    await fetch("/api/auth/logout", { method: "POST" });
    router.push("/login");
    router.refresh();
  }

  return (
    <Sidebar>
      <SidebarHeader className="gap-3 px-4 py-4">
        <DomainSwitcher />
      </SidebarHeader>
      <Separator />
      <SidebarContent className="pt-2">
        <SidebarGroup>
          <SidebarGroupLabel className="text-[10px] uppercase tracking-widest">
            Audit
          </SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {auditNav.map((item) => {
                const isActive =
                  item.href === "/"
                    ? pathname === "/"
                    : pathname.startsWith(item.href);
                return (
                  <SidebarMenuItem key={item.href}>
                    <SidebarMenuButton
                      isActive={isActive}
                      render={<Link href={item.href} />}
                    >
                      <item.icon className="h-4 w-4" />
                      <span>{item.title}</span>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                );
              })}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>

        <SidebarGroup>
          <SidebarGroupLabel className="text-[10px] uppercase tracking-widest">
            Account
          </SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {accountNav.map((item) => {
                const isActive = pathname.startsWith(item.href);
                return (
                  <SidebarMenuItem key={item.href}>
                    <SidebarMenuButton
                      isActive={isActive}
                      render={<Link href={item.href} />}
                    >
                      <item.icon className="h-4 w-4" />
                      <span>{item.title}</span>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                );
              })}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
      <SidebarFooter className="px-4 py-4">
        {email && (
          <div className="rounded-lg border border-border/60 bg-muted/40 px-3 py-2.5">
            <p className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">
              Signed in as
            </p>
            <p className="truncate text-xs font-semibold">{email}</p>
            <button
              type="button"
              onClick={handleLogout}
              className="mt-2 flex items-center gap-1.5 text-[11px] font-medium text-muted-foreground hover:text-foreground"
            >
              <LogOut className="h-3 w-3" />
              Sign out
            </button>
          </div>
        )}
      </SidebarFooter>
    </Sidebar>
  );
}
