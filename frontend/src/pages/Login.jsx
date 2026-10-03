import { useState } from "react";
import { Navigate, useLocation, useNavigate } from "react-router-dom";
import { LockKeyhole, Mail, ShieldCheck, SunMedium } from "lucide-react";
import api from "../services/api";
import "../login.css";

function Login() {
  const navigate = useNavigate();
  const location = useLocation();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  if (localStorage.getItem("solar_crm_token")) {
    return <Navigate to="/dashboard" replace />;
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const { data } = await api.post("/auth/login", { email, password });

      localStorage.setItem("solar_crm_token", data.access_token);
      localStorage.setItem("solar_crm_user", JSON.stringify(data.user));

      navigate(location.state?.from || "/dashboard", { replace: true });
    } catch (err) {
      setError(err.response?.data?.detail || "Unable to sign in.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="login-page">
      <div className="login-shell">
        <section className="login-showcase" aria-hidden="true">
          <div className="login-showcase-badge">
            <SunMedium size={18} />
            SOLAR AI CRM
          </div>

          <div className="login-showcase-copy">
            <p>SMART SOLAR SALES OPERATIONS</p>
            <h2>Turn solar enquiries into qualified opportunities.</h2>
            <span>
              One workspace for leads, proposals, products, packages and your
              AI-powered sales assistant.
            </span>
          </div>

          <div className="login-feature-row">
            <div>
              <ShieldCheck size={18} />
              <span>Role-based access</span>
            </div>
            <div>
              <SunMedium size={18} />
              <span>AI sales workflow</span>
            </div>
          </div>
        </section>

        <section className="login-card">
          <div className="login-brand-icon">
            <SunMedium size={30} />
          </div>

          <p className="topbar-label">SOLAR CRM</p>
          <h1>Staff Sign In</h1>
          <p className="login-subtitle">
            Welcome back to Solar AI Sales Agent
          </p>

          <form onSubmit={handleSubmit} className="login-form">
            <label>
              Email
              <div className="login-input-wrap">
                <Mail size={18} />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="admin@company.com"
                  autoComplete="email"
                  required
                />
              </div>
            </label>

            <label>
              Password
              <div className="login-input-wrap">
                <LockKeyhole size={18} />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter your password"
                  autoComplete="current-password"
                  required
                />
              </div>
            </label>

            {error && <div className="login-error">{error}</div>}

            <button type="submit" className="login-button" disabled={loading}>
              {loading ? "Signing in..." : "Sign In"}
            </button>
          </form>

          <p className="login-security-note">
            <ShieldCheck size={15} />
            Secure access for authorized CRM staff
          </p>
        </section>
      </div>
    </div>
  );
}

export default Login;
