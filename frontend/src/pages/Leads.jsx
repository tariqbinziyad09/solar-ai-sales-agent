import { useEffect, useMemo, useState } from "react";

import {

    AlertTriangle,

    CalendarClock,

    Columns3,

    List,

    Mail,

    MapPin,

    Phone,

    Search,

    SlidersHorizontal,

    Users,

    Wallet,

    X,

} from "lucide-react";

import { useNavigate } from "react-router-dom";

import api from "../services/api";



const PIPELINE = [

    { key: "new", label: "New" },

    { key: "contacted", label: "Contacted" },

    { key: "qualified", label: "Qualified" },

    { key: "proposal", label: "Proposal" },

    { key: "won", label: "Won" },

    { key: "lost", label: "Lost" },

];



const ALLOWED_TRANSITIONS = {

    new: ["contacted", "lost"],

    contacted: ["qualified", "lost"],

    qualified: ["proposal", "lost"],

    proposal: ["won", "lost"],

    won: [],

    lost: [],

};



function Leads() {

    const navigate = useNavigate();

    const [leads, setLeads] = useState([]);

    const [loading, setLoading] = useState(true);

    const [error, setError] = useState("");

    const [view, setView] = useState("kanban");



    // CRM filters

    const [search, setSearch] = useState("");

    const [status, setStatus] = useState("");

    const [level, setLevel] = useState("");

    const [city, setCity] = useState("");



    // Pipeline interaction state

    const [draggedLeadId, setDraggedLeadId] = useState(null);

    const [dragOverStage, setDragOverStage] = useState("");

    const [movingLeadId, setMovingLeadId] = useState(null);

    const [pipelineMessage, setPipelineMessage] = useState("");



    useEffect(() => {

        const timer = setTimeout(() => {

            loadLeads();

        }, 350);



        return () => clearTimeout(timer);

    }, [search, status, level, city]);



    async function loadLeads() {

        try {

            setLoading(true);

            setError("");



            const params = {};

            if (search.trim()) params.search = search.trim();

            if (status) params.status = status;

            if (level) params.qualification_level = level;

            if (city.trim()) params.city = city.trim();



            const response = await api.get("/leads", { params });

            setLeads(Array.isArray(response.data) ? response.data : []);

        } catch (err) {

            console.error("Failed to load leads:", err);

            setError("Unable to load leads.");

        } finally {

            setLoading(false);

        }

    }



    function clearFilters() {

        setSearch("");

        setStatus("");

        setLevel("");

        setCity("");

    }



    const hasFilters = search.trim() || status || level || city.trim();



    const groupedLeads = useMemo(() => {

        return PIPELINE.reduce((groups, stage) => {

            groups[stage.key] = leads.filter((lead) => lead.status === stage.key);

            return groups;

        }, {});

    }, [leads]);



    function formatMoney(value) {

        if (value === null || value === undefined) return "Budget not set";

        return `PKR ${Number(value).toLocaleString()}`;

    }



    function formatDateTime(value) {

        if (!value) return null;

        const date = new Date(value);

        if (Number.isNaN(date.getTime())) return null;

        return date.toLocaleString("en-PK", {

            day: "2-digit",

            month: "short",

            hour: "2-digit",

            minute: "2-digit",

        });

    }



    function followUpState(lead) {

        if (!lead.next_follow_up_at || lead.follow_up_completed_at) return null;

        const followUp = new Date(lead.next_follow_up_at);

        if (Number.isNaN(followUp.getTime())) return null;

        return followUp < new Date() ? "overdue" : "scheduled";

    }



    function canMove(fromStatus, toStatus) {

        if (fromStatus === toStatus) return true;

        return (ALLOWED_TRANSITIONS[fromStatus] || []).includes(toStatus);

    }



    async function moveLead(lead, targetStatus) {

        if (!lead || lead.status === targetStatus) return;



        if (!canMove(lead.status, targetStatus)) {

            setPipelineMessage(

                `Lead cannot move directly from ${lead.status} to ${targetStatus}.`

            );

            return;

        }



        const oldStatus = lead.status;



        // Optimistic UI makes the board feel immediate.

        setLeads((current) =>

            current.map((item) =>

                item.id === lead.id ? { ...item, status: targetStatus } : item

            )

        );

        setMovingLeadId(lead.id);

        setPipelineMessage("");



        try {

            const response = await api.patch(`/leads/${lead.id}`, {

                status: targetStatus,

            });



            setLeads((current) =>

                current.map((item) =>

                    item.id === lead.id ? response.data : item

                )

            );

            setPipelineMessage(

                `${lead.name || `Lead #${lead.id}`} moved to ${targetStatus}.`

            );

        } catch (err) {

            // Restore the card if backend rejects the transition.

            setLeads((current) =>

                current.map((item) =>

                    item.id === lead.id ? { ...item, status: oldStatus } : item

                )

            );



            setPipelineMessage(

                err?.response?.data?.detail ||

                "Unable to update the lead pipeline stage."

            );

        } finally {

            setMovingLeadId(null);

        }

    }



    function handleDragStart(event, lead) {

        setDraggedLeadId(lead.id);

        event.dataTransfer.effectAllowed = "move";

        event.dataTransfer.setData("text/plain", String(lead.id));

    }



    function handleDragEnd() {

        setDraggedLeadId(null);

        setDragOverStage("");

    }



    function handleDragOver(event, stage) {

        event.preventDefault();

        event.dataTransfer.dropEffect = "move";

        setDragOverStage(stage);

    }



    function handleDrop(event, targetStatus) {

        event.preventDefault();

        const id = Number(

            event.dataTransfer.getData("text/plain") || draggedLeadId

        );

        const lead = leads.find((item) => item.id === id);

        setDragOverStage("");

        setDraggedLeadId(null);

        if (lead) moveLead(lead, targetStatus);

    }



    function PipelineCard({ lead }) {

        const followUp = followUpState(lead);

        const followUpTime = formatDateTime(lead.next_follow_up_at);



        return (

            <article
                className="pipeline-card"

                draggable={movingLeadId !== lead.id}

                onDragStart={(event) => handleDragStart(event, lead)}

                onDragEnd={handleDragEnd}

                onClick={() => navigate(`/leads/${lead.id}`)}

                style={{

                    background: "var(--card-bg, #fff)",

                    border: "1px solid rgba(15, 23, 42, 0.09)",

                    borderRadius: "14px",

                    padding: "14px",

                    cursor: movingLeadId === lead.id ? "wait" : "grab",

                    boxShadow: "0 4px 14px rgba(15, 23, 42, 0.05)",

                    opacity: draggedLeadId === lead.id ? 0.5 : 1,

                }}

            >

                <div

                    style={{

                        display: "flex",

                        justifyContent: "space-between",

                        gap: "10px",

                        alignItems: "flex-start",

                    }}

                >

                    <div style={{ minWidth: 0 }}>

                        <strong style={{ display: "block" }}>

                            {lead.name || `Lead #${lead.id}`}

                        </strong>

                        <span style={{ fontSize: "11px", opacity: 0.58 }}>

                            Lead #{lead.id}

                        </span>

                    </div>



                    <span

                        className={`qualification-badge ${lead.qualification_level || "unqualified"

                            }`}

                        style={{ flexShrink: 0 }}

                    >

                        {lead.qualification_level || "Not Scored"}

                    </span>

                </div>



                <div

                    style={{

                        display: "grid",

                        gap: "7px",

                        marginTop: "12px",

                        fontSize: "12px",

                        opacity: 0.76,

                    }}

                >

                    {lead.phone && (

                        <span style={{ display: "flex", gap: "6px", alignItems: "center" }}>

                            <Phone size={13} /> {lead.phone}

                        </span>

                    )}

                    {lead.city && (

                        <span style={{ display: "flex", gap: "6px", alignItems: "center" }}>

                            <MapPin size={13} /> {lead.city}

                        </span>

                    )}

                    <span style={{ display: "flex", gap: "6px", alignItems: "center" }}>

                        <Wallet size={13} /> {formatMoney(lead.budget)}

                    </span>

                </div>



                <div

                    style={{

                        display: "flex",

                        justifyContent: "space-between",

                        gap: "8px",

                        alignItems: "center",

                        marginTop: "12px",

                        paddingTop: "10px",

                        borderTop: "1px solid rgba(15, 23, 42, 0.07)",

                    }}

                >

                    <span style={{ fontSize: "12px", fontWeight: 700 }}>

                        Score {lead.qualification_score ?? "—"}

                    </span>



                    {followUp && followUpTime && (

                        <span

                            title={lead.follow_up_note || "Sales follow-up"}

                            style={{

                                display: "flex",

                                alignItems: "center",

                                gap: "4px",

                                fontSize: "11px",

                                fontWeight: 700,

                            }}

                        >

                            {followUp === "overdue" ? (

                                <AlertTriangle size={13} />

                            ) : (

                                <CalendarClock size={13} />

                            )}

                            {followUpTime}

                        </span>

                    )}

                </div>



                {(ALLOWED_TRANSITIONS[lead.status] || []).length > 0 && (

                    <div

                        onClick={(event) => event.stopPropagation()}

                        style={{ marginTop: "10px" }}

                    >

                        <select

                            value=""

                            disabled={movingLeadId === lead.id}

                            onChange={(event) => {

                                if (event.target.value) {

                                    moveLead(lead, event.target.value);

                                }

                            }}

                            style={{

                                width: "100%",

                                minHeight: "34px",

                                borderRadius: "9px",

                                border: "1px solid rgba(15, 23, 42, 0.12)",

                                background: "transparent",

                                padding: "0 8px",

                            }}

                        >

                            <option value="">Move lead...</option>

                            {(ALLOWED_TRANSITIONS[lead.status] || []).map((next) => (

                                <option key={next} value={next}>

                                    {next.charAt(0).toUpperCase() + next.slice(1)}

                                </option>

                            ))}

                        </select>

                    </div>

                )}

            </article>

        );

    }



    return (

        <div className="leads-page">

            <div className="page-heading">

                <div>

                    <p className="page-eyebrow">CRM PIPELINE</p>

                    <h1>Leads</h1>

                    <p>

                        Manage customer leads and move opportunities through your

                        solar sales pipeline.

                    </p>

                </div>



                <div

                    style={{

                        display: "flex",

                        gap: "10px",

                        alignItems: "center",

                        flexWrap: "wrap",

                    }}

                >

                    <div className="records-count">

                        <Users size={18} />

                        <span>{leads.length} Leads</span>

                    </div>



                    <div

                        style={{

                            display: "flex",

                            padding: "4px",

                            border: "1px solid rgba(15, 23, 42, 0.1)",

                            borderRadius: "10px",

                        }}

                    >

                        <button

                            type="button"

                            onClick={() => setView("kanban")}

                            aria-label="Kanban view"

                            style={{

                                border: 0,

                                borderRadius: "7px",

                                padding: "7px 10px",

                                cursor: "pointer",

                                fontWeight: 700,

                                opacity: view === "kanban" ? 1 : 0.55,

                            }}

                        >

                            <Columns3 size={16} />

                        </button>

                        <button

                            type="button"

                            onClick={() => setView("list")}

                            aria-label="List view"

                            style={{

                                border: 0,

                                borderRadius: "7px",

                                padding: "7px 10px",

                                cursor: "pointer",

                                fontWeight: 700,

                                opacity: view === "list" ? 1 : 0.55,

                            }}

                        >

                            <List size={16} />

                        </button>

                    </div>

                </div>

            </div>



            <div className="lead-filters">

                <div className="filter-title">

                    <SlidersHorizontal size={17} />

                    <span>Filters</span>

                </div>



                <div className="search-field">

                    <Search size={17} />

                    <input

                        type="text"

                        placeholder="Search name, phone or email..."

                        value={search}

                        onChange={(event) => setSearch(event.target.value)}

                    />

                </div>



                <select value={status} onChange={(event) => setStatus(event.target.value)}>

                    <option value="">All Statuses</option>

                    {PIPELINE.map((stage) => (

                        <option key={stage.key} value={stage.key}>

                            {stage.label}

                        </option>

                    ))}

                </select>



                <select value={level} onChange={(event) => setLevel(event.target.value)}>

                    <option value="">All Levels</option>

                    <option value="hot">Hot</option>

                    <option value="warm">Warm</option>

                    <option value="cold">Cold</option>

                </select>



                <input

                    className="city-filter"

                    type="text"

                    placeholder="City..."

                    value={city}

                    onChange={(event) => setCity(event.target.value)}

                />



                {hasFilters && (

                    <button className="clear-filter-btn" type="button" onClick={clearFilters}>

                        <X size={15} />

                        Clear

                    </button>

                )}

            </div>



            {error && <div className="leads-error">{error}</div>}



            {pipelineMessage && (

                <div

                    style={{

                        marginBottom: "14px",

                        padding: "10px 13px",

                        borderRadius: "10px",

                        border: "1px solid rgba(15, 23, 42, 0.1)",

                        fontSize: "13px",

                    }}

                >

                    {pipelineMessage}

                </div>

            )}



            {view === "kanban" ? (

                <div

                    style={{

                        display: "grid",

                        gridTemplateColumns: "repeat(6, minmax(260px, 1fr))",

                        gap: "14px",

                        overflowX: "auto",

                        paddingBottom: "14px",

                        alignItems: "start",

                    }}

                >

                    {PIPELINE.map((stage) => {

                        const stageLeads = groupedLeads[stage.key] || [];

                        return (

                            <section

                                key={stage.key}

                                onDragOver={(event) => handleDragOver(event, stage.key)}

                                onDragLeave={() => setDragOverStage("")}

                                onDrop={(event) => handleDrop(event, stage.key)}

                                style={{

                                    minWidth: "260px",

                                    minHeight: "420px",

                                    padding: "12px",

                                    borderRadius: "16px",

                                    border:

                                        dragOverStage === stage.key

                                            ? "2px dashed currentColor"

                                            : "1px solid rgba(15, 23, 42, 0.08)",

                                    background: "rgba(15, 23, 42, 0.025)",

                                }}

                            >

                                <header

                                    style={{

                                        display: "flex",

                                        justifyContent: "space-between",

                                        alignItems: "center",

                                        marginBottom: "12px",

                                    }}

                                >

                                    <strong>{stage.label}</strong>

                                    <span

                                        style={{

                                            minWidth: "26px",

                                            height: "26px",

                                            borderRadius: "999px",

                                            display: "grid",

                                            placeItems: "center",

                                            fontSize: "12px",

                                            fontWeight: 800,

                                            background: "rgba(15, 23, 42, 0.08)",

                                        }}

                                    >

                                        {stageLeads.length}

                                    </span>

                                </header>



                                <div className="kanban-card-list" style={{ display: "grid", gap: "10px" }}>

                                    {loading ? (

                                        <p style={{ opacity: 0.6, fontSize: "13px" }}>

                                            Loading...

                                        </p>

                                    ) : stageLeads.length === 0 ? (

                                        <p style={{ opacity: 0.5, fontSize: "12px" }}>

                                            Drop a valid lead here

                                        </p>

                                    ) : (

                                        stageLeads.map((lead) => (

                                            <PipelineCard key={lead.id} lead={lead} />

                                        ))

                                    )}

                                </div>

                            </section>

                        );

                    })}

                </div>

            ) : (

                <div className="table-card">

                    <div className="table-responsive">

                        <table className="crm-table">

                            <thead>

                                <tr>

                                    <th>Customer</th>

                                    <th>Contact</th>

                                    <th>City</th>

                                    <th>System</th>

                                    <th>Score</th>

                                    <th>Level</th>

                                    <th>Status</th>

                                </tr>

                            </thead>

                            <tbody>

                                {!loading &&

                                    leads.map((lead) => (

                                        <tr

                                            key={lead.id}

                                            className="clickable-row"

                                            onClick={() => navigate(`/leads/${lead.id}`)}

                                        >

                                            <td>

                                                <div className="customer-cell">

                                                    <div className="customer-avatar">

                                                        {lead.name?.charAt(0).toUpperCase() || "?"}

                                                    </div>

                                                    <div>

                                                        <strong>{lead.name}</strong>

                                                        <span>Lead #{lead.id}</span>

                                                    </div>

                                                </div>

                                            </td>

                                            <td>

                                                <div className="contact-cell">

                                                    <span>

                                                        <Phone size={14} />

                                                        {lead.phone || "-"}

                                                    </span>

                                                    {lead.email && (

                                                        <span>

                                                            <Mail size={14} />

                                                            {lead.email}

                                                        </span>

                                                    )}

                                                </div>

                                            </td>

                                            <td>{lead.city || "-"}</td>

                                            <td>{lead.interested_system || "-"}</td>

                                            <td><strong>{lead.qualification_score ?? "-"}</strong></td>

                                            <td>

                                                <span

                                                    className={`qualification-badge ${lead.qualification_level || "unqualified"

                                                        }`}

                                                >

                                                    {lead.qualification_level || "Not Scored"}

                                                </span>

                                            </td>

                                            <td>

                                                <span className={`status-badge status-${lead.status}`}>

                                                    {lead.status}

                                                </span>

                                            </td>

                                        </tr>

                                    ))}



                                {loading && (

                                    <tr>

                                        <td colSpan="7" className="empty-table">

                                            Loading leads...

                                        </td>

                                    </tr>

                                )}



                                {!loading && leads.length === 0 && (

                                    <tr>

                                        <td colSpan="7" className="empty-table">

                                            No leads match these filters.

                                        </td>

                                    </tr>

                                )}

                            </tbody>

                        </table>

                    </div>

                </div>

            )}

        </div>

    );

}



export default Leads;
