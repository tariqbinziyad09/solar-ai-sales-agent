import { useEffect, useRef, useState } from "react";

import api, {
    downloadAuthenticatedFile,
} from "../services/api";





import {







    Bot,







    CheckCircle2,







    CircleDollarSign,







    ExternalLink,







    FileText,







    MessageSquarePlus,







    Send,







    Sparkles,







    Sun,







    User,







    Zap,



    Gauge,



    BatteryCharging,



    Activity,



    ClipboardList,



    AirVent,



    Fan,



    Refrigerator,



    Lightbulb,



    Tv,



    Laptop,







} from "lucide-react";







































function AIAgent() {







    const [sessionId, setSessionId] = useState(null);







    const [leadId, setLeadId] = useState(null);















    const [messages, setMessages] = useState([]);







    const [message, setMessage] = useState("");















    const [recommendations, setRecommendations] = useState([]);







    const [requirements, setRequirements] = useState(null);







    // Generated quotation for the current AI conversation.



    const [quotation, setQuotation] = useState(null);







    // Latest deterministic preliminary solar sizing returned by backend.



    const [sizing, setSizing] = useState(null);



    const [showAssumptions, setShowAssumptions] = useState(false);















    const [loading, setLoading] = useState(false);







    const [error, setError] = useState("");















    const messagesEndRef = useRef(null);























    // =========================================================







    // INITIAL WELCOME MESSAGE







    // =========================================================







    useEffect(() => {







        setMessages([







            {







                id: "welcome",







                role: "assistant",







                text:







                    "Assalam-o-Alaikum! Main aapka Solar AI Sales Assistant hoon. " +







                    "Aap mujhe apni solar requirements bata sakte hain — jaise " +







                    "system size, budget aur battery backup requirement.",







            },







        ]);







    }, []);























    // =========================================================







    // AUTO SCROLL







    // =========================================================







    useEffect(() => {







        messagesEndRef.current?.scrollIntoView({







            behavior: "smooth",







        });







    }, [messages, loading]);























    // =========================================================







    // SEND MESSAGE







    // POST /api/agent/chat







    // =========================================================







    async function sendMessage(event) {







        event.preventDefault();















        const cleanMessage = message.trim();















        if (!cleanMessage || loading) {







            return;







        }















        const customerMessage = {







            id: `customer-${Date.now()}`,







            role: "customer",







            text: cleanMessage,







        };















        setMessages((current) => [







            ...current,







            customerMessage,







        ]);















        setMessage("");







        setError("");







        setLoading(true);















        try {







            const response = await api.post(







                "/agent/chat",







                {







                    session_id: sessionId,







                    message: cleanMessage,







                }







            );















            const data = response.data;















            // Save backend-created session ID.







            setSessionId(data.session_id);















            // CRM lead remains null until backend creates one.







            setLeadId(data.lead_id ?? null);















            // Complete accumulated requirements.







            setRequirements(







                data.extracted_requirements ?? null







            );















            // Package recommendations.



            setRecommendations(



                data.recommendations ?? []



            );







            // Preliminary sizing analysis (appliances/monthly units).



            // Keep the latest valid sizing visible during the same session.



            if (data.sizing) {



                setSizing(data.sizing);



            }







            // Keep the latest generated quotation visible.



            if (data.quotation) {



                setQuotation(data.quotation);



            }















            // Add AI response to chat.







            const assistantMessage = {







                id: `assistant-${Date.now()}`,







                role: "assistant",







                text: data.reply,







            };















            setMessages((current) => [







                ...current,







                assistantMessage,







            ]);







        } catch (err) {







            console.error(







                "AI Sales Agent Error:",







                err







            );















            const detail =







                err.response?.data?.detail;















            setError(







                typeof detail === "string"







                    ? detail







                    : "AI Sales Agent se response nahi mil saka."







            );







        } finally {







            setLoading(false);







        }







    }























    // =========================================================







    // START NEW CHAT







    // =========================================================







    function startNewChat() {







        setSessionId(null);







        setLeadId(null);







        setRecommendations([]);







        setRequirements(null);







        setQuotation(null);



        setSizing(null);



        setShowAssumptions(false);







        setError("");







        setMessage("");















        setMessages([







            {







                id: `welcome-${Date.now()}`,







                role: "assistant",







                text:







                    "Assalam-o-Alaikum! New solar consultation start ho gayi hai. " +







                    "Aap approximately kitne kW ka solar system chahte hain?",







            },







        ]);







    }























    // =========================================================







    // QUICK MESSAGE







    // =========================================================







    function useQuickMessage(text) {







        setMessage(text);







    }























    // =========================================================







    // FORMAT MONEY







    // =========================================================







    function formatMoney(value) {







        if (







            value === null ||







            value === undefined







        ) {







            return "Not provided";







        }















        return `PKR ${Number(







            value







        ).toLocaleString()}`;







    }























    // =========================================================







    // BOOLEAN DISPLAY







    // =========================================================







    function formatBackup(value) {







        if (value === true) {







            return "Required";







        }















        if (value === false) {







            return "Not Required";







        }















        return "Not provided";







    }



























    // =========================================================



    // QUOTATION PDF URL



    // =========================================================



    async function downloadQuotationPDF() {
        if (!quotation?.pdf_url) {
            setError("Quotation PDF URL available nahi hai.");
            return;
        }

        setError("");

        try {
            await downloadAuthenticatedFile(
                quotation.pdf_url,
                quotation.proposal_number
                    ? `${quotation.proposal_number}.pdf`
                    : "solar-quotation.pdf"
            );
        } catch (err) {
            console.error("Quotation PDF download failed:", err);

            setError(
                err.response?.data?.detail ||
                "Quotation PDF download nahi ho saka."
            );
        }
    }









    return (







        <div className="ai-agent-page">















            {/* =====================================================







          PAGE HEADER







      ====================================================== */}







            <div className="ai-agent-header ai-agent-hero">















                <div>







                    <p className="page-eyebrow">







                        AI SALES ASSISTANT







                    </p>















                    <h1>AI Sales Agent</h1>















                    <p>







                        Intelligent solar consultation,







                        qualification and package recommendations.







                    </p>







                </div>























                <button







                    type="button"







                    className="new-chat-button"







                    onClick={startNewChat}







                >







                    <MessageSquarePlus size={17} />







                    New Conversation







                </button>















            </div>























            {/* =====================================================







          MAIN GRID







      ====================================================== */}







            <div className="ai-agent-grid">















                {/* ===================================================







            LEFT SIDE - CHAT







        ==================================================== */}







                <div className="ai-chat-card ai-chat-premium">















                    {/* CHAT HEADER */}







                    <div className="ai-chat-header">















                        <div className="ai-agent-identity">















                            <div className="ai-agent-avatar">







                                <Bot size={22} />







                            </div>















                            <div>







                                <strong>







                                    Solar AI Assistant







                                </strong>















                                <span>







                                    <i />







                                    Online







                                </span>







                            </div>















                        </div>























                        <div className="ai-session-info">















                            {sessionId ? (







                                <>







                                    <span>







                                        Session







                                    </span>















                                    <strong>







                                        #{sessionId}







                                    </strong>







                                </>







                            ) : (







                                <span>







                                    New Session







                                </span>







                            )}















                        </div>















                    </div>























                    {/* CHAT MESSAGES */}







                    <div className="ai-chat-messages">















                        {messages.map((item) => (







                            <div







                                key={item.id}







                                className={







                                    item.role === "customer"







                                        ? "ai-message-row customer"







                                        : "ai-message-row assistant"







                                }







                            >















                                {item.role === "assistant" && (







                                    <div className="message-avatar assistant">







                                        <Bot size={16} />







                                    </div>







                                )}























                                <div







                                    className={







                                        item.role === "customer"







                                            ? "ai-message customer-message"







                                            : "ai-message assistant-message"







                                    }







                                >







                                    {item.text}







                                </div>























                                {item.role === "customer" && (







                                    <div className="message-avatar customer">







                                        <User size={16} />







                                    </div>







                                )}















                            </div>







                        ))}























                        {/* TYPING */}







                        {loading && (







                            <div className="ai-message-row assistant">















                                <div className="message-avatar assistant">







                                    <Bot size={16} />







                                </div>















                                <div className="ai-message assistant-message typing-message">







                                    <span />







                                    <span />







                                    <span />







                                </div>















                            </div>







                        )}























                        <div ref={messagesEndRef} />















                    </div>























                    {/* ERROR */}







                    {error && (







                        <div className="ai-chat-error">







                            {error}







                        </div>







                    )}























                    {/* QUICK PROMPTS */}







                    {messages.length <= 2 && (







                        <div className="quick-prompts">















                            <button







                                type="button"







                                onClick={() =>







                                    useQuickMessage(







                                        "Mujhe 10 kW hybrid solar system chahiye."







                                    )







                                }







                            >







                                10 kW Hybrid







                            </button>















                            <button







                                type="button"







                                onClick={() =>







                                    useQuickMessage(







                                        "Mera budget 12 lakh hai."







                                    )







                                }







                            >







                                Budget 12 Lakh







                            </button>















                            <button







                                type="button"







                                onClick={() =>







                                    useQuickMessage(







                                        "Mujhe battery backup bhi chahiye."







                                    )







                                }







                            >







                                Battery Backup







                            </button>















                        </div>







                    )}























                    {/* INPUT */}







                    <form







                        className="ai-chat-input"







                        onSubmit={sendMessage}







                    >















                        <input







                            type="text"







                            value={message}







                            maxLength={2000}







                            disabled={loading}







                            placeholder="Type customer's solar requirements..."







                            onChange={(event) =>







                                setMessage(event.target.value)







                            }







                        />















                        <button







                            type="submit"







                            disabled={







                                loading ||







                                !message.trim()







                            }







                        >







                            <Send size={17} />







                        </button>















                    </form>















                </div>























                {/* ===================================================







            RIGHT SIDE







        ==================================================== */}







                <div className="ai-agent-sidebar ai-insights-sidebar">















                    {/* REQUIREMENTS */}







                    <div className="ai-side-card">















                        <div className="ai-side-card-header">















                            <div>







                                <Sparkles size={18} />















                                <h3>







                                    Extracted Requirements







                                </h3>







                            </div>















                            <span className="live-badge">







                                LIVE







                            </span>















                        </div>























                        <div className="requirement-list">















                            <div className="requirement-item">















                                <div className="requirement-icon">







                                    <Zap size={16} />







                                </div>















                                <div>







                                    <span>







                                        System Size







                                    </span>















                                    <strong>







                                        {requirements?.required_kw







                                            ? `${requirements.required_kw} kW`







                                            : "Not provided"}







                                    </strong>







                                </div>















                            </div>























                            <div className="requirement-item">















                                <div className="requirement-icon">







                                    <CircleDollarSign size={16} />







                                </div>















                                <div>







                                    <span>







                                        Budget







                                    </span>















                                    <strong>







                                        {formatMoney(







                                            requirements?.budget







                                        )}







                                    </strong>







                                </div>















                            </div>























                            <div className="requirement-item">















                                <div className="requirement-icon">







                                    <Sun size={16} />







                                </div>















                                <div>







                                    <span>







                                        System Type







                                    </span>















                                    <strong>







                                        {requirements?.system_type







                                            ? requirements.system_type







                                            : "Not provided"}







                                    </strong>







                                </div>















                            </div>























                            <div className="requirement-item">















                                <div className="requirement-icon">







                                    <CheckCircle2 size={16} />







                                </div>















                                <div>







                                    <span>







                                        Battery Backup







                                    </span>















                                    <strong>







                                        {formatBackup(







                                            requirements?.needs_backup







                                        )}







                                    </strong>







                                </div>















                            </div>















                        </div>























                        {/* CRM */}







                        <div className="ai-crm-status">















                            <span>







                                CRM Lead







                            </span>















                            {leadId ? (







                                <strong className="crm-created">







                                    Lead #{leadId}







                                </strong>







                            ) : (







                                <strong>







                                    Not created yet







                                </strong>







                            )}















                        </div>















                    </div>























                    {/* APPLIANCE BREAKDOWN */}



                    {requirements?.appliances?.length > 0 && (



                        <div className="ai-side-card">



                            <div className="ai-side-card-header">



                                <div>



                                    <Zap size={18} />



                                    <h3>Appliance Breakdown</h3>



                                </div>







                                <span className="live-badge">



                                    {requirements.appliances.length} TYPES



                                </span>



                            </div>







                            <div className="requirement-list" style={{ gap: "6px" }}>



                                {requirements.appliances.map(



                                    (item, index) => {



                                        const name =



                                            item.appliance



                                                ?.replaceAll("_", " ")



                                                ?.toLowerCase() ?? "appliance";







                                        const ApplianceIcon =



                                            name === "ac"



                                                ? AirVent



                                                : name.includes("fan")



                                                    ? Fan



                                                    : name.includes("fridge") ||



                                                        name.includes("refrigerator")



                                                        ? Refrigerator



                                                        : name.includes("light") ||



                                                            name.includes("bulb")



                                                            ? Lightbulb



                                                            : name.includes("tv") ||



                                                                name.includes("television")



                                                                ? Tv



                                                                : name.includes("laptop") ||



                                                                    name.includes("computer")



                                                                    ? Laptop



                                                                    : Zap;







                                        return (



                                            <div



                                                className="requirement-item"



                                                style={{ padding: "9px 10px" }}



                                                key={`${item.appliance}-${index}`}



                                            >



                                                <div className="requirement-icon">



                                                    <ApplianceIcon size={16} />



                                                </div>







                                                <div style={{ flex: 1 }}>



                                                    <span



                                                        style={{



                                                            textTransform:



                                                                "capitalize",



                                                        }}



                                                    >



                                                        {item.quantity ?? 1} ×{" "}



                                                        {name}



                                                    </span>







                                                    <strong>



                                                        {[



                                                            item.capacity_ton



                                                                ? `${item.capacity_ton} ton`



                                                                : null,



                                                            item.wattage



                                                                ? `${item.wattage} W`



                                                                : null,



                                                            item.hours_per_day !==



                                                                null &&



                                                                item.hours_per_day !==



                                                                undefined



                                                                ? `${item.hours_per_day} hrs/day`



                                                                : null,



                                                        ]



                                                            .filter(Boolean)



                                                            .join(" • ") ||



                                                            "Using preliminary defaults"}



                                                    </strong>



                                                </div>



                                            </div>



                                        );



                                    }



                                )}



                            </div>







                            {requirements.monthly_units && (



                                <div



                                    className="requirement-footer"



                                    style={{ marginTop: "10px" }}



                                >



                                    <span>Monthly Consumption</span>



                                    <strong>



                                        {requirements.monthly_units} units



                                    </strong>



                                </div>



                            )}



                        </div>



                    )}











                    {/* SIZING ANALYSIS */}



                    {sizing && (



                        <div



                            className="ai-side-card"



                            style={{



                                border: "1px solid rgba(59, 130, 246, 0.30)",



                            }}



                        >



                            <div className="ai-side-card-header">



                                <div>



                                    <Gauge size={18} />



                                    <h3>Sizing Analysis</h3>



                                </div>







                                <span className="live-badge">



                                    PRELIMINARY



                                </span>



                            </div>







                            <div className="requirement-list">



                                <div className="requirement-item">



                                    <div className="requirement-icon">



                                        <Activity size={16} />



                                    </div>



                                    <div>



                                        <span>Estimated Peak Load</span>



                                        <strong>



                                            {Number(



                                                sizing.estimated_peak_load_kw



                                            ).toFixed(2)} kW



                                        </strong>



                                    </div>



                                </div>







                                <div className="requirement-item">



                                    <div className="requirement-icon">



                                        <Zap size={16} />



                                    </div>



                                    <div>



                                        <span>Daily Energy</span>



                                        <strong>



                                            {Number(



                                                sizing.estimated_daily_energy_kwh



                                            ).toFixed(2)} kWh/day



                                        </strong>



                                    </div>



                                </div>







                                <div className="requirement-item">



                                    <div className="requirement-icon">



                                        <Sun size={16} />



                                    </div>



                                    <div>



                                        <span>Recommended System</span>



                                        <strong>



                                            {Number(



                                                sizing.recommended_system_kw



                                            ).toFixed(1)} kW



                                        </strong>



                                    </div>



                                </div>







                                {sizing.estimated_battery_kwh !== null &&



                                    sizing.estimated_battery_kwh !== undefined && (



                                        <div className="requirement-item">



                                            <div className="requirement-icon">



                                                <BatteryCharging size={16} />



                                            </div>



                                            <div>



                                                <span>



                                                    Preliminary Battery



                                                </span>



                                                <strong>



                                                    {Number(



                                                        sizing.estimated_battery_kwh



                                                    ).toFixed(2)} kWh



                                                </strong>



                                            </div>



                                        </div>



                                    )}



                            </div>







                            {sizing.assumptions?.length > 0 && (



                                <div



                                    style={{



                                        marginTop: "10px",



                                        borderTop: "1px solid rgba(15, 23, 42, 0.08)",



                                        paddingTop: "10px",



                                    }}



                                >



                                    <button



                                        type="button"



                                        onClick={() =>



                                            setShowAssumptions((current) => !current)



                                        }



                                        style={{



                                            width: "100%",



                                            border: 0,



                                            background: "transparent",



                                            padding: 0,



                                            display: "flex",



                                            alignItems: "center",



                                            justifyContent: "space-between",



                                            cursor: "pointer",



                                            font: "inherit",



                                        }}



                                    >



                                        <span



                                            style={{



                                                display: "flex",



                                                alignItems: "center",



                                                gap: "6px",



                                                fontWeight: 700,



                                            }}



                                        >



                                            <ClipboardList size={14} />



                                            Assumptions



                                        </span>







                                        <span



                                            style={{



                                                fontSize: "11px",



                                                opacity: 0.65,



                                            }}



                                        >



                                            {showAssumptions



                                                ? "Hide"



                                                : `${sizing.assumptions.length} details`}



                                        </span>



                                    </button>







                                    {showAssumptions && (



                                        <div



                                            className="recommendation-reasons"



                                            style={{ marginTop: "8px" }}



                                        >



                                            {sizing.assumptions.map(



                                                (assumption, index) => (



                                                    <div key={index}>



                                                        <CheckCircle2 size={12} />



                                                        <span>{assumption}</span>



                                                    </div>



                                                )



                                            )}



                                        </div>



                                    )}



                                </div>



                            )}







                            <p



                                style={{



                                    margin: "12px 0 0",



                                    fontSize: "12px",



                                    lineHeight: 1.5,



                                    opacity: 0.72,



                                }}



                            >



                                Preliminary estimate only. Final design should



                                verify appliance ratings, usage, site conditions



                                and backup duration.



                            </p>



                        </div>



                    )}











                    {/* QUOTATION */}



                    {quotation && (



                        <div



                            className="ai-side-card"



                            style={{



                                border: "1px solid rgba(34, 197, 94, 0.35)",



                            }}



                        >



                            <div className="ai-side-card-header">



                                <div>



                                    <FileText size={18} />



                                    <h3>Quotation Generated</h3>



                                </div>







                                <span className="live-badge">READY</span>



                            </div>







                            <div className="requirement-list">



                                <div className="requirement-item">



                                    <div className="requirement-icon">



                                        <FileText size={16} />



                                    </div>



                                    <div>



                                        <span>Proposal Number</span>



                                        <strong>{quotation.proposal_number}</strong>



                                    </div>



                                </div>







                                <div className="requirement-item">



                                    <div className="requirement-icon">



                                        <Sun size={16} />



                                    </div>



                                    <div>



                                        <span>Package</span>



                                        <strong>Package #{quotation.package_id}</strong>



                                    </div>



                                </div>







                                <div className="requirement-item">



                                    <div className="requirement-icon">



                                        <CircleDollarSign size={16} />



                                    </div>



                                    <div>



                                        <span>Total Price</span>



                                        <strong>{formatMoney(quotation.total_price)}</strong>



                                    </div>



                                </div>







                                <div className="requirement-item">



                                    <div className="requirement-icon">



                                        <CheckCircle2 size={16} />



                                    </div>



                                    <div>



                                        <span>Status</span>



                                        <strong style={{ textTransform: "capitalize" }}>



                                            {quotation.status}



                                        </strong>



                                    </div>



                                </div>



                            </div>







                            {quotation.pdf_url && (
                                <button
                                    type="button"
                                    onClick={downloadQuotationPDF}
                                    className="new-chat-button"
                                    style={{
                                        width: "100%",
                                        marginTop: "14px",
                                        justifyContent: "center",
                                        boxSizing: "border-box",
                                    }}
                                >
                                    <ExternalLink size={16} />
                                    Download Quotation PDF
                                </button>
                            )}



                        </div>



                    )}















                    {/* RECOMMENDATIONS */}







                    <div className="ai-side-card">















                        <div className="ai-side-card-header">















                            <div>







                                <Sun size={18} />















                                <h3>







                                    Recommendations







                                </h3>







                            </div>















                        </div>























                        {recommendations.length === 0 ? (







                            <div className="no-recommendation">















                                <Sun size={27} />















                                <strong>







                                    No package yet







                                </strong>















                                <p>







                                    Package recommendations will appear







                                    after the required solar information







                                    is collected.







                                </p>















                            </div>







                        ) : (







                            <div className="recommendation-list">















                                {recommendations.map(







                                    (recommendation, index) => (







                                        <div







                                            key={







                                                recommendation.package_id







                                            }







                                            className={







                                                index === 0







                                                    ? "recommendation-card best"







                                                    : "recommendation-card"







                                            }







                                        >















                                            {index === 0 && (







                                                <div className="best-match-label">







                                                    BEST MATCH







                                                </div>







                                            )}























                                            <div className="recommendation-title">















                                                <div>







                                                    <strong>







                                                        {recommendation.name}







                                                    </strong>















                                                    <span>







                                                        Package #







                                                        {







                                                            recommendation.package_id







                                                        }







                                                    </span>







                                                </div>























                                                <div className="match-score">







                                                    {







                                                        recommendation.match_score







                                                    }







                                                    %







                                                </div>















                                            </div>























                                            <div className="recommendation-specs">















                                                <span>







                                                    {







                                                        recommendation.system_size_kw







                                                    }{" "}







                                                    kW







                                                </span>















                                                <span>







                                                    {







                                                        recommendation.system_type







                                                    }







                                                </span>















                                            </div>























                                            <div className="recommendation-price">







                                                {formatMoney(







                                                    recommendation.package_price







                                                )}







                                            </div>























                                            {recommendation.reasons?.length >







                                                0 && (







                                                    <div className="recommendation-reasons">















                                                        {recommendation.reasons.map(







                                                            (reason, reasonIndex) => (







                                                                <div







                                                                    key={reasonIndex}







                                                                >







                                                                    <CheckCircle2







                                                                        size={12}







                                                                    />















                                                                    <span>







                                                                        {reason}







                                                                    </span>







                                                                </div>







                                                            )







                                                        )}















                                                    </div>







                                                )}















                                        </div>







                                    )







                                )}















                            </div>







                        )}















                    </div>















                </div>















            </div>















        </div>







    );







}























export default AIAgent;