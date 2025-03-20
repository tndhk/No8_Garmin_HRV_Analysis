import pytest
import os
import tempfile
from datetime import date, datetime, timedelta
from unittest.mock import patch, MagicMock
from pathlib import Path

# プロジェクトのルートディレクトリをPATHに追加
project_root = str(Path(__file__).parent.parent.parent)
import sys
sys.path.insert(0, project_root)

from app.service.data_service import DataService
from app.data_source.data_source_interface import DataSourceInterface
from app.repository.repository_interface import RepositoryInterface
from app.models.database_models import init_db
from app.repository.sqlite_repository import SQLiteRepository
from app.models.models import RHRData, HRVData, Activity


class FailingDataSource(DataSourceInterface):
    """テスト用の故障するデータソース"""
    
    def __init__(self, fail_on=None):
        """
        コンストラクタ
        
        Args:
            fail_on: どのメソッドで失敗させるかのリスト ('connect', 'get_rhr_data', 'get_hrv_data', 'get_training_data')
        """
        self.fail_on = fail_on or []
        self.is_connected = False
    
    def connect(self, username: str, password: str) -> bool:
        """接続（'connect'が指定されていれば失敗する）"""
        if 'connect' in self.fail_on:
            return False
        self.is_connected = True
        return True
    
    def get_rhr_data(self, start_date: date, end_date: date):
        """RHRデータ取得（'get_rhr_data'が指定されていれば例外を発生させる）"""
        if not self.is_connected:
            raise ConnectionError("データソースに接続されていません")
        
        if 'get_rhr_data' in self.fail_on:
            raise Exception("RHRデータ取得中にエラーが発生しました")
        
        # 正常系：モックデータを返す
        result = []
        current_date = start_date
        while current_date <= end_date:
            result.append({
                'date': current_date.isoformat(),
                'rhr': 60
            })
            current_date += timedelta(days=1)
        return result
    
    def get_hrv_data(self, start_date: date, end_date: date):
        """HRVデータ取得（'get_hrv_data'が指定されていれば例外を発生させる）"""
        if not self.is_connected:
            raise ConnectionError("データソースに接続されていません")
        
        if 'get_hrv_data' in self.fail_on:
            raise Exception("HRVデータ取得中にエラーが発生しました")
        
        # 正常系：モックデータを返す
        result = []
        current_date = start_date
        while current_date <= end_date:
            result.append({
                'date': current_date.isoformat(),
                'hrv': 45
            })
            current_date += timedelta(days=1)
        return result
    
    def get_training_data(self, start_date: date, end_date: date):
        """トレーニングデータ取得（'get_training_data'が指定されていれば例外を発生させる）"""
        if not self.is_connected:
            raise ConnectionError("データソースに接続されていません")
        
        if 'get_training_data' in self.fail_on:
            raise Exception("トレーニングデータ取得中にエラーが発生しました")
        
        # 正常系：モックデータを返す
        result = []
        current_date = start_date
        while current_date <= end_date:
            result.append({
                'date': current_date.isoformat(),
                'activities': [{
                    'activity_id': f"test_{current_date.isoformat()}",
                    'activity_type': 'running',
                    'start_time': f"{current_date.isoformat()}T10:00:00",
                    'duration': 3600,
                    'distance': 5000,
                    'is_l2_training': True,
                    'intensity': 'L2'
                }]
            })
            current_date += timedelta(days=1)
        return result


class FailingRepository(SQLiteRepository):
    """テスト用の故障するリポジトリ"""
    
    def __init__(self, session_factory, fail_on=None):
        """
        コンストラクタ
        
        Args:
            session_factory: SQLAlchemyセッションファクトリ
            fail_on: どのメソッドで失敗させるかのリスト
        """
        super().__init__(session_factory)
        self.fail_on = fail_on or []
    
    def save_rhr_data(self, rhr_data):
        """RHRデータ保存（'save_rhr_data'が指定されていれば失敗する）"""
        if 'save_rhr_data' in self.fail_on:
            return False
        return super().save_rhr_data(rhr_data)
    
    def save_hrv_data(self, hrv_data):
        """HRVデータ保存（'save_hrv_data'が指定されていれば失敗する）"""
        if 'save_hrv_data' in self.fail_on:
            return False
        return super().save_hrv_data(hrv_data)
    
    def save_activities(self, activities):
        """アクティビティ保存（'save_activities'が指定されていれば失敗する）"""
        if 'save_activities' in self.fail_on:
            return False
        return super().save_activities(activities)


