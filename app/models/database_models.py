from sqlalchemy import Column, Integer, Float, String, Boolean, Date, DateTime, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# データベースのベースクラス
Base = declarative_base()

class RHRRecord(Base):
    """安静時心拍数のデータベースモデル"""
    __tablename__ = 'rhr_records'
    
    id = Column(Integer, primary_key=True)
    date = Column(Date, unique=True, index=True, nullable=False)
    rhr = Column(Integer, nullable=True)  # NULL許容に変更
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

class HRVRecord(Base):
    """心拍変動のデータベースモデル"""
    __tablename__ = 'hrv_records'
    
    id = Column(Integer, primary_key=True)
    date = Column(Date, unique=True, index=True, nullable=False)
    hrv = Column(Float, nullable=True)  # NULL許容に変更
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
    distance = Column(Float, nullable=True)  # メートル単位
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
    try:
        logger.info(f"データベースを初期化します: {db_path}")
        
        # データディレクトリの存在確認と作成
        if db_path.startswith('sqlite:///'):
            db_file = db_path[len('sqlite:///'):]
            db_dir = os.path.dirname(db_file)
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir)
                logger.info(f"データディレクトリを作成しました: {db_dir}")
        
        engine = create_engine(db_path)
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        
        logger.info("データベースの初期化が完了しました")
        return engine, Session
    except Exception as e:
        logger.error(f"データベースの初期化中にエラーが発生しました: {str(e)}", exc_info=True)
        raise