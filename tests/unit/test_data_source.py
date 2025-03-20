import pytest
from datetime import date, datetime, timedelta
from unittest.mock import MagicMock, patch

from app.data_source.data_source_interface import DataSourceInterface
from app.data_source.garmin_data_source import GarminDataSource
from app.data_source.mock_data_source import MockDataSource
from app.data_source.data_source_factory import DataSourceFactory


class TestDataSource:
    """データソースのテストクラス"""
    
    def test_data_source_interface(self):
        """DataSourceInterfaceの抽象メソッドが正しく定義されているかテスト"""
        # 抽象クラスなので直接インスタンス化はできない
        with pytest.raises(TypeError):
            DataSourceInterface()
    
    def test_mock_data_source_connect(self):
        """MockDataSourceのconnectメソッドをテスト"""
        mock_ds = MockDataSource()
        
        # 接続前のフラグ確認
        assert mock_ds.is_connected == False
        
        # 接続実行
        result = mock_ds.connect("dummy_user", "dummy_pass")
        
        # 接続後のフラグとリターン値を確認
        assert result == True
        assert mock_ds.is_connected == True
    
    def test_mock_data_source_get_rhr_data(self):
        """MockDataSourceのget_rhr_dataメソッドをテスト"""
        mock_ds = MockDataSource()
        mock_ds.connect("dummy_user", "dummy_pass")
        
        # 5日分のデータを要求
        start_date = date(2023, 1, 1)
        end_date = date(2023, 1, 5)
        
        rhr_data = mock_ds.get_rhr_data(start_date, end_date)
        
        # 結果の検証
        assert len(rhr_data) == 5  # 5日分取得できているか
        assert all("date" in item for item in rhr_data)  # 全項目にdateキーがあるか
        assert all("rhr" in item for item in rhr_data)   # 全項目にrhrキーがあるか
        
        # 日付順に並んでいるか
        dates = [item["date"] for item in rhr_data]
        expected_dates = [
            (start_date + timedelta(days=i)).isoformat() 
            for i in range((end_date - start_date).days + 1)
        ]
        assert dates == expected_dates
    
    def test_mock_data_source_get_hrv_data(self):
        """MockDataSourceのget_hrv_dataメソッドをテスト"""
        mock_ds = MockDataSource()
        mock_ds.connect("dummy_user", "dummy_pass")
        
        # 5日分のデータを要求
        start_date = date(2023, 1, 1)
        end_date = date(2023, 1, 5)
        
        hrv_data = mock_ds.get_hrv_data(start_date, end_date)
        
        # 結果の検証
        assert len(hrv_data) == 5  # 5日分取得できているか
        assert all("date" in item for item in hrv_data)  # 全項目にdateキーがあるか
        assert all("hrv" in item for item in hrv_data)   # 全項目にhrvキーがあるか
        
        # 日付順に並んでいるか
        dates = [item["date"] for item in hrv_data]
        expected_dates = [
            (start_date + timedelta(days=i)).isoformat() 
            for i in range((end_date - start_date).days + 1)
        ]
        assert dates == expected_dates
    
    def test_mock_data_source_get_training_data(self):
        """MockDataSourceのget_training_dataメソッドをテスト"""
        mock_ds = MockDataSource()
        mock_ds.connect("dummy_user", "dummy_pass")
        
        # 10日分のデータを要求（活動がある日を確実に含めるため）
        start_date = date(2023, 1, 1)
        end_date = date(2023, 1, 10)
        
        training_data = mock_ds.get_training_data(start_date, end_date)
        
        # 結果の検証
        assert len(training_data) == 10  # 10日分取得できているか
        assert all("date" in item for item in training_data)  # 全項目にdateキーがあるか
        assert all("activities" in item for item in training_data)  # 全項目にactivitiesキーがあるか
        
        # 少なくとも1つの活動データがあるか
        has_activities = any(len(item["activities"]) > 0 for item in training_data)
        assert has_activities == True
        
        # アクティビティの形式が正しいか
        for day_data in training_data:
            for activity in day_data["activities"]:
                assert "activity_id" in activity
                assert "activity_type" in activity
                assert "start_time" in activity
                assert "duration" in activity
                assert "is_l2_training" in activity
                assert "intensity" in activity
    
    def test_garmin_data_source_connect_fail(self):
        """GarminDataSourceの接続失敗をテスト"""
        with patch('garminconnect.Garmin') as mock_garmin:
            # ログイン失敗を模擬
            mock_client = MagicMock()
            mock_client.login.side_effect = Exception("Login failed")
            mock_garmin.return_value = mock_client
            
            garmin_ds = GarminDataSource()
            result = garmin_ds.connect("user", "wrong_pass")
            
            assert result == False
            assert garmin_ds.is_connected == False
    
    def test_garmin_data_source_connect_success(self):
        """GarminDataSourceの接続成功をテスト"""
        with patch('garminconnect.Garmin') as mock_garmin:
            # ログイン成功を模擬
            mock_client = MagicMock()
            mock_garmin.return_value = mock_client
            
            garmin_ds = GarminDataSource()
            result = garmin_ds.connect("user", "pass")
            
            assert result == True
            assert garmin_ds.is_connected == True
            mock_client.login.assert_called_once()
    
    def test_garmin_data_source_get_data_without_connection(self):
        """接続せずにデータ取得を試みた場合のテスト"""
        garmin_ds = GarminDataSource()
        
        with pytest.raises(ConnectionError):
            garmin_ds.get_rhr_data(date(2023, 1, 1), date(2023, 1, 5))
    
    def test_data_source_factory(self):
        """DataSourceFactoryのテスト"""
        # 環境変数が設定されていない状態でのデフォルト
        with patch('os.environ.get', return_value='garmin'):
            ds = DataSourceFactory.create_data_source()
            assert isinstance(ds, GarminDataSource)
        
        # mock指定
        ds = DataSourceFactory.create_data_source('mock')
        assert isinstance(ds, MockDataSource)
        
        # garmin指定
        ds = DataSourceFactory.create_data_source('garmin')
        assert isinstance(ds, GarminDataSource)
        
        # 不明なタイプの指定
        ds = DataSourceFactory.create_data_source('unknown')
        assert isinstance(ds, GarminDataSource)  # デフォルト値