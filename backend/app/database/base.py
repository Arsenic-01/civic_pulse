from sqlalchemy.orm import declarative_base

Base = declarative_base()

# Import all models here so SQLAlchemy registers them automatically
def import_models():
    from app.models.user import UserModel
    from app.models.protest import ProtestModel, ProtestStatusHistoryModel
    from app.models.report import VolunteerApplicationModel, VolunteerReportModel
    from app.models.evidence import EvidenceModel
    from app.models.subscription import EventSubscriptionModel
    from app.models.notification import NotificationModel, AuditLogModel