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
        self.is_connected = False
    
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
        
        logger.info(f"データソースに接続します: username={username}")
        success = self.data_source.connect(username, password)
        if success:
            self.is_connected = True
            logger.info("データソースへの接続に成功しました")
        else:
            logger.error("データソースへの接続に失敗しました")
        return success
    
    def ensure_connected(self) -> bool:
        """
        接続状態を確認し、必要に応じて再接続する
        
        Returns:
            bool: 接続済みまたは再接続成功時はTrue
        """
        if self.is_connected:
            logger.debug("データソースに既に接続されています")
            return True
        
        logger.info("データソースに接続されていません。再接続を試みます...")
        return self.connect()
    
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
        
        # 接続を確認・再接続
        if not self.ensure_connected():
            logger.error("データソースへの接続に失敗しました")
            return False
        
        # RHRデータを取得・保存
        rhr_success = self._fetch_and_save_rhr(start_date, end_date)
        
        # HRVデータを取得・保存
        hrv_success = self._fetch_and_save_hrv(start_date, end_date)
        
        # トレーニングデータを取得・保存
        training_success = self._fetch_and_save_training(start_date, end_date)
        
        overall_success = rhr_success and hrv_success and training_success
        if overall_success:
            logger.info("すべてのデータの取得・保存が完了しました")
        else:
            logger.error("一部のデータの取得・保存に失敗しました")
            
        return overall_success
    
    def _fetch_and_save_rhr(self, start_date: date, end_date: date) -> bool:
        """RHRデータを取得して保存する"""
        try:
            logger.info("RHRデータを取得しています...")
            rhr_data_dict = self.data_source.get_rhr_data(start_date, end_date)
            
            logger.info(f"{len(rhr_data_dict)}件のRHRデータを取得しました")
            
            # データの内容をサンプル表示（最初の3件）
            for i, data in enumerate(rhr_data_dict[:3]):
                logger.info(f"RHRデータサンプル{i+1}: {data}")
            
            # 辞書型からモデルに変換
            rhr_data = []
            for data in rhr_data_dict:
                try:
                    rhr_model = RHRData.from_dict(data)
                    # NULL値チェック
                    if rhr_model.rhr is None:
                        logger.warning(f"RHR値がNULLのデータがあります: {data}")
                    rhr_data.append(rhr_model)
                except Exception as e:
                    logger.error(f"RHRデータの変換中にエラーが発生しました: {str(e)}, データ: {data}")
            
            # 変換後のデータをサンプル表示
            for i, data in enumerate(rhr_data[:3]):
                logger.info(f"変換後のRHRデータサンプル{i+1}: date={data.date}, rhr={data.rhr}")
            
            logger.info("RHRデータを保存しています...")
            success = self.repository.save_rhr_data(rhr_data)
            
            if success:
                logger.info("RHRデータの保存が完了しました")
            else:
                logger.error("RHRデータの保存に失敗しました")
            
            return success
            
        except Exception as e:
            logger.error(f"RHRデータの取得・保存中にエラーが発生しました: {str(e)}", exc_info=True)
            return False
    
    def _fetch_and_save_hrv(self, start_date: date, end_date: date) -> bool:
        """HRVデータを取得して保存する"""
        try:
            logger.info("HRVデータを取得しています...")
            hrv_data_dict = self.data_source.get_hrv_data(start_date, end_date)
            
            logger.info(f"{len(hrv_data_dict)}件のHRVデータを取得しました")
            
            # データの内容をサンプル表示（最初の3件）
            for i, data in enumerate(hrv_data_dict[:3]):
                logger.info(f"HRVデータサンプル{i+1}: {data}")
            
            # 辞書型からモデルに変換
            hrv_data = []
            for data in hrv_data_dict:
                try:
                    hrv_model = HRVData.from_dict(data)
                    # NULL値チェック
                    if hrv_model.hrv is None:
                        logger.warning(f"HRV値がNULLのデータがあります: {data}")
                    hrv_data.append(hrv_model)
                except Exception as e:
                    logger.error(f"HRVデータの変換中にエラーが発生しました: {str(e)}, データ: {data}")
            
            # 変換後のデータをサンプル表示
            for i, data in enumerate(hrv_data[:3]):
                logger.info(f"変換後のHRVデータサンプル{i+1}: date={data.date}, hrv={data.hrv}")
            
            logger.info("HRVデータを保存しています...")
            success = self.repository.save_hrv_data(hrv_data)
            
            if success:
                logger.info("HRVデータの保存が完了しました")
            else:
                logger.error("HRVデータの保存に失敗しました")
            
            return success
            
        except Exception as e:
            logger.error(f"HRVデータの取得・保存中にエラーが発生しました: {str(e)}", exc_info=True)
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
                    try:
                        activity = Activity.from_dict(date_obj, activity_data)
                        activities.append(activity)
                    except Exception as e:
                        logger.error(f"アクティビティデータの変換中にエラーが発生しました: {str(e)}, データ: {activity_data}")
            
            logger.info(f"合計{len(activities)}件のアクティビティを抽出しました")
            
            # アクティビティデータのサンプル表示
            for i, activity in enumerate(activities[:3]):
                logger.info(f"アクティビティサンプル{i+1}: date={activity.date}, type={activity.activity_type}, is_l2={activity.is_l2_training}")
            
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
            logger.error(f"トレーニングデータの取得・保存中にエラーが発生しました: {str(e)}", exc_info=True)
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
        logger.info(f"{start_date}から{end_date}までの日別データを取得します")
        daily_data = self.repository.get_daily_data(start_date, end_date)
        logger.info(f"{len(daily_data)}件の日別データを取得しました")
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
        logger.info(f"{start_date}から{end_date}までの週別データを取得します")
        weekly_data = self.repository.get_weekly_data(start_date, end_date)
        logger.info(f"{len(weekly_data)}件の週別データを取得しました")
        return weekly_data