import Link from "next/link";
import {
  ChevronDown,
  LayoutDashboard,
  Library,
  LogOut,
  ScrollText,
  Search,
  Settings,
  User,
} from "lucide-react";

import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { cn } from "@/lib/utils";
import { Brand } from "@/components/brand";

const NAV = [
  { label: "Assistant", icon: Search, active: true },
  { label: "Dashboard", icon: LayoutDashboard, active: false },
  { label: "Knowledge Base", icon: Library, active: false },
  { label: "Compliance Audit", icon: ScrollText, active: false },
];

export function SiteHeader() {
  return (
    <header className="sticky top-0 z-40 border-b bg-background/80 backdrop-blur">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between gap-4 px-4 sm:px-6 lg:px-8">
        <Brand />

        <nav className="hidden items-center gap-1 md:flex">
          {NAV.map(({ label, icon: Icon, active }) => (
            <Link
              key={label}
              href="#"
              className={cn(
                "flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium text-muted-foreground transition-colors hover:bg-accent hover:text-accent-foreground",
                active && "bg-accent text-accent-foreground"
              )}
            >
              <Icon className="h-4 w-4" />
              {label}
            </Link>
          ))}
        </nav>

        <div className="flex items-center gap-3">
          <Badge variant="gold" className="hidden sm:inline-flex">
            Internal · RM-facing
          </Badge>

          <DropdownMenu>
            <DropdownMenuTrigger className="flex items-center gap-2 rounded-full border bg-background p-1 pr-3">
              <Avatar className="h-8 w-8">
                <AvatarFallback className="bg-primary text-primary-foreground">
                  BK
                </AvatarFallback>
              </Avatar>
              <span className="hidden text-sm font-medium sm:block">
                Bhawana · RM-12
              </span>
              <ChevronDown className="h-3.5 w-3.5 text-muted-foreground" />
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-56">
              <DropdownMenuLabel className="flex flex-col gap-0.5">
                <span className="text-sm font-semibold">Bhawana Kumari</span>
                <span className="text-xs font-normal text-muted-foreground">
                  Relationship Manager · Branch 04
                </span>
              </DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem>
                <User />
                Profile
              </DropdownMenuItem>
              <DropdownMenuItem>
                <Settings />
                Preferences
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem>
                <LogOut />
                Sign out
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>
    </header>
  );
}