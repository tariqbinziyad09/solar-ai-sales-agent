import { useEffect, useMemo, useState } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import {
  Bot,
  Boxes,
  FileText,
  LayoutDashboard,
  LogOut,
  Menu,
  PackageOpen,
  Settings,
  ShieldCheck,
  Users,
  X,
  Zap,
} from "lucide-react";
import api from "../../services/api";

const roleLabels = {
  admin: "Administrator",
  sales_manager: "Sales Manager",
  sales_executive: "Sales Executive",
};

function DashboardLayout() {
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const [user, setUser] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem("solar_crm_user")) || null;
    } catch {
      return null;
    }
  });

  useEffect(() => {
    api
      .get("/auth/me")
      .then(({ data }) => {
        setUser(data);
        localStorage.setItem("solar_crm_user", JSON.stringify(data));
      })
      .catch(() => { });
  }, []);

  useEffect(() => {
    function refreshUserFromStorage() {
      try {
        const updatedUser =
          JSON.parse(localStorage.getItem("solar_crm_user")) || null;
        setUser(updatedUser);
      } catch {
        setUser(null);
      }
    }

    window.addEventListener(
      "solar-crm-user-updated",
      refreshUserFromStorage
    );

    return () => {
      window.removeEventListener(
        "solar-crm-user-updated",
        refreshUserFromStorage
      );
    };
  }, []);

  const role = user?.role;

  const menuItems = useMemo(() => {
    const items = [
      {
        name: "Dashboard",
        path: "/dashboard",
        icon: LayoutDashboard,
        roles: ["admin", "sales_manager", "sales_executive"],
      },
      {
        name: role === "sales_executive" ? "My Leads" : "Leads",
        path: "/leads",
        icon: Users,
        roles: ["admin", "sales_manager", "sales_executive"],
      },
      {
        name: "Proposals",
        path: "/proposals",
        icon: FileText,
        roles: ["admin", "sales_manager", "sales_executive"],
      },
      {
        name: "Products",
        path: "/products",
        icon: Boxes,
        roles: ["admin", "sales_manager", "sales_executive"],
      },
      {
        name: "Packages",
        path: "/packages",
        icon: PackageOpen,
        roles: ["admin", "sales_manager", "sales_executive"],
      },
      {
        name: "AI Sales Agent",
        path: "/ai-agent",
        icon: Bot,
        roles: ["admin", "sales_manager", "sales_executive"],
      },
      {
        name: "Staff Management",
        path: "/staff",
        icon: ShieldCheck,
        roles: ["admin"],
      },
    ];

    return items.filter((item) => item.roles.includes(role));
  }, [role]);

  function logout() {
    localStorage.removeItem("solar_crm_token");
    localStorage.removeItem("solar_crm_user");
    navigate("/login", { replace: true });
  }

  function closeSidebar() {
    setSidebarOpen(false);
  }

  const initial = user?.name?.trim()?.charAt(0)?.toUpperCase() || "U";

  return (
    <div className="app-shell">
      <button
        type="button"
        className="mobile-sidebar-toggle"
        onClick={() => setSidebarOpen((open) => !open)}
        aria-label={sidebarOpen ? "Close navigation" : "Open navigation"}
        aria-expanded={sidebarOpen}
      >
        {sidebarOpen ? <X size={21} /> : <Menu size={21} />}
      </button>

      {sidebarOpen && (
        <button
          type="button"
          className="sidebar-backdrop"
          aria-label="Close navigation"
          onClick={closeSidebar}
        />
      )}

      <aside className={sidebarOpen ? "sidebar mobile-open" : "sidebar"}>
        <div className="brand">
          <div className="brand-icon">
            <Zap size={22} />
          </div>

          <div>
            <h2>Solar AI</h2>
            <span>Sales Agent</span>
          </div>
        </div>

        <div className="sidebar-section-label">WORKSPACE</div>

        <nav className="sidebar-nav">
          {menuItems.map((item) => {
            const Icon = item.icon;

            return (
              <NavLink
                key={item.path}
                to={item.path}
                onClick={closeSidebar}
                className={({ isActive }) =>
                  isActive ? "nav-item active" : "nav-item"
                }
              >
                <Icon size={20} />
                <span>{item.name}</span>
              </NavLink>
            );
          })}
        </nav>

        <div className="sidebar-footer">
          <div className="sidebar-user-mini">
            <div className="avatar">{initial}</div>
            <div>
              <strong>{user?.name || "Staff User"}</strong>
              <span>{roleLabels[role] || "CRM User"}</span>
            </div>
          </div>

          <NavLink
            to="/settings"
            onClick={closeSidebar}
            className={({ isActive }) =>
              isActive
                ? "nav-item settings-button active"
                : "nav-item settings-button"
            }
          >
            <Settings size={20} />
            <span>Settings</span>
          </NavLink>

          <button
            type="button"
            className="nav-item settings-button logout-button"
            onClick={logout}
          >
            <LogOut size={20} />
            <span>Logout</span>
          </button>
        </div>
      </aside>

      <main className="main-area">
        <header className="topbar">
          <div className="topbar-copy">
            <p className="topbar-label">SOLAR CRM</p>
            <h3>Solar AI Sales Agent</h3>
          </div>

          <div className="admin-profile">
            <div className="avatar">{initial}</div>
            <div>
              <strong>{user?.name || "Staff User"}</strong>
              <span>{roleLabels[role] || "CRM User"}</span>
            </div>
          </div>
        </header>

        <section className="page-content">
          <Outlet />
        </section>
      </main>
    </div>
  );
}

export default DashboardLayout;
