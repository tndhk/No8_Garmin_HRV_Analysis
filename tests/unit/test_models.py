import pytest
from datetime import date, datetime, timedelta

from app.models.models import RHRData, HRVData, Activity, DailyData, WeeklyData


class TestModels:
    """モデルクラスのテスト"""
    
    def test_rhr_data_creation(self):
        """RHRDataの作成テスト"""
        test_date = datetime(2023, 1, 1)
        rhr_data = RHRData(date=test_date, rhr=60)
        
        assert rhr_data.date == test_date
        assert rhr_data.rhr == 60
    
    def test_rhr_data_from_dict(self):
        """RHRData.from_dictメソッドのテスト"""
        data_dict = {
            'date': '2023-01-01',
            'rhr': 60
        }
        
        rhr_data = RHRData.from_dict(data_dict)
        
        assert rhr_data.date.date() == date(2023, 1, 1)
        assert rhr_data.rhr == 60
    
    def test_hrv_data_creation(self):
        """HRVDataの作成テスト"""
        test_date = datetime(2023, 1, 1)
        hrv_data = HRVData(date=test_date, hrv=45.5)
        
        assert hrv_data.date == test_date
        assert hrv_data.hrv == 45.5
    
    def test_hrv_data_from_dict(self):
        """HRVData.from_dictメソッドのテスト"""
        data_dict = {
            'date': '2023-01-01',
            'hrv': 45.5
        }
        
        hrv_data = HRVData.from_dict(data_dict)
        
        assert hrv_data.date.date() == date(2023, 1, 1)
        assert hrv_data.hrv == 45.5
    
    def test_activity_creation(self):
        """Activityの作成テスト"""
        test_date = datetime(2023, 1, 1)
        start_time = datetime(2023, 1, 1, 10, 0)
        
        activity = Activity(
            activity_id="test123",
            date=test_date,
            activity_type="running",
            start_time=start_time,
            duration=3600,
            distance=5000,
            is_l2_training=True,
            intensity="L2"
        )
        
        assert activity.activity_id == "test123"
        assert activity.date == test_date
        assert activity.activity_type == "running"
        assert activity.start_time == start_time
        assert activity.duration == 3600
        assert activity.distance == 5000
        assert activity.is_l2_training == True
        assert activity.intensity == "L2"
    
    def test_activity_duration_properties(self):
        """Activity期間プロパティのテスト"""
        test_date = datetime(2023, 1, 1)
        activity = Activity(
            activity_id="test123",
            date=test_date,
            activity_type="cycling",
            start_time=test_date,
            duration=3600  # 1時間 (秒)
        )
        
        assert activity.duration_minutes == 60.0
        assert activity.duration_hours == 1.0
    
    def test_activity_from_dict(self):
        """Activity.from_dictメソッドのテスト"""
        test_date = datetime(2023, 1, 1)
        
        data_dict = {
            'activity_id': 'test123',
            'activity_type': 'running',
            'start_time': '2023-01-01T10:00:00',
            'duration': 3600,
            'distance': 5000,
            'is_l2_training': True,
            'intensity': 'L2'
        }
        
        activity = Activity.from_dict(test_date, data_dict)
        
        assert activity.activity_id == "test123"
        assert activity.date == test_date
        assert activity.activity_type == "running"
        assert activity.start_time.hour == 10
        assert activity.start_time.minute == 0
        assert activity.duration == 3600
        assert activity.distance == 5000
        assert activity.is_l2_training == True
        assert activity.intensity == "L2"
    
    def test_daily_data_creation(self):
        """DailyDataの作成テスト"""
        test_date = datetime(2023, 1, 1)
        
        daily_data = DailyData(
            date=test_date,
            rhr=60,
            hrv=45.5
        )
        
        assert daily_data.date == test_date
        assert daily_data.rhr == 60
        assert daily_data.hrv == 45.5
        assert daily_data.activities == []
    
    def test_daily_data_with_activities(self):
        """アクティビティを持つDailyDataのテスト"""
        test_date = datetime(2023, 1, 1)
        
        activity1 = Activity(
            activity_id="act1",
            date=test_date,
            activity_type="running",
            start_time=test_date.replace(hour=10),
            duration=3600,
            is_l2_training=True
        )
        
        activity2 = Activity(
            activity_id="act2",
            date=test_date,
            activity_type="cycling",
            start_time=test_date.replace(hour=15),
            duration=1800,
            is_l2_training=False
        )
        
        daily_data = DailyData(
            date=test_date,
            rhr=60,
            hrv=45.5,
            activities=[activity1, activity2]
        )
        
        assert daily_data.has_activities == True
        assert len(daily_data.activities) == 2
        assert daily_data.total_duration == 3600 + 1800  # 5400秒
        assert daily_data.l2_duration == 3600  # L2トレーニングは1つ目のみ
        assert pytest.approx(daily_data.l2_duration_hours) == 1.0
        assert pytest.approx(daily_data.l2_percentage) == (3600 / 5400) * 100
    
    def test_weekly_data_creation(self):
        """WeeklyDataの作成テスト"""
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 1, 7)
        
        # 日別データの作成
        daily_data = []
        for i in range(7):
            day_date = start_date + timedelta(days=i)
            
            # 日によって異なるRHRとHRV値
            rhr = 60 - i
            hrv = 45 + i
            
            # アクティビティ（偶数日のみL2トレーニング）
            activities = []
            if i % 2 == 0:  # 偶数日
                act = Activity(
                    activity_id=f"act{i}",
                    date=day_date,
                    activity_type="running",
                    start_time=day_date.replace(hour=10),
                    duration=3600,
                    is_l2_training=True
                )
                activities.append(act)
            else:  # 奇数日
                act = Activity(
                    activity_id=f"act{i}",
                    date=day_date,
                    activity_type="cycling",
                    start_time=day_date.replace(hour=15),
                    duration=1800,
                    is_l2_training=False
                )
                activities.append(act)
            
            day = DailyData(
                date=day_date,
                rhr=rhr,
                hrv=hrv,
                activities=activities
            )
            daily_data.append(day)
        
        # 週別データの作成
        weekly_data = WeeklyData(
            start_date=start_date,
            end_date=end_date,
            daily_data=daily_data
        )
        
        # テスト
        assert weekly_data.start_date == start_date
        assert weekly_data.end_date == end_date
        assert len(weekly_data.daily_data) == 7
        
        # 平均値の計算
        expected_avg_rhr = sum([60 - i for i in range(7)]) / 7
        expected_avg_hrv = sum([45 + i for i in range(7)]) / 7
        
        assert pytest.approx(weekly_data.avg_rhr) == expected_avg_rhr
        assert pytest.approx(weekly_data.avg_hrv) == expected_avg_hrv
        
        # L2トレーニング時間（偶数日のみ3600秒=1時間）
        expected_l2_hours = 4  # 0, 2, 4, 6日目の4日間分
        assert pytest.approx(weekly_data.total_l2_hours) == expected_l2_hours
        
        # 総トレーニング時間（偶数日は3600秒、奇数日は1800秒）
        expected_total_hours = (4 * 3600 + 3 * 1800) / 3600  # 5.5時間
        assert pytest.approx(weekly_data.total_training_hours) == expected_total_hours
        
        # L2割合
        expected_l2_percentage = (expected_l2_hours / expected_total_hours) * 100
        assert pytest.approx(weekly_data.l2_percentage) == expected_l2_percentage