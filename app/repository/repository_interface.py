from abc import ABC, abstractmethod
from datetime import date, datetime
from typing import List, Optional, Dict, Any

from app.models.models import RHRData, HRVData, Activity, DailyData, WeeklyData

class RepositoryInterface(ABC):
    """
    データ永続化のための抽象インターフェース
    """
    
    @abstractmethod
    def save_rhr_data(self, rhr_data: List[RHRData]) -> bool:
        """
        RHRデータを保存する
        
        Args:
            rhr_data: 保存するRHRデータのリスト
            
        Returns:
            bool: 保存成功時はTrue
        """
        pass
    
    @abstractmethod
    def save_hrv_data(self, hrv_data: List[HRVData]) -> bool:
        """
        HRVデータを保存する
        
        Args:
            hrv_data: 保存するHRVデータのリスト
            
        Returns:
            bool: 保存成功時はTrue
        """
        pass
    
    @abstractmethod
    def save_activities(self, activities: List[Activity]) -> bool:
        """
        アクティビティデータを保存する
        
        Args:
            activities: 保存するアクティビティのリスト
            
        Returns:
            bool: 保存成功時はTrue
        """
        pass
    
    @abstractmethod
    def get_rhr_data(self, start_date: date, end_date: date) -> List[RHRData]:
        """
        指定期間のRHRデータを取得する
        
        Args:
            start_date: 開始日
            end_date: 終了日
            
        Returns:
            List[RHRData]: RHRデータのリスト
        """
        pass
    
    @abstractmethod
    def get_hrv_data(self, start_date: date, end_date: date) -> List[HRVData]:
        """
        指定期間のHRVデータを取得する
        
        Args:
            start_date: 開始日
            end_date: 終了日
            
        Returns:
            List[HRVData]: HRVデータのリスト
        """
        pass
    
    @abstractmethod
    def get_activities(self, start_date: date, end_date: date) -> List[Activity]:
        """
        指定期間のアクティビティを取得する
        
        Args:
            start_date: 開始日
            end_date: 終了日
            
        Returns:
            List[Activity]: アクティビティのリスト
        """
        pass
    
    @abstractmethod
    def get_daily_data(self, start_date: date, end_date: date) -> List[DailyData]:
        """
        指定期間の日別データを取得する
        
        Args:
            start_date: 開始日
            end_date: 終了日
            
        Returns:
            List[DailyData]: 日別データのリスト
        """
        pass
    
    @abstractmethod
    def get_weekly_data(self, start_date: date, end_date: date) -> List[WeeklyData]:
        """
        指定期間の週別データを取得する
        
        Args:
            start_date: 開始日
            end_date: 終了日
            
        Returns:
            List[WeeklyData]: 週別データのリスト
        """
        pass