import time
import logging
from datetime import date, datetime, timedelta
from typing import Dict, List, Any, Optional

from garminconnect import Garmin

from app.data_source.data_source_interface import DataSourceInterface

logger = logging.getLogger(__name__)

class GarminDataSource(DataSourceInterface):
    """
    Garmin Connect APIを使用してデータを取得するデータソース実装
    """
    
    def __init__(self):
        self.client = None
        self.is_connected = False
        self.request_delay = 1.0  # API呼び出し間の待機時間（秒）
    
    def connect(self, username: str, password: str) -> bool:
        """
        Garmin Connect APIに接続する
        
        Args:
            username: Garminアカウントのユーザー名
            password: Garminアカウントのパスワード
            
        Returns:
            bool: 接続成功時はTrue、失敗時はFalse
        """
        try:
            self.client = Garmin(username, password)
            self.client.login()
            self.is_connected = True
            return True
        except Exception as e:
            logger.error(f"Garmin Connect APIへの接続に失敗しました: {str(e)}")
            self.is_connected = False
            return False
    
    def _check_connection(self):
        """接続状態を確認し、未接続の場合は例外を発生させる"""
        if not self.is_connected or self.client is None:
            raise ConnectionError("Garmin Connect APIに接続されていません。connect()メソッドを先に呼び出してください。")
    
    def _delay_request(self):
        """API制限を回避するための待機時間"""
        time.sleep(self.request_delay)
    
    def get_rhr_data(self, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """
        指定された期間の安静時心拍数(RHR)データを取得する
        
        Args:
            start_date: データ取得開始日
            end_date: データ取得終了日
            
        Returns:
            List[Dict[str, Any]]: 日付ごとのRHRデータのリスト
        """
        self._check_connection()
        
        results = []
        current_date = start_date
        
        while current_date <= end_date:
            try:
                logger.info(f"取得中: {current_date} のRHRデータ")
                rhr_data = self.client.get_rhr_day(current_date.isoformat())
                
                # データを整形
                if rhr_data and 'restingHeartRate' in rhr_data:
                    results.append({
                        'date': current_date.isoformat(),
                        'rhr': rhr_data['restingHeartRate']
                    })
                else:
                    # データがない場合は日付のみ記録
                    results.append({
                        'date': current_date.isoformat(),
                        'rhr': None
                    })
                
                self._delay_request()
                
            except Exception as e:
                logger.error(f"{current_date}のRHRデータ取得中にエラーが発生しました: {str(e)}")
                results.append({
                    'date': current_date.isoformat(),
                    'rhr': None
                })
            
            current_date += timedelta(days=1)
        
        return results
    
    def get_hrv_data(self, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """
        指定された期間の心拍変動(HRV)データを取得する
        
        Args:
            start_date: データ取得開始日
            end_date: データ取得終了日
            
        Returns:
            List[Dict[str, Any]]: 日付ごとのHRVデータのリスト
        """
        self._check_connection()
        
        results = []
        current_date = start_date
        
        while current_date <= end_date:
            try:
                logger.info(f"取得中: {current_date} のHRVデータ")
                stats = self.client.get_stats(current_date.isoformat())
                
                # HRVデータを抽出（APIの仕様に依存する）
                if stats and 'hrv' in stats and 'avgHRV' in stats['hrv']:
                    results.append({
                        'date': current_date.isoformat(),
                        'hrv': stats['hrv']['avgHRV']
                    })
                else:
                    # データがない場合は日付のみ記録
                    results.append({
                        'date': current_date.isoformat(),
                        'hrv': None
                    })
                
                self._delay_request()
                
            except Exception as e:
                logger.error(f"{current_date}のHRVデータ取得中にエラーが発生しました: {str(e)}")
                results.append({
                    'date': current_date.isoformat(),
                    'hrv': None
                })
            
            current_date += timedelta(days=1)
        
        return results
    
    def get_training_data(self, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """
        指定された期間のトレーニングデータを取得する
        
        Args:
            start_date: データ取得開始日
            end_date: データ取得終了日
            
        Returns:
            List[Dict[str, Any]]: 日付ごとのトレーニングデータのリスト
        """
        self._check_connection()
        
        results = []
        current_date = start_date
        
        while current_date <= end_date:
            try:
                logger.info(f"取得中: {current_date} のアクティビティデータ")
                activities = self.client.get_activities_by_date(
                    current_date.isoformat(), 
                    current_date.isoformat()
                )
                
                # 各アクティビティを処理
                daily_activities = []
                for activity in activities:
                    # L2トレーニングの判定（心拍ゾーンに基づく）
                    is_l2 = self._is_l2_training(activity)
                    
                    activity_data = {
                        'activity_id': activity.get('activityId'),
                        'activity_type': activity.get('activityType', {}).get('typeKey'),
                        'start_time': activity.get('startTimeLocal'),
                        'duration': activity.get('duration'),  # 秒単位
                        'distance': activity.get('distance'),
                        'is_l2_training': is_l2,
                        'intensity': 'L2' if is_l2 else 'Other'
                    }
                    
                    daily_activities.append(activity_data)
                
                results.append({
                    'date': current_date.isoformat(),
                    'activities': daily_activities
                })
                
                self._delay_request()
                
            except Exception as e:
                logger.error(f"{current_date}のトレーニングデータ取得中にエラーが発生しました: {str(e)}")
                results.append({
                    'date': current_date.isoformat(),
                    'activities': []
                })
            
            current_date += timedelta(days=1)
        
        return results
    
    def _is_l2_training(self, activity: Dict[str, Any]) -> bool:
        """
        アクティビティがL2トレーニング（低強度持久トレーニング）かどうかを判定する
        
        注: この実装は簡略化されており、実際にはさらに詳細な心拍ゾーン分析が必要
        
        Args:
            activity: アクティビティデータ
            
        Returns:
            bool: L2トレーニングの場合はTrue
        """
        try:
            # L2トレーニングの判定ロジック
            # 例: 心拍ゾーン1-2の時間が全体の70%以上
            # 詳細なデータが必要な場合は、activity_idを使って追加データを取得する必要あり
            
            # この実装では、実際のゾーンデータを取得するためのアクティビティIDを保存
            return True  # 簡単のため、すべてL2としてマーク（実際の実装では修正必要）
        except Exception:
            return False