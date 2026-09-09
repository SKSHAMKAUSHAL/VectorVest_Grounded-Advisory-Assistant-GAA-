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

        db.commit()
        print("Database seeding completed successfully.")
        print(f"- Seeded Tenant: branch_12_central ({branch_central.branch_name})")
        print(f"- Seeded Tenant: branch_01_north ({branch_north.branch_name})")
        print("- Seeded RM: rm@wealth.bank.com / AdvisoryPass2024!")
        print("- Seeded Compliance: compliance@wealth.bank.com / AuditSecure2024!")
        print("- Seeded North RM: rm_north@wealth.bank.com / NorthPass2024!")

    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
