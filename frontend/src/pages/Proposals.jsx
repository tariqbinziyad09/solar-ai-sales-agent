import { useEffect, useState } from "react";

import { useNavigate } from "react-router-dom";
import api, {
    downloadProposalPdf,
} from "../services/api";
import {

    CalendarDays,

    Download,

    Eye,

    FileText,

    Package,

    User,

} from "lucide-react";







function Proposals() {

    const navigate = useNavigate();



    const [proposals, setProposals] = useState([]);

    const [loading, setLoading] = useState(true);

    const [error, setError] = useState("");





    // =========================================================

    // LOAD ALL PROPOSALS

    // GET /api/proposals

    // =========================================================

    useEffect(() => {

        loadProposals();

    }, []);





    async function loadProposals() {

        try {

            setLoading(true);

            setError("");



            const response = await api.get("/proposals");



            console.log("Proposals:", response.data);



            setProposals(response.data);

        } catch (err) {

            console.error("Unable to load proposals:", err);



            setError("Unable to load proposals.");

        } finally {

            setLoading(false);

        }

    }





    // =========================================================

    // FORMAT MONEY

    // =========================================================

    function formatMoney(value) {

        if (value === null || value === undefined) {

            return "PKR 0";

        }



        return `PKR ${Number(value).toLocaleString()}`;

    }





    // =========================================================

    // FORMAT DATE

    // =========================================================

    function formatDate(value) {

        if (!value) {

            return "—";

        }



        return new Date(value).toLocaleDateString("en-PK", {

            day: "2-digit",

            month: "short",

            year: "numeric",

        });

    }





    // =========================================================

    // FORMAT STATUS

    // =========================================================

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

    // OPEN PROPOSAL DETAILS

    // IMPORTANT:

    // Backend proposal uses "id", not "proposal_id".

    // =========================================================

    function openProposal(proposal) {

        if (!proposal?.id) {

            console.error(

                "Proposal ID is missing:",

                proposal

            );



            return;

        }



        navigate(`/proposals/${proposal.id}`);

    }





    // =========================================================

    // DOWNLOAD PDF

    // =========================================================

    async function downloadProposal(event, proposal) {
        event.stopPropagation();

        if (!proposal?.id) {
            console.error(
                "Cannot download PDF. Proposal ID missing:",
                proposal
            );

            return;
        }

        setError("");

        try {
            await downloadProposalPdf(
                proposal.id,
                proposal.proposal_number
            );
        } catch (err) {
            console.error(
                "Unable to download proposal PDF:",
                err
            );

            setError(
                err.response?.data?.detail ||
                "Unable to download proposal PDF."
            );
        }
    }

    // =========================================================

    // LOADING

    // =========================================================

    if (loading) {

        return (

            <div className="table-card">

                <div style={{ padding: "30px" }}>

                    Loading proposals...

                </div>

            </div>

        );

    }





    return (

        <div className="proposals-page">



            {/* =====================================================

          PAGE HEADER

      ====================================================== */}

            <div className="page-header proposals-hero">



                <div>

                    <p className="page-eyebrow">

                        SALES QUOTATIONS

                    </p>



                    <h1>Proposals</h1>



                    <p>

                        Manage customer quotations and solar

                        system proposals.

                    </p>

                </div>



                <div className="records-count">

                    <FileText size={17} />



                    {proposals.length}{" "}

                    {proposals.length === 1

                        ? "Proposal"

                        : "Proposals"}

                </div>



            </div>





            {/* =====================================================

          ERROR

      ====================================================== */}

            {error && (

                <div className="leads-error">

                    {error}

                </div>

            )}





            {/* =====================================================

          PROPOSALS TABLE

      ====================================================== */}

            <div className="table-card">



                <div className="proposal-table-heading">



                    <div>

                        <h3>Sales Proposals</h3>



                        <p>

                            Latest customer quotations and their

                            current status.

                        </p>

                    </div>



                </div>





                <div className="table-responsive">



                    <table className="crm-table">



                        <thead>

                            <tr>

                                <th>Proposal</th>

                                <th>Customer</th>

                                <th>Package</th>

                                <th>Components</th>

                                <th>Total</th>

                                <th>Status</th>

                                <th>Date</th>

                                <th>Actions</th>

                            </tr>

                        </thead>





                        <tbody>



                            {proposals.length === 0 ? (

                                <tr>

                                    <td

                                        colSpan="8"

                                        className="empty-table"

                                    >

                                        No proposals found.

                                    </td>

                                </tr>

                            ) : (

                                proposals.map((proposal) => (



                                    <tr

                                        key={proposal.id}

                                        className="clickable-row"

                                        onClick={() =>

                                            openProposal(proposal)

                                        }

                                    >



                                        {/* Proposal Number */}

                                        <td>

                                            <div className="proposal-cell">



                                                <div className="proposal-icon">

                                                    <FileText size={17} />

                                                </div>



                                                <div>

                                                    <strong>

                                                        {proposal.proposal_number}

                                                    </strong>



                                                    <span>

                                                        ID #{proposal.id}

                                                    </span>

                                                </div>



                                            </div>

                                        </td>





                                        {/* Customer */}

                                        <td>

                                            <div className="proposal-simple-cell">

                                                <User size={15} />



                                                <span>

                                                    Lead #{proposal.lead_id}

                                                </span>

                                            </div>

                                        </td>





                                        {/* Package */}

                                        <td>

                                            <div className="proposal-simple-cell">

                                                <Package size={15} />



                                                <span>

                                                    Package #{proposal.package_id}

                                                </span>

                                            </div>

                                        </td>





                                        {/* Components */}

                                        <td>

                                            <span className="component-count">

                                                {proposal.items?.length || 0} Items

                                            </span>

                                        </td>





                                        {/* Price */}

                                        <td>

                                            <div className="proposal-price-cell">



                                                <strong>

                                                    {formatMoney(

                                                        proposal.total_price

                                                    )}

                                                </strong>



                                                {Number(proposal.discount) > 0 && (

                                                    <span>

                                                        Discount{" "}

                                                        {formatMoney(

                                                            proposal.discount

                                                        )}

                                                    </span>

                                                )}



                                            </div>

                                        </td>





                                        {/* Status */}

                                        <td>

                                            <span

                                                className={`proposal-status proposal-status-${proposal.status}`}

                                            >

                                                {formatStatus(

                                                    proposal.status

                                                )}

                                            </span>

                                        </td>





                                        {/* Date */}

                                        <td>

                                            <div className="proposal-simple-cell">

                                                <CalendarDays size={14} />



                                                <span>

                                                    {formatDate(

                                                        proposal.created_at

                                                    )}

                                                </span>

                                            </div>

                                        </td>





                                        {/* Actions */}

                                        <td>

                                            <div className="proposal-actions">



                                                {/* VIEW */}

                                                <button

                                                    type="button"

                                                    className="proposal-action-btn"

                                                    title="View Proposal"

                                                    onClick={(event) => {

                                                        event.stopPropagation();



                                                        openProposal(proposal);

                                                    }}

                                                >

                                                    <Eye size={16} />

                                                </button>





                                                {/* DOWNLOAD PDF */}

                                                <button

                                                    type="button"

                                                    className="proposal-action-btn"

                                                    title="Download PDF"

                                                    onClick={(event) =>

                                                        downloadProposal(

                                                            event,

                                                            proposal

                                                        )

                                                    }

                                                >

                                                    <Download size={16} />

                                                </button>



                                            </div>

                                        </td>



                                    </tr>

                                ))

                            )}



                        </tbody>



                    </table>



                </div>

            </div>

        </div>

    );

}





export default Proposals;