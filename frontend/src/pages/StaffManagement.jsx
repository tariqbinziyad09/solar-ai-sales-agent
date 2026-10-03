import { useEffect, useState } from "react";
import {
  CheckCircle2,
  Plus,
  RefreshCw,
  ShieldCheck,
  UserRound,
  UserX,
  Users,
} from "lucide-react";
import api from "../services/api";

const roleLabels = {
  admin: "Administrator",
  sales_manager: "Sales Manager",
  sales_executive: "Sales Executive",
};

function StaffManagement() {
  const [staff, setStaff] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const [form, setForm] = useState({
    name: "",
    email: "",
    password: "",
    role: "sales_executive",
  });

  async function loadStaff() {
    setLoading(true);
    setError("");

    try {
      const { data } = await api.get("/users");
      setStaff(data);
    } catch (err) {
      setError(err.response?.data?.detail || "Unable to load staff accounts.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadStaff();
  }, []);

  function handleChange(event) {
    const { name, value } = event.target;
    setForm((current) => ({ ...current, [name]: value }));
  }

  async function handleCreate(event) {
    event.preventDefault();
    setSaving(true);
    setError("");
    setSuccess("");

    try {
      await api.post("/users", form);
      setForm({
        name: "",
        email: "",
        password: "",
        role: "sales_executive",
      });
      setSuccess("Staff account created successfully.");
      await loadStaff();
    } catch (err) {
      setError(err.response?.data?.detail || "Unable to create staff account.");
    } finally {
      setSaving(false);
    }
  }

  async function toggleStatus(member) {
    const nextStatus = !member.is_active;
    setError("");
    setSuccess("");

    try {
      await api.patch(`/users/${member.id}/status`, {
        is_active: nextStatus,
      });

      setSuccess(
        `${member.name} has been ${nextStatus ? "activated" : "deactivated"}.`
      );

      await loadStaff();
    } catch (err) {
      setError(err.response?.data?.detail || "Unable to update staff status.");
    }
  }

  const activeCount = staff.filter((member) => member.is_active).length;

  return (
    <div className="staff-page staff-page-polished">
      <div className="page-header staff-hero">
        <div>
          <p className="topbar-label">ADMINISTRATION</p>
          <h1>Staff Management</h1>
          <p>Create and manage internal Solar CRM staff accounts.</p>
        </div>

        <button
          type="button"
          className="secondary-button staff-refresh-button"
          onClick={loadStaff}
          disabled={loading}
        >
          <RefreshCw size={18} />
          Refresh
        </button>
      </div>

      <div className="staff-summary-grid">
        <div className="staff-summary-card">
          <Users size={20} />
          <div>
            <span>Total Accounts</span>
            <strong>{staff.length}</strong>
          </div>
        </div>

        <div className="staff-summary-card">
          <CheckCircle2 size={20} />
          <div>
            <span>Active Staff</span>
            <strong>{activeCount}</strong>
          </div>
        </div>

        <div className="staff-summary-card">
          <UserX size={20} />
          <div>
            <span>Inactive Staff</span>
            <strong>{Math.max(staff.length - activeCount, 0)}</strong>
          </div>
        </div>
      </div>

      {error && <div className="staff-message error-message">{error}</div>}
      {success && <div className="staff-message success-message">{success}</div>}

      <div className="staff-grid">
        <section className="staff-card staff-create-card">
          <div className="staff-card-heading">
            <div className="staff-card-icon">
              <Plus size={20} />
            </div>
            <div>
              <h2>Add Staff Member</h2>
              <p>Create a Manager or Sales Executive account.</p>
            </div>
          </div>

          <form className="staff-form" onSubmit={handleCreate}>
            <label>
              Full Name
              <input
                type="text"
                name="name"
                value={form.name}
                onChange={handleChange}
                minLength={2}
                required
                placeholder="e.g. Ali Khan"
              />
            </label>

            <label>
              Email
              <input
                type="email"
                name="email"
                value={form.email}
                onChange={handleChange}
                required
                placeholder="ali@solarcrm.com"
              />
            </label>

            <label>
              Temporary Password
              <input
                type="password"
                name="password"
                value={form.password}
                onChange={handleChange}
                required
                minLength={8}
                placeholder="Minimum 8 characters"
              />
            </label>

            <label>
              Role
              <select name="role" value={form.role} onChange={handleChange}>
                <option value="sales_executive">Sales Executive</option>
                <option value="sales_manager">Sales Manager</option>
              </select>
            </label>

            <button type="submit" className="primary-button" disabled={saving}>
              <ShieldCheck size={18} />
              {saving ? "Creating..." : "Create Staff Account"}
            </button>
          </form>
        </section>

        <section className="staff-card staff-list-card">
          <div className="staff-card-heading">
            <div className="staff-card-icon">
              <Users size={20} />
            </div>
            <div>
              <h2>CRM Staff</h2>
              <p>{staff.length} account(s) in the system.</p>
            </div>
          </div>

          {loading ? (
            <div className="staff-empty">Loading staff...</div>
          ) : staff.length === 0 ? (
            <div className="staff-empty">No staff accounts found.</div>
          ) : (
            <div className="staff-list">
              {staff.map((member) => (
                <article className="staff-member" key={member.id}>
                  <div className="staff-member-main">
                    <div className="staff-avatar">
                      {member.name?.charAt(0)?.toUpperCase() || "U"}
                    </div>

                    <div>
                      <div className="staff-name-row">
                        <strong>{member.name}</strong>
                        <span
                          className={
                            member.is_active
                              ? "staff-status active"
                              : "staff-status inactive"
                          }
                        >
                          {member.is_active ? (
                            <CheckCircle2 size={14} />
                          ) : (
                            <UserX size={14} />
                          )}
                          {member.is_active ? "Active" : "Inactive"}
                        </span>
                      </div>

                      <p>{member.email}</p>

                      <span className="staff-role">
                        <UserRound size={14} />
                        {roleLabels[member.role] || member.role}
                      </span>
                    </div>
                  </div>

                  <button
                    type="button"
                    className={
                      member.is_active
                        ? "staff-action danger"
                        : "staff-action"
                    }
                    onClick={() => toggleStatus(member)}
                  >
                    {member.is_active ? "Deactivate" : "Activate"}
                  </button>
                </article>
              ))}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}

export default StaffManagement;
