import logging
from datetime import date, datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from app.repository.repository_interface import RepositoryInterface
from app.models.models import RHRData, HRVData, Activity, DailyData, WeeklyData
from app.models.database_models import RHRRecord, HRVRecord, ActivityRecord

logger = logging.getLogger(__name__)

class SQLiteRepository(RepositoryInterface):
    """
    SQLiteを使用したリポジトリの実装
    """
    
    def __init__(self, session_factory):
        """
        コンストラクタ
        
        Args:
            session_factory: SQLAlchemy セッションファクトリ
        """
        self.session_factory = session_factory
    
    def save_rhr_data(self, rhr_data: List[RHRData]) -> bool:
        """
        RHRデータを保存する
        
        Args:
            rhr_data: 保存するRHRデータのリスト
            
        Returns:
            bool: 保存成功時はTrue
        """
        try:
            with self.session_factory() as session:
                for data in rhr_data:
                    if data.rhr is None:
                        continue
                    
                    # 既存レコードを検索
                    existing = session.query(RHRRecord).filter(
                        RHRRecord.date == data.date.date()
                    ).first()
                    
                    if existing:
                        # 既存レコードを更新
                        existing.rhr = data.rhr
                    else:
                        # 新規レコードを作成
                        record = RHRRecord(
                            date=data.date.date(),
                            rhr=data.rhr
                        )
                        session.add(record)
                
                session.commit()
            return True
        
        except Exception as e:
            logger.error(f"RHRデータ保存中にエラーが発生しました: {str(e)}")
            return False
    
    def save_hrv_data(self, hrv_data: List[HRVData]) -> bool:
        """
        HRVデータを保存する
        
        Args:
            hrv_data: 保存するHRVデータのリスト
            
        Returns:
            bool: 保存成功時はTrue
        """
        try:
            with self.session_factory() as session:
                for data in hrv_data:
                    if data.hrv is None:
                        continue
                    
                    # 既存レコードを検索
                    existing = session.query(HRVRecord).filter(
                        HRVRecord.date == data.date.date()
                    ).first()
                    
                    if existing:
                        # 既存レコードを更新
                        existing.hrv = data.hrv
                    else:
                        # 新規レコードを作成
                        record = HRVRecord(
                            date=data.date.date(),
                            hrv=data.hrv
                        )
                        session.add(record)
                
                session.commit()
            return True
        
        except Exception as e:
            logger.error(f"HRVデータ保存中にエラーが発生しました: {str(e)}")
            return False
    
    def save_activities(self, activities: List[Activity]) -> bool:
        """
        アクティビティデータを保存する
        
        Args:
            activities: 保存するアクティビティのリスト
            
        Returns:
            bool: 保存成功時はTrue
        """
        try:
            with self.session_factory() as session:
                for activity in activities:
                    # 既存レコードを検索
                    existing = session.query(ActivityRecord).filter(
                        ActivityRecord.activity_id == activity.activity_id
                    ).first()
                    
                    if existing:
                        # 既存レコードを更新
                        existing.date = activity.date.date()
                        existing.activity_type = activity.activity_type
                        existing.start_time = activity.start_time
                        existing.duration = activity.duration
                        existing.distance = activity.distance
                        existing.is_l2_training = activity.is_l2_training
                        existing.intensity = activity.intensity
                    else:
                        # 新規レコードを作成
                        record = ActivityRecord(
                            activity_id=activity.activity_id,
                            date=activity.date.date(),
                            activity_type=activity.activity_type,
                            start_time=activity.start_time,
                            duration=activity.duration,
                            distance=activity.distance,
                            is_l2_training=activity.is_l2_training,
                            intensity=activity.intensity
                        )
                        session.add(record)
                
                session.commit()
            return True
        
        except Exception as e:
            logger.error(f"アクティビティデータ保存中にエラーが発生しました: {str(e)}")
            return False
    
    def get_rhr_data(self, start_date: date, end_date: date) -> List[RHRData]:
        """
        指定期間のRHRデータを取得する
        
        Args:
            start_date: 開始日
            end_date: 終了日
            
        Returns:
            List[RHRData]: RHRデータのリスト
        """
        try:
            with self.session_factory() as session:
                records = session.query(RHRRecord).filter(
                    RHRRecord.date >= start_date,
                    RHRRecord.date <= end_date
                ).order_by(RHRRecord.date).all()
                
                return [
                    RHRData(
                        date=datetime.combine(record.date, datetime.min.time()),
                        rhr=record.rhr
                    )
                    for record in records
                ]
        
        except Exception as e:
            logger.error(f"RHRデータ取得中にエラーが発生しました: {str(e)}")
            return []
    
    def get_hrv_data(self, start_date: date, end_date: date) -> List[HRVData]:
        """
        指定期間のHRVデータを取得する
        
        Args:
            start_date: 開始日
            end_date: 終了日
            
        Returns:
            List[HRVData]: HRVデータのリスト
        """
        try:
            with self.session_factory() as session:
                records = session.query(HRVRecord).filter(
                    HRVRecord.date >= start_date,
                    HRVRecord.date <= end_date
                ).order_by(HRVRecord.date).all()
                
                return [
                    HRVData(
                        date=datetime.combine(record.date, datetime.min.time()),
                        hrv=record.hrv
                    )
                    for record in records
                ]
        
        except Exception as e:
            logger.error(f"HRVデータ取得中にエラーが発生しました: {str(e)}")
            return []
    
    def get_activities(self, start_date: date, end_date: date) -> List[Activity]:
        """
        指定期間のアクティビティを取得する
        
        Args:
            start_date: 開始日
            end_date: 終了日
            
        Returns:
            List[Activity]: アクティビティのリスト
        """
        try:
            with self.session_factory() as session:
                records = session.query(ActivityRecord).filter(
                    ActivityRecord.date >= start_date,
                    ActivityRecord.date <= end_date
                ).order_by(ActivityRecord.date, ActivityRecord.start_time).all()
                
                return [
                    Activity(
                        activity_id=record.activity_id,
                        date=datetime.combine(record.date, datetime.min.time()),
                        activity_type=record.activity_type,
                        start_time=record.start_time,
                        duration=record.duration,
                        distance=record.distance,
                        is_l2_training=record.is_l2_training,
                        intensity=record.intensity
                    )
                    for record in records
                ]
        
        except Exception as e:
            logger.error(f"アクティビティデータ取得中にエラーが発生しました: {str(e)}")
            return []
    
    def get_daily_data(self, start_date: date, end_date: date) -> List[DailyData]:
        """
        指定期間の日別データを取得する
        
        Args:
            start_date: 開始日
            end_date: 終了日
            
        Returns:
            List[DailyData]: 日別データのリスト
        """
        # RHRデータを取得
        rhr_data = {data.date.date(): data.rhr for data in self.get_rhr_data(start_date, end_date)}
        
        # HRVデータを取得
        hrv_data = {data.date.date(): data.hrv for data in self.get_hrv_data(start_date, end_date)}
        
        # アクティビティを取得
        activities = self.get_activities(start_date, end_date)
        
        # アクティビティを日付ごとにグループ化
        activities_by_date = {}
        for activity in activities:
            date_key = activity.date.date()
            if date_key not in activities_by_date:
                activities_by_date[date_key] = []
            activities_by_date[date_key].append(activity)
        
        # 日別データを構築
        daily_data = []
        current_date = start_date
        while current_date <= end_date:
            date_obj = datetime.combine(current_date, datetime.min.time())
            daily = DailyData(
                date=date_obj,
                rhr=rhr_data.get(current_date),
                hrv=hrv_data.get(current_date),
                activities=activities_by_date.get(current_date, [])
            )
            daily_data.append(daily)
            current_date += timedelta(days=1)
        
        return daily_data
    
    def get_weekly_data(self, start_date: date, end_date: date) -> List[WeeklyData]:
        """
        指定期間の週別データを取得する
        
        Args:
            start_date: 開始日
            end_date: 終了日
            
        Returns:
            List[WeeklyData]: 週別データのリスト
        """
        # 日別データを取得
        daily_data = self.get_daily_data(start_date, end_date)
        
        # 週の開始日（月曜日）に揃える
        first_date = daily_data[0].date
        days_to_subtract = first_date.weekday()
        aligned_start = first_date - timedelta(days=days_to_subtract)
        
        # 週別データのリストを構築
        weekly_data = []
        current_week_start = aligned_start
        
        while current_week_start <= daily_data[-1].date:
            current_week_end = current_week_start + timedelta(days=6)
            
            # この週のデータを抽出
            week_data = [
                d for d in daily_data
                if current_week_start <= d.date <= current_week_end
            ]
            
            if week_data:
                weekly = WeeklyData(
                    start_date=current_week_start,
                    end_date=current_week_end,
                    daily_data=week_data
                )
                weekly_data.append(weekly)
            
            current_week_start += timedelta(days=7)
        
        return weekly_data