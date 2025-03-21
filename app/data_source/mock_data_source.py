import random
import logging
from datetime import date, datetime, timedelta
from typing import Dict, List, Any

from app.data_source.data_source_interface import DataSourceInterface

logger = logging.getLogger(__name__)

class MockDataSource(DataSourceInterface):
    """
    テスト用のモックデータソース
    実際のAPIに接続せずにテストデータを生成する
    """
    
    def __init__(self):
        self.is_connected = False
        
    def connect(self, username: str, password: str) -> bool:
        """モック接続 - 常に成功する"""
        logger.info(f"MockDataSourceに接続しています: username={username}")
        self.is_connected = True
        return True
    
    def get_rhr_data(self, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """
        モックRHRデータを生成する
        
        Args:
            start_date: データ取得開始日
            end_date: データ取得終了日
            
        Returns:
            List[Dict[str, Any]]: 日付ごとのRHRデータのリスト
        """
        if not self.is_connected:
            logger.error("モックデータソースに接続されていません")
            raise ConnectionError("モックデータソースに接続されていません")
        
        logger.info(f"モックRHRデータを生成します: {start_date} から {end_date}")
        results = []
        current_date = start_date
        
        # 基準となるRHR値
        base_rhr = 55
        
        while current_date <= end_date:
            # リアルなRHRの日々の変動をシミュレート
            daily_variation = random.randint(-3, 3)
            weekly_cycle = 2 * (current_date.weekday() - 3) / 3  # 週の中で変動するパターン
            
            # 長期的な改善トレンドをシミュレート (200日かけて5bpmの改善)
            days_passed = (current_date - start_date).days
            long_term_improvement = -5 * (days_passed / 200) if days_passed <= 200 else -5
            
            # 整数値としてRHRを計算
            rhr = round(base_rhr + daily_variation + weekly_cycle + long_term_improvement)
            
            # 日付をISOフォーマットに変換
            date_str = current_date.isoformat()
            
            # 重要: 辞書のキーと値が正しいことを確認
            data = {
                'date': date_str,
                'rhr': rhr  # 必ず整数値
            }
            results.append(data)
            
            # データを詳細にログ出力
            logger.debug(f"生成したRHRデータ: date={date_str}, rhr={rhr}")
            
            current_date += timedelta(days=1)
        
        # 一部のデータを詳細にログ出力
        for i, data in enumerate(results[:3]):
            logger.info(f"生成したRHRデータサンプル{i+1}: date={data['date']}, rhr={data['rhr']}")
        
        logger.info(f"合計{len(results)}件のRHRデータを生成しました")
        return results
    
    def get_hrv_data(self, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """
        モックHRVデータを生成する
        
        Args:
            start_date: データ取得開始日
            end_date: データ取得終了日
            
        Returns:
            List[Dict[str, Any]]: 日付ごとのHRVデータのリスト
        """
        if not self.is_connected:
            logger.error("モックデータソースに接続されていません")
            raise ConnectionError("モックデータソースに接続されていません")
        
        logger.info(f"モックHRVデータを生成します: {start_date} から {end_date}")
        results = []
        current_date = start_date
        
        # 基準となるHRV値
        base_hrv = 48
        
        while current_date <= end_date:
            # リアルなHRVの日々の変動をシミュレート
            daily_variation = random.randint(-5, 5)
            weekly_cycle = -3 * (current_date.weekday() - 3) / 3  # 週の中で変動するパターン
            
            # 長期的な改善トレンドをシミュレート (200日かけて10msの改善)
            days_passed = (current_date - start_date).days
            long_term_improvement = 10 * (days_passed / 200) if days_passed <= 200 else 10
            
            # 浮動小数点値としてHRVを計算
            hrv = round(base_hrv + daily_variation + weekly_cycle + long_term_improvement)
            
            # 日付をISOフォーマットに変換
            date_str = current_date.isoformat()
            
            # 重要: 辞書のキーと値が正しいことを確認
            data = {
                'date': date_str,
                'hrv': float(hrv)  # 必ず浮動小数点値
            }
            results.append(data)
            
            # データを詳細にログ出力
            logger.debug(f"生成したHRVデータ: date={date_str}, hrv={hrv}")
            
            current_date += timedelta(days=1)
        
        # 一部のデータを詳細にログ出力
        for i, data in enumerate(results[:3]):
            logger.info(f"生成したHRVデータサンプル{i+1}: date={data['date']}, hrv={data['hrv']}")
        
        logger.info(f"合計{len(results)}件のHRVデータを生成しました")
        return results
    
    def get_training_data(self, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """
        モックトレーニングデータを生成する
        
        Args:
            start_date: データ取得開始日
            end_date: データ取得終了日
            
        Returns:
            List[Dict[str, Any]]: 日付ごとのトレーニングデータのリスト
        """
        if not self.is_connected:
            logger.error("モックデータソースに接続されていません")
            raise ConnectionError("モックデータソースに接続されていません")
        
        logger.info(f"モックトレーニングデータを生成します: {start_date} から {end_date}")
        results = []
        current_date = start_date
        
        # トレーニングをシミュレート
        while current_date <= end_date:
            daily_activities = []
            
            # 60%の確率でその日にアクティビティがある
            if random.random() < 0.6:
                # アクティビティの種類
                activity_types = ['cycling', 'running', 'swimming', 'walking', 'virtual_ride', 'road_biking']
                activity_type = random.choice(activity_types)
                
                # 活動時間 (30分〜2時間)
                duration = random.randint(30 * 60, 120 * 60)  # 秒単位
                
                # L2トレーニングの割合を徐々に増やす (200日かけて30%から70%へ)
                days_passed = (current_date - start_date).days
                l2_probability = 0.3 + (0.4 * min(days_passed / 200, 1.0))
                
                is_l2 = random.random() < l2_probability
                
                # 距離 (活動タイプによって異なる)
                if activity_type == 'cycling' or activity_type == 'virtual_ride' or activity_type == 'road_biking':
                    speed = random.uniform(20, 30)  # km/h
                    distance = (duration / 3600) * speed * 1000  # メートル単位
                elif activity_type == 'running':
                    speed = random.uniform(8, 12)  # km/h
                    distance = (duration / 3600) * speed * 1000  # メートル単位
                else:
                    distance = random.uniform(1000, 10000)  # メートル単位
                
                activity_data = {
                    'activity_id': f"mock_{current_date.isoformat()}_{random.randint(1000, 9999)}",
                    'activity_type': activity_type,
                    'start_time': f"{current_date.isoformat()}T{random.randint(6, 20):02d}:00:00",
                    'duration': duration,
                    'distance': distance,
                    'is_l2_training': is_l2,
                    'intensity': 'L2' if is_l2 else 'Other'
                }
                
                daily_activities.append(activity_data)
            
            results.append({
                'date': current_date.isoformat(),
                'activities': daily_activities
            })
            
            current_date += timedelta(days=1)
        
        logger.info(f"合計{len(results)}件の日別トレーニングデータを生成しました")
        # アクティビティの総数も表示
        total_activities = sum(len(day['activities']) for day in results)
        logger.info(f"合計{total_activities}件のアクティビティを生成しました")
        return results