class TestErrorHandling:
    """エラーハンドリングの統合テスト"""
    
    @pytest.fixture
    def temp_db(self):
        """テスト用の一時的なSQLiteデータベースを作成"""
        db_fd, db_path = tempfile.mkstemp(suffix='.db')
        db_url = f'sqlite:///{db_path}'
        
        engine, Session = init_db(db_url)
        
        yield db_url, Session
        
        os.close(db_fd)
        os.unlink(db_path)
    
    def test_connect_failure(self, temp_db):
        """接続失敗時のエラーハンドリングテスト"""
        _, Session = temp_db
        
        # 接続に失敗するデータソース
        failing_data_source = FailingDataSource(fail_on=['connect'])
        
        # 正常なリポジトリ
        repository = SQLiteRepository(Session)
        
        # データサービス
        data_service = DataService(data_source=failing_data_source, repository=repository)
        
        # 環境変数をモック化
        with patch.dict('os.environ', {'GARMIN_USERNAME': 'test', 'GARMIN_PASSWORD': 'test'}):
            # 接続を試みる
            result = data_service.connect()
            
            # 接続に失敗するはず
            assert result == False
            assert data_service.is_connected == False
            
            # データ取得も失敗するはず
            start_date = date.today() - timedelta(days=7)
            end_date = date.today()
            result = data_service.fetch_and_save_data(start_date, end_date)
            assert result == False
    
    def test_data_retrieval_failures(self, temp_db):
        """データ取得失敗時のエラーハンドリングテスト"""
        _, Session = temp_db
        
        # 各データ取得メソッドで個別にテスト
        failure_scenarios = [
            'get_rhr_data',
            'get_hrv_data',
            'get_training_data'
        ]
        
        for fail_method in failure_scenarios:
            # 特定のメソッドで失敗するデータソース
            failing_data_source = FailingDataSource(fail_on=[fail_method])
            
            # 正常なリポジトリ
            repository = SQLiteRepository(Session)
            
            # データサービス
            data_service = DataService(data_source=failing_data_source, repository=repository)
            
            # 接続
            with patch.dict('os.environ', {'GARMIN_USERNAME': 'test', 'GARMIN_PASSWORD': 'test'}):
                data_service.connect()
                
                # データ取得と保存
                start_date = date.today() - timedelta(days=3)  # 少ない日数で十分
                end_date = date.today()
                
                # データ取得を試みる
                result = data_service.fetch_and_save_data(start_date, end_date)
                
                # 現在の実装では、データ取得メソッドのいずれかが失敗すると全体が失敗する
                assert result == False
    
    def test_data_save_failures(self, temp_db):
        """データ保存失敗時のエラーハンドリングテスト"""
        _, Session = temp_db
        
        # 各保存メソッドで個別にテスト
        failure_scenarios = [
            'save_rhr_data',
            'save_hrv_data',
            'save_activities'
        ]
        
        for fail_method in failure_scenarios:
            # 正常なデータソース
            data_source = FailingDataSource()
            
            # 特定のメソッドで失敗するリポジトリ
            failing_repository = FailingRepository(Session, fail_on=[fail_method])
            
            # データサービス
            data_service = DataService(data_source=data_source, repository=failing_repository)
            
            # 接続
            with patch.dict('os.environ', {'GARMIN_USERNAME': 'test', 'GARMIN_PASSWORD': 'test'}):
                data_service.connect()
                
                # データ取得と保存
                start_date = date.today() - timedelta(days=3)  # 少ない日数で十分
                end_date = date.today()
                
                # 保存に失敗するが、例外は発生しないはず
                result = data_service.fetch_and_save_data(start_date, end_date)
                
                if fail_method == 'save_rhr_data':
                    # RHRデータ保存に失敗すると全体が失敗
                    assert result == False
                elif fail_method == 'save_hrv_data':
                    # HRVデータ保存に失敗すると全体が失敗
                    assert result == False
                elif fail_method == 'save_activities':
                    # アクティビティ保存に失敗すると全体が失敗
                    assert result == False
    
    def test_multiple_failures(self, temp_db):
        """複数の障害が発生する場合のエラーハンドリングテスト"""
        _, Session = temp_db
        
        # 複数のメソッドで失敗するデータソース
        failing_data_source = FailingDataSource(fail_on=['get_rhr_data', 'get_hrv_data'])
        
        # 複数のメソッドで失敗するリポジトリ
        failing_repository = FailingRepository(Session, fail_on=['save_activities'])
        
        # データサービス
        data_service = DataService(data_source=failing_data_source, repository=failing_repository)
        
        # 接続
        with patch.dict('os.environ', {'GARMIN_USERNAME': 'test', 'GARMIN_PASSWORD': 'test'}):
            data_service.connect()
            
            # データ取得と保存
            start_date = date.today() - timedelta(days=3)
            end_date = date.today()
            
            # 複数のエラーがあるが、処理は続行されるはず
            result = data_service.fetch_and_save_data(start_date, end_date)
            
            # 複数のエラーがあるので、False
            assert result == False