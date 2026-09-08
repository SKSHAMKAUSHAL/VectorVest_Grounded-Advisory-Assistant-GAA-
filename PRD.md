Product Requirement Document
Grounded Advisory Assistant — Wealth Management Division
Sprint #2 Deliverable · AI Application Development with RAG
Team Name: Team02 Project Name: Grounded Advisory Assistant (GAA) Team Members: Bhawana Kumari · Sksham Kaushal · Manvi Dadhwal

1. Business Problem Statement
Problem: The Wealth Management division's 60+ relationship managers (RMs) give investment advice by recalling investment policies, tax rules, and product brochures from memory or outdated local copies. These documents live across three disconnected repositories (Policy Wiki, Compliance SharePoint, Product Portal) with no single source of truth and no tool that grounds an RM's answer in the current, approved version of these materials. In Q2 internal audits, 22% of sampled client conversations contained advice that either cited superseded tax rules or referenced a discontinued product variant.
Goal: Deploy a retrieval-augmented generation (RAG) assistant that grounds every RM-facing answer in the current approved corpus, reducing policy/tax-rule misstatements to near zero and cutting the time RMs spend searching for the right clause or brochure section.
Primary Users: 60 relationship managers across 12 branches who need instant, cited answers during or before client meetings.
Success Criteria: ≥90% of sampled advisory answers pass a compliance grounding audit (cited to a current-version source) within 60 days of launch; RM document-lookup time reduced from an average of 14 minutes per query to ≤2 minutes.
✅ Specific · Quantified · Named users · Measurable success

2. Stakeholder Map
Type
Who
Role in this PRD
Primary Users
60 relationship managers (12 branches)
Ask natural-language questions before/during client meetings; need cited, current answers in ≤2 minutes
Secondary Users
8 branch compliance officers
Periodically audit RM conversations against the assistant's cited sources; need a "why did it say this" trace view
Data Owners
Compliance & Policy Documentation team (owns investment policy PDFs, tax circulars) + Product Marketing (owns brochures)
Must confirm document inventory, version-control process, and update cadence before ingestion is scoped
Approvers
Head of Wealth Management (business sign-off) + Chief Compliance Officer (regulatory sign-off) + Head of Data Platform (technical sign-off)
All three must approve before any client-facing pilot

Business Impact Justification:
Operational: RMs spend an estimated 14 min/query searching across three repositories; at ~6 queries/day per RM across 60 RMs, that is ~84 hours of lost productive time daily.
Compliance/Risk: 22% of sampled advisory conversations in the last audit cycle referenced outdated tax rules or discontinued products — a direct regulatory exposure (potential mis-selling findings).
Client Experience: Inconsistent answers across RMs erode client trust in the advisory relationship, particularly when two RMs give conflicting guidance on the same product.

3. Dataset & Data Source Documentation
Per the golden rule: no feature is planned around a field or document type that has not been personally confirmed to exist, in the correct format, with a known owner and refresh cadence.
Source
Format
Owner
Refresh Cadence
Status
Investment Policy Manual
PDF, ~340 pages, versioned (v4.2 current)
Compliance & Policy Documentation
Reviewed quarterly; ad-hoc amendments via circular
⚠️ Confirm version-control process — currently no single "latest" flag in SharePoint
Tax Rule Circulars
PDF/DOCX, ~90 individual circulars
Compliance & Policy Documentation
Issued ad-hoc (avg. 2–4/month), superseding prior circulars
⚠️ No supersession index exists — must be built or requested
Product Brochures
PDF, ~45 active products
Product Marketing
Updated on product relaunch (~quarterly)
✅ Verified — Product Portal has a "current version" API field
Discontinued Product Archive
PDF
Product Marketing
Static — updated when a product is sunset
✅ Verified — must be explicitly excluded from the retrieval index, not just deprioritized

Known data quality risks:
Tax circulars have no machine-readable "supersedes circular #X" field — this must be resolved manually or via a compliance-maintained index before ingestion, or the assistant risks retrieving outdated tax guidance and stating it as current.
Policy Manual page numbers shift between versions, so citations must reference section/clause IDs, not page numbers.
Golden rule check: Ingestion of tax circulars is blocked until Compliance confirms a supersession-tracking mechanism. This is documented as a risk in Section 8, not assumed away.

4. KPI & Success Metrics
Metric Name + Measurement Method + Numeric Target + Timeline
KPI
Method
Target
Timeline
Grounding Accuracy
Compliance officer audit of 100 sampled Q&A pairs against cited source document version
≥90% correctly grounded in current-version material
60 days post-launch
RM Adoption (DAU)
Application login/session logs
≥75% of 60 RMs (≥45 users) use the assistant at least once/day
30 days post-launch
Query Resolution Time
Pre/post time-tracking study (self-logged by 15 RM sample)
Reduce average lookup time from 14 min to ≤2 min
45 days post-launch
Citation Coverage
Automated check: % of generated answers containing at least one source citation
≥98% of answers include a verifiable citation
Launch day (hard gate)
Refusal Correctness
Manual review of 50 out-of-scope/ambiguous queries
≥95% of queries with no grounding evidence are correctly refused rather than answered speculatively
60 days post-launch


