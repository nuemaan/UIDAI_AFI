import { 
  LayoutDashboard, 
  Map, 
  BarChart3, 
  Target, 
  Layers,
  Info,
  Upload
} from "lucide-react";
import { NavLink } from "@/components/NavLink";
import { useLocation } from "react-router-dom";
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarHeader,
  SidebarFooter,
  useSidebar,
} from "@/components/ui/sidebar";
import DataSourceBadge from "./DataSourceBadge";

const navigationItems = [
  { 
    title: "National Overview", 
    url: "/", 
    icon: LayoutDashboard,
    description: "AFI distribution & summary"
  },
  { 
    title: "State Comparison", 
    url: "/states", 
    icon: BarChart3,
    description: "State-wise rankings"
  },
  { 
    title: "District Hotspots", 
    url: "/districts", 
    icon: Target,
    description: "High friction areas"
  },
  { 
    title: "AFI Decomposition", 
    url: "/decomposition", 
    icon: Layers,
    description: "Why friction exists"
  },
  { 
    title: "District Typologies", 
    url: "/typologies", 
    icon: Map,
    description: "AI-driven clusters"
  },
  { 
    title: "Data Upload", 
    url: "/upload", 
    icon: Upload,
    description: "Upload CSV data"
  },
];

export function AppSidebar() {
  const { state } = useSidebar();
  const collapsed = state === "collapsed";
  const location = useLocation();

  return (
    <Sidebar collapsible="icon">
      <SidebarHeader className="border-b border-sidebar-border px-4 py-4">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary text-primary-foreground font-bold text-lg">
            AFI
          </div>
          {!collapsed && (
            <div className="flex flex-col">
              <span className="font-semibold text-sidebar-foreground">
                AFI Dashboard
              </span>
              <span className="text-xs text-muted-foreground">
                Aadhaar Friction Index
              </span>
            </div>
          )}
        </div>
      </SidebarHeader>

      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>Analytics</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {navigationItems.map((item) => (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton 
                    asChild
                    isActive={location.pathname === item.url}
                    tooltip={collapsed ? item.title : undefined}
                  >
                    <NavLink 
                      to={item.url} 
                      end 
                      className="flex items-center gap-3"
                      activeClassName="bg-sidebar-accent text-sidebar-accent-foreground"
                    >
                      <item.icon className="h-4 w-4 shrink-0" />
                      {!collapsed && (
                        <div className="flex flex-col">
                          <span>{item.title}</span>
                          <span className="text-xs text-muted-foreground">
                            {item.description}
                          </span>
                        </div>
                      )}
                    </NavLink>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter className="border-t border-sidebar-border p-4">
        <div className="space-y-2">
          <DataSourceBadge />
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <Info className="h-3 w-3" />
            {!collapsed && <span>UIDAI Policy Support Tool</span>}
          </div>
        </div>
      </SidebarFooter>
    </Sidebar>
  );
}
