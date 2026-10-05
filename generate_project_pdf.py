import os
import sys
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    KeepTogether,
    HRFlowable,
)
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas to dynamically compute and print total page numbers: Page X of Y.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        if self._pageNumber == 1:
            return  # Skip header/footer on title cover page
        
        self.saveState()
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#64748B"))
        
        # Header
        self.drawString(54, 750, "WEALTHGUARD AI  |  Grounded Advisory Assistant (GAA)")
        self.setFont("Helvetica", 8)
        self.drawRightString(558, 750, "Enterprise Documentation & Architecture Report")
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.5)
        self.line(54, 742, 558, 742)
        
        # Footer
        self.line(54, 45, 558, 45)
        self.setFont("Helvetica", 8)
        self.drawString(54, 32, "Confidential - For Internal Enterprise Assessment Only")
        self.drawRightString(558, 32, f"Page {self._pageNumber} of {page_count}")
        self.restoreState()


def build_pdf(filename="WealthGuard_GAA_Project_Report.pdf"):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54,
    )

    styles = getSampleStyleSheet()

    # Custom Palettes
    navy_dark = colors.HexColor("#0B132B")
    navy_primary = colors.HexColor("#1C2541")
    gold_accent = colors.HexColor("#D4AF37")
    emerald = colors.HexColor("#10B981")
    slate_dark = colors.HexColor("#1E293B")
    slate_light = colors.HexColor("#F8FAFC")
    border_color = colors.HexColor("#E2E8F0")

    # Typography Styles
    title_style = ParagraphStyle(
        "CoverTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=26,
        leading=32,
        textColor=navy_dark,
        alignment=0,
        spaceAfter=10,
    )

    subtitle_style = ParagraphStyle(
        "CoverSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=13,
        leading=18,
        textColor=colors.HexColor("#475569"),
        spaceAfter=25,
    )

    h1_style = ParagraphStyle(
        "Heading1_Custom",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=16,
        leading=20,
        textColor=navy_dark,
        spaceBefore=14,
        spaceAfter=8,
        keepWithNext=True,
    )

    h2_style = ParagraphStyle(
        "Heading2_Custom",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        textColor=navy_primary,
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True,
    )

    body_style = ParagraphStyle(
        "Body_Custom",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=14,
        textColor=slate_dark,
        spaceAfter=6,
    )

    bullet_style = ParagraphStyle(
        "Bullet_Custom",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13.5,
        textColor=slate_dark,
        leftIndent=15,
        spaceAfter=4,
    )

    callout_style = ParagraphStyle(
        "Callout_Custom",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=9,
        leading=13.5,
        textColor=colors.HexColor("#0F172A"),
    )

    story = []

    # ================= COVER BANNER / HEADER =================
    story.append(Spacer(1, 20))
    story.append(Paragraph("WEALTHGUARD GAA", ParagraphStyle(
        "SubTag",
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=12,
        textColor=gold_accent,
        spaceAfter=6,
    )))
    story.append(Paragraph("Grounded Advisory Assistant (GAA)", title_style))
    story.append(Paragraph("Production-Grade Multi-Tenant Retrieval-Augmented Generation (RAG) System for Wealth Managers, Advisory Desks & Compliance Teams", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=2, color=gold_accent, spaceBefore=0, spaceAfter=15))

    # Metadata Block Table
    meta_data = [
        [Paragraph("<b>Author / Project:</b>", body_style), Paragraph("WealthGuard Technical Operations", body_style),
         Paragraph("<b>Date:</b>", body_style), Paragraph(datetime.now().strftime("%B %d, %Y"), body_style)],
        [Paragraph("<b>Architecture:</b>", body_style), Paragraph("FastAPI + Groq + ChromaDB + Next.js 14", body_style),
         Paragraph("<b>Compliance:</b>", body_style), Paragraph("Zero-Hallucination & Tenant Isolation", body_style)],
    ]
    t_meta = Table(meta_data, colWidths=[110, 150, 90, 150])
    t_meta.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), slate_light),
        ('BOX', (0,0), (-1,-1), 1, border_color),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_meta)
    story.append(Spacer(1, 20))

    # ================= 1. EXECUTIVE SUMMARY =================
    story.append(Paragraph("1. Executive Summary", h1_style))
    story.append(Paragraph(
        "The <b>Grounded Advisory Assistant (GAA)</b> is an enterprise-grade AI decision support terminal built for private wealth management, relationship managers (RMs), and compliance auditors. "
        "Unlike generic LLM chat solutions, GAA enforces <b>strict grounded generation</b>: every response must be verifiable against bank-approved branch policy documents, fund factsheets, and regulatory circulars. If documentation does not support the query, the system triggers an automatic compliance refusal, completely eliminating costly financial hallucinations.",
        body_style
    ))
    story.append(Paragraph(
        "Powered by ultra-fast <b>Groq LLM inference</b>, tenant-scoped vector indexing, and real-time Server-Sent Events (SSE) streaming, GAA delivers sub-second response times with interactive, verifiable clause citation badges and slide-out excerpt inspection.",
        body_style
    ))

    # ================= 2. ARCHITECTURE & TECH STACK =================
    story.append(Spacer(1, 10))
    story.append(Paragraph("2. System Architecture & Tech Stack", h1_style))
    
    stack_data = [
        [Paragraph("<b>Layer</b>", body_style), Paragraph("<b>Technology</b>", body_style), Paragraph("<b>Key Capability</b>", body_style)],
        [Paragraph("<b>Inference Engine</b>", body_style), Paragraph("Groq API (openai/gpt-oss-20b / Llama3)", body_style), Paragraph("Ultra-low latency streaming, 100% cost-effective cloud execution.", body_style)],
        [Paragraph("<b>Vector Storage</b>", body_style), Paragraph("ChromaDB + Custom Deterministic Embedding", body_style), Paragraph("Clause-level chunking, Cosine similarity, strict metadata filtering.", body_style)],
        [Paragraph("<b>Backend API</b>", body_style), Paragraph("FastAPI, SQLAlchemy, SQLite/PostgreSQL", body_style), Paragraph("Async SSE token streams, multi-tenant isolation, PBKDF2/JWT auth.", body_style)],
        [Paragraph("<b>Frontend UI</b>", body_style), Paragraph("Next.js 14, React, TailwindCSS, Lucide Icons", body_style), Paragraph("Enterprise dark UI, interactive citation drawer, persistent chat history.", body_style)],
    ]
    t_stack = Table(stack_data, colWidths=[100, 160, 240])
    t_stack.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), navy_primary),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('BOX', (0,0), (-1,-1), 0.5, border_color),
        ('INNERGRID', (0,0), (-1,-1), 0.5, border_color),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('PADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_stack)

    # ================= 3. CORE FEATURES IN SHORT =================
    story.append(Spacer(1, 15))
    story.append(Paragraph("3. Core Features in Short", h1_style))
    
    features = [
        ("Zero-Hallucination Grounding", "Every answer is synthesized strictly from retrieved policy documents. If the similarity score is below the threshold, the system triggers an automatic compliance referral to Legal & Compliance."),
        ("Interactive Verifiable Citations", "Direct clause citations (e.g. [Doc: Policy_2024, Clause: Sec. 4.2]) rendered as clickable badges that open a slide-out drawer showing page number, similarity score, and verbatim excerpt."),
        ("Multi-Tenant Branch Isolation", "Complete logical separation between bank branches/accounts. Relationship managers can never retrieve, query, or view another branch's internal policies."),
        ("Fast Groq Cloud LLM", "Integrated directly with Groq's high-speed inference engine, providing rapid streaming responses without requiring OpenAI credits or paid subscriptions."),
        ("Document Knowledge Base Store", "Allows branch admins to upload, parse, and vector-index PDFs, Word documents, and policy circulars with automatic chunking and metadata extraction."),
        ("Compliance Audit Trail", "Complete logging of queries, rewritten standalone queries, retrieved chunk IDs, similarity scores, latency, and refusal decisions for regulatory reporting."),
        ("Persistent Chat History", "Robust client-side session management preserving conversation context across page navigation between Advisory Chat and Document Store."),
        ("Role-Based Access Control (RBAC)", "Distinguishes between Relationship Managers (RMs - advisory queries) and Compliance Admins (document management, audit review, and deletion permissions)."),
    ]

    for title, desc in features:
        story.append(Paragraph(f"• <b>{title}:</b> {desc}", bullet_style))

    # ================= PAGE BREAK FOR TESTING & SECURITY =================
    story.append(PageBreak())

    # ================= 4. SECURITY & TEST ATTACK SUITE =================
    story.append(Paragraph("4. Security & Attack Simulation Verification", h1_style))
    story.append(Paragraph(
        "WealthGuard GAA features a dedicated, automated attack simulation and SLA verification test suite (`pytest`) designed to validate zero-hallucination compliance and multi-tenant security barriers under hostile conditions.",
        body_style
    ))

    test_matrix = [
        [Paragraph("<b>Attack Scenario / Test Category</b>", body_style), Paragraph("<b>Attack Vector / Methodology</b>", body_style), Paragraph("<b>Expected Defense Outcome</b>", body_style)],
        [
            Paragraph("<b>Cross-Tenant Breach</b>", body_style),
            Paragraph("User from Branch A requests private wealth policies stored in Branch B.", body_style),
            Paragraph("<font color='#10B981'><b>PASSED:</b></font> Vector query metadata filter restricts search exclusively to Branch A account_id.", body_style)
        ],
        [
            Paragraph("<b>Hallucination Injection</b>", body_style),
            Paragraph("Adversarial query asking for unverified tax exemption loopholes not in doc store.", body_style),
            Paragraph("<font color='#10B981'><b>PASSED:</b></font> Grounding threshold triggers Refusal Protocol; zero invented terms emitted.", body_style)
        ],
        [
            Paragraph("<b>Prompt Injection / Jailbreak</b>", body_style),
            Paragraph("Prefix instructions attempting to override system instructions and leak raw prompts.", body_style),
            Paragraph("<font color='#10B981'><b>PASSED:</b></font> LLM prompt isolation shields system guardrails and context structure.", body_style)
        ],
        [
            Paragraph("<b>Unauthorized Document Tamper</b>", body_style),
            Paragraph("RM role attempts to call DELETE /documents endpoint.", body_style),
            Paragraph("<font color='#10B981'><b>PASSED:</b></font> HTTP 403 Forbidden enforced via FastAPI RBAC dependency.", body_style)
        ],
    ]
    t_tests = Table(test_matrix, colWidths=[130, 180, 190])
    t_tests.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), navy_primary),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('BOX', (0,0), (-1,-1), 0.5, border_color),
        ('INNERGRID', (0,0), (-1,-1), 0.5, border_color),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('PADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_tests)

    # ================= 5. HOW TO RUN & TEST =================
    story.append(Spacer(1, 15))
    story.append(Paragraph("5. Step-by-Step Testing & Execution Guide", h1_style))

    story.append(Paragraph("Step 1: Backend Execution", h2_style))
    story.append(Paragraph("Navigate to the `backend/` directory, configure your `.env` file with your `GROQ_API_KEY`, and start the FastAPI ASGI server:", body_style))
    story.append(Paragraph("<code>cd backend<br/>python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload</code>", ParagraphStyle("CodeBox", fontName="Courier", fontSize=8.5, leading=12, backColor=slate_light, borderPadding=6, spaceAfter=6)))

    story.append(Paragraph("Step 2: Frontend Execution", h2_style))
    story.append(Paragraph("Navigate to the `frontend/` directory, install packages, and launch Next.js in development mode:", body_style))
    story.append(Paragraph("<code>cd frontend<br/>npm install<br/>npm run dev</code>", ParagraphStyle("CodeBox2", fontName="Courier", fontSize=8.5, leading=12, backColor=slate_light, borderPadding=6, spaceAfter=6)))

    story.append(Paragraph("Step 3: Running Automated Security & Unit Tests", h2_style))
    story.append(Paragraph("Execute the complete comprehensive automated test suite (including tenant attacks and SLA verification):", body_style))
    story.append(Paragraph("<code>cd backend<br/>python -m pytest tests/ -v</code>", ParagraphStyle("CodeBox3", fontName="Courier", fontSize=8.5, leading=12, backColor=slate_light, borderPadding=6, spaceAfter=6)))

    story.append(Spacer(1, 15))
    # Callout Box
    callout_data = [[
        Paragraph(
            "<b>Ready for Enterprise Production:</b> WealthGuard GAA delivers a complete compliance-hardened advisory interface. All OpenAI dependencies have been cleanly replaced with Groq API key support, and chat history persistence across the Document Store is verified and stable.",
            callout_style
        )
    ]]
    t_callout = Table(callout_data, colWidths=[500])
    t_callout.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#FEF3C7")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#F59E0B")),
        ('PADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(t_callout)

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"[SUCCESS] Generated PDF documentation: {filename}")

if __name__ == "__main__":
    out_pdf = "WealthGuard_GAA_Project_Report.pdf"
    if len(sys.argv) > 1:
        out_pdf = sys.argv[1]
    build_pdf(out_pdf)
