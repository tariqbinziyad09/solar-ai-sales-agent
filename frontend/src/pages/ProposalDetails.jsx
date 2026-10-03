import { useEffect, useState } from "react";
import api, {
    downloadProposalPdf,
} from "../services/api";
import {

    useNavigate,

    useParams,

} from "react-router-dom";



import {

    ArrowLeft,

    CalendarDays,

    CheckCircle2,

    Download,

    FileText,

    Package,

    Send,

    User,

    XCircle,

} from "lucide-react";









function ProposalDetails() {

    // IMPORTANT:

    // This name must match App.jsx:

    // /proposals/:proposalId

    const { proposalId } = useParams();



    const navigate = useNavigate();



    const [proposal, setProposal] = useState(null);

    const [loading, setLoading] = useState(true);

    const [statusLoading, setStatusLoading] =

        useState(false);

    const [error, setError] = useState("");





    // =========================================================

    // LOAD PROPOSAL

    // =========================================================

    useEffect(() => {

        if (!proposalId) {

            setError("Proposal ID is missing.");

            setLoading(false);

            return;

        }



        loadProposal();

    }, [proposalId]);





    async function loadProposal() {

        try {

            setLoading(true);

            setError("");



            console.log(

                "Loading Proposal ID:",

                proposalId

            );



            const response = await api.get(

                `/proposals/${proposalId}`

            );



            console.log(

                "Proposal details:",

                response.data

            );



            setProposal(response.data);



        } catch (err) {

            console.error(

                "Failed to load proposal:",

                err

            );



            setError(

                err.response?.data?.detail ||

                "Unable to load proposal details."

            );



        } finally {

            setLoading(false);

        }

    }





    // =========================================================

    // CHANGE STATUS

    // =========================================================

    async function changeStatus(newStatus) {

        try {

            setStatusLoading(true);

            setError("");



            const response = await api.patch(

                `/proposals/${proposalId}/status`,

                {

                    status: newStatus,

                }

            );



            setProposal(response.data);



        } catch (err) {

            console.error(

                "Failed to update proposal:",

                err

            );



            setError(

                err.response?.data?.detail ||

                "Unable to update proposal status."

            );



        } finally {

            setStatusLoading(false);

        }

    }





    // =========================================================

    // DOWNLOAD PDF

    // =========================================================

    async function downloadPDF() {
        if (!proposalId) {
            return;
        }

        setError("");

        try {
            await downloadProposalPdf(
                proposalId,
                proposal?.proposal_number
            );
        } catch (err) {
            console.error(
                "Failed to download proposal PDF:",
                err
            );

            setError(
                err.response?.data?.detail ||
                "Unable to download proposal PDF."
            );
        }
    }





    // =========================================================

    // FORMAT MONEY

    // =========================================================

    function formatMoney(value) {

        if (

            value === null ||

            value === undefined

        ) {

            return "PKR 0";

        }



        return `PKR ${Number(

            value

        ).toLocaleString()}`;

    }





    // =========================================================

    // FORMAT DATE

    // =========================================================

    function formatDate(value) {

        if (!value) {

            return "—";

        }



        return new Date(value).toLocaleString(

            "en-PK",

            {

                day: "2-digit",

                month: "short",

                year: "numeric",

                hour: "2-digit",

                minute: "2-digit",

            }

        );

    }





    function formatStatus(value) {

        if (!value) {

            return "Unknown";

        }



        return (

            value.charAt(0).toUpperCase() +

            value.slice(1)

        );

    }





    // =========================================================

    // LOADING

    // =========================================================

    if (loading) {

        return (

            <div className="proposal-detail-card proposal-components-card">

                <div style={{ padding: "30px" }}>

                    Loading proposal...

                </div>

            </div>

        );

    }





    // =========================================================

    // ERROR / NOT FOUND

    // =========================================================

    if (!proposal) {

        return (

            <div>

                <button

                    type="button"

                    className="back-button"

                    onClick={() =>

                        navigate("/proposals")

                    }

                >

                    <ArrowLeft size={17} />

                    Back to Proposals

                </button>



                <div className="leads-error">

                    {error || "Proposal not found."}

                </div>

            </div>

        );

    }





    return (

        <div className="proposal-details-page">



            {/* BACK BUTTON */}

            <button

                type="button"

                className="back-button"

                onClick={() =>

                    navigate("/proposals")

                }

            >

                <ArrowLeft size={17} />

                Back to Proposals

            </button>





            {/* =====================================================

          HEADER

      ====================================================== */}

            <div className="proposal-details-header proposal-details-hero">



                <div>

                    <p className="page-eyebrow">

                        SALES QUOTATION

                    </p>



                    <h1>

                        {proposal.proposal_number}

                    </h1>



                    <p>

                        Customer solar system quotation and

                        pricing details.

                    </p>

                </div>





                <span

                    className={`proposal-status proposal-status-${proposal.status}`}

                >

                    {formatStatus(proposal.status)}

                </span>



            </div>





            {error && (

                <div className="leads-error proposal-detail-error">

                    {error}

                </div>

            )}





            {/* =====================================================

          SUMMARY

      ====================================================== */}

            <div className="proposal-summary-grid">



                {/* CUSTOMER */}

                <div className="proposal-summary-card">



                    <div className="proposal-summary-icon">

                        <User size={20} />

                    </div>



                    <div>

                        <span>Customer</span>



                        <strong>

                            Lead #{proposal.lead_id}

                        </strong>



                        <button

                            type="button"

                            onClick={() =>

                                navigate(

                                    `/leads/${proposal.lead_id}`

                                )

                            }

                        >

                            View Customer

                        </button>

                    </div>



                </div>





                {/* PACKAGE */}

                <div className="proposal-summary-card">



                    <div className="proposal-summary-icon">

                        <Package size={20} />

                    </div>



                    <div>

                        <span>Solar Package</span>



                        <strong>

                            Package #{proposal.package_id}

                        </strong>



                        <small>

                            {proposal.items?.length || 0}{" "}

                            components

                        </small>

                    </div>



                </div>





                {/* CREATED */}

                <div className="proposal-summary-card">



                    <div className="proposal-summary-icon">

                        <CalendarDays size={20} />

                    </div>



                    <div>

                        <span>Created</span>



                        <strong>

                            {formatDate(

                                proposal.created_at

                            )}

                        </strong>



                        <small>

                            Updated:{" "}

                            {formatDate(

                                proposal.updated_at

                            )}

                        </small>

                    </div>



                </div>



            </div>





            {/* =====================================================

          COMPONENTS

      ====================================================== */}

            <div className="proposal-detail-card">



                <div className="proposal-section-header">



                    <div>

                        <div className="proposal-section-title">

                            <Package size={19} />



                            <h3>

                                Quotation Components

                            </h3>

                        </div>



                        <p>

                            Product prices stored as proposal

                            snapshots.

                        </p>

                    </div>



                    <span className="component-count">

                        {proposal.items?.length || 0} Items

                    </span>



                </div>





                <div className="table-responsive">



                    <table className="proposal-items-table">



                        <thead>

                            <tr>

                                <th>Component</th>

                                <th>Quantity</th>

                                <th>Unit Price</th>

                                <th>Line Total</th>

                            </tr>

                        </thead>





                        <tbody>



                            {proposal.items?.map(

                                (item) => (

                                    <tr key={item.id}>



                                        <td>

                                            <div className="proposal-product">



                                                <div className="product-icon">

                                                    <Package size={16} />

                                                </div>



                                                <div>

                                                    <strong>

                                                        {item.product_name}

                                                    </strong>



                                                    <span>

                                                        Product #

                                                        {item.product_id}

                                                    </span>

                                                </div>



                                            </div>

                                        </td>





                                        <td>

                                            {item.quantity}

                                        </td>





                                        <td>

                                            {formatMoney(

                                                item.unit_price

                                            )}

                                        </td>





                                        <td>

                                            <strong>

                                                {formatMoney(

                                                    item.line_total

                                                )}

                                            </strong>

                                        </td>



                                    </tr>

                                )

                            )}



                        </tbody>



                    </table>



                </div>

            </div>





            {/* =====================================================

          NOTES + PRICE

      ====================================================== */}

            <div className="proposal-bottom-grid">



                {/* NOTES */}

                <div className="proposal-detail-card proposal-notes-card">



                    <div className="proposal-section-title">

                        <FileText size={19} />



                        <h3>

                            Proposal Notes

                        </h3>

                    </div>



                    <p>

                        {proposal.notes ||

                            "No additional notes were added to this proposal."}

                    </p>



                </div>





                {/* PRICE */}

                <div className="proposal-detail-card proposal-price-summary-card">



                    <h3 className="price-summary-title">

                        Price Summary

                    </h3>





                    <div className="proposal-price-row">



                        <span>

                            Subtotal

                        </span>



                        <strong>

                            {formatMoney(

                                proposal.subtotal

                            )}

                        </strong>



                    </div>





                    <div className="proposal-price-row discount-row">



                        <span>

                            Discount

                        </span>



                        <strong>

                            -{" "}

                            {formatMoney(

                                proposal.discount

                            )}

                        </strong>



                    </div>





                    <div className="proposal-final-total">



                        <span>

                            Final Total

                        </span>



                        <strong>

                            {formatMoney(

                                proposal.total_price

                            )}

                        </strong>



                    </div>



                </div>



            </div>





            {/* =====================================================

          ACTION BAR

      ====================================================== */}

            <div className="proposal-action-bar proposal-lifecycle-bar">



                <div>

                    <strong>

                        Proposal Actions

                    </strong>



                    <span>

                        Manage quotation lifecycle and PDF.

                    </span>

                </div>





                <div className="proposal-detail-actions">



                    {/* PDF */}

                    <button

                        type="button"

                        className="proposal-secondary-button"

                        onClick={downloadPDF}

                    >

                        <Download size={17} />

                        Download PDF

                    </button>





                    {/* DRAFT -> SENT */}

                    {proposal.status === "draft" && (

                        <button

                            type="button"

                            className="proposal-primary-button"

                            disabled={statusLoading}

                            onClick={() =>

                                changeStatus("sent")

                            }

                        >

                            <Send size={17} />



                            {statusLoading

                                ? "Updating..."

                                : "Mark as Sent"}

                        </button>

                    )}





                    {/* SENT -> ACCEPTED / REJECTED */}

                    {proposal.status === "sent" && (

                        <>

                            <button

                                type="button"

                                className="proposal-reject-button"

                                disabled={statusLoading}

                                onClick={() =>

                                    changeStatus("rejected")

                                }

                            >

                                <XCircle size={17} />

                                Reject

                            </button>





                            <button

                                type="button"

                                className="proposal-primary-button"

                                disabled={statusLoading}

                                onClick={() =>

                                    changeStatus("accepted")

                                }

                            >

                                <CheckCircle2 size={17} />



                                {statusLoading

                                    ? "Updating..."

                                    : "Accept Proposal"}

                            </button>

                        </>

                    )}





                    {/* ACCEPTED */}

                    {proposal.status ===

                        "accepted" && (

                            <div className="proposal-final-message accepted">



                                <CheckCircle2 size={17} />



                                Proposal Accepted



                            </div>

                        )}





                    {/* REJECTED */}

                    {proposal.status ===

                        "rejected" && (

                            <div className="proposal-final-message rejected">



                                <XCircle size={17} />



                                Proposal Rejected



                            </div>

                        )}



                </div>



            </div>



        </div>

    );

}





export default ProposalDetails;