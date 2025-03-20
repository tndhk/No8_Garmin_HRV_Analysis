import pytest
import os
import tempfile
from datetime import date, datetime, timedelta
from unittest.mock import patch

from app.service.data_service import DataService
from app.analysis.analysis_service import AnalysisService
from app.data_source.mock_data_source import MockDataSource
from app.models.database_models import init_db
from app.repository.sqlite_repository import SQLiteRepository


class TestDataFlowIntegration:
    """データフロー統合テスト"""
    
    @pytest.fixture
    def temp_db(self):
        """テスト用の一時的なSQLiteデータベースを作成"""
        # 一時ファイルの作成
        db_fd, db_path = tempfile.mkstemp(suffix='.db')
        db_url = f'sqlite:///{db_path}'
        
        # データベースの初期化
        engine, Session = init_db(db_url)
        
        yield db_url, Session
        
        # テスト後のクリーンアップ
        os.close(db_fd)
        os.unlink(db_path)
    
    @pytest.fixture
    def setup_services(self, temp_db):
        """テスト用のサービスをセットアップ"""
        db_url, Session = temp_db
        
        # モックデータソースを使用
        data_source = MockDataSource()
        
        # リポジトリの設定
        repository = SQLiteRepository(Session)
        
        # データサービスの設定
        data_service = DataService(data_source=data_source, repository=repository)
        
        # 分析サービスの設定
        analysis_service = AnalysisService()
        
        return data_service, analysis_service
    
    def test_end_to_end_data_flow(self, setup_services):
        """エンドツーエンドのデータフロー統合テスト"""
        data_service, analysis_service = setup_services
        
        # モックデータソースに接続
        success = data_service.connect()
        assert success == True
        
        # 日付範囲の設定（短めの期間でテスト）
        end_date = date.today()
        start_date = end_date - timedelta(days=29)  # 30日間
        
        # データ取得と保存
        success = data_service.fetch_and_save_data(start_date, end_date)
        assert success == True
        
        # 日別データの取得
        daily_data = data_service.get_daily_data(start_date, end_date)
        assert len(daily_data) == 30  # 30日分
        
        # 週別データの取得
        weekly_data = data_service.get_weekly_data(start_date, end_date)
        assert len(weekly_data) >= 4  # 少なくとも4週間分
        
        # 分析用データフレームの作成
        daily_df = analysis_service.create_time_series_dataframe(daily_data)
        assert len(daily_df) == 30
        
        weekly_df = analysis_service.create_weekly_dataframe(weekly_data)
        assert len(weekly_df) >= 4
        
        # L2とHRVの相関分析
        correlation = analysis_service.calculate_l2_hrv_correlation(weekly_df)
        assert 'correlation' in correlation
        
        # トレンド分析
        trend_analysis = analysis_service.generate_trend_analysis(weekly_df)
        assert 'message' in trend_analysis
        
        # レポート生成
        report = analysis_service.generate_summary_report(weekly_df)
        assert isinstance(report, str)
        assert len(report) > 0
    
    def test_data_retrieval_with_no_data(self, setup_services):
        """データがない状態でのデータ取得テスト"""
        data_service, analysis_service = setup_services
        
        # モックデータソースに接続
        success = data_service.connect()
        assert success == True
        
        # データを取得する前に、直接リポジトリからデータを取得
        end_date = date.today()
        start_date = end_date - timedelta(days=7)
        
        # データがない状態でのデータ取得
        daily_data = data_service.get_daily_data(start_date, end_date)
        assert len(daily_data) == 8  # 8日分（開始日と終了日を含む）
        
        # 活動がないことを確認
        for day in daily_data:
            assert day.rhr is None
            assert day.hrv is None
            assert len(day.activities) == 0