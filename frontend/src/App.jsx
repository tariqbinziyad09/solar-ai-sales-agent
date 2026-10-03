import {
  BrowserRouter,
  Navigate,
  Outlet,
  Route,
  Routes,
} from "react-router-dom";
import "./App.css";
import DashboardLayout from "./components/layout/DashboardLayout";
import ProtectedRoute from "./components/auth/ProtectedRoute";

import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import Leads from "./pages/Leads";
import LeadDetails from "./pages/LeadDetails";
import Proposals from "./pages/Proposals";
import ProposalDetails from "./pages/ProposalDetails";
import Products from "./pages/Products";
import Packages from "./pages/Packages";
import AIAgent from "./pages/AIAgent";
import StaffManagement from "./pages/StaffManagement";
import Settings from "./pages/Settings";


/*
 * Frontend role guard.
 *
 * IMPORTANT:
 * This improves UX/navigation only.
 * Backend RBAC remains the authoritative security layer.
 */
function RoleRoute({ allowedRoles }) {
  let user = null;

  try {
    user = JSON.parse(localStorage.getItem("solar_crm_user"));
  } catch {
    user = null;
  }

  if (!user?.role || !allowedRoles.includes(user.role)) {
    return <Navigate to="/dashboard" replace />;
  }

  return <Outlet />;
}


function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />

        <Route element={<ProtectedRoute />}>
          <Route element={<DashboardLayout />}>
            <Route
              path="/"
              element={<Navigate to="/dashboard" replace />}
            />

            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/leads" element={<Leads />} />
            <Route path="/leads/:leadId" element={<LeadDetails />} />
            <Route path="/proposals" element={<Proposals />} />
            <Route
              path="/proposals/:proposalId"
              element={<ProposalDetails />}
            />
            <Route path="/products" element={<Products />} />
            <Route path="/packages" element={<Packages />} />
            <Route path="/ai-agent" element={<AIAgent />} />
            <Route path="/settings" element={<Settings />} />

            <Route element={<RoleRoute allowedRoles={["admin"]} />}>
              <Route path="/staff" element={<StaffManagement />} />
            </Route>
          </Route>
        </Route>

        <Route
          path="*"
          element={<Navigate to="/dashboard" replace />}
        />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
