from sqlalchemy import Column, Integer, String, Date
from database import Base
from sqlalchemy.orm import Session
from datetime import date, timedelta

class RejectedAd(Base):
    __tablename__ = "rejected_ads"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date)
    team = Column(String)
    campaign = Column(String)
    ad_name = Column(String)
    reasons = Column(String)

def get_yesterday_rejections(db: Session, team: str):
    yesterday = date.today() - timedelta(days=1)
    return db.query(RejectedAd).filter(
        RejectedAd.date == yesterday,
        RejectedAd.team == team
    ).all()

def compare_rejections(today_data, yesterday_data):
    today_set = set((item.campaign, item.ad_name, item.reasons) for item in today_data)
    yesterday_set = set((item.campaign, item.ad_name, item.reasons) for item in yesterday_data)

    new_rejections = today_set - yesterday_set
    resolved_rejections = yesterday_set - today_set

    return {
        "new": list(new_rejections),
        "resolved": list(resolved_rejections)
    }