5. User Stories
As a [role], I want to [action], so that [business benefit].
US-01: As a relationship manager, I want to ask a natural-language question about a client's applicable tax treatment, so that I can give an answer grounded in the current circular during the client call instead of pausing to search three systems.
US-02: As a relationship manager, I want every answer to show the exact source document, version, and clause it was drawn from, so that I can show the client the underlying material and defend the advice in a compliance review.
US-03: As a relationship manager, I want the assistant to explicitly say when it cannot find grounding evidence for a question, so that I never repeat an unverified answer to a client.
US-04: As a compliance officer, I want to review a log of an RM's query, the retrieved sources, and the generated answer, so that I can audit advisory conversations without re-interviewing the RM.
US-05: As a compliance officer, I want discontinued products to be excluded from any answer unless explicitly asked about historical products, so that RMs are never nudged toward recommending a sunset product.
US-06: As an RM, I want to ask follow-up questions in the same conversation (e.g., "what about NRIs?") and have the assistant retain context, so that I don't have to restate the full question each time.

6. Feature Scope — v1.0
✅ In Scope
Natural-language Q&A over Investment Policy Manual, Tax Circulars, and active Product Brochures
Inline source citation (document name, version, clause/section ID) on every generated answer
Explicit refusal response when retrieval confidence is below threshold (no fabricated answers)
Conversational follow-up support within a single session (multi-turn context)
Compliance audit view: query, retrieved chunks, generated answer, timestamp
Exclusion of discontinued products from default retrieval scope
❌ Out of Scope — v1.0
Direct client-facing chat (v1 is internal, RM-facing only)
Automated regeneration/re-ingestion when a new circular is issued (manual re-index trigger for v1)
Multi-language support (English only)
Personalized client-portfolio integration (assistant answers policy/product questions, not "what should this specific client buy")
Mobile app (web/internal portal only)
Real-time streaming ingestion of new documents (batch re-index only)
Scope note: "Can we also connect it to client portfolio data so it gives personalized recommendations?" is a v2 request — it introduces suitability/advice-generation risk that requires separate compliance review and is explicitly deferred.

7. RAG Pipeline Architecture & Data Workflow
Ingestion: Policy Manual (PDF), Tax Circulars (PDF/DOCX), Product Brochures (PDF) pulled from SharePoint/Product Portal via scheduled batch job (weekly, or on-demand trigger by Compliance after a new circular is issued)
Processing: Text extraction → cleaning (remove headers/footers/watermarks) → chunking by clause/section boundary (not fixed token count alone) → metadata tagging (source doc, version, effective date, clause ID)
Embedding: Each chunk embedded via API; embeddings + metadata stored in vector database with document version and effective-date fields indexed for filtering
Retrieval: Top-K semantic retrieval + metadata filter to exclude superseded circulars and discontinued products; re-ranking step applied before context injection
Generation: Retrieved chunks injected into prompt with instruction to cite clause/document and to refuse if evidence is insufficient
Delivery: Internal web chat interface, streamed response with inline citations; compliance audit log written on every query

8. Risk Analysis
Risk
Likelihood
Impact
Mitigation
Assistant retrieves a superseded tax circular and presents it as current
Medium
High — direct compliance/regulatory exposure
Require effective-date + supersession metadata on every circular before ingestion; block launch until Compliance confirms this index exists
Model generates an answer not fully supported by retrieved chunks (hallucination)
Medium
High — RM repeats fabricated advice to a client
Enforce citation-required generation; run automated groundedness check on a sample of responses; refuse when retrieval confidence is low
Discontinued product resurfaces in an answer
Low
High — mis-selling risk
Hard metadata filter excluding discontinued archive from default retrieval scope; explicit test case in QA
RMs over-trust the tool and stop cross-checking with compliance for edge cases
Medium
Medium
Mandatory RM training on tool limitations at rollout; UI disclaimer on every answer: "Verify with Compliance for client-specific suitability"
Document re-index lag after a new circular is issued
Medium
Medium — stale answers between issue date and re-index
"Last indexed" timestamp shown in UI; Compliance-triggered manual re-index workflow with SLA of ≤24h
Vector DB metadata schema drifts as new document types are added
Low
Medium
Schema validation step in ingestion pipeline; change notifications to Data Platform


9. Validation Checklist (Pre-Submission)
[x] Business problem is specific and quantified with audit evidence (22% misstatement rate)
[x] Every KPI has a numeric target, method, and timeline
[x] All stakeholders named with roles and ownership
[x] Dataset ownership confirmed; open item (tax circular supersession index) flagged as a blocking risk, not assumed
[x] Every user story follows Role + Action + Business Benefit
[x] v1 scope explicitly bounded with an out-of-scope list
[x] Data workflow documented end-to-end, ingestion → generation → delivery
[x] Risks documented with likelihood, impact, and mitigation (including RAG-specific risks: hallucination, stale grounding, citation gaps)
[x] Free of aspirational, unmeasurable language
[ ] Stakeholder alignment review — pending sign-off from CCO and Head of Wealth Management
