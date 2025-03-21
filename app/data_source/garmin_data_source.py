import time
import logging
import json
from datetime import date, datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union

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
            logger.info(f"Garmin Connect APIに接続しています: {username}")
            self.client = Garmin(username, password)
            self.client.login()
            
            # 接続テストとしてユーザープロファイルを取得
            user_profile = self.client.get_user_profile()
            if 'userData' in user_profile and 'weight' in user_profile['userData']:
                weight_kg = user_profile['userData']['weight'] / 1000  # グラムからkgに変換
                logger.info(f"Garmin Connect APIに接続しました。体重: {weight_kg:.1f}kg")
            else:
                logger.info("Garmin Connect APIに接続しました。")
            
            self.is_connected = True
            return True
        except Exception as e:
            logger.error(f"Garmin Connect APIへの接続に失敗しました: {str(e)}", exc_info=True)
            self.is_connected = False
            return False
    
    def _check_connection(self):
        """接続状態を確認し、未接続の場合は例外を発生させる"""
        if not self.is_connected or self.client is None:
            logger.error("Garmin Connect APIに接続されていません")
            raise ConnectionError("Garmin Connect APIに接続されていません。connect()メソッドを先に呼び出してください。")
    
    def _delay_request(self):
        """API制限を回避するための待機時間"""
        time.sleep(self.request_delay)
    
    def _safe_api_call(self, api_func, *args, **kwargs):
        """
        APIコールを安全に実行し、エラーハンドリングを行う
        
        Args:
            api_func: 呼び出すAPIメソッド
            *args, **kwargs: APIメソッドに渡す引数
            
        Returns:
            Any: APIからのレスポンス
        """
        try:
            result = api_func(*args, **kwargs)
            return result
        except Exception as e:
            logger.error(f"APIコール中にエラーが発生しました: {str(e)}", exc_info=True)
            return None
    
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
        
        logger.info(f"RHRデータの取得を開始します: {start_date} から {end_date}")
        
        while current_date <= end_date:
            date_str = current_date.isoformat()
            logger.info(f"取得中: {date_str} のRHRデータ")
            
            try:
                # 方法1: get_rhr_day メソッドを使用 - これが最も信頼性の高い方法
                rhr_value = None
                rhr_data = self._safe_api_call(self.client.get_rhr_day, date_str)
                
                if rhr_data and isinstance(rhr_data, dict):
                    # API診断の結果から、allMetricsの中のWELLNESS_RESTING_HEART_RATEにデータが格納されていることがわかった
                    if 'allMetrics' in rhr_data and isinstance(rhr_data['allMetrics'], dict):
                        metrics_map = rhr_data['allMetrics'].get('metricsMap', {})
                        if 'WELLNESS_RESTING_HEART_RATE' in metrics_map:
                            hrr_metrics = metrics_map['WELLNESS_RESTING_HEART_RATE']
                            if isinstance(hrr_metrics, list) and len(hrr_metrics) > 0:
                                rhr_value = hrr_metrics[0].get('value')
                                logger.info(f"RHR値を取得しました: {date_str} -> {rhr_value}")
                
                # 方法2: バックアップとしてget_statsを使用
                if rhr_value is None:
                    stats = self._safe_api_call(self.client.get_stats, date_str)
                    if stats and 'restingHeartRate' in stats:
                        rhr_value = stats['restingHeartRate']
                        logger.info(f"get_stats からRHR値を取得しました: {date_str} -> {rhr_value}")
                
                # 方法3: 睡眠データから取得を試みる
                if rhr_value is None:
                    sleep_data = self._safe_api_call(self.client.get_sleep_data, date_str)
                    if sleep_data and 'restingHeartRate' in sleep_data:
                        rhr_value = sleep_data['restingHeartRate']
                        logger.info(f"睡眠データからRHR値を取得しました: {date_str} -> {rhr_value}")
                
                # データ型の確認と変換
                if rhr_value is not None:
                    try:
                        rhr_value = int(float(rhr_value))  # 整数値に変換
                    except (ValueError, TypeError):
                        logger.warning(f"RHR値が数値ではありません: {rhr_value}")
                        rhr_value = None
                
                # データを記録
                results.append({
                    'date': date_str,
                    'rhr': rhr_value
                })
                
                self._delay_request()
                
            except Exception as e:
                logger.error(f"{date_str}のRHRデータ取得中にエラーが発生しました: {str(e)}", exc_info=True)
                results.append({
                    'date': date_str,
                    'rhr': None
                })
            
            current_date += timedelta(days=1)
        
        # 取得したデータのサマリーをログ出力
        valid_data_count = sum(1 for item in results if item['rhr'] is not None)
        logger.info(f"RHRデータ取得完了: 合計{len(results)}日分, 有効データ{valid_data_count}日分")
        
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
        
        logger.info(f"HRVデータの取得を開始します: {start_date} から {end_date}")
        
        while current_date <= end_date:
            date_str = current_date.isoformat()
            logger.info(f"取得中: {date_str} のHRVデータ")
            
            try:
                # API診断の結果から、睡眠データにHRV情報が含まれていることがわかった
                hrv_value = None
                sleep_data = self._safe_api_call(self.client.get_sleep_data, date_str)
                
                if sleep_data and isinstance(sleep_data, dict):
                    # 平均夜間HRV値を取得
                    if 'avgOvernightHrv' in sleep_data:
                        hrv_value = sleep_data['avgOvernightHrv']
                        logger.info(f"平均夜間HRV値を取得しました: {date_str} -> {hrv_value}")
                    
                    # 詳細なHRVデータがある場合は平均を計算
                    elif 'hrvData' in sleep_data and isinstance(sleep_data['hrvData'], list) and len(sleep_data['hrvData']) > 0:
                        hrv_values = [item.get('value') for item in sleep_data['hrvData'] if item.get('value') is not None]
                        if hrv_values:
                            hrv_value = sum(hrv_values) / len(hrv_values)
                            logger.info(f"HRVデータの平均値を計算しました: {date_str} -> {hrv_value}")
                
                # データ型の確認と変換
                if hrv_value is not None:
                    try:
                        hrv_value = float(hrv_value)  # 浮動小数点値に変換
                    except (ValueError, TypeError):
                        logger.warning(f"HRV値が数値ではありません: {hrv_value}")
                        hrv_value = None
                
                # データを記録
                results.append({
                    'date': date_str,
                    'hrv': hrv_value
                })
                
                self._delay_request()
                
            except Exception as e:
                logger.error(f"{date_str}のHRVデータ取得中にエラーが発生しました: {str(e)}", exc_info=True)
                results.append({
                    'date': date_str,
                    'hrv': None
                })
            
            current_date += timedelta(days=1)
        
        # 取得したデータのサマリーをログ出力
        valid_data_count = sum(1 for item in results if item['hrv'] is not None)
        logger.info(f"HRVデータ取得完了: 合計{len(results)}日分, 有効データ{valid_data_count}日分")
        
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
        
        logger.info(f"トレーニングデータの取得を開始します: {start_date} から {end_date}")
        
        while current_date <= end_date:
            date_str = current_date.isoformat()
            logger.info(f"取得中: {date_str} のアクティビティデータ")
            
            try:
                # API診断の結果からget_activities_by_dateを使用
                activities = self._safe_api_call(
                    self.client.get_activities_by_date,
                    date_str, 
                    date_str
                )
                
                # APIレスポンスのデバッグ出力
                if activities:
                    logger.debug(f"アクティビティ取得成功: {date_str}, 件数: {len(activities)}")
                else:
                    logger.info(f"アクティビティデータなし: {date_str}")
                
                # 各アクティビティを処理
                daily_activities = []
                if activities and isinstance(activities, list):
                    for activity in activities:
                        try:
                            # 必要なフィールドがあるか確認
                            activity_id = activity.get('activityId')
                            
                            # activityTypeがdict形式か確認
                            activity_type = None
                            if 'activityType' in activity and isinstance(activity['activityType'], dict):
                                activity_type = activity['activityType'].get('typeKey')
                            
                            start_time = activity.get('startTimeLocal')
                            duration = activity.get('duration')  # 秒単位
                            distance = activity.get('distance')
                            
                            # 必須フィールドがなければスキップ
                            if not all([activity_id, activity_type, start_time, duration]):
                                missing = []
                                if not activity_id: missing.append("activity_id")
                                if not activity_type: missing.append("activity_type")
                                if not start_time: missing.append("start_time")
                                if not duration: missing.append("duration")
                                logger.warning(f"必須フィールドがないアクティビティをスキップ: 不足={missing}")
                                continue
                            
                            # L2トレーニングの判定
                            is_l2 = self._is_l2_training(activity)
                            
                            activity_data = {
                                'activity_id': str(activity_id),  # 常に文字列に変換
                                'activity_type': activity_type,
                                'start_time': start_time,
                                'duration': float(duration),  # 確実に数値に変換
                                'distance': float(distance) if distance is not None else None,
                                'is_l2_training': bool(is_l2),  # 確実にブール値に変換
                                'intensity': 'L2' if is_l2 else 'Other'
                            }
                            
                            daily_activities.append(activity_data)
                            logger.debug(f"アクティビティ処理成功: {activity_id}, タイプ: {activity_type}")
                            
                        except Exception as e:
                            logger.error(f"アクティビティデータの処理中にエラーが発生しました: {str(e)}", exc_info=True)
                
                results.append({
                    'date': date_str,
                    'activities': daily_activities
                })
                
                logger.info(f"{date_str}のアクティビティ: {len(daily_activities)}件")
                self._delay_request()
                
            except Exception as e:
                logger.error(f"{date_str}のトレーニングデータ取得中にエラーが発生しました: {str(e)}", exc_info=True)
                results.append({
                    'date': date_str,
                    'activities': []
                })
            
            current_date += timedelta(days=1)
        
        # 取得したデータのサマリーをログ出力
        total_activities = sum(len(day['activities']) for day in results)
        logger.info(f"トレーニングデータ取得完了: 合計{len(results)}日分, アクティビティ{total_activities}件")
        
        return results
    
    def _is_l2_training(self, activity: Dict[str, Any]) -> bool:
        """
        アクティビティがL2トレーニング（低強度持久トレーニング）かどうかを判定する
        
        Args:
            activity: アクティビティデータ
            
        Returns:
            bool: L2トレーニングの場合はTrue
        """
        try:
            # API診断の結果からactivityTypeの構造を確認
            activity_type = None
            if 'activityType' in activity and isinstance(activity['activityType'], dict):
                activity_type = activity['activityType'].get('typeKey', '').lower()
            
            if not activity_type:
                return False
            
            # 持久系のアクティビティタイプ
            endurance_activities = ['cycling', 'running', 'swimming', 'walking', 'hiking', 'elliptical', 
                                   'virtual_ride', 'road_biking', 'mountain_biking', 'indoor_cycling']
            
            if not any(endurance in activity_type for endurance in endurance_activities):
                return False
            
            # ゾーン1-2の時間をチェック（L2判定に利用）
            has_l2_zones = False
            if 'hrTimeInZone_1' in activity and 'hrTimeInZone_2' in activity:
                zone1_time = float(activity['hrTimeInZone_1']) if activity['hrTimeInZone_1'] else 0
                zone2_time = float(activity['hrTimeInZone_2']) if activity['hrTimeInZone_2'] else 0
                total_zone_time = 0
                
                # すべてのゾーンの合計を計算
                for i in range(1, 6):
                    zone_key = f'hrTimeInZone_{i}'
                    if zone_key in activity and activity[zone_key]:
                        try:
                            total_zone_time += float(activity[zone_key])
                        except (ValueError, TypeError):
                            pass
                
                # ゾーン1と2が70%以上ならL2
                if total_zone_time > 0:
                    l2_percentage = (zone1_time + zone2_time) / total_zone_time * 100
                    if l2_percentage >= 70:
                        has_l2_zones = True
                        logger.debug(f"ゾーン1-2が{l2_percentage:.1f}%でL2と判定")
            
            # 平均心拍数をチェック
            if not has_l2_zones and 'averageHR' in activity and activity['averageHR']:
                avg_hr = float(activity['averageHR'])
                # 一般的に心拍数が低い場合はL2
                # 最大心拍数の70%未満が一般的なL2ゾーン
                # 最大心拍数の見積もり: 220 - 年齢（仮に30歳と想定）
                max_hr_estimate = 220 - 30
                if avg_hr < 0.7 * max_hr_estimate:
                    has_l2_zones = True
                    logger.debug(f"平均心拍数{avg_hr}bpmでL2と判定")
            
            # パワーゾーンをチェック
            if not has_l2_zones and 'powerTimeInZone_1' in activity and 'powerTimeInZone_2' in activity:
                zone1_time = float(activity['powerTimeInZone_1']) if activity['powerTimeInZone_1'] else 0
                zone2_time = float(activity['powerTimeInZone_2']) if activity['powerTimeInZone_2'] else 0
                total_zone_time = 0
                
                # すべてのゾーンの合計を計算
                for i in range(1, 8):  # パワーゾーンは7つまである
                    zone_key = f'powerTimeInZone_{i}'
                    if zone_key in activity and activity[zone_key]:
                        try:
                            total_zone_time += float(activity[zone_key])
                        except (ValueError, TypeError):
                            pass
                
                # ゾーン1と2が80%以上ならL2
                if total_zone_time > 0:
                    l2_percentage = (zone1_time + zone2_time) / total_zone_time * 100
                    if l2_percentage >= 80:
                        has_l2_zones = True
                        logger.debug(f"パワーゾーン1-2が{l2_percentage:.1f}%でL2と判定")
            
            # トレーニング効果ラベルをチェック
            if not has_l2_zones and 'trainingEffectLabel' in activity:
                te_label = activity.get('trainingEffectLabel', '').upper()
                if te_label in ['AEROBIC_BASE', 'RECOVERY', 'ACTIVE_RECOVERY']:
                    has_l2_zones = True
                    logger.debug(f"トレーニング効果ラベル'{te_label}'でL2と判定")
            
            # 長時間活動はL2である可能性が高い
            if not has_l2_zones and 'duration' in activity and activity['duration']:
                duration = float(activity['duration'])
                if duration > 7200:  # 2時間以上
                    has_l2_zones = True
                    logger.debug(f"長時間活動（{duration/3600:.1f}時間）でL2と判定")
            
            return has_l2_zones
            
        except Exception as e:
            logger.error(f"L2トレーニング判定中にエラーが発生しました: {str(e)}")
            return False  # エラー時はデフォルトでFalse