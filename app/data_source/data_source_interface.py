from abc import ABC, abstractmethod
from datetime import date
from typing import Dict, List, Any, Optional

class DataSourceInterface(ABC):
    """
    データソースの抽象インターフェース
    外部APIへの依存を抽象化し、テストやモックが容易になるようにする
    """
    
    @abstractmethod
    def connect(self, username: str, password: str) -> bool:
        """
        データソースへの接続を確立する
        
        Args:
            username: アカウントのユーザー名
            password: アカウントのパスワード
            
        Returns:
            bool: 接続成功時はTrue、失敗時はFalse
        """
        pass
    
    @abstractmethod
    def get_rhr_data(self, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """
        指定された期間の安静時心拍数(RHR)データを取得する
        
        Args:
            start_date: データ取得開始日
            end_date: データ取得終了日
            
        Returns:
            List[Dict[str, Any]]: 日付ごとのRHRデータのリスト
            例: [{'date': '2023-01-01', 'rhr': 55}, ...]
        """
        pass
    
    @abstractmethod
    def get_hrv_data(self, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """
        指定された期間の心拍変動(HRV)データを取得する
        
        Args:
            start_date: データ取得開始日
            end_date: データ取得終了日
            
        Returns:
            List[Dict[str, Any]]: 日付ごとのHRVデータのリスト
            例: [{'date': '2023-01-01', 'hrv': 67}, ...]
        """
        pass
    
    @abstractmethod
    def get_training_data(self, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """
        指定された期間のトレーニングデータを取得する
        
        Args:
            start_date: データ取得開始日
            end_date: データ取得終了日
            
        Returns:
            List[Dict[str, Any]]: 日付ごとのトレーニングデータのリスト
            例: [{'date': '2023-01-01', 'activity_type': 'cycling', 'duration': 3600, 'intensity': 'L2'}, ...]
        """
        pass