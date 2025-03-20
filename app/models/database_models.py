from sqlalchemy import Column, Integer, Float, String, Boolean, Date, DateTime, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
import os
from datetime import datetime

# データベースのベースクラス
Base = declarative_base()

class RHRRecord(Base):
    """安静時心拍数のデータベースモデル"""
    __tablename__ = 'rhr_records'
    
    id = Column(Integer, primary_key=True)
    date = Column(Date, unique=True, index=True, nullable=False)
    rhr = Column(Integer)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

class HRVRecord(Base):
    """心拍変動のデータベースモデル"""
    __tablename__ = 'hrv_records'
    
    id = Column(Integer, primary_key=True)
    date = Column(Date, unique=True, index=True, nullable=False)
    hrv = Column(Float)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

class ActivityRecord(Base):
    """アクティビティのデータベースモデル"""
    __tablename__ = 'activity_records'
    
    id = Column(Integer, primary_key=True)
    activity_id = Column(String, unique=True, index=True, nullable=False)
    date = Column(Date, index=True, nullable=False)
    activity_type = Column(String, nullable=False)
    start_time = Column(DateTime, nullable=False)
    duration = Column(Float, nullable=False)  # 秒単位
    distance = Column(Float)  # メートル単位
    is_l2_training = Column(Boolean, default=False)
    intensity = Column(String, default='Other')
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

# データベース初期化関数
def init_db(db_path='sqlite:///data/garmin_data.db'):
    """
    データベースを初期化し、接続セッションを返す
    
    Args:
        db_path: データベースファイルのパス
    
    Returns:
        tuple: (engine, sessionmaker)
    """
    engine = create_engine(db_path)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return engine, Session