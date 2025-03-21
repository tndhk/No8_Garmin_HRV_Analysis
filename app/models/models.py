from datetime import datetime
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class RHRData:
    """安静時心拍数データモデル"""
    date: datetime
    rhr: Optional[int] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RHRData':
        """辞書からインスタンスを生成する"""
        try:
            date_obj = datetime.fromisoformat(data['date']) if isinstance(data['date'], str) else data['date']
            rhr_value = data.get('rhr')
            
            # RHR値のバリデーション
            if rhr_value is not None:
                try:
                    rhr_value = int(rhr_value)  # 確実に整数に変換
                    
                    # 現実的な範囲かチェック
                    if rhr_value < 30 or rhr_value > 150:
                        logger.warning(f"現実的ではないRHR値: {rhr_value}, 日付: {date_obj}")
                except (ValueError, TypeError):
                    logger.warning(f"RHR値を整数に変換できません: {rhr_value}, 日付: {date_obj}")
                    rhr_value = None
            
            return cls(
                date=date_obj,
                rhr=rhr_value
            )
        except Exception as e:
            logger.error(f"RHRDataの変換中にエラーが発生しました: {str(e)}, データ: {data}")
            # 最低限必要なデータで作成
            if 'date' in data:
                try:
                    date_obj = datetime.fromisoformat(data['date']) if isinstance(data['date'], str) else data['date']
                    return cls(date=date_obj, rhr=None)
                except:
                    pass
            raise


@dataclass
class HRVData:
    """心拍変動データモデル"""
    date: datetime
    hrv: Optional[float] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'HRVData':
        """辞書からインスタンスを生成する"""
        try:
            date_obj = datetime.fromisoformat(data['date']) if isinstance(data['date'], str) else data['date']
            hrv_value = data.get('hrv')
            
            # HRV値のバリデーション
            if hrv_value is not None:
                try:
                    hrv_value = float(hrv_value)  # 確実に浮動小数点に変換
                    
                    # 現実的な範囲かチェック
                    if hrv_value < 10 or hrv_value > 150:
                        logger.warning(f"現実的ではないHRV値: {hrv_value}, 日付: {date_obj}")
                except (ValueError, TypeError):
                    logger.warning(f"HRV値を浮動小数点に変換できません: {hrv_value}, 日付: {date_obj}")
                    hrv_value = None
            
            return cls(
                date=date_obj,
                hrv=hrv_value
            )
        except Exception as e:
            logger.error(f"HRVDataの変換中にエラーが発生しました: {str(e)}, データ: {data}")
            # 最低限必要なデータで作成
            if 'date' in data:
                try:
                    date_obj = datetime.fromisoformat(data['date']) if isinstance(data['date'], str) else data['date']
                    return cls(date=date_obj, hrv=None)
                except:
                    pass
            raise


@dataclass
class Activity:
    """アクティビティデータモデル"""
    activity_id: str
    date: datetime
    activity_type: str
    start_time: datetime
    duration: float  # 秒単位
    distance: Optional[float] = None  # メートル単位
    is_l2_training: bool = False
    intensity: str = 'Other'
    
    @property
    def duration_minutes(self) -> float:
        """活動時間を分単位で返す"""
        return self.duration / 60
    
    @property
    def duration_hours(self) -> float:
        """活動時間を時間単位で返す"""
        return self.duration / 3600
    
    @classmethod
    def from_dict(cls, date: datetime, data: Dict[str, Any]) -> 'Activity':
        """辞書からインスタンスを生成する"""
        try:
            start_time = datetime.fromisoformat(data['start_time']) if isinstance(data['start_time'], str) else data['start_time']
            
            return cls(
                activity_id=data['activity_id'],
                date=date,
                activity_type=data['activity_type'],
                start_time=start_time,
                duration=data['duration'],
                distance=data.get('distance'),
                is_l2_training=data.get('is_l2_training', False),
                intensity=data.get('intensity', 'Other')
            )
        except Exception as e:
            logger.error(f"Activityの変換中にエラーが発生しました: {str(e)}, データ: {data}")
            raise


@dataclass
class DailyData:
    """日別データモデル"""
    date: datetime
    rhr: Optional[int] = None
    hrv: Optional[float] = None
    activities: List[Activity] = None
    
    def __post_init__(self):
        if self.activities is None:
            self.activities = []
    
    @property
    def has_activities(self) -> bool:
        """アクティビティがあるかどうか"""
        return len(self.activities) > 0
    
    @property
    def total_duration(self) -> float:
        """その日の総トレーニング時間（秒）"""
        return sum(a.duration for a in self.activities)
    
    @property
    def l2_duration(self) -> float:
        """その日のL2トレーニング時間（秒）"""
        return sum(a.duration for a in self.activities if a.is_l2_training)
    
    @property
    def l2_duration_hours(self) -> float:
        """その日のL2トレーニング時間（時間）"""
        return self.l2_duration / 3600
    
    @property
    def l2_percentage(self) -> float:
        """全トレーニングに占めるL2の割合（%）"""
        if self.total_duration == 0:
            return 0
        return (self.l2_duration / self.total_duration) * 100


@dataclass
class WeeklyData:
    """週別データモデル"""
    start_date: datetime
    end_date: datetime
    daily_data: List[DailyData]
    
    @property
    def avg_rhr(self) -> Optional[float]:
        """週の平均RHR"""
        rhr_values = [d.rhr for d in self.daily_data if d.rhr is not None]
        return sum(rhr_values) / len(rhr_values) if rhr_values else None
    
    @property
    def avg_hrv(self) -> Optional[float]:
        """週の平均HRV"""
        hrv_values = [d.hrv for d in self.daily_data if d.hrv is not None]
        return sum(hrv_values) / len(hrv_values) if hrv_values else None
    
    @property
    def total_l2_hours(self) -> float:
        """週のL2トレーニング総時間（時間）"""
        return sum(d.l2_duration_hours for d in self.daily_data)
    
    @property
    def total_training_hours(self) -> float:
        """週のトレーニング総時間（時間）"""
        return sum(d.total_duration for d in self.daily_data) / 3600
    
    @property
    def l2_percentage(self) -> float:
        """週のL2トレーニング割合（%）"""
        if self.total_training_hours == 0:
            return 0
        return (self.total_l2_hours / self.total_training_hours) * 100