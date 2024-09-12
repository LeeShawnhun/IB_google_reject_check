from sqlalchemy import Column, Integer, String, Date
from database import Base

class RejectedAd(Base):
    __tablename__ = "rejected_ads"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date)
    campaign = Column(String)
    ad_name = Column(String)
    reasons = Column(String)