import logging
import os
from datetime import date, datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple

from app.data_source.data_source_interface import DataSourceInterface
from app.data_source.data_source_factory import DataSourceFactory
from app.repository.repository_interface import RepositoryInterface
from app.repository.repository_factory import RepositoryFactory
from app.models.models import RHRData, HRVData, Activity, DailyData, WeeklyData

logger = logging.getLogger(__name__)

class DataService:
    """
    データ取得・保存のためのサービスクラス
    """
    
    def __init__(self, 
                 data_source: Optional[DataSourceInterface] = None,
                 repository: Optional[RepositoryInterface] = None):
        """
        コンストラクタ
        
        Args:
            data_source: データソース（指定しない場合はファクトリーから取得）
            repository: リポジトリ（指定しない場合はファクトリーから取得）
        """
        self.data_source = data_source or DataSourceFactory.create_data_source()
        self.repository = repository or RepositoryFactory.create_repository()
    
    def connect(self) -> bool:
        """
        データソースに接続する
        
        Returns:
            bool: 接続成功時はTrue
        """
        username = os.environ.get('GARMIN_USERNAME')
        password = os.environ.get('GARMIN_PASSWORD')
        
        if not username or not password:
            logger.error("環境変数 GARMIN_USERNAME および GARMIN_PASSWORD が設定されていません")
            return False
        
        return self.data_source.connect(username, password)
    
    def fetch_and_save_data(self, start_date: date, end_date: date) -> bool:
        """
        指定期間のデータを取得し、保存する
        
        Args:
            start_date: 開始日
            end_date: 終了日
            
        Returns:
            bool: 処理成功時はTrue
        """
        logger.info(f"{start_date}から{end_date}までのデータを取得します")
        
        # RHRデータを取得・保存
        rhr_success = self._fetch_and_save_rhr(start_date, end_date)
        
        # HRVデータを取得・保存
        hrv_success = self._fetch_and_save_hrv(start_date, end_date)
        
        # トレーニングデータを取得・保存
        training_success = self._fetch_and_save_training(start_date, end_date)
        
        return rhr_success and hrv_success and training_success
    
    def _fetch_and_save_rhr(self, start_date: date, end_date: date) -> bool:
        """RHRデータを取得して保存する"""
        try:
            logger.info("RHRデータを取得しています...")
            rhr_data_dict = self.data_source.get_rhr_data(start_date, end_date)
            
            logger.info(f"{len(rhr_data_dict)}件のRHRデータを取得しました")
            
            # 辞書型からモデルに変換
            rhr_data = [RHRData.from_dict(data) for data in rhr_data_dict]
            
            logger.info("RHRデータを保存しています...")
            success = self.repository.save_rhr_data(rhr_data)
            
            if success:
                logger.info("RHRデータの保存が完了しました")
            else:
                logger.error("RHRデータの保存に失敗しました")
            
            return success
            
        except Exception as e:
            logger.error(f"RHRデータの取得・保存中にエラーが発生しました: {str(e)}")
            return False
    
    def _fetch_and_save_hrv(self, start_date: date, end_date: date) -> bool:
        """HRVデータを取得して保存する"""
        try:
            logger.info("HRVデータを取得しています...")
            hrv_data_dict = self.data_source.get_hrv_data(start_date, end_date)
            
            logger.info(f"{len(hrv_data_dict)}件のHRVデータを取得しました")
            
            # 辞書型からモデルに変換
            hrv_data = [HRVData.from_dict(data) for data in hrv_data_dict]
            
            logger.info("HRVデータを保存しています...")
            success = self.repository.save_hrv_data(hrv_data)
            
            if success:
                logger.info("HRVデータの保存が完了しました")
            else:
                logger.error("HRVデータの保存に失敗しました")
            
            return success
            
        except Exception as e:
            logger.error(f"HRVデータの取得・保存中にエラーが発生しました: {str(e)}")
            return False
    
    def _fetch_and_save_training(self, start_date: date, end_date: date) -> bool:
        """トレーニングデータを取得して保存する"""
        try:
            logger.info("トレーニングデータを取得しています...")
            training_data_dict = self.data_source.get_training_data(start_date, end_date)
            
            logger.info(f"{len(training_data_dict)}件の日別トレーニングデータを取得しました")
            
            # アクティビティリストに変換
            activities = []
            for day_data in training_data_dict:
                date_obj = datetime.fromisoformat(day_data['date']) if isinstance(day_data['date'], str) else day_data['date']
                
                for activity_data in day_data.get('activities', []):
                    activity = Activity.from_dict(date_obj, activity_data)
                    activities.append(activity)
            
            logger.info(f"合計{len(activities)}件のアクティビティを抽出しました")
            
            if activities:
                logger.info("トレーニングデータを保存しています...")
                success = self.repository.save_activities(activities)
                
                if success:
                    logger.info("トレーニングデータの保存が完了しました")
                else:
                    logger.error("トレーニングデータの保存に失敗しました")
                
                return success
            else:
                logger.info("保存するトレーニングデータがありませんでした")
                return True
            
        except Exception as e:
            logger.error(f"トレーニングデータの取得・保存中にエラーが発生しました: {str(e)}")
            return False
    
    def get_daily_data(self, start_date: date, end_date: date) -> List[DailyData]:
        """
        指定期間の日別データを取得する
        
        Args:
            start_date: 開始日
            end_date: 終了日
            
        Returns:
            List[DailyData]: 日別データのリスト
        """
        return self.repository.get_daily_data(start_date, end_date)
    
    def get_weekly_data(self, start_date: date, end_date: date) -> List[WeeklyData]:
        """
        指定期間の週別データを取得する
        
        Args:
            start_date: 開始日
            end_date: 終了日
            
        Returns:
            List[WeeklyData]: 週別データのリスト
        """
        return self.repository.get_weekly_data(start_date, end_date)