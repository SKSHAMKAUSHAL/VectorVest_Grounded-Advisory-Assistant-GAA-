from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine, Base
from app.core.security import get_password_hash
from app.models.models import Account, User

def seed_database():
    """Seeds default multi-tenant accounts and demo users."""
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()

    try:
        # 1. Seed Accounts
        branch_central = db.query(Account).filter(Account.id == "branch_12_central").first()
        if not branch_central:
            branch_central = Account(
                id="branch_12_central",
                branch_name="Central Wealth Advisory Branch #12",
                branch_code="BR-CENTRAL-12",
            )
            db.add(branch_central)

        branch_north = db.query(Account).filter(Account.id == "branch_01_north").first()
        if not branch_north:
            branch_north = Account(
                id="branch_01_north",
                branch_name="North Regional Wealth Branch #01",
                branch_code="BR-NORTH-01",
            )
            db.add(branch_north)

        db.commit()

        # 2. Seed Users
        # RM 1 - Branch Central
        rm_user = db.query(User).filter(User.email == "rm@wealth.bank.com").first()
        if not rm_user:
            rm_user = User(
                id="usr_rm_sksham",
                account_id="branch_12_central",
                email="rm@wealth.bank.com",
                password_hash=get_password_hash("AdvisoryPass2024!"),
                full_name="Sksham Kaushal (Senior RM)",
                role="RM",
                is_active=True,
            )
            db.add(rm_user)

        # Compliance Officer - Branch Central
        compliance_user = db.query(User).filter(User.email == "compliance@wealth.bank.com").first()
        if not compliance_user:
            compliance_user = User(
                id="usr_comp_bhawana",
                account_id="branch_12_central",
                email="compliance@wealth.bank.com",
                password_hash=get_password_hash("AuditSecure2024!"),
                full_name="Bhawana Kumari (Compliance Officer)",
                role="ComplianceAdmin",
                is_active=True,
            )
            db.add(compliance_user)

        # RM 2 - Branch North (Isolated Tenant)
        rm_north = db.query(User).filter(User.email == "rm_north@wealth.bank.com").first()
        if not rm_north:
            rm_north = User(
                id="usr_rm_manvi",
                account_id="branch_01_north",
                email="rm_north@wealth.bank.com",
                password_hash=get_password_hash("NorthPass2024!"),
                full_name="Manvi Dadhwal (North RM)",
                role="RM",
                is_active=True,
            )
            db.add(rm_north)

        # 3. Seed Baseline Approved Banking Policies for Demo
        from datetime import date
        from app.models.models import Document
        from app.services.vector_store import vector_store
        from app.services.embedding import embedding_service

        doc1 = db.query(Document).filter(Document.id == "doc_tax_circ_02_2024").first()
        if not doc1:
            doc1 = Document(
                id="doc_tax_circ_02_2024",
                account_id="branch_12_central",
                uploaded_by=compliance_user.id,
                filename="Tax_Rule_Circular_02_2024.pdf",
                file_path="uploads/Tax_Rule_Circular_02_2024.pdf",
                doc_type="tax_circular",
                version="v2.1",
                effective_date=date(2024, 1, 1),
                is_discontinued=False,
                total_pages=12,
                total_chunks=2,
                status="indexed",
            )
            db.add(doc1)

        doc2 = db.query(Document).filter(Document.id == "doc_wealth_policy_2024").first()
        if not doc2:
            doc2 = Document(
                id="doc_wealth_policy_2024",
                account_id="branch_12_central",
                uploaded_by=compliance_user.id,
                filename="Wealth_Portfolio_Advisory_Policy_v1.pdf",
                file_path="uploads/Wealth_Portfolio_Advisory_Policy_v1.pdf",
                doc_type="policy",
                version="v1.0",
                effective_date=date(2024, 1, 1),
                is_discontinued=False,
                total_pages=8,
                total_chunks=1,
                status="indexed",
            )
            db.add(doc2)

        doc3 = db.query(Document).filter(Document.id == "doc_fund_900_notice").first()
        if not doc3:
            doc3 = Document(
                id="doc_fund_900_notice",
                account_id="branch_12_central",
                uploaded_by=compliance_user.id,
                filename="Discontinued_Fund_900_Notice.pdf",
                file_path="uploads/Discontinued_Fund_900_Notice.pdf",
                doc_type="product_circular",
                version="v1.0",
                effective_date=date(2023, 1, 1),
                is_discontinued=True,
                total_pages=2,
                total_chunks=1,
                status="indexed",
            )
            db.add(doc3)

        db.commit()

        # Seed Vector Chunks into ChromaDB for branch_12_central
        sample_chunks = [
            {
                "id": "chunk_seed_tax_01",
                "text": "Section 4.2.1 High Yield Debt Funds Tax Exemption: Under amended schedule 4, long-term capital gains on High-Yield Debt Funds shall be taxed at 10% without indexation for domestic resident individual accounts.",
                "metadata": {
                    "account_id": "branch_12_central",
                    "document_id": "doc_tax_circ_02_2024",
                    "document_name": "Tax_Rule_Circular_02_2024.pdf",
                    "document_version": "v2.1",
                    "doc_type": "tax_circular",
                    "clause_id": "Section 4.2.1",
                    "page_number": 6,
                    "chunk_index": 0,
                    "is_discontinued": False,
                    "effective_date": "2024-01-01",
                },
            },
            {
                "id": "chunk_seed_tax_02",
                "text": "Section 4.2.2 Tax and policy treatment for Non-Resident Indian (NRI) clients: Approved tax and policy treatment for Non-Resident Indian (NRI) clients under Schedule 4: witholding at source is fixed at 15% with double tax treaty credits applicable.",
                "metadata": {
                    "account_id": "branch_12_central",
                    "document_id": "doc_tax_circ_02_2024",
                    "document_name": "Tax_Rule_Circular_02_2024.pdf",
                    "document_version": "v2.1",
                    "doc_type": "tax_circular",
                    "clause_id": "Section 4.2.2",
                    "page_number": 7,
                    "chunk_index": 1,
                    "is_discontinued": False,
                    "effective_date": "2024-01-01",
                },
            },
            {
                "id": "chunk_seed_wealth_01",
                "text": "Section 2.1 KYC and Accredited Investor Thresholds: Relationship Managers must ensure clients maintain a minimum liquid net worth of $250,000 to qualify for Tier 1 wealth advisory portfolios. Verification must be renewed every 24 months.",
                "metadata": {
                    "account_id": "branch_12_central",
                    "document_id": "doc_wealth_policy_2024",
                    "document_name": "Wealth_Portfolio_Advisory_Policy_v1.pdf",
                    "document_version": "v1.0",
                    "doc_type": "policy",
                    "clause_id": "Section 2.1",
                    "page_number": 3,
                    "chunk_index": 0,
                    "is_discontinued": False,
                    "effective_date": "2024-01-01",
                },
            },
            {
                "id": "chunk_seed_fund900_01",
                "text": "Section 9.0 Discontinued Fund Status: Global Alpha Fund 900 was officially discontinued effective January 1, 2023. No further subscriptions or top-ups are permitted for any client tier.",
                "metadata": {
                    "account_id": "branch_12_central",
                    "document_id": "doc_fund_900_notice",
                    "document_name": "Discontinued_Fund_900_Notice.pdf",
                    "document_version": "v1.0",
                    "doc_type": "product_circular",
                    "clause_id": "Section 9.0",
                    "page_number": 1,
                    "chunk_index": 0,
                    "is_discontinued": True,
                    "effective_date": "2023-01-01",
                },
            },
        ]

        # Calculate embeddings and add to vector store
        embeddings = [embedding_service.get_embedding(c["text"]) for c in sample_chunks]
        vector_store.collection.upsert(
            ids=[c["id"] for c in sample_chunks],
            documents=[c["text"] for c in sample_chunks],
            metadatas=[c["metadata"] for c in sample_chunks],
            embeddings=embeddings,
        )

        print("Database seeding completed successfully.")
        print(f"- Seeded Tenant: branch_12_central ({branch_central.branch_name})")
        print(f"- Seeded Tenant: branch_01_north ({branch_north.branch_name})")
        print("- Seeded RM: rm@wealth.bank.com / AdvisoryPass2024!")
        print("- Seeded Compliance: compliance@wealth.bank.com / AuditSecure2024!")
        print("- Seeded North RM: rm_north@wealth.bank.com / NorthPass2024!")
        print(f"- Seeded {len(sample_chunks)} baseline policy chunks into vector store.")

    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
