import pytest
import os
import tempfile
import pandas as pd
import numpy as np
from datetime import date, datetime, timedelta
from pathlib import Path

# プロジェクトのルートディレクトリをPATHに追加
project_root = str(Path(__file__).parent.parent.parent)
import sys
sys.path.insert(0, project_root)

from app.service.data_service import DataService
from app.analysis.analysis_service import AnalysisService
from app.data_source.mock_data_source import MockDataSource
from app.models.database_models import init_db
from app.repository.sqlite_repository import SQLiteRepository
from app.models.models import DailyData, WeeklyData, Activity, RHRData, HRVData


class TestAnalysisIntegration:
    """分析サービスの統合テスト"""
    
    @pytest.fixture
    def temp_db(self):
        """テスト用の一時的なSQLiteデータベースを作成"""
        db_fd, db_path = tempfile.mkstemp(suffix='.db')
        db_url = f'sqlite:///{db_path}'
        
        engine, Session = init_db(db_url)
        
        yield db_url, Session
        
        os.close(db_fd)
        os.unlink(db_path)
    
    @pytest.fixture
    def setup_analysis_service(self):
        """分析サービスのセットアップ"""
        return AnalysisService()
    
    @pytest.fixture
    def setup_test_data(self, temp_db):
        """テスト用のデータを準備"""
        _, Session = temp_db
        
        # モックデータソースを使用
        data_source = MockDataSource()
        
        # リポジトリの設定
        repository = SQLiteRepository(Session)
        
        # データサービスの設定
        data_service = DataService(data_source=data_source, repository=repository)
        
        # モックデータソースに接続
        data_service.connect()
        
        # 日付範囲の設定
        end_date = date.today()
        start_date = end_date - timedelta(days=89)  # 90日間
        
        # データ取得と保存
        data_service.fetch_and_save_data(start_date, end_date)
        
        # 日別データと週別データの取得
        daily_data = data_service.get_daily_data(start_date, end_date)
        weekly_data = data_service.get_weekly_data(start_date, end_date)
        
        return daily_data, weekly_data
    
    def test_dataframe_creation(self, setup_analysis_service, setup_test_data):
        """データフレーム作成のテスト"""
        analysis_service = setup_analysis_service
        daily_data, weekly_data = setup_test_data
        
        # 日別データフレームの作成
        daily_df = analysis_service.create_time_series_dataframe(daily_data)
        
        # 結果の検証
        assert len(daily_df) == len(daily_data)
        assert 'rhr' in daily_df.columns
        assert 'hrv' in daily_df.columns
        assert 'total_duration' in daily_df.columns
        assert 'l2_duration' in daily_df.columns
        assert 'l2_percentage' in daily_df.columns
        
        # 週別データフレームの作成
        weekly_df = analysis_service.create_weekly_dataframe(weekly_data)
        
        # 結果の検証
        assert len(weekly_df) == len(weekly_data)
        assert 'avg_rhr' in weekly_df.columns
        assert 'avg_hrv' in weekly_df.columns
        assert 'total_training_hours' in weekly_df.columns
        assert 'l2_hours' in weekly_df.columns
        assert 'l2_percentage' in weekly_df.columns
    
    def test_correlation_analysis(self, setup_analysis_service, setup_test_data):
        """相関分析のテスト"""
        analysis_service = setup_analysis_service
        _, weekly_data = setup_test_data
        
        # 週別データフレームの作成
        weekly_df = analysis_service.create_weekly_dataframe(weekly_data)
        
        # L2トレーニングとHRVの相関分析
        hrv_corr = analysis_service.calculate_l2_hrv_correlation(weekly_df)
        
        # 結果の検証
        assert 'correlation' in hrv_corr
        assert 'p_value' in hrv_corr
        assert 'has_significant_correlation' in hrv_corr
        assert 'message' in hrv_corr
        
        # L2トレーニングとRHRの相関分析
        rhr_corr = analysis_service.calculate_l2_rhr_correlation(weekly_df)
        
        # 結果の検証
        assert 'correlation' in rhr_corr
        assert 'p_value' in rhr_corr
        assert 'has_significant_correlation' in rhr_corr
        assert 'message' in rhr_corr
    
    def test_time_lagged_correlation(self, setup_analysis_service, setup_test_data):
        """時間差相関分析のテスト"""
        analysis_service = setup_analysis_service
        _, weekly_data = setup_test_data
        
        # 週別データフレームの作成
        weekly_df = analysis_service.create_weekly_dataframe(weekly_data)
        
        # 時間差相関分析
        lagged_corr = analysis_service.calculate_time_lagged_correlation(weekly_df, lag_weeks=1)
        
        # 結果の検証
        assert 'hrv_correlation' in lagged_corr
        assert 'hrv_p_value' in lagged_corr
        assert 'rhr_correlation' in lagged_corr
        assert 'rhr_p_value' in lagged_corr
        assert 'message' in lagged_corr
        
        # 異なる遅延でのテスト
        lagged_corr_2 = analysis_service.calculate_time_lagged_correlation(weekly_df, lag_weeks=2)
        assert 'hrv_correlation' in lagged_corr_2
    
    def test_trend_analysis(self, setup_analysis_service, setup_test_data):
        """トレンド分析のテスト"""
        analysis_service = setup_analysis_service
        _, weekly_data = setup_test_data
        
        # 週別データフレームの作成
        weekly_df = analysis_service.create_weekly_dataframe(weekly_data)
        
        # トレンド分析
        trend_analysis = analysis_service.generate_trend_analysis(weekly_df)
        
        # 結果の検証
        assert 'message' in trend_analysis
        
        # 十分なデータがあれば詳細な結果も含まれる
        if len(weekly_df) >= 4:
            assert 'hrv_change' in trend_analysis
            assert 'rhr_change' in trend_analysis
            assert 'l2_change' in trend_analysis
    
    def test_summary_report(self, setup_analysis_service, setup_test_data):
        """サマリーレポート生成のテスト"""
        analysis_service = setup_analysis_service
        _, weekly_data = setup_test_data
        
        # 週別データフレームの作成
        weekly_df = analysis_service.create_weekly_dataframe(weekly_data)
        
        # サマリーレポート生成
        report = analysis_service.generate_summary_report(weekly_df)
        
        # 結果の検証
        assert isinstance(report, str)
        assert len(report) > 0
        
        # レポートには各セクションが含まれているはず
        assert "# HRV/RHR長期トレンド分析レポート" in report
        assert "## 分析期間" in report
        assert "## 長期トレンド" in report
        assert "## 相関分析" in report
        assert "## 推奨事項" in report
    
    def test_analysis_with_partial_data(self, setup_analysis_service):
        """一部のデータのみが存在する場合の分析テスト"""
        analysis_service = setup_analysis_service
        
        # HRVデータのみ存在する日別データ
        daily_data_hrv_only = []
        base_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        for i in range(30):
            date_obj = base_date - timedelta(days=i)
            daily = DailyData(
                date=date_obj,
                hrv=45 + i * 0.5,
                rhr=None,
                activities=[]
            )
            daily_data_hrv_only.append(daily)
        
        # データフレームの作成
        daily_df_hrv_only = analysis_service.create_time_series_dataframe(daily_data_hrv_only)
        
        # 結果の検証
        assert 'hrv' in daily_df_hrv_only.columns
        assert daily_df_hrv_only['rhr'].isna().all()  # RHRはすべてNaN
        
        # アクティビティデータのみ存在する日別データ
        daily_data_activities_only = []
        
        for i in range(30):
            date_obj = base_date - timedelta(days=i)
            
            activities = []
            if i % 3 == 0:  # 3日ごとにアクティビティを追加
                activity = Activity(
                    activity_id=f"test_{i}",
                    date=date_obj,
                    activity_type="running",
                    start_time=date_obj.replace(hour=10),
                    duration=3600,
                    distance=5000,
                    is_l2_training=True,
                    intensity="L2"
                )
                activities.append(activity)
            
            daily = DailyData(
                date=date_obj,
                hrv=None,
                rhr=None,
                activities=activities
            )
            daily_data_activities_only.append(daily)
        
        # データフレームの作成
        daily_df_activities_only = analysis_service.create_time_series_dataframe(daily_data_activities_only)
        
        # 結果の検証
        assert daily_df_activities_only['hrv'].isna().all()  # HRVはすべてNaN
        assert daily_df_activities_only['rhr'].isna().all()  # RHRはすべてNaN
        assert 'total_duration' in daily_df_activities_only.columns
        assert not daily_df_activities_only['total_duration'].isna().all()  # 活動時間が存在
    
    def test_analysis_with_unusual_data(self, setup_analysis_service):
        """異常値を含むデータでの分析テスト"""
        analysis_service = setup_analysis_service
        
        # 異常値を含む日別データの作成
        daily_data = []
        base_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        for i in range(30):
            date_obj = base_date - timedelta(days=i)
            
            # 10日目に異常値を入れる
            if i == 10:
                hrv = 200  # 通常より非常に高い値
                rhr = 30   # 通常より非常に低い値
            else:
                hrv = 45 + i * 0.5
                rhr = 60 - i * 0.3
            
            daily = DailyData(
                date=date_obj,
                hrv=hrv,
                rhr=rhr,
                activities=[]
            )
            daily_data.append(daily)
        
        # データフレームの作成
        daily_df = analysis_service.create_time_series_dataframe(daily_data)
        
        # 結果の検証 - データフレーム作成は成功するはず
        assert len(daily_df) == 30
        assert 'hrv' in daily_df.columns
        assert 'rhr' in daily_df.columns
        
        # 週別データを作成
        weekly_data = []
        
        # 4週間分のデータを作成
        start_idx = 0
        for week in range(4):
            end_idx = start_idx + 7
            if end_idx > len(daily_data):
                end_idx = len(daily_data)
            
            week_days = daily_data[start_idx:end_idx]
            
            weekly = WeeklyData(
                start_date=week_days[0].date,
                end_date=week_days[-1].date,
                daily_data=week_days
            )
            
            weekly_data.append(weekly)
            start_idx = end_idx
        
        # 週別データフレームの作成
        weekly_df = analysis_service.create_weekly_dataframe(weekly_data)
        
        # 結果の検証 - データフレーム作成は成功するはず
        assert len(weekly_df) == 4
        assert 'avg_hrv' in weekly_df.columns
        assert 'avg_rhr' in weekly_df.columns
        
        # トレンド分析
        trend_analysis = analysis_service.generate_trend_analysis(weekly_df)
        assert 'message' in trend_analysis
        
        # 相関分析
        hrv_corr = analysis_service.calculate_l2_hrv_correlation(weekly_df)
        assert 'correlation' in hrv_corr