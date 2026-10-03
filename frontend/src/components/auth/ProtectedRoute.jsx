import { Navigate, Outlet, useLocation } from "react-router-dom";
function ProtectedRoute() {
  const location = useLocation();
  if (!localStorage.getItem("solar_crm_token"))
    return <Navigate to="/login" replace state={{from:location.pathname}} />;
  return <Outlet />;
}
export default ProtectedRoute;
