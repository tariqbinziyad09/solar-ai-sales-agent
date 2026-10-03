import { useEffect, useState } from "react";







import { useNavigate, useParams } from "react-router-dom";







import {







    ArrowLeft,







    Mail,







    MapPin,







    Phone,







    Zap,







    History,







    Brain,







    MessageSquare,







    Wallet,







    Gauge,







    Globe,







    CalendarClock,







    CheckCircle2,







    AlertTriangle,







    ListTodo,







    Plus,







    Trash2,



    UserRoundCheck,







} from "lucide-react";







import api from "../services/api";







function LeadDetails() {







    const { leadId } = useParams();







    const navigate = useNavigate();







    // Frontend visibility only. Backend RBAC remains authoritative.



    const [currentUser] = useState(() => {



        try {



            return JSON.parse(localStorage.getItem("solar_crm_user")) || null;



        } catch {



            return null;



        }



    });







    const canAssignLead =



        currentUser?.role === "admin" ||



        currentUser?.role === "sales_manager";



    // Lead deletion: Admin / Sales Manager only.

    const canDeleteLead =

        currentUser?.role === "admin" ||

        currentUser?.role === "sales_manager";







    // Main data







    const [lead, setLead] = useState(null);







    const [activities, setActivities] = useState([]);







    const [intelligence, setIntelligence] = useState(null);







    // Page states







    const [loading, setLoading] = useState(true);







    const [error, setError] = useState("");



    const [deletingLead, setDeletingLead] = useState(false);

    const [deleteLeadError, setDeleteLeadError] = useState("");







    const [followUpAt, setFollowUpAt] = useState("");







    const [followUpNote, setFollowUpNote] = useState("");







    const [followUpSaving, setFollowUpSaving] = useState(false);







    const [followUpMessage, setFollowUpMessage] = useState("");















    // Lead assignment



    const [salesExecutives, setSalesExecutives] = useState([]);



    const [selectedExecutiveId, setSelectedExecutiveId] = useState("");



    const [assignmentSaving, setAssignmentSaving] = useState(false);



    const [assignmentMessage, setAssignmentMessage] = useState("");







    // Sales tasks







    const [tasks, setTasks] = useState([]);







    const [taskTitle, setTaskTitle] = useState("");







    const [taskDescription, setTaskDescription] = useState("");







    const [taskPriority, setTaskPriority] = useState("medium");







    const [taskDueAt, setTaskDueAt] = useState("");







    const [taskSaving, setTaskSaving] = useState(false);







    const [taskMessage, setTaskMessage] = useState("");
    // CRM Notes
    const [notes, setNotes] = useState([]);
    const [noteContent, setNoteContent] = useState("");
    const [noteSaving, setNoteSaving] = useState(false);
    const [noteMessage, setNoteMessage] = useState("");
    const [editingNoteId, setEditingNoteId] = useState(null);
    const [editingNoteContent, setEditingNoteContent] = useState("");
    const [noteActionId, setNoteActionId] = useState(null);

    const canManageNote = (note) =>
        note.author_user_id === currentUser?.id ||
        currentUser?.role === "admin" ||
        currentUser?.role === "sales_manager";









    // =========================================================







    // LOAD ALL LEAD DATA







    // =========================================================







    useEffect(() => {







        loadLead();







        loadActivities();







        loadIntelligence();







        loadTasks();
        loadNotes();







        if (canAssignLead) {



            loadSalesExecutives();



        }







    }, [leadId, canAssignLead]);







    // =========================================================







    // GET LEAD DETAILS







    // GET /api/leads/{lead_id}







    // =========================================================







    async function loadLead() {







        try {







            setLoading(true);







            setError("");







            const response = await api.get(`/leads/${leadId}`);







            setLead(response.data);



            setSelectedExecutiveId(



                response.data.assigned_to_user_id



                    ? String(response.data.assigned_to_user_id)



                    : ""



            );







            const nextFollowUp = response.data.next_follow_up_at;







            setFollowUpAt(







                nextFollowUp







                    ? new Date(nextFollowUp).toISOString().slice(0, 16)







                    : ""







            );







            setFollowUpNote(response.data.follow_up_note || "");







        } catch (err) {







            console.error("Failed to load lead:", err);







            setError("Unable to load lead details.");







        } finally {







            setLoading(false);







        }







    }







    // =========================================================







    // GET CRM ACTIVITY TIMELINE







    // GET /api/leads/{lead_id}/activities







    // =========================================================







    async function loadActivities() {







        try {







            const response = await api.get(







                `/leads/${leadId}/activities`







            );







            setActivities(response.data);







        } catch (err) {







            console.error(







                "Failed to load activities:",







                err







            );







        }







    }







    // =========================================================







    // GET SALES INTELLIGENCE







    // GET /api/leads/{lead_id}/intelligence







    // =========================================================







    async function loadIntelligence() {







        try {







            const response = await api.get(







                `/leads/${leadId}/intelligence`







            );







            setIntelligence(response.data);







        } catch (err) {







            console.error(







                "Failed to load sales intelligence:",







                err







            );







        }







    }







    async function loadTasks() {







        try {







            const response = await api.get(`/leads/${leadId}/tasks`);







            setTasks(Array.isArray(response.data) ? response.data : []);







        } catch (err) {







            console.error("Failed to load sales tasks:", err);







        }







    }















    async function addTask() {







        if (!taskTitle.trim()) {







            setTaskMessage("Task title is required.");







            return;







        }







        try {







            setTaskSaving(true);







            setTaskMessage("");







            await api.post(`/leads/${leadId}/tasks`, {







                title: taskTitle.trim(),







                description: taskDescription.trim() || null,







                priority: taskPriority,







                due_at: taskDueAt ? new Date(taskDueAt).toISOString() : null,







            });







            setTaskTitle("");







            setTaskDescription("");







            setTaskPriority("medium");







            setTaskDueAt("");







            await Promise.all([loadTasks(), loadActivities()]);







            setTaskMessage("Sales task created.");







        } catch (err) {







            setTaskMessage(err?.response?.data?.detail || "Unable to create task.");







        } finally {







            setTaskSaving(false);







        }







    }















    async function toggleTask(task) {







        try {







            await api.patch(`/leads/${leadId}/tasks/${task.id}`, {







                status: task.status === "completed" ? "pending" : "completed",







            });







            await Promise.all([loadTasks(), loadActivities()]);







        } catch (err) {







            setTaskMessage(err?.response?.data?.detail || "Unable to update task.");







        }







    }















    async function removeTask(task) {







        if (!window.confirm(`Delete task "${task.title}"?`)) return;







        try {







            await api.delete(`/leads/${leadId}/tasks/${task.id}`);







            await Promise.all([loadTasks(), loadActivities()]);







        } catch (err) {







            setTaskMessage(err?.response?.data?.detail || "Unable to delete task.");







        }







    }















    // =========================================================
    // CRM NOTES
    // =========================================================
    async function loadNotes() {
        try {
            const response = await api.get(`/leads/${leadId}/notes`);
            setNotes(Array.isArray(response.data) ? response.data : []);
        } catch (err) {
            console.error("Failed to load CRM notes:", err);
            setNoteMessage(err?.response?.data?.detail || "Unable to load CRM notes.");
        }
    }

    async function addNote() {
        const cleanContent = noteContent.trim();
        if (!cleanContent) {
            setNoteMessage("Please write a note first.");
            return;
        }
        try {
            setNoteSaving(true);
            setNoteMessage("");
            await api.post(`/leads/${leadId}/notes`, { content: cleanContent });
            setNoteContent("");
            await Promise.all([loadNotes(), loadActivities()]);
            setNoteMessage("CRM note added successfully.");
        } catch (err) {
            console.error("Failed to add CRM note:", err);
            setNoteMessage(err?.response?.data?.detail || "Unable to add CRM note.");
        } finally {
            setNoteSaving(false);
        }
    }

    function startEditingNote(note) {
        setEditingNoteId(note.id);
        setEditingNoteContent(note.content);
        setNoteMessage("");
    }

    function cancelEditingNote() {
        setEditingNoteId(null);
        setEditingNoteContent("");
    }

    async function saveEditedNote(note) {
        const content = editingNoteContent.trim();
        if (!content) return setNoteMessage("Note content cannot be empty.");
        try {
            setNoteActionId(note.id);
            await api.patch(`/leads/${leadId}/notes/${note.id}`, { content });
            cancelEditingNote();
            await Promise.all([loadNotes(), loadActivities()]);
            setNoteMessage("CRM note updated successfully.");
        } catch (err) {
            setNoteMessage(err?.response?.data?.detail || "Unable to update CRM note.");
        } finally {
            setNoteActionId(null);
        }
    }

    async function removeNote(note) {
        if (!canManageNote(note) || !window.confirm("Delete this CRM note permanently?")) return;
        try {
            setNoteActionId(note.id);
            await api.delete(`/leads/${leadId}/notes/${note.id}`);
            if (editingNoteId === note.id) cancelEditingNote();
            await Promise.all([loadNotes(), loadActivities()]);
            setNoteMessage("CRM note deleted successfully.");
        } catch (err) {
            setNoteMessage(err?.response?.data?.detail || "Unable to delete CRM note.");
        } finally {
            setNoteActionId(null);
        }
    }

    // =========================================================



    // LEAD ASSIGNMENT



    // Admin / Sales Manager only



    // =========================================================







    async function loadSalesExecutives() {



        try {



            const response = await api.get("/users/sales-executives");



            setSalesExecutives(Array.isArray(response.data) ? response.data : []);



        } catch (err) {



            console.error("Failed to load Sales Executives:", err);



            setAssignmentMessage(



                err?.response?.data?.detail || "Unable to load Sales Executives."



            );



        }



    }







    async function saveAssignment() {



        if (!canAssignLead) return;







        try {



            setAssignmentSaving(true);



            setAssignmentMessage("");







            const assignedToUserId = selectedExecutiveId



                ? Number(selectedExecutiveId)



                : null;







            await api.patch(`/leads/${leadId}/assign`, {



                assigned_to_user_id: assignedToUserId,



            });







            await Promise.all([loadLead(), loadActivities()]);







            setAssignmentMessage(



                assignedToUserId



                    ? "Lead assignment updated successfully."



                    : "Lead has been unassigned."



            );



        } catch (err) {



            console.error("Failed to update lead assignment:", err);



            setAssignmentMessage(



                err?.response?.data?.detail || "Unable to update lead assignment."



            );



        } finally {



            setAssignmentSaving(false);



        }



    }







    function getAssignedExecutiveName() {



        if (!lead?.assigned_to_user_id) return "Unassigned";







        const assignedUser = salesExecutives.find(



            (user) => user.id === lead.assigned_to_user_id



        );







        return assignedUser?.name || `Staff #${lead.assigned_to_user_id}`;



    }







    // =========================================================

    // DELETE LEAD

    // Admin / Sales Manager only

    // DELETE /api/leads/{lead_id}

    // =========================================================

    async function deleteLead() {

        if (!canDeleteLead || deletingLead) return;



        const confirmed = window.confirm(

            `Delete lead "${lead.name}" permanently? This action cannot be undone.`

        );

        if (!confirmed) return;



        try {

            setDeletingLead(true);

            setDeleteLeadError("");

            await api.delete(`/leads/${leadId}`);

            navigate("/leads", { replace: true });

        } catch (err) {

            console.error("Failed to delete lead:", err);

            setDeleteLeadError(

                err?.response?.data?.detail || "Unable to delete lead."

            );

        } finally {

            setDeletingLead(false);

        }

    }





    // =========================================================







    // FORMAT ACTIVITY TYPE







    // lead_created -> Lead Created







    // =========================================================







    function formatActivityType(type) {







        if (!type) {







            return "CRM Activity";







        }







        return type







            .replaceAll("\\\\\\\\\\_", " ")







            .replace(/\b\w/g, (letter) =>







                letter.toUpperCase()







            );







    }







    // =========================================================







    // FORMAT DATE







    // =========================================================







    function formatActivityDate(date) {







        if (!date) {







            return "";







        }







        return new Date(date).toLocaleString("en-PK", {







            day: "2-digit",







            month: "short",







            year: "numeric",







            hour: "2-digit",







            minute: "2-digit",







        });







    }







    // =========================================================







    // FORMAT MONEY







    // =========================================================







    function formatMoney(value) {







        if (value === null || value === undefined) {







            return "Not specified";







        }







        return `PKR ${Number(value).toLocaleString()}`;







    }







    // =========================================================







    async function saveFollowUp() {







        if (!followUpAt) {







            setFollowUpMessage("Please select a follow-up date and time.");







            return;







        }







        try {







            setFollowUpSaving(true);







            setFollowUpMessage("");







            await api.patch(`/leads/${leadId}`, {







                next_follow_up_at: new Date(followUpAt).toISOString(),







                follow_up_note: followUpNote.trim() || null,







                follow_up_completed_at: null,







            });







            await Promise.all([loadLead(), loadActivities()]);







            setFollowUpMessage("Follow-up scheduled successfully.");







        } catch (err) {







            console.error("Failed to schedule follow-up:", err);







            setFollowUpMessage(err?.response?.data?.detail || "Unable to schedule follow-up.");







        } finally {







            setFollowUpSaving(false);







        }







    }















    async function completeFollowUp() {







        try {







            setFollowUpSaving(true);







            setFollowUpMessage("");







            await api.patch(`/leads/${leadId}`, {







                follow_up_completed_at: new Date().toISOString(),







                follow_up_note: followUpNote.trim() || lead.follow_up_note || null,







            });







            await Promise.all([loadLead(), loadActivities()]);







            setFollowUpMessage("Follow-up marked as completed.");







        } catch (err) {







            console.error("Failed to complete follow-up:", err);







            setFollowUpMessage(err?.response?.data?.detail || "Unable to complete follow-up.");







        } finally {







            setFollowUpSaving(false);







        }







    }















    function getFollowUpState() {







        if (!lead?.next_follow_up_at) return "none";







        if (lead.follow_up_completed_at) return "completed";







        const followUp = new Date(lead.next_follow_up_at);







        const now = new Date();







        if (followUp < now) return "overdue";







        const sameDay =







            followUp.getFullYear() === now.getFullYear() &&







            followUp.getMonth() === now.getMonth() &&







            followUp.getDate() === now.getDate();







        return sameDay ? "today" : "upcoming";







    }















    // LOADING STATE







    // =========================================================







    if (loading) {







        return (







            <div className="detail-card">







                <p>Loading lead details...</p>







            </div>







        );







    }







    // =========================================================







    // ERROR STATE







    // =========================================================







    if (error) {







        return (







            <>







                <button







                    className="back-button"







                    type="button"







                    onClick={() => navigate("/leads")}







                >







                    <ArrowLeft size={17} />







                    Back to Leads







                </button>







                <div className="leads-error">







                    {error}







                </div>







            </>







        );







    }







    // =========================================================







    // LEAD NOT FOUND







    // =========================================================







    if (!lead) {







        return <p>Lead not found.</p>;







    }







    return (
        <div className="lead-details-page">







            {/* =====================================================







          BACK BUTTON







      ====================================================== */}







            <button







                className="back-button"







                type="button"







                onClick={() => navigate("/leads")}







            >







                <ArrowLeft size={17} />







                Back to Leads







            </button>







            {/* =====================================================







          LEAD HEADER







      ====================================================== */}







            <div className="lead-details-header">







                <div>







                    <p className="lead-number">







                        LEAD #{lead.id}







                    </p>







                    <h1>{lead.name}</h1>







                    <p>







                        Customer profile and sales information







                    </p>







                </div>







                <div

                    style={{

                        display: "flex",

                        alignItems: "center",

                        gap: "10px",

                        flexWrap: "wrap",

                        justifyContent: "flex-end",

                    }}

                >

                    <span className={`status-badge status-${lead.status}`}>

                        {lead.status}

                    </span>



                    {canDeleteLead && (

                        <button

                            type="button"

                            onClick={deleteLead}

                            disabled={deletingLead}

                            title="Delete lead"

                            style={{

                                display: "inline-flex",

                                alignItems: "center",

                                gap: "7px",

                                padding: "9px 12px",

                                border: "1px solid #dc2626",

                                borderRadius: "10px",

                                background: "transparent",

                                color: "#dc2626",

                                cursor: deletingLead ? "not-allowed" : "pointer",

                                opacity: deletingLead ? 0.65 : 1,

                                fontWeight: 600,

                            }}

                        >

                            <Trash2 size={16} />

                            {deletingLead ? "Deleting..." : "Delete Lead"}

                        </button>

                    )}

                </div>





            </div>



            {deleteLeadError && (

                <div className="leads-error" style={{ marginTop: "12px" }}>

                    {deleteLeadError}

                </div>

            )}



            {/* =====================================================







          CONTACT + SALES INFORMATION







      ====================================================== */}







            <div className="lead-info-grid">







                {/* CONTACT INFORMATION */}







                <div className="detail-card">







                    <h3>Contact Information</h3>







                    <div className="detail-item">







                        <Phone size={18} />







                        <div>







                            <span>Phone</span>







                            <strong>







                                {lead.phone || "Not provided"}







                            </strong>







                        </div>







                    </div>







                    <div className="detail-item">







                        <Mail size={18} />







                        <div>







                            <span>Email</span>







                            <strong>







                                {lead.email || "Not provided"}







                            </strong>







                        </div>







                    </div>







                    <div className="detail-item">







                        <MapPin size={18} />







                        <div>







                            <span>Location</span>







                            <strong>







                                {lead.city || "Not provided"}







                                {lead.province







                                    ? `, ${lead.province}`







                                    : ""}







                            </strong>







                        </div>







                    </div>







                </div>







                {/* SALES INFORMATION */}







                <div className="detail-card">







                    <h3>Sales Information</h3>







                    <div className="detail-item">







                        <Zap size={18} />







                        <div>







                            <span>Required System</span>







                            <strong>







                                {lead.system_size_kw







                                    ? `${lead.system_size_kw} kW`







                                    : lead.interested_system ||







                                    "Not specified"}







                            </strong>







                        </div>







                    </div>







                    <div className="detail-row">







                        <span>Budget</span>







                        <strong>







                            {formatMoney(lead.budget)}







                        </strong>







                    </div>







                    <div className="detail-row">







                        <span>Monthly Bill</span>







                        <strong>







                            {formatMoney(lead.monthly_bill)}







                        </strong>







                    </div>







                    <div className="detail-row">







                        <span>







                            Qualification Score







                        </span>







                        <strong>







                            {lead.qualification_score ??







                                "Not scored"}







                        </strong>







                    </div>







                    <div className="detail-row">







                        <span>







                            Qualification Level







                        </span>







                        <span







                            className={`qualification-badge ${lead.qualification_level ||







                                "unqualified"







                                }`}







                        >







                            {lead.qualification_level ||







                                "Not Scored"}







                        </span>







                    </div>







                </div>







            </div>







            {/* =====================================================



          LEAD ASSIGNMENT



          Admin / Sales Manager only



      ====================================================== */}



            {canAssignLead && (



                <div className="detail-card" style={{ marginTop: "22px" }}>



                    <div style={{ display: "flex", justifyContent: "space-between", gap: "16px", flexWrap: "wrap", alignItems: "center" }}>



                        <div>



                            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>



                                <UserRoundCheck size={19} />



                                <h3 style={{ margin: 0 }}>Lead Assignment</h3>



                            </div>



                            <p style={{ margin: "6px 0 0", opacity: 0.7 }}>



                                Assign this lead to an active Sales Executive.



                            </p>



                        </div>







                        <span className="status-badge status-contacted">



                            {getAssignedExecutiveName()}



                        </span>



                    </div>







                    <div style={{ display: "grid", gridTemplateColumns: "minmax(240px, 1fr) auto", gap: "10px", marginTop: "18px", alignItems: "end" }}>



                        <label style={{ display: "grid", gap: "7px" }}>



                            <span style={{ fontSize: "12px", opacity: 0.72 }}>



                                Sales Executive



                            </span>







                            <select



                                value={selectedExecutiveId}



                                onChange={(event) => setSelectedExecutiveId(event.target.value)}



                                disabled={assignmentSaving}



                                style={{ width: "100%", boxSizing: "border-box", padding: "11px 12px", border: "1px solid #d8dee8", borderRadius: "10px", background: "transparent" }}



                            >



                                <option value="">Unassigned</option>



                                {salesExecutives.map((executive) => (



                                    <option key={executive.id} value={executive.id}>



                                        {executive.name} — {executive.email}



                                    </option>



                                ))}



                            </select>



                        </label>







                        <button



                            type="button"



                            className="back-button"



                            onClick={saveAssignment}



                            disabled={assignmentSaving}



                            style={{ margin: 0 }}



                        >



                            <UserRoundCheck size={16} />



                            {assignmentSaving



                                ? "Saving..."



                                : lead.assigned_to_user_id



                                    ? "Update Assignment"



                                    : "Assign Lead"}



                        </button>



                    </div>







                    {assignmentMessage && (



                        <p style={{ margin: "12px 0 0", fontSize: "13px" }}>



                            {assignmentMessage}



                        </p>



                    )}



                </div>



            )}







            {/* =====================================================







          SALES FOLLOW-UP







      ====================================================== */}







            <div className="detail-card" style={{ marginTop: "22px" }}>







                <div style={{ display: "flex", justifyContent: "space-between", gap: "16px", flexWrap: "wrap" }}>







                    <div>







                        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>







                            <CalendarClock size={19} />







                            <h3 style={{ margin: 0 }}>Sales Follow-up</h3>







                        </div>







                        <p style={{ margin: "6px 0 0", opacity: 0.7 }}>







                            Schedule the next customer call or message.







                        </p>







                    </div>







                    {getFollowUpState() !== "none" && (







                        <span className={`status-badge ${getFollowUpState() === "overdue"







                            ? "status-lost"







                            : getFollowUpState() === "completed"







                                ? "status-won"







                                : "status-contacted"







                            }`}>







                            {getFollowUpState() === "overdue" && <AlertTriangle size={13} />}







                            {getFollowUpState()}







                        </span>







                    )}







                </div>















                <div style={{







                    display: "grid",







                    gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",







                    gap: "14px",







                    marginTop: "18px",







                }}>







                    <label style={{ display: "grid", gap: "7px" }}>







                        <span style={{ fontSize: "12px", opacity: 0.72 }}>Next follow-up</span>







                        <input







                            type="datetime-local"







                            value={followUpAt}







                            onChange={(event) => setFollowUpAt(event.target.value)}







                            style={{ width: "100%", boxSizing: "border-box", padding: "11px 12px", border: "1px solid #d8dee8", borderRadius: "10px", background: "transparent" }}







                        />







                    </label>







                    <label style={{ display: "grid", gap: "7px" }}>







                        <span style={{ fontSize: "12px", opacity: 0.72 }}>Follow-up note</span>







                        <input







                            type="text"







                            maxLength={500}







                            placeholder="e.g. Call about revised 5kW quotation"







                            value={followUpNote}







                            onChange={(event) => setFollowUpNote(event.target.value)}







                            style={{ width: "100%", boxSizing: "border-box", padding: "11px 12px", border: "1px solid #d8dee8", borderRadius: "10px", background: "transparent" }}







                        />







                    </label>







                </div>















                {lead.next_follow_up_at && (







                    <div style={{ marginTop: "13px", fontSize: "13px", opacity: 0.76 }}>







                        Current: {formatActivityDate(lead.next_follow_up_at)}







                        {lead.follow_up_note ? ` — ${lead.follow_up_note}` : ""}







                    </div>







                )}















                <div style={{ display: "flex", gap: "10px", flexWrap: "wrap", marginTop: "16px" }}>







                    <button type="button" className="back-button" onClick={saveFollowUp} disabled={followUpSaving} style={{ margin: 0 }}>







                        <CalendarClock size={16} />







                        {followUpSaving ? "Saving..." : "Schedule / Reschedule"}







                    </button>







                    {lead.next_follow_up_at && !lead.follow_up_completed_at && (







                        <button type="button" className="back-button" onClick={completeFollowUp} disabled={followUpSaving} style={{ margin: 0 }}>







                            <CheckCircle2 size={16} />







                            Mark Completed







                        </button>







                    )}







                </div>







                {followUpMessage && <p style={{ margin: "12px 0 0", fontSize: "13px" }}>{followUpMessage}</p>}







            </div>















            {/* =====================================================







          SALES INTELLIGENCE







      ====================================================== */}







            {intelligence && (







                <div className="intelligence-card">







                    {/* HEADER */}







                    <div className="intelligence-header">







                        <div>







                            <div className="intelligence-title">







                                <Brain size={20} />







                                <h3>Sales Intelligence</h3>







                            </div>







                            <p>







                                Customer qualification and AI sales context.







                            </p>







                        </div>







                        <span className="ai-badge">







                            AI CRM







                        </span>







                    </div>







                    {/* INTELLIGENCE CARDS */}







                    <div className="intelligence-grid">







                        {/* Qualification */}







                        <div className="intel-box">







                            <div className="intel-icon">







                                <Gauge size={19} />







                            </div>







                            <div>







                                <span>Qualification</span>







                                <strong>







                                    {intelligence.qualification_score ??







                                        "Not Scored"}







                                </strong>







                                <small>







                                    {intelligence.qualification_level







                                        ? intelligence.qualification_level.toUpperCase()







                                        : "Not qualified yet"}







                                </small>







                            </div>







                        </div>







                        {/* Budget */}







                        <div className="intel-box">







                            <div className="intel-icon">







                                <Wallet size={19} />







                            </div>







                            <div>







                                <span>Customer Budget</span>







                                <strong>







                                    {formatMoney(







                                        intelligence.budget







                                    )}







                                </strong>







                                <small>







                                    Available investment







                                </small>







                            </div>







                        </div>







                        {/* Interested System */}







                        <div className="intel-box">







                            <div className="intel-icon">







                                <Zap size={19} />







                            </div>







                            <div>







                                <span>Interested System</span>







                                <strong>







                                    {intelligence.interested_system ||







                                        "Not specified"}







                                </strong>







                                <small>







                                    Solar requirement







                                </small>







                            </div>







                        </div>







                        {/* Lead Source */}







                        <div className="intel-box">







                            <div className="intel-icon">







                                <Globe size={19} />







                            </div>







                            <div>







                                <span>Lead Source</span>







                                <strong>







                                    {intelligence.source ||







                                        "Unknown"}







                                </strong>







                                <small>







                                    Customer acquisition source







                                </small>







                            </div>







                        </div>







                    </div>







                    {/* =================================================







              AI CHAT SESSIONS







          ================================================== */}







                    <div className="chat-intelligence">







                        <div className="chat-intelligence-header">







                            <MessageSquare size={18} />







                            <div>







                                <strong>







                                    AI Chat Sessions







                                </strong>







                                <span>







                                    Conversation history linked with this lead







                                </span>







                            </div>







                        </div>







                        {intelligence.chat_sessions?.length > 0 ? (







                            <div className="chat-session-list">







                                {intelligence.chat_sessions.map(







                                    (session, index) => (







                                        <div







                                            className="chat-session-item"







                                            // IMPORTANT:







                                            // Backend field is session_id,







                                            // not session.id







                                            key={







                                                session.session_id ??







                                                `session-${index}`







                                            }







                                        >







                                            <div>







                                                <strong>







                                                    Session #







                                                    {session.session_id ??







                                                        index + 1}







                                                </strong>







                                                <span>







                                                    AI sales conversation







                                                </span>







                                            </div>







                                            <span className="session-badge">







                                                Connected







                                            </span>







                                        </div>







                                    )







                                )}







                            </div>







                        ) : (







                            <div className="no-chat-session">







                                <MessageSquare size={20} />







                                <div>







                                    <strong>







                                        No AI chat sessions yet







                                    </strong>







                                    <p>







                                        This lead has not been linked







                                        with an AI sales conversation.







                                    </p>







                                </div>







                            </div>







                        )}







                    </div>







                </div>







            )}















            {/* =====================================================
                CRM NOTES
            ====================================================== */}
            <div className="activity-card crm-notes-card" style={{ marginBottom: "20px" }}>
                <div className="activity-header">
                    <div>
                        <div className="activity-title">
                            <MessageSquare size={19} />
                            <h3>CRM Notes</h3>
                        </div>
                        <p>Internal sales notes and customer context for this lead.</p>
                    </div>
                    <span className="activity-count">
                        {notes.length} {notes.length === 1 ? "Note" : "Notes"}
                    </span>
                </div>

                <div style={{ display: "grid", gap: "10px", marginBottom: "18px" }}>
                    <textarea
                        className="crm-control"
                        rows="3"
                        maxLength={5000}
                        placeholder="Add an internal CRM note, e.g. customer prefers installation next week..."
                        value={noteContent}
                        onChange={(event) => setNoteContent(event.target.value)}
                        disabled={noteSaving}
                        style={{ width: "100%", boxSizing: "border-box", resize: "vertical" }}
                    />
                    <div style={{ display: "flex", justifyContent: "space-between", gap: "10px", alignItems: "center", flexWrap: "wrap" }}>
                        <small style={{ opacity: 0.68 }}>{noteContent.length}/5000 characters</small>
                        <button className="crm-btn crm-btn-primary" type="button" onClick={addNote} disabled={noteSaving || !noteContent.trim()}>
                            <Plus size={15} /> {noteSaving ? "Adding..." : "Add Note"}
                        </button>
                    </div>
                    {noteMessage && <small>{noteMessage}</small>}
                </div>

                {notes.length === 0 ? (
                    <div className="empty-activity">No CRM notes for this lead yet.</div>
                ) : (
                    <div style={{ display: "grid", gap: "10px" }}>
                        {notes.map((note) => (
                            <div key={note.id} style={{ border: "1px solid rgba(15, 23, 42, 0.09)", borderRadius: "12px", padding: "13px 14px" }}>
                                <div style={{ display: "flex", justifyContent: "space-between", gap: "12px", alignItems: "center", flexWrap: "wrap", marginBottom: "7px" }}>
                                    <strong style={{ fontSize: "13px" }}>
                                        {note.author_name || `Staff #${note.author_user_id}`}
                                    </strong>
                                    <span style={{ fontSize: "11px", opacity: 0.65 }}>
                                        {formatActivityDate(note.created_at)}
                                    </span>
                                </div>
                                {editingNoteId === note.id ? (
                                    <div style={{ display: "grid", gap: "9px" }}>
                                        <textarea
                                            className="crm-control"
                                            rows="3"
                                            maxLength={5000}
                                            value={editingNoteContent}
                                            onChange={(event) => setEditingNoteContent(event.target.value)}
                                            disabled={noteActionId === note.id}
                                        />
                                        <div style={{ display: "flex", gap: "8px", justifyContent: "flex-end" }}>
                                            <button className="crm-btn crm-btn-secondary" type="button" onClick={cancelEditingNote}>Cancel</button>
                                            <button className="crm-btn crm-btn-primary" type="button" onClick={() => saveEditedNote(note)} disabled={noteActionId === note.id || !editingNoteContent.trim()}>
                                                {noteActionId === note.id ? "Saving..." : "Save Changes"}
                                            </button>
                                        </div>
                                    </div>
                                ) : (
                                    <>
                                        <p style={{ margin: 0, whiteSpace: "pre-wrap", overflowWrap: "anywhere", lineHeight: 1.55 }}>
                                            {note.content}
                                        </p>
                                        {canManageNote(note) && (
                                            <div style={{ display: "flex", gap: "8px", justifyContent: "flex-end", marginTop: "10px" }}>
                                                <button className="crm-btn crm-btn-secondary" type="button" onClick={() => startEditingNote(note)}>Edit</button>
                                                <button className="crm-btn crm-btn-danger" type="button" onClick={() => removeNote(note)} disabled={noteActionId === note.id}>
                                                    <Trash2 size={14} /> {noteActionId === note.id ? "Deleting..." : "Delete"}
                                                </button>
                                            </div>
                                        )}
                                    </>
                                )}
                            </div>
                        ))}
                    </div>
                )}
            </div>

            {/* =====================================================







                SALES TASK MANAGEMENT







            ====================================================== */}







            <div className="activity-card crm-notes-card" style={{ marginBottom: "20px" }}>







                <div className="activity-header">







                    <div>







                        <div className="activity-title">







                            <ListTodo size={19} />







                            <h3>Sales Tasks</h3>







                        </div>







                        <p>Track calls, quotations, site surveys and other sales actions.</p>







                    </div>







                    <span className="activity-count">







                        {tasks.filter((task) => task.status === "pending").length} Open







                    </span>







                </div>















                <div style={{ display: "grid", gap: "10px", marginBottom: "16px" }}>







                    <input
                        className="crm-control"
                        type="text"
                        placeholder="Task title e.g. Call customer"







                        value={taskTitle}







                        onChange={(event) => setTaskTitle(event.target.value)}







                    />







                    <textarea
                        className="crm-control"
                        rows="2"
                        placeholder="Optional task details..."







                        value={taskDescription}







                        onChange={(event) => setTaskDescription(event.target.value)}







                    />







                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr auto", gap: "10px" }}>







                        <select className="crm-control" value={taskPriority} onChange={(event) => setTaskPriority(event.target.value)}>







                            <option value="low">Low Priority</option>







                            <option value="medium">Medium Priority</option>







                            <option value="high">High Priority</option>







                        </select>







                        <input
                            className="crm-control"
                            type="datetime-local"
                            value={taskDueAt}







                            onChange={(event) => setTaskDueAt(event.target.value)}







                        />







                        <button className="crm-btn crm-btn-primary" type="button" onClick={addTask} disabled={taskSaving}>







                            <Plus size={15} /> {taskSaving ? "Adding..." : "Add Task"}







                        </button>







                    </div>







                    {taskMessage && <small>{taskMessage}</small>}







                </div>















                {tasks.length === 0 ? (







                    <div className="empty-activity">No sales tasks for this lead.</div>







                ) : (







                    <div style={{ display: "grid", gap: "9px" }}>







                        {tasks.map((task) => {







                            const overdue =







                                task.status === "pending" &&







                                task.due_at &&







                                new Date(task.due_at) < new Date();







                            return (







                                <div







                                    key={task.id}







                                    style={{







                                        border: "1px solid rgba(15, 23, 42, 0.09)",







                                        borderRadius: "12px",







                                        padding: "12px",







                                        display: "flex",







                                        justifyContent: "space-between",







                                        gap: "12px",







                                        alignItems: "center",







                                        opacity: task.status === "completed" ? 0.62 : 1,







                                    }}







                                >







                                    <div>







                                        <strong style={{ textDecoration: task.status === "completed" ? "line-through" : "none" }}>







                                            {task.title}







                                        </strong>







                                        <div style={{ fontSize: "11px", opacity: 0.68, marginTop: "4px" }}>







                                            {task.priority.toUpperCase()}







                                            {task.due_at ? ` • ${formatActivityDate(task.due_at)}` : ""}







                                            {overdue ? " • OVERDUE" : ""}







                                        </div>







                                        {task.description && (







                                            <div style={{ fontSize: "12px", marginTop: "5px", opacity: 0.75 }}>







                                                {task.description}







                                            </div>







                                        )}







                                    </div>







                                    <div style={{ display: "flex", gap: "7px" }}>







                                        <button className="crm-btn crm-btn-secondary" type="button" onClick={() => toggleTask(task)}>







                                            <CheckCircle2 size={15} />







                                            {task.status === "completed" ? "Reopen" : "Complete"}







                                        </button>







                                        <button className="crm-btn crm-btn-icon-danger" type="button" onClick={() => removeTask(task)} title="Delete task">







                                            <Trash2 size={15} />







                                        </button>







                                    </div>







                                </div>







                            );







                        })}







                    </div>







                )}







            </div>















            {/* =====================================================







          ACTIVITY TIMELINE







      ====================================================== */}







            <div className="activity-card">







                <div className="activity-header">







                    <div>







                        <div className="activity-title">







                            <History size={19} />







                            <h3>Activity Timeline</h3>







                        </div>







                        <p>







                            Complete CRM history for this customer.







                        </p>







                    </div>







                    <span className="activity-count">







                        {activities.length}{" "}







                        {activities.length === 1







                            ? "Activity"







                            : "Activities"}







                    </span>







                </div>







                {activities.length === 0 ? (







                    <div className="empty-activity">







                        No activity recorded for this lead yet.







                    </div>







                ) : (







                    <div className="activity-timeline">







                        {activities.map((activity) => (







                            <div







                                className="activity-item"







                                key={activity.id}







                            >







                                <div className="timeline-marker">







                                    <div className="timeline-dot" />







                                </div>







                                <div className="activity-content">







                                    <div className="activity-content-header">







                                        <strong>







                                            {formatActivityType(







                                                activity.activity_type







                                            )}







                                        </strong>







                                        {activity.created_at && (







                                            <span>







                                                {formatActivityDate(







                                                    activity.created_at







                                                )}







                                            </span>







                                        )}







                                    </div>







                                    <p>







                                        {activity.description ||







                                            "CRM activity recorded."}







                                    </p>







                                </div>







                            </div>







                        ))}







                    </div>







                )}







            </div>







        </div>







    );







}







export default LeadDetails;
