"""
Proposal PDF Service
====================

Generates a professional customer-facing solar quotation
from the proposal snapshot stored in the database.
"""

from io import BytesIO

from app.models.proposal import Proposal
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def format_pkr(amount: float) -> str:
    """Format an amount as Pakistani Rupees."""

    return f"PKR {amount:,.0f}"


def generate_proposal_pdf(
    proposal: Proposal,
) -> BytesIO:
    """
    Generate a professional PDF quotation.

    Historical proposal/item snapshot values are used so
    later catalog price changes do not alter the quotation.
    """

    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title=proposal.proposal_number,
        author="Solar AI Sales Agent",
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "QuotationTitle",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontSize=20,
        spaceAfter=6,
    )

    subtitle_style = ParagraphStyle(
        "QuotationSubtitle",
        parent=styles["Normal"],
        alignment=TA_CENTER,
        fontSize=10,
        textColor=colors.grey,
        spaceAfter=18,
    )

    section_style = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontSize=12,
        spaceBefore=10,
        spaceAfter=6,
    )

    right_style = ParagraphStyle(
        "RightAligned",
        parent=styles["Normal"],
        alignment=TA_RIGHT,
    )

    story = []

    # --------------------------------------------------
    # HEADER
    # --------------------------------------------------
    story.append(
        Paragraph(
            "SOLAR SYSTEM QUOTATION",
            title_style,
        )
    )

    story.append(
        Paragraph(
            "Solar AI Sales Agent",
            subtitle_style,
        )
    )

    # --------------------------------------------------
    # PROPOSAL INFORMATION
    # --------------------------------------------------
    proposal_info = [
        [
            "Proposal Number",
            proposal.proposal_number,
            "Date",
            proposal.created_at.strftime("%d %B %Y"),
        ],
        [
            "Status",
            proposal.status.upper(),
            "Lead ID",
            str(proposal.lead_id),
        ],
    ]

    info_table = Table(
        proposal_info,
        colWidths=[
            35 * mm,
            50 * mm,
            25 * mm,
            45 * mm,
        ],
    )

    info_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.whitesmoke),
                ("BACKGROUND", (2, 0), (2, -1), colors.whitesmoke),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("PADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )

    story.append(info_table)
    story.append(Spacer(1, 12))

    # --------------------------------------------------
    # CUSTOMER
    # --------------------------------------------------
    story.append(
        Paragraph(
            "Customer Information",
            section_style,
        )
    )

    # Proposal currently stores lead_id rather than a
    # duplicated customer snapshot, so we use its Lead
    # relationship/data when available.
    lead = getattr(proposal, "lead", None)

    if lead is not None:
        customer_data = [
            ["Customer Name", lead.name],
            ["Phone", lead.phone],
            ["Email", lead.email or "-"],
            ["City", lead.city or "-"],
        ]
    else:
        customer_data = [
            ["Lead ID", str(proposal.lead_id)],
        ]

    customer_table = Table(
        customer_data,
        colWidths=[45 * mm, 120 * mm],
    )

    customer_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.whitesmoke),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("PADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )

    story.append(customer_table)
    story.append(Spacer(1, 12))

    # --------------------------------------------------
    # PRODUCTS
    # --------------------------------------------------
    story.append(
        Paragraph(
            "System Components",
            section_style,
        )
    )

    item_data = [
        [
            "#",
            "Product",
            "Qty",
            "Unit Price",
            "Reference Total",
        ]
    ]

    for number, item in enumerate(proposal.items, start=1):
        item_data.append(
            [
                str(number),
                item.product_name,
                str(item.quantity),
                format_pkr(item.unit_price),
                format_pkr(item.line_total),
            ]
        )

    item_table = Table(
        item_data,
        colWidths=[
            10 * mm,
            65 * mm,
            15 * mm,
            35 * mm,
            40 * mm,
        ],
        repeatRows=1,
    )

    item_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("ALIGN", (2, 1), (-1, -1), "RIGHT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("PADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )

    story.append(item_table)
    story.append(Spacer(1, 15))

    # --------------------------------------------------
    # FINAL PACKAGE PRICING
    # --------------------------------------------------
    pricing_data = [
        [
            "Package Price",
            format_pkr(proposal.subtotal),
        ],
        [
            "Discount",
            format_pkr(proposal.discount),
        ],
        [
            "Final Quotation",
            format_pkr(proposal.total_price),
        ],
    ]

    pricing_table = Table(
        pricing_data,
        colWidths=[55 * mm, 45 * mm],
        hAlign="RIGHT",
    )

    pricing_table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTNAME", (0, 2), (-1, 2), "Helvetica-Bold"),
                ("BACKGROUND", (0, 2), (-1, 2), colors.whitesmoke),
                ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                ("LINEABOVE", (0, 2), (-1, 2), 1, colors.black),
                ("PADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )

    story.append(pricing_table)

    # --------------------------------------------------
    # NOTES
    # --------------------------------------------------
    if proposal.notes:
        story.append(Spacer(1, 15))

        story.append(
            Paragraph(
                "Notes",
                section_style,
            )
        )

        story.append(
            Paragraph(
                proposal.notes,
                styles["BodyText"],
            )
        )

    story.append(Spacer(1, 20))

    story.append(
        Paragraph(
            "This quotation was generated from the verified "
            "proposal record. Product line prices are snapshots "
            "for reference; the package price above is the agreed "
            "complete-system quotation.",
            styles["BodyText"],
        )
    )

    document.build(story)

    buffer.seek(0)

    return buffer
