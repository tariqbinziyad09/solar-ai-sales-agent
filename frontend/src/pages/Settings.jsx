import { useEffect, useState } from "react";
import {
  BadgeCheck,
  KeyRound,
  LockKeyhole,
  Mail,
  Save,
  Settings as SettingsIcon,
  ShieldCheck,
  UserRound,
} from "lucide-react";
import api from "../services/api";

const roleLabels = {
  admin: "Administrator",
  sales_manager: "Sales Manager",
  sales_executive: "Sales Executive",
};

function Settings() {
  const [user, setUser] = useState(null);
  const [profile, setProfile] = useState({ name: "", email: "" });
  const [passwords, setPasswords] = useState({
    current_password: "",
    new_password: "",
    confirm_password: "",
  });

  const [loading, setLoading] = useState(true);
  const [savingProfile, setSavingProfile] = useState(false);
  const [savingPassword, setSavingPassword] = useState(false);
  const [profileMessage, setProfileMessage] = useState("");
  const [profileError, setProfileError] = useState("");
  const [passwordMessage, setPasswordMessage] = useState("");
  const [passwordError, setPasswordError] = useState("");

  useEffect(() => {
    loadProfile();
  }, []);

  async function loadProfile() {
    setLoading(true);

    try {
      const { data } = await api.get("/auth/me");
      setUser(data);
      setProfile({
        name: data.name || "",
        email: data.email || "",
      });
      localStorage.setItem("solar_crm_user", JSON.stringify(data));
    } catch (err) {
      setProfileError(
        err.response?.data?.detail || "Unable to load account settings."
      );
    } finally {
      setLoading(false);
    }
  }

  function handleProfileChange(event) {
    const { name, value } = event.target;
    setProfile((current) => ({ ...current, [name]: value }));
  }

  function handlePasswordChange(event) {
    const { name, value } = event.target;
    setPasswords((current) => ({ ...current, [name]: value }));
  }

  async function saveProfile(event) {
    event.preventDefault();
    setProfileError("");
    setProfileMessage("");

    if (!profile.name.trim() || !profile.email.trim()) {
      setProfileError("Name aur email required hain.");
      return;
    }

    setSavingProfile(true);

    try {
      const { data } = await api.patch("/auth/me", {
        name: profile.name.trim(),
        email: profile.email.trim(),
      });

      setUser(data);
      setProfile({ name: data.name, email: data.email });
      localStorage.setItem("solar_crm_user", JSON.stringify(data));
      setProfileMessage("Profile successfully updated.");

      // DashboardLayout also reads this event and refreshes the sidebar/topbar.
      window.dispatchEvent(new Event("solar-crm-user-updated"));
    } catch (err) {
      setProfileError(
        err.response?.data?.detail || "Unable to update profile."
      );
    } finally {
      setSavingProfile(false);
    }
  }

  async function changePassword(event) {
    event.preventDefault();
    setPasswordError("");
    setPasswordMessage("");

    if (passwords.new_password !== passwords.confirm_password) {
      setPasswordError("New password aur confirm password match nahi karte.");
      return;
    }

    if (passwords.new_password.length < 8) {
      setPasswordError("New password kam az kam 8 characters ka hona chahiye.");
      return;
    }

    setSavingPassword(true);

    try {
      const { data } = await api.post("/auth/change-password", passwords);

      setPasswordMessage(data.message || "Password successfully changed.");
      setPasswords({
        current_password: "",
        new_password: "",
        confirm_password: "",
      });
    } catch (err) {
      const detail = err.response?.data?.detail;

      setPasswordError(
        typeof detail === "string"
          ? detail
          : "Unable to change password."
      );
    } finally {
      setSavingPassword(false);
    }
  }

  if (loading) {
    return (
      <div className="settings-page">
        <div className="settings-loading">Loading settings...</div>
      </div>
    );
  }

  return (
    <div className="settings-page">
      <div className="settings-hero">
        <div>
          <p className="page-eyebrow">ACCOUNT & SECURITY</p>
          <h1>Settings</h1>
          <p>
            Manage your Solar CRM profile and account security.
          </p>
        </div>

        <div className="settings-hero-icon">
          <SettingsIcon size={26} />
        </div>
      </div>

      <div className="settings-grid">
        <section className="settings-card">
          <div className="settings-card-header">
            <div className="settings-card-icon">
              <UserRound size={20} />
            </div>
            <div>
              <h2>My Profile</h2>
              <p>Update your personal CRM account information.</p>
            </div>
          </div>

          <form className="settings-form" onSubmit={saveProfile}>
            <label>
              <span>Full Name</span>
              <div className="settings-input-wrap">
                <UserRound size={17} />
                <input
                  name="name"
                  value={profile.name}
                  onChange={handleProfileChange}
                  minLength={2}
                  maxLength={120}
                  required
                />
              </div>
            </label>

            <label>
              <span>Email Address</span>
              <div className="settings-input-wrap">
                <Mail size={17} />
                <input
                  type="email"
                  name="email"
                  value={profile.email}
                  onChange={handleProfileChange}
                  required
                />
              </div>
            </label>

            {profileError && (
              <div className="settings-alert error">{profileError}</div>
            )}

            {profileMessage && (
              <div className="settings-alert success">{profileMessage}</div>
            )}

            <button
              type="submit"
              className="settings-primary-button"
              disabled={savingProfile}
            >
              <Save size={17} />
              {savingProfile ? "Saving..." : "Save Profile"}
            </button>
          </form>
        </section>

        <section className="settings-card">
          <div className="settings-card-header">
            <div className="settings-card-icon">
              <ShieldCheck size={20} />
            </div>
            <div>
              <h2>Account Information</h2>
              <p>Your CRM access and account status.</p>
            </div>
          </div>

          <div className="settings-account-list">
            <div>
              <span>Role</span>
              <strong>{roleLabels[user?.role] || user?.role || "CRM User"}</strong>
            </div>

            <div>
              <span>Account Status</span>
              <strong className={user?.is_active ? "account-active" : ""}>
                <BadgeCheck size={16} />
                {user?.is_active ? "Active" : "Inactive"}
              </strong>
            </div>

            <div>
              <span>User ID</span>
              <strong>#{user?.id}</strong>
            </div>
          </div>

          <p className="settings-info-note">
            Role aur account status security reasons ki wajah se yahan
            editable nahi hain. Administrator Staff Management se access
            control manage karta hai.
          </p>
        </section>

        <section className="settings-card settings-security-card">
          <div className="settings-card-header">
            <div className="settings-card-icon">
              <KeyRound size={20} />
            </div>
            <div>
              <h2>Change Password</h2>
              <p>Verify your current password before setting a new one.</p>
            </div>
          </div>

          <form className="settings-form" onSubmit={changePassword}>
            <label>
              <span>Current Password</span>
              <div className="settings-input-wrap">
                <LockKeyhole size={17} />
                <input
                  type="password"
                  name="current_password"
                  value={passwords.current_password}
                  onChange={handlePasswordChange}
                  autoComplete="current-password"
                  required
                />
              </div>
            </label>

            <div className="settings-password-grid">
              <label>
                <span>New Password</span>
                <div className="settings-input-wrap">
                  <KeyRound size={17} />
                  <input
                    type="password"
                    name="new_password"
                    value={passwords.new_password}
                    onChange={handlePasswordChange}
                    minLength={8}
                    maxLength={72}
                    autoComplete="new-password"
                    required
                  />
                </div>
              </label>

              <label>
                <span>Confirm New Password</span>
                <div className="settings-input-wrap">
                  <KeyRound size={17} />
                  <input
                    type="password"
                    name="confirm_password"
                    value={passwords.confirm_password}
                    onChange={handlePasswordChange}
                    minLength={8}
                    maxLength={72}
                    autoComplete="new-password"
                    required
                  />
                </div>
              </label>
            </div>

            {passwordError && (
              <div className="settings-alert error">{passwordError}</div>
            )}

            {passwordMessage && (
              <div className="settings-alert success">{passwordMessage}</div>
            )}

            <button
              type="submit"
              className="settings-primary-button"
              disabled={savingPassword}
            >
              <KeyRound size={17} />
              {savingPassword ? "Updating..." : "Change Password"}
            </button>
          </form>
        </section>
      </div>
    </div>
  );
}

export default Settings;
