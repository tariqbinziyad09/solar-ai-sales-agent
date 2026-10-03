import { useEffect, useState } from "react";

import {

    BadgeCheck,

    CircleCheckBig,

    CircleDollarSign,

    FileText,

    Flame,

    Snowflake,

    Target,

    TrendingUp,

    Users,

    Waves,

    ArrowRight,

    Clock3,

    Activity,

    CalendarClock,

    AlertTriangle,

    Bell,

    BellRing,

    ChevronDown,

    ListTodo,

} from "lucide-react";

import api from "../services/api";

function Dashboard() {

    const [summary, setSummary] = useState(null);

    const [error, setError] = useState("");

    const [loading, setLoading] = useState(true);

    const [recentLeads, setRecentLeads] = useState([]);

    const [recentProposals, setRecentProposals] = useState([]);

    const [recentActivities, setRecentActivities] = useState([]);

    const [allLeads, setAllLeads] = useState([]);

    const [showReminders, setShowReminders] = useState(false);

    const [openTasks, setOpenTasks] = useState([]);

    useEffect(() => {

        async function loadDashboard() {

            try {

                // Load summary plus operational CRM records in parallel.

                // Both list endpoints already return newest records first.

                const [

                    summaryResponse,

                    leadsResponse,

                    proposalsResponse,

                    activitiesResponse,

                    tasksResponse,

                ] = await Promise.all([

                    api.get("/leads/summary"),

                    api.get("/leads"),

                    api.get("/proposals"),

                    api.get("/leads/recent-activities?limit=8"),

                    api.get("/leads/tasks/open?limit=100"),

                ]);

                setSummary(summaryResponse.data);

                setAllLeads(Array.isArray(leadsResponse.data) ? leadsResponse.data : []);

                setRecentLeads(

                    Array.isArray(leadsResponse.data)

                        ? leadsResponse.data.slice(0, 5)

                        : []

                );

                setRecentProposals(

                    Array.isArray(proposalsResponse.data)

                        ? proposalsResponse.data.slice(0, 5)

                        : []

                );

                // Reuse the existing per-lead CRM timeline endpoint.

                // We only inspect the five newest leads to keep the dashboard

                // lightweight and avoid adding a duplicate activity system.

                setRecentActivities(

                    Array.isArray(activitiesResponse.data)

                        ? activitiesResponse.data

                        : []

                );

                setOpenTasks(

                    Array.isArray(tasksResponse.data) ? tasksResponse.data : []

                );

            } catch (err) {

                console.error("Dashboard Error:", err);

                setError("Unable to load CRM dashboard.");

            } finally {

                setLoading(false);

            }

        }

        loadDashboard();

    }, []);

    function formatMoney(value) {

        return `PKR ${Number(value ?? 0).toLocaleString()}`;

    }

    function formatDate(value) {

        if (!value) return "—";

        const date = new Date(value);

        if (Number.isNaN(date.getTime())) return "—";

        return date.toLocaleDateString(undefined, {

            day: "2-digit",

            month: "short",

            year: "numeric",

        });

    }

    function formatDateTime(value) {

        if (!value) return "—";

        const date = new Date(value);

        if (Number.isNaN(date.getTime())) return "—";

        return date.toLocaleString(undefined, {

            day: "2-digit",

            month: "short",

            hour: "2-digit",

            minute: "2-digit",

        });

    }

    function titleCase(value) {

        if (!value) return "—";

        return String(value)

            .replaceAll("_", " ")

            .replace(/\b\w/g, (character) => character.toUpperCase());

    }

    function openLead(id) {

        if (id) window.location.href = `/leads/${id}`;

    }

    function openProposal(id) {

        if (id) window.location.href = `/proposals/${id}`;

    }

    function getOpenFollowUps() {

        return allLeads.filter((lead) => lead.next_follow_up_at && !lead.follow_up_completed_at);

    }

    function getTodayFollowUps() {

        const now = new Date();

        return getOpenFollowUps().filter((lead) => {

            const date = new Date(lead.next_follow_up_at);

            return date.getFullYear() === now.getFullYear()

                && date.getMonth() === now.getMonth()

                && date.getDate() === now.getDate();

        });

    }

    function getOverdueFollowUps() {

        const now = new Date();

        return getOpenFollowUps().filter((lead) => new Date(lead.next_follow_up_at) < now);

    }

    function getUpcomingFollowUps() {

        const now = new Date();

        return getOpenFollowUps()

            .filter((lead) => new Date(lead.next_follow_up_at) >= now)

            .sort((a, b) => new Date(a.next_follow_up_at) - new Date(b.next_follow_up_at))

            .slice(0, 5);

    }

    function getReminderFollowUps() {

        const now = new Date();

        const endOfToday = new Date();

        endOfToday.setHours(23, 59, 59, 999);

        return getOpenFollowUps()

            .filter((lead) => new Date(lead.next_follow_up_at) <= endOfToday)

            .sort(

                (a, b) =>

                    new Date(a.next_follow_up_at) -

                    new Date(b.next_follow_up_at)

            );

    }

    function getReminderType(lead) {

        const followUp = new Date(lead.next_follow_up_at);

        const now = new Date();

        return followUp < now ? "Overdue" : "Today";

    }

    function percentage(value, total) {

        if (!total || total <= 0) return 0;

        return Math.min(100, Math.round((Number(value ?? 0) / total) * 100));

    }

    if (loading) {

        return <p>Loading dashboard...</p>;

    }

    if (error) {

        return <p>{error}</p>;

    }

    const cards = [

        { title: "Total Leads", value: summary.total_leads, icon: Users },

        { title: "Hot Leads", value: summary.hot_leads, icon: Flame },

        { title: "Qualified", value: summary.qualified_leads, icon: TrendingUp },

        { title: "Won Deals", value: summary.won_leads, icon: CircleCheckBig },

        { title: "Total Proposals", value: summary.total_proposals, icon: FileText },

        {

            title: "Quotation Value",

            value: formatMoney(summary.total_proposal_value),

            icon: CircleDollarSign,

        },

        {

            title: "Accepted Sales",

            value: formatMoney(summary.accepted_sales_value),

            icon: BadgeCheck,

        },

        {

            title: "Conversion Rate",

            value: `${Number(summary.conversion_rate ?? 0).toFixed(1)}%`,

            icon: Target,

        },

    ];

    const pipeline = [

        ["New", summary.new_leads],

        ["Contacted", summary.contacted_leads],

        ["Qualified", summary.qualified_leads],

        ["Proposal", summary.proposal_leads],

        ["Won", summary.won_leads],

        ["Lost", summary.lost_leads],

    ];

    const qualification = [

        { title: "Hot", value: summary.hot_leads, icon: Flame },

        { title: "Warm", value: summary.warm_leads, icon: Waves },

        { title: "Cold", value: summary.cold_leads, icon: Snowflake },

    ];

    const proposalLifecycle = [

        ["Draft", summary.draft_proposals],

        ["Sent", summary.sent_proposals],

        ["Accepted", summary.accepted_proposals],

        ["Rejected", summary.rejected_proposals],

    ];

    return (
        <div className="dashboard-page">
            <>

            <div className="page-heading">

                <div>

                    <p className="page-eyebrow">SALES ANALYTICS</p>

                    <h1>Dashboard Overview</h1>

                    <p>

                        Monitor leads, quotations, sales performance and

                        conversion across your solar CRM.

                    </p>

                </div>

                <div style={{ position: "relative" }}>

                    <button

                        type="button"

                        onClick={() => setShowReminders((current) => !current)}

                        aria-label="Sales follow-up reminders"

                        title="Sales follow-up reminders"

                        style={{

                            position: "relative",

                            width: "44px",

                            height: "44px",

                            borderRadius: "12px",

                            border: "1px solid rgba(15, 23, 42, 0.1)",

                            background: "var(--card-bg, #fff)",

                            display: "grid",

                            placeItems: "center",

                            cursor: "pointer",

                        }}

                    >

                        {getReminderFollowUps().length > 0 ? (

                            <BellRing size={20} />

                        ) : (

                            <Bell size={20} />

                        )}

                        {getReminderFollowUps().length > 0 && (

                            <span

                                style={{

                                    position: "absolute",

                                    top: "-6px",

                                    right: "-6px",

                                    minWidth: "20px",

                                    height: "20px",

                                    padding: "0 5px",

                                    borderRadius: "999px",

                                    background: "#dc2626",

                                    color: "#fff",

                                    display: "grid",

                                    placeItems: "center",

                                    fontSize: "10px",

                                    fontWeight: 800,

                                }}

                            >

                                {getReminderFollowUps().length > 99

                                    ? "99+"

                                    : getReminderFollowUps().length}

                            </span>

                        )}

                    </button>

                    {showReminders && (

                        <div

                            style={{

                                position: "absolute",

                                zIndex: 50,

                                right: 0,

                                top: "52px",

                                width: "min(390px, 88vw)",

                                maxHeight: "440px",

                                overflowY: "auto",

                                background: "var(--card-bg, #fff)",

                                border: "1px solid rgba(15, 23, 42, 0.1)",

                                borderRadius: "16px",

                                boxShadow: "0 18px 50px rgba(15, 23, 42, 0.16)",

                                padding: "12px",

                            }}

                        >

                            <div

                                style={{

                                    display: "flex",

                                    alignItems: "center",

                                    justifyContent: "space-between",

                                    gap: "12px",

                                    padding: "4px 4px 10px",

                                }}

                            >

                                <div>

                                    <strong>Follow-up Reminders</strong>

                                    <div style={{ fontSize: "11px", opacity: 0.62, marginTop: "2px" }}>

                                        Today and overdue sales tasks

                                    </div>

                                </div>

                                <span className="dashboard-panel-badge">

                                    {getReminderFollowUps().length} due

                                </span>

                            </div>

                            {getReminderFollowUps().length === 0 ? (

                                <div

                                    style={{

                                        padding: "20px 8px",

                                        textAlign: "center",

                                        fontSize: "13px",

                                        opacity: 0.62,

                                    }}

                                >

                                    No follow-ups are due today.

                                </div>

                            ) : (

                                getReminderFollowUps().map((lead) => (

                                    <button

                                        type="button"

                                        key={lead.id}

                                        onClick={() => openLead(lead.id)}

                                        style={{

                                            width: "100%",

                                            border: 0,

                                            borderTop: "1px solid rgba(15, 23, 42, 0.07)",

                                            background: "transparent",

                                            padding: "11px 6px",

                                            cursor: "pointer",

                                            textAlign: "left",

                                        }}

                                    >

                                        <div

                                            style={{

                                                display: "flex",

                                                justifyContent: "space-between",

                                                gap: "12px",

                                                alignItems: "flex-start",

                                            }}

                                        >

                                            <div style={{ minWidth: 0 }}>

                                                <strong style={{ fontSize: "13px" }}>

                                                    {lead.name || `Lead #${lead.id}`}

                                                </strong>

                                                <div

                                                    style={{

                                                        marginTop: "3px",

                                                        fontSize: "11px",

                                                        opacity: 0.65,

                                                    }}

                                                >

                                                    {lead.follow_up_note || "Sales follow-up"}

                                                </div>

                                            </div>

                                            <span

                                                style={{

                                                    fontSize: "10px",

                                                    fontWeight: 800,

                                                    whiteSpace: "nowrap",

                                                }}

                                            >

                                                {getReminderType(lead)}

                                            </span>

                                        </div>

                                        <div

                                            style={{

                                                display: "flex",

                                                alignItems: "center",

                                                gap: "5px",

                                                marginTop: "7px",

                                                fontSize: "11px",

                                                opacity: 0.7,

                                            }}

                                        >

                                            <CalendarClock size={12} />

                                            {formatDateTime(lead.next_follow_up_at)}

                                        </div>

                                    </button>

                                ))

                            )}

                            <button

                                type="button"

                                onClick={() => setShowReminders(false)}

                                style={{

                                    width: "100%",

                                    marginTop: "8px",

                                    border: 0,

                                    background: "transparent",

                                    cursor: "pointer",

                                    padding: "7px",

                                    fontSize: "11px",

                                    opacity: 0.62,

                                    display: "flex",

                                    alignItems: "center",

                                    justifyContent: "center",

                                    gap: "4px",

                                }}

                            >

                                Close <ChevronDown size={13} />

                            </button>

                        </div>

                    )}

                </div>

            </div>

            <div className="stats-grid">

                {cards.map((card) => {

                    const Icon = card.icon;

                    return (

                        <div className="stat-card" key={card.title}>

                            <div className="stat-card-top">

                                <div>

                                    <span>{card.title}</span>

                                    <strong>{card.value}</strong>

                                </div>

                                <div className="stat-icon">

                                    <Icon size={21} />

                                </div>

                            </div>

                        </div>

                    );

                })}

            </div>

            <div className="dashboard-analytics-grid">

                <section className="dashboard-panel">

                    <div className="dashboard-panel-header">

                        <div className="dashboard-panel-title">

                            <TrendingUp size={18} />

                            <h3>Sales Pipeline</h3>

                        </div>

                        <span className="dashboard-panel-badge">

                            {summary.total_leads} leads

                        </span>

                    </div>

                    <div className="dashboard-panel-body">

                        {pipeline.map(([label, value]) => (

                            <div className="dashboard-metric-row" key={label}>

                                <div className="dashboard-metric-top">

                                    <span className="dashboard-metric-label">

                                        {label}

                                    </span>

                                    <strong className="dashboard-metric-value">

                                        {value}

                                    </strong>

                                </div>

                                <div className="dashboard-progress">

                                    <div

                                        className="dashboard-progress-fill"

                                        style={{

                                            width: `${percentage(

                                                value,

                                                summary.total_leads

                                            )}%`,

                                        }}

                                    />

                                </div>

                            </div>

                        ))}

                    </div>

                </section>

                <section className="dashboard-panel">

                    <div className="dashboard-panel-header">

                        <div className="dashboard-panel-title">

                            <Target size={18} />

                            <h3>Lead Qualification</h3>

                        </div>

                    </div>

                    <div className="dashboard-panel-body">

                        <div className="dashboard-qualification-list">

                            {qualification.map((item) => {

                                const Icon = item.icon;

                                return (

                                    <div

                                        className="dashboard-qualification-item"

                                        key={item.title}

                                    >

                                        <div className="dashboard-qualification-icon">

                                            <Icon size={16} />

                                        </div>

                                        <div className="dashboard-qualification-copy">

                                            <span>{item.title} Leads</span>

                                            <strong>{item.value}</strong>

                                        </div>

                                        <span className="dashboard-qualification-share">

                                            {percentage(

                                                item.value,

                                                summary.total_leads

                                            )}

                                            %

                                        </span>

                                    </div>

                                );

                            })}

                        </div>

                    </div>

                </section>

                <section className="dashboard-panel">

                    <div className="dashboard-panel-header">

                        <div className="dashboard-panel-title">

                            <FileText size={18} />

                            <h3>Proposal Lifecycle</h3>

                        </div>

                        <span className="dashboard-panel-badge">

                            {summary.total_proposals} total

                        </span>

                    </div>

                    <div className="dashboard-panel-body">

                        {proposalLifecycle.map(([label, value]) => (

                            <div className="dashboard-metric-row" key={label}>

                                <div className="dashboard-metric-top">

                                    <span className="dashboard-metric-label">

                                        {label}

                                    </span>

                                    <strong className="dashboard-metric-value">

                                        {value}

                                    </strong>

                                </div>

                                <div className="dashboard-progress">

                                    <div

                                        className="dashboard-progress-fill"

                                        style={{

                                            width: `${percentage(

                                                value,

                                                summary.total_proposals

                                            )}%`,

                                        }}

                                    />

                                </div>

                            </div>

                        ))}

                        <div className="dashboard-revenue-strip">

                            <div className="dashboard-revenue-box">

                                <span>Quotation Value</span>

                                <strong>

                                    {formatMoney(summary.total_proposal_value)}

                                </strong>

                            </div>

                            <div className="dashboard-revenue-box">

                                <span>Accepted Value</span>

                                <strong>

                                    {formatMoney(summary.accepted_sales_value)}

                                </strong>

                            </div>

                            <div className="dashboard-revenue-box">

                                <span>Conversion</span>

                                <strong>

                                    {Number(

                                        summary.conversion_rate ?? 0

                                    ).toFixed(1)}

                                    %

                                </strong>

                            </div>

                        </div>

                    </div>

                </section>

            </div>

            <div

                className="dashboard-analytics-grid"

                style={{ marginTop: "24px" }}

            >

                <section className="dashboard-panel">

                    <div className="dashboard-panel-header">

                        <div className="dashboard-panel-title">

                            <Users size={18} />

                            <h3>Recent Leads</h3>

                        </div>

                        <button

                            type="button"

                            className="dashboard-panel-badge"

                            onClick={() => (window.location.href = "/leads")}

                            style={{ cursor: "pointer" }}

                        >

                            View all <ArrowRight size={12} />

                        </button>

                    </div>

                    <div className="dashboard-panel-body">

                        {recentLeads.length === 0 ? (

                            <p style={{ opacity: 0.65, margin: 0 }}>

                                No leads available yet.

                            </p>

                        ) : (

                            recentLeads.map((lead) => (

                                <button

                                    type="button"

                                    key={lead.id}

                                    onClick={() => openLead(lead.id)}

                                    className="dashboard-metric-row"

                                    style={{

                                        width: "100%",

                                        border: 0,

                                        background: "transparent",

                                        textAlign: "left",

                                        cursor: "pointer",

                                    }}

                                >

                                    <div className="dashboard-metric-top">

                                        <div>

                                            <strong className="dashboard-metric-label">

                                                {lead.name || `Lead #${lead.id}`}

                                            </strong>

                                            <div

                                                style={{

                                                    display: "flex",

                                                    gap: "8px",

                                                    marginTop: "4px",

                                                    fontSize: "12px",

                                                    opacity: 0.68,

                                                }}

                                            >

                                                <span>{lead.city || "No city"}</span>

                                                <span>•</span>

                                                <span>{formatDate(lead.created_at)}</span>

                                            </div>

                                        </div>

                                        <div style={{ textAlign: "right" }}>

                                            <strong className="dashboard-metric-value">

                                                {titleCase(lead.status)}

                                            </strong>

                                            <div

                                                style={{

                                                    fontSize: "11px",

                                                    marginTop: "4px",

                                                    opacity: 0.7,

                                                }}

                                            >

                                                {titleCase(

                                                    lead.qualification_level

                                                )}

                                                {lead.qualification_score !==

                                                    null &&

                                                    lead.qualification_score !==

                                                    undefined

                                                    ? ` • ${lead.qualification_score}/100`

                                                    : ""}

                                            </div>

                                        </div>

                                    </div>

                                </button>

                            ))

                        )}

                    </div>

                </section>

                <section className="dashboard-panel">

                    <div className="dashboard-panel-header">

                        <div className="dashboard-panel-title">

                            <FileText size={18} />

                            <h3>Latest Proposals</h3>

                        </div>

                        <button

                            type="button"

                            className="dashboard-panel-badge"

                            onClick={() =>

                                (window.location.href = "/proposals")

                            }

                            style={{ cursor: "pointer" }}

                        >

                            View all <ArrowRight size={12} />

                        </button>

                    </div>

                    <div className="dashboard-panel-body">

                        {recentProposals.length === 0 ? (

                            <p style={{ opacity: 0.65, margin: 0 }}>

                                No proposals available yet.

                            </p>

                        ) : (

                            recentProposals.map((proposal) => (

                                <button

                                    type="button"

                                    key={proposal.id}

                                    onClick={() => openProposal(proposal.id)}

                                    className="dashboard-metric-row"

                                    style={{

                                        width: "100%",

                                        border: 0,

                                        background: "transparent",

                                        textAlign: "left",

                                        cursor: "pointer",

                                    }}

                                >

                                    <div className="dashboard-metric-top">

                                        <div>

                                            <strong className="dashboard-metric-label">

                                                {proposal.proposal_number ||

                                                    `Proposal #${proposal.id}`}

                                            </strong>

                                            <div

                                                style={{

                                                    display: "flex",

                                                    alignItems: "center",

                                                    gap: "5px",

                                                    marginTop: "4px",

                                                    fontSize: "12px",

                                                    opacity: 0.68,

                                                }}

                                            >

                                                <Clock3 size={12} />

                                                {formatDate(

                                                    proposal.created_at

                                                )}

                                                {proposal.lead_id

                                                    ? ` • Lead #${proposal.lead_id}`

                                                    : ""}

                                            </div>

                                        </div>

                                        <div style={{ textAlign: "right" }}>

                                            <strong className="dashboard-metric-value">

                                                {formatMoney(

                                                    proposal.total_price

                                                )}

                                            </strong>

                                            <div

                                                style={{

                                                    fontSize: "11px",

                                                    marginTop: "4px",

                                                    opacity: 0.7,

                                                }}

                                            >

                                                {titleCase(proposal.status)}

                                            </div>

                                        </div>

                                    </div>

                                </button>

                            ))

                        )}

                    </div>

                </section>

            </div>

            <div className="dashboard-analytics-grid" style={{ marginTop: "24px" }}>

                <section className="dashboard-panel">

                    <div className="dashboard-panel-header">

                        <div className="dashboard-panel-title">

                            <CalendarClock size={18} />

                            <h3>Sales Follow-ups</h3>

                        </div>

                        <span className="dashboard-panel-badge">{getOpenFollowUps().length} open</span>

                    </div>

                    <div className="dashboard-panel-body">

                        <div className="dashboard-metric-row">

                            <div className="dashboard-metric-top">

                                <strong className="dashboard-metric-label">Today</strong>

                                <strong className="dashboard-metric-value">{getTodayFollowUps().length}</strong>

                            </div>

                        </div>

                        <div className="dashboard-metric-row">

                            <div className="dashboard-metric-top">

                                <strong className="dashboard-metric-label">Overdue</strong>

                                <strong className="dashboard-metric-value">{getOverdueFollowUps().length}</strong>

                            </div>

                        </div>

                    </div>

                </section>

                <section className="dashboard-panel">

                    <div className="dashboard-panel-header">

                        <div className="dashboard-panel-title">

                            <AlertTriangle size={18} />

                            <h3>Next Follow-ups</h3>

                        </div>

                        <span className="dashboard-panel-badge">Upcoming</span>

                    </div>

                    <div className="dashboard-panel-body">

                        {getUpcomingFollowUps().length === 0 ? (

                            <p style={{ opacity: 0.65, margin: 0 }}>No upcoming follow-ups scheduled.</p>

                        ) : (

                            getUpcomingFollowUps().map((lead) => (

                                <button

                                    type="button"

                                    key={lead.id}

                                    onClick={() => openLead(lead.id)}

                                    className="dashboard-metric-row"

                                    style={{ width: "100%", border: 0, background: "transparent", textAlign: "left", cursor: "pointer" }}

                                >

                                    <div className="dashboard-metric-top">

                                        <div>

                                            <strong className="dashboard-metric-label">{lead.name || `Lead #${lead.id}`}</strong>

                                            <div style={{ fontSize: "12px", opacity: 0.68, marginTop: "4px" }}>

                                                {lead.follow_up_note || "Sales follow-up"}

                                            </div>

                                        </div>

                                        <strong className="dashboard-metric-value" style={{ fontSize: "12px" }}>

                                            {formatDateTime(lead.next_follow_up_at)}

                                        </strong>

                                    </div>

                                </button>

                            ))

                        )}

                    </div>

                </section>

            </div>

            <section className="dashboard-panel" style={{ marginTop: "24px" }}>

                <div className="dashboard-panel-header">

                    <div className="dashboard-panel-title">

                        <ListTodo size={18} />

                        <h3>Sales Task Queue</h3>

                    </div>

                    <span className="dashboard-panel-badge">

                        {openTasks.length} open

                    </span>

                </div>

                <div className="dashboard-panel-body">

                    {openTasks.length === 0 ? (

                        <p style={{ opacity: 0.65, margin: 0 }}>No open sales tasks.</p>

                    ) : (

                        openTasks.slice(0, 8).map((task) => {

                            const overdue = task.due_at && new Date(task.due_at) < new Date();

                            return (

                                <button

                                    type="button"

                                    key={task.id}

                                    onClick={() => openLead(task.lead_id)}

                                    className="dashboard-metric-row"

                                    style={{ width: "100%", border: 0, background: "transparent", textAlign: "left", cursor: "pointer" }}

                                >

                                    <div className="dashboard-metric-top">

                                        <div>

                                            <strong className="dashboard-metric-label">{task.title}</strong>

                                            <div style={{ fontSize: "11px", opacity: 0.68, marginTop: "4px" }}>

                                                Lead #{task.lead_id} • {titleCase(task.priority)} priority

                                            </div>

                                        </div>

                                        <div style={{ textAlign: "right", fontSize: "11px" }}>

                                            <strong>{overdue ? "Overdue" : task.due_at ? "Upcoming" : "No due date"}</strong>

                                            {task.due_at && (

                                                <div style={{ opacity: 0.65, marginTop: "4px" }}>

                                                    {formatDateTime(task.due_at)}

                                                </div>

                                            )}

                                        </div>

                                    </div>

                                </button>

                            );

                        })

                    )}

                </div>

            </section>

            <section

                className="dashboard-panel"

                style={{ marginTop: "24px" }}

            >

                <div className="dashboard-panel-header">

                    <div className="dashboard-panel-title">

                        <Activity size={18} />

                        <h3>Recent CRM Activity</h3>

                    </div>

                    <span className="dashboard-panel-badge">

                        Latest {recentActivities.length}

                    </span>

                </div>

                <div className="dashboard-panel-body">

                    {recentActivities.length === 0 ? (

                        <p style={{ opacity: 0.65, margin: 0 }}>

                            No recent CRM activity available yet.

                        </p>

                    ) : (

                        recentActivities.map((activity, index) => (

                            <button

                                type="button"

                                key={

                                    activity.id ??

                                    `${activity.lead_id}-${activity.created_at}-${index}`

                                }

                                onClick={() => openLead(activity.lead_id)}

                                className="dashboard-metric-row"

                                style={{

                                    width: "100%",

                                    border: 0,

                                    background: "transparent",

                                    textAlign: "left",

                                    cursor: "pointer",

                                }}

                            >

                                <div className="dashboard-metric-top">

                                    <div style={{ minWidth: 0 }}>

                                        <div

                                            style={{

                                                display: "flex",

                                                alignItems: "center",

                                                gap: "8px",

                                                flexWrap: "wrap",

                                            }}

                                        >

                                            <strong className="dashboard-metric-label">

                                                {activity.lead_name}

                                            </strong>

                                            <span

                                                className="dashboard-panel-badge"

                                                style={{ fontSize: "10px" }}

                                            >

                                                {titleCase(

                                                    activity.activity_type

                                                )}

                                            </span>

                                        </div>

                                        <div

                                            style={{

                                                marginTop: "5px",

                                                fontSize: "12px",

                                                lineHeight: 1.5,

                                                opacity: 0.72,

                                            }}

                                        >

                                            {activity.description ||

                                                "CRM activity recorded."}

                                        </div>

                                    </div>

                                    <div

                                        style={{

                                            display: "flex",

                                            alignItems: "center",

                                            gap: "5px",

                                            fontSize: "11px",

                                            opacity: 0.62,

                                            whiteSpace: "nowrap",

                                            marginLeft: "14px",

                                        }}

                                    >

                                        <Clock3 size={12} />

                                        {formatDateTime(

                                            activity.created_at

                                        )}

                                    </div>

                                </div>

                            </button>

                        ))

                    )}

                </div>

            </section>

        </>
        </div>

    );

}

export default Dashboard;
