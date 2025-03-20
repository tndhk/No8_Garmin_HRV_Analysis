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
from app.visualization.visualization_service import VisualizationService
from app.data_source.mock_data_source import MockDataSource
from app.models.database_models import init_db
from app.repository.sqlite_repository import SQLiteRepository
from app.models.models import DailyData, WeeklyData, Activity


class TestVisualizationIntegration:
    """可視化サービスの統合テスト"""
    
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
        
        # 可視化サービスの設定
        visualization_service = VisualizationService()
        
        return data_service, analysis_service, visualization_service
    
    @pytest.fixture
    def prepare_test_data(self, setup_services):
        """テスト用のデータを準備"""
        data_service, analysis_service, _ = setup_services
        
        # モックデータソースに接続
        data_service.connect()
        
        # 日付範囲の設定
        end_date = date.today()
        start_date = end_date - timedelta(days=59)  # 60日間
        
        # データ取得と保存
        data_service.fetch_and_save_data(start_date, end_date)
        
        # 日別データと週別データの取得
        daily_data = data_service.get_daily_data(start_date, end_date)
        weekly_data = data_service.get_weekly_data(start_date, end_date)
        
        # データフレームの作成
        daily_df = analysis_service.create_time_series_dataframe(daily_data)
        weekly_df = analysis_service.create_weekly_dataframe(weekly_data)
        
        return daily_data, weekly_data, daily_df, weekly_df
    
    def test_visualization_data_flow(self, setup_services, prepare_test_data):
        """可視化サービスのデータフロー統合テスト"""
        _, _, visualization_service = setup_services
        _, _, daily_df, weekly_df = prepare_test_data
        
        # HRV/RHRトレンドグラフの作成
        hrv_rhr_fig = visualization_service.create_hrv_rhr_trend_plot(daily_df)
        assert hrv_rhr_fig is not None
        assert "HRVとRHRの長期トレンド" in hrv_rhr_fig.layout.title.text
        
        # L2トレーニング時間グラフの作成
        l2_fig = visualization_service.create_l2_training_plot(daily_df)
        assert l2_fig is not None
        assert "L2トレーニング時間の推移" in l2_fig.layout.title.text
        
        # 相関散布図の作成
        corr_fig = visualization_service.create_correlation_plot(weekly_df)
        assert corr_fig is not None
        
        # 積み上げ棒グラフの作成
        stack_fig = visualization_service.create_stacked_bar_chart(weekly_df)
        assert stack_fig is not None
        assert "週別トレーニング時間の内訳" in stack_fig.layout.title.text
        
        # L2トレーニング割合グラフの作成
        l2_pct_fig = visualization_service.create_l2_percentage_plot(weekly_df)
        assert l2_pct_fig is not None
        assert "週別L2トレーニング割合" in l2_pct_fig.layout.title.text
        
        # ヒートマップの作成
        heatmap_fig = visualization_service.create_heatmap(weekly_df)
        assert heatmap_fig is not None
    
    def test_partial_data_visualization(self, setup_services):
        """一部のデータのみが存在する場合の可視化テスト"""
        _, analysis_service, visualization_service = setup_services
        
        # HRVデータのみ存在する日別データを作成
        daily_data = []
        base_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        for i in range(30):
            date_obj = base_date - timedelta(days=i)
            daily = DailyData(
                date=date_obj,
                hrv=45 + i * 0.5,
                rhr=None,
                activities=[]
            )
            daily_data.append(daily)
        
        # データフレームを作成
        daily_df = analysis_service.create_time_series_dataframe(daily_data)
        
        # HRV/RHRトレンドグラフの作成（RHRはないがHRVはある）
        hrv_rhr_fig = visualization_service.create_hrv_rhr_trend_plot(daily_df)
        assert hrv_rhr_fig is not None
        assert len(hrv_rhr_fig.data) >= 1  # 少なくともHRVのグラフは存在するはず
        
        # L2トレーニング時間グラフの作成（アクティビティなし）
        l2_fig = visualization_service.create_l2_training_plot(daily_df)
        assert l2_fig is not None
        
        # RHRデータのみ存在する日別データを作成
        daily_data = []
        
        for i in range(30):
            date_obj = base_date - timedelta(days=i)
            daily = DailyData(
                date=date_obj,
                hrv=None,
                rhr=60 - i * 0.3,
                activities=[]
            )
            daily_data.append(daily)
        
        # データフレームを作成
        daily_df = analysis_service.create_time_series_dataframe(daily_data)
        
        # HRV/RHRトレンドグラフの作成（HRVはないがRHRはある）
        hrv_rhr_fig = visualization_service.create_hrv_rhr_trend_plot(daily_df)
        assert hrv_rhr_fig is not None
        assert len(hrv_rhr_fig.data) >= 1  # 少なくともRHRのグラフは存在するはず

    def test_empty_data_visualization(self, setup_services):
        """データが存在しない場合の可視化テスト"""
        _, analysis_service, visualization_service = setup_services
        
        # 空のデータフレームを作成
        empty_df = pd.DataFrame()
        
        # 各可視化メソッドがエラーなく実行できることを確認
        hrv_rhr_fig = visualization_service.create_hrv_rhr_trend_plot(empty_df)
        assert hrv_rhr_fig is not None
        
        l2_fig = visualization_service.create_l2_training_plot(empty_df)
        assert l2_fig is not None
        
        corr_fig = visualization_service.create_correlation_plot(empty_df)
        assert corr_fig is not None
        
        stack_fig = visualization_service.create_stacked_bar_chart(empty_df)
        assert stack_fig is not None
        
        l2_pct_fig = visualization_service.create_l2_percentage_plot(empty_df)
        assert l2_pct_fig is not None
        
        heatmap_fig = visualization_service.create_heatmap(empty_df)
        assert heatmap_fig is not None