import pytest
from datetime import date, datetime, timedelta
from unittest.mock import MagicMock, patch, create_autospec
import os
import tempfile

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.repository.repository_interface import RepositoryInterface
from app.repository.sqlite_repository import SQLiteRepository
from app.repository.repository_factory import RepositoryFactory
from app.models.models import RHRData, HRVData, Activity, DailyData, WeeklyData
from app.models.database_models import Base, RHRRecord, HRVRecord, ActivityRecord, init_db


class TestRepository:
    """リポジトリのテストクラス"""
    
    @pytest.fixture
    def temp_db(self):
        """テスト用の一時的なSQLiteデータベースを作成"""
        # 一時ファイルの作成
        db_fd, db_path = tempfile.mkstemp(suffix='.db')
        db_url = f'sqlite:///{db_path}'
        
        # データベースの初期化
        engine, Session = init_db(db_url)
        
        # テスト用のデータをセットアップ
        yield engine, Session
        
        # テスト後のクリーンアップ
        os.close(db_fd)
        os.unlink(db_path)
    
    def test_repository_interface(self):
        """RepositoryInterfaceの抽象メソッドが正しく定義されているかテスト"""
        # 抽象クラスなので直接インスタンス化はできない
        with pytest.raises(TypeError):
            RepositoryInterface()
    
    def test_sqlite_repository_save_and_get_rhr(self, temp_db):
        """SQLiteRepositoryのRHRデータ保存・取得をテスト"""
        _, Session = temp_db
        repo = SQLiteRepository(Session)
        
        # テスト用のRHRデータ作成
        test_date = datetime(2023, 1, 1)
        rhr_data = [
            RHRData(date=test_date, rhr=60),
            RHRData(date=test_date + timedelta(days=1), rhr=58),
            RHRData(date=test_date + timedelta(days=2), rhr=62)
        ]
        
        # データ保存
        result = repo.save_rhr_data(rhr_data)
        assert result == True
        
        # データ取得
        retrieved = repo.get_rhr_data(
            test_date.date(),
            (test_date + timedelta(days=2)).date()
        )
        
        # 結果検証
        assert len(retrieved) == 3
        assert retrieved[0].date.date() == test_date.date()
        assert retrieved[0].rhr == 60
        assert retrieved[1].rhr == 58
        assert retrieved[2].rhr == 62
    
    def test_sqlite_repository_save_and_get_hrv(self, temp_db):
        """SQLiteRepositoryのHRVデータ保存・取得をテスト"""
        _, Session = temp_db
        repo = SQLiteRepository(Session)
        
        # テスト用のHRVデータ作成
        test_date = datetime(2023, 1, 1)
        hrv_data = [
            HRVData(date=test_date, hrv=45.5),
            HRVData(date=test_date + timedelta(days=1), hrv=48.2),
            HRVData(date=test_date + timedelta(days=2), hrv=46.8)
        ]
        
        # データ保存
        result = repo.save_hrv_data(hrv_data)
        assert result == True
        
        # データ取得
        retrieved = repo.get_hrv_data(
            test_date.date(),
            (test_date + timedelta(days=2)).date()
        )
        
        # 結果検証
        assert len(retrieved) == 3
        assert retrieved[0].date.date() == test_date.date()
        assert retrieved[0].hrv == 45.5
        assert retrieved[1].hrv == 48.2
        assert retrieved[2].hrv == 46.8
    
    def test_sqlite_repository_save_and_get_activities(self, temp_db):
        """SQLiteRepositoryのアクティビティデータ保存・取得をテスト"""
        _, Session = temp_db
        repo = SQLiteRepository(Session)
        
        # テスト用のアクティビティデータ作成
        test_date = datetime(2023, 1, 1)
        activities = [
            Activity(
                activity_id="act123",
                date=test_date,
                activity_type="cycling",
                start_time=datetime(2023, 1, 1, 10, 0),
                duration=3600,
                distance=30000,
                is_l2_training=True,
                intensity="L2"
            ),
            Activity(
                activity_id="act124",
                date=test_date + timedelta(days=1),
                activity_type="running",
                start_time=datetime(2023, 1, 2, 8, 0),
                duration=1800,
                distance=5000,
                is_l2_training=False,
                intensity="Other"
            )
        ]
        
        # データ保存
        result = repo.save_activities(activities)
        assert result == True
        
        # データ取得
        retrieved = repo.get_activities(
            test_date.date(),
            (test_date + timedelta(days=1)).date()
        )
        
        # 結果検証
        assert len(retrieved) == 2
        assert retrieved[0].activity_id == "act123"
        assert retrieved[0].activity_type == "cycling"
        assert retrieved[0].is_l2_training == True
        assert retrieved[1].activity_id == "act124"
        assert retrieved[1].activity_type == "running"
        assert retrieved[1].is_l2_training == False
    
    def test_sqlite_repository_daily_data(self, temp_db):
        """SQLiteRepositoryの日別データ取得をテスト"""
        _, Session = temp_db
        repo = SQLiteRepository(Session)
        
        # テスト用のデータ作成と保存
        test_date = datetime(2023, 1, 1)
        
        # RHRデータ
        rhr_data = [
            RHRData(date=test_date, rhr=60),
            RHRData(date=test_date + timedelta(days=1), rhr=58)
        ]
        repo.save_rhr_data(rhr_data)
        
        # HRVデータ
        hrv_data = [
            HRVData(date=test_date, hrv=45.5),
            HRVData(date=test_date + timedelta(days=1), hrv=48.2)
        ]
        repo.save_hrv_data(hrv_data)
        
        # アクティビティデータ
        activities = [
            Activity(
                activity_id="act123",
                date=test_date,
                activity_type="cycling",
                start_time=datetime(2023, 1, 1, 10, 0),
                duration=3600,
                distance=30000,
                is_l2_training=True,
                intensity="L2"
            ),
            Activity(
                activity_id="act124",
                date=test_date + timedelta(days=1),
                activity_type="running",
                start_time=datetime(2023, 1, 2, 8, 0),
                duration=1800,
                distance=5000,
                is_l2_training=False,
                intensity="Other"
            )
        ]
        repo.save_activities(activities)
        
        # 日別データ取得
        daily_data = repo.get_daily_data(
            test_date.date(),
            (test_date + timedelta(days=1)).date()
        )
        
        # 結果検証
        assert len(daily_data) == 2
        assert daily_data[0].date.date() == test_date.date()
        assert daily_data[0].rhr == 60
        assert daily_data[0].hrv == 45.5
        assert len(daily_data[0].activities) == 1
        assert daily_data[0].activities[0].activity_id == "act123"
        
        assert daily_data[1].date.date() == (test_date + timedelta(days=1)).date()
        assert daily_data[1].rhr == 58
        assert daily_data[1].hrv == 48.2
        assert len(daily_data[1].activities) == 1
        assert daily_data[1].activities[0].activity_id == "act124"
    
    def test_sqlite_repository_weekly_data(self, temp_db):
        """SQLiteRepositoryの週別データ取得をテスト"""
        _, Session = temp_db
        repo = SQLiteRepository(Session)
        
        # 2週間分のテストデータを作成（2023/1/1は月曜日と仮定）
        start_date = datetime(2023, 1, 1)  # 月曜日
        
        # 日別データを保存
        for i in range(14):  # 2週間分
            current_date = start_date + timedelta(days=i)
            
            # RHRデータ（曜日によって変動させる）
            rhr = 60 - (i % 7)  # 月曜が最も高く、日曜が最も低い
            repo.save_rhr_data([RHRData(date=current_date, rhr=rhr)])
            
            # HRVデータ（曜日によって変動させる）
            hrv = 45 + (i % 7)  # 月曜が最も低く、日曜が最も高い
            repo.save_hrv_data([HRVData(date=current_date, hrv=hrv)])
            
            # アクティビティ（週末にのみ設定）
            if i % 7 >= 5:  # 土日のみ
                activity = Activity(
                    activity_id=f"act{i}",
                    date=current_date,
                    activity_type="cycling" if i % 2 == 0 else "running",
                    start_time=current_date.replace(hour=10),
                    duration=3600,
                    distance=30000 if i % 2 == 0 else 10000,
                    is_l2_training=True,
                    intensity="L2"
                )
                repo.save_activities([activity])
        
        # 週別データ取得
        weekly_data = repo.get_weekly_data(
            start_date.date(),
            (start_date + timedelta(days=13)).date()
        )
        
        # 結果検証
        assert len(weekly_data) == 2  # 2週間分
        
        # 1週目のチェック
        assert weekly_data[0].start_date.date() == start_date.date()
        assert weekly_data[0].end_date.date() == (start_date + timedelta(days=6)).date()
        assert len(weekly_data[0].daily_data) == 7  # 7日分
        
        # 2週目のチェック
        assert weekly_data[1].start_date.date() == (start_date + timedelta(days=7)).date()
        assert weekly_data[1].end_date.date() == (start_date + timedelta(days=13)).date()
        assert len(weekly_data[1].daily_data) == 7  # 7日分
        
        # アクティビティが正しく含まれているか
        activities_week1 = [a for d in weekly_data[0].daily_data for a in d.activities]
        activities_week2 = [a for d in weekly_data[1].daily_data for a in d.activities]
        
        assert len(activities_week1) == 2  # 土日の2日分
        assert len(activities_week2) == 2  # 土日の2日分
    
    def test_repository_factory(self):
        """RepositoryFactoryのテスト"""
        # データベースパスを一時的に変更
        with patch('os.environ.get', return_value='sqlite:///test.db'):
            with patch('app.models.database_models.init_db') as mock_init_db:
                mock_init_db.return_value = (None, MagicMock())
                
                repo = RepositoryFactory.create_repository()
                assert isinstance(repo, SQLiteRepository)
                
                # init_dbが正しく呼ばれたか
                mock_init_db.assert_called_once_with('sqlite:///test.db')