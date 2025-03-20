import pytest
from datetime import date, datetime, timedelta
from unittest.mock import MagicMock, patch

from app.service.data_service import DataService
from app.models.models import RHRData, HRVData, Activity, DailyData, WeeklyData


class TestDataService:
    """データサービスのテストクラス"""
    
    @pytest.fixture
    def mock_data_source(self):
        """モックデータソースを作成"""
        mock_ds = MagicMock()
        mock_ds.connect.return_value = True
        return mock_ds
    
    @pytest.fixture
    def mock_repository(self):
        """モックリポジトリを作成"""
        mock_repo = MagicMock()
        mock_repo.save_rhr_data.return_value = True
        mock_repo.save_hrv_data.return_value = True
        mock_repo.save_activities.return_value = True
        return mock_repo
    
    @pytest.fixture
    def data_service(self, mock_data_source, mock_repository):
        """テスト用のDataServiceインスタンスを作成"""
        return DataService(
            data_source=mock_data_source,
            repository=mock_repository
        )
    
    def test_connect_success(self, data_service, mock_data_source):
        """接続成功のテスト"""
        with patch.dict('os.environ', {'GARMIN_USERNAME': 'test_user', 'GARMIN_PASSWORD': 'test_pass'}):
            result = data_service.connect()
            
            assert result == True
            assert data_service.is_connected == True
            mock_data_source.connect.assert_called_once_with('test_user', 'test_pass')
    
    def test_connect_failure(self, data_service, mock_data_source):
        """接続失敗のテスト"""
        mock_data_source.connect.return_value = False
        
        with patch.dict('os.environ', {'GARMIN_USERNAME': 'test_user', 'GARMIN_PASSWORD': 'test_pass'}):
            result = data_service.connect()
            
            assert result == False
            assert data_service.is_connected == False
    
    def test_connect_missing_credentials(self, data_service, mock_data_source):
        """認証情報が不足している場合のテスト"""
        with patch.dict('os.environ', {}, clear=True):
            result = data_service.connect()
            
            assert result == False
            mock_data_source.connect.assert_not_called()
    
    def test_ensure_connected_already_connected(self, data_service):
        """すでに接続済みの場合のテスト"""
        data_service.is_connected = True
        
        result = data_service.ensure_connected()
        
        assert result == True
    
    def test_ensure_connected_reconnect(self, data_service):
        """再接続が必要な場合のテスト"""
        data_service.is_connected = False
        
        with patch.object(data_service, 'connect', return_value=True):
            result = data_service.ensure_connected()
            
            assert result == True
            data_service.connect.assert_called_once()
    
    def test_fetch_and_save_data_success(self, data_service):
        """データ取得・保存成功のテスト"""
        data_service.is_connected = True
        
        with patch.object(data_service, '_fetch_and_save_rhr', return_value=True) as mock_rhr, \
             patch.object(data_service, '_fetch_and_save_hrv', return_value=True) as mock_hrv, \
             patch.object(data_service, '_fetch_and_save_training', return_value=True) as mock_training:
            
            start_date = date(2023, 1, 1)
            end_date = date(2023, 1, 7)
            
            result = data_service.fetch_and_save_data(start_date, end_date)
            
            assert result == True
            mock_rhr.assert_called_once_with(start_date, end_date)
            mock_hrv.assert_called_once_with(start_date, end_date)
            mock_training.assert_called_once_with(start_date, end_date)
    
    def test_fetch_and_save_data_not_connected(self, data_service):
        """未接続状態でのデータ取得・保存テスト"""
        data_service.is_connected = False
        
        with patch.object(data_service, 'ensure_connected', return_value=False):
            start_date = date(2023, 1, 1)
            end_date = date(2023, 1, 7)
            
            result = data_service.fetch_and_save_data(start_date, end_date)
            
            assert result == False
    
    def test_fetch_and_save_rhr(self, data_service, mock_data_source, mock_repository):
        """RHRデータ取得・保存のテスト"""
        # モックデータの準備
        mock_rhr_data = [
            {'date': '2023-01-01', 'rhr': 60},
            {'date': '2023-01-02', 'rhr': 58}
        ]
        mock_data_source.get_rhr_data.return_value = mock_rhr_data
        
        start_date = date(2023, 1, 1)
        end_date = date(2023, 1, 2)
        
        result = data_service._fetch_and_save_rhr(start_date, end_date)
        
        assert result == True
        mock_data_source.get_rhr_data.assert_called_once_with(start_date, end_date)
        mock_repository.save_rhr_data.assert_called_once()
        
        # 保存されたデータが正しく変換されているか確認
        saved_data = mock_repository.save_rhr_data.call_args[0][0]
        assert len(saved_data) == 2
        assert isinstance(saved_data[0], RHRData)
        assert saved_data[0].rhr == 60
    
    def test_fetch_and_save_hrv(self, data_service, mock_data_source, mock_repository):
        """HRVデータ取得・保存のテスト"""
        # モックデータの準備
        mock_hrv_data = [
            {'date': '2023-01-01', 'hrv': 45.5},
            {'date': '2023-01-02', 'hrv': 48.2}
        ]
        mock_data_source.get_hrv_data.return_value = mock_hrv_data
        
        start_date = date(2023, 1, 1)
        end_date = date(2023, 1, 2)
        
        result = data_service._fetch_and_save_hrv(start_date, end_date)
        
        assert result == True
        mock_data_source.get_hrv_data.assert_called_once_with(start_date, end_date)
        mock_repository.save_hrv_data.assert_called_once()
        
        # 保存されたデータが正しく変換されているか確認
        saved_data = mock_repository.save_hrv_data.call_args[0][0]
        assert len(saved_data) == 2
        assert isinstance(saved_data[0], HRVData)
        assert saved_data[0].hrv == 45.5
    
    def test_fetch_and_save_training(self, data_service, mock_data_source, mock_repository):
        """トレーニングデータ取得・保存のテスト"""
        # モックデータの準備
        mock_training_data = [
            {'date': '2023-01-01', 'activities': [
                {'activity_id': 'act1', 'activity_type': 'running', 'start_time': '2023-01-01T10:00:00',
                 'duration': 3600, 'distance': 5000, 'is_l2_training': True, 'intensity': 'L2'}
            ]},
            {'date': '2023-01-02', 'activities': []}
        ]
        mock_data_source.get_training_data.return_value = mock_training_data
        
        start_date = date(2023, 1, 1)
        end_date = date(2023, 1, 2)
        
        result = data_service._fetch_and_save_training(start_date, end_date)
        
        assert result == True
        mock_data_source.get_training_data.assert_called_once_with(start_date, end_date)
        mock_repository.save_activities.assert_called_once()
        
        # 保存されたデータが正しく変換されているか確認
        saved_data = mock_repository.save_activities.call_args[0][0]
        assert len(saved_data) == 1
        assert isinstance(saved_data[0], Activity)
        assert saved_data[0].activity_id == 'act1'
        assert saved_data[0].is_l2_training == True
    
    def test_fetch_and_save_training_no_activities(self, data_service, mock_data_source, mock_repository):
        """アクティビティがない場合のトレーニングデータ取得・保存テスト"""
        # アクティビティがないデータ
        mock_training_data = [
            {'date': '2023-01-01', 'activities': []},
            {'date': '2023-01-02', 'activities': []}
        ]
        mock_data_source.get_training_data.return_value = mock_training_data
        
        start_date = date(2023, 1, 1)
        end_date = date(2023, 1, 2)
        
        result = data_service._fetch_and_save_training(start_date, end_date)
        
        assert result == True
        mock_data_source.get_training_data.assert_called_once_with(start_date, end_date)
        # アクティビティがないのでsave_activitiesは呼ばれない
        mock_repository.save_activities.assert_not_called()
    
    def test_get_daily_data(self, data_service, mock_repository):
        """日別データ取得のテスト"""
        start_date = date(2023, 1, 1)
        end_date = date(2023, 1, 7)
        
        expected_data = [DailyData(date=datetime(2023, 1, 1))]
        mock_repository.get_daily_data.return_value = expected_data
        
        result = data_service.get_daily_data(start_date, end_date)
        
        assert result == expected_data
        mock_repository.get_daily_data.assert_called_once_with(start_date, end_date)
    
    def test_get_weekly_data(self, data_service, mock_repository):
        """週別データ取得のテスト"""
        start_date = date(2023, 1, 1)
        end_date = date(2023, 1, 28)
        
        expected_data = [WeeklyData(
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 1, 7),
            daily_data=[]
        )]
        mock_repository.get_weekly_data.return_value = expected_data
        
        result = data_service.get_weekly_data(start_date, end_date)
        
        assert result == expected_data
        mock_repository.get_weekly_data.assert_called_once_with(start_date, end_date)