import pytest
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import date, datetime, timedelta

from app.visualization.visualization_service import VisualizationService


class TestVisualizationService:
    """可視化サービスのテストクラス"""
    
    @pytest.fixture
    def visualization_service(self):
        """可視化サービスのインスタンスを作成"""
        return VisualizationService()
    
    @pytest.fixture
    def sample_daily_df(self):
        """テスト用の日別データフレームを作成"""
        # テスト用のデータを作成
        dates = pd.date_range(start='2023-01-01', periods=30)
        
        data = {
            'rhr': [60 - i * 0.2 + np.random.normal(0, 1) for i in range(30)],
            'hrv': [45 + i * 0.3 + np.random.normal(0, 2) for i in range(30)],
            'total_duration': [1.5 + np.random.normal(0, 0.5) for _ in range(30)],
            'l2_duration': [0.8 + np.random.normal(0, 0.3) for _ in range(30)],
            'l2_percentage': [55 + np.random.normal(0, 5) for _ in range(30)]
        }
        
        df = pd.DataFrame(data, index=dates)
        return df
    
    @pytest.fixture
    def sample_weekly_df(self):
        """テスト用の週別データフレームを作成"""
        # テスト用のデータを作成
        dates = pd.date_range(start='2023-01-01', periods=8, freq='W')
        
        data = {
            'week_end': dates + pd.Timedelta(days=6),
            'avg_rhr': [58 - i * 0.5 + np.random.normal(0, 0.5) for i in range(8)],
            'avg_hrv': [47 + i * 0.8 + np.random.normal(0, 1) for i in range(8)],
            'total_training_hours': [5 + i * 0.2 + np.random.normal(0, 0.5) for i in range(8)],
            'l2_hours': [3 + i * 0.3 + np.random.normal(0, 0.3) for i in range(8)],
            'l2_percentage': [60 + i * 1.5 + np.random.normal(0, 2) for i in range(8)]
        }
        
        df = pd.DataFrame(data, index=dates)
        return df
    
    def test_create_hrv_rhr_trend_plot(self, visualization_service, sample_daily_df):
        """HRV/RHRトレンドグラフ作成のテスト"""
        fig = visualization_service.create_hrv_rhr_trend_plot(sample_daily_df)
        
        # 結果がPlotlyのFigureオブジェクトであることを確認
        assert isinstance(fig, go.Figure)
        
        # サブプロットが2つあることを確認（HRVとRHR）
        assert len(fig.data) >= 2  # 移動平均線がある場合はさらに多くなる
        
        # グラフのタイトルが正しいことを確認
        assert "HRVとRHRの長期トレンド" in fig.layout.title.text
    
    def test_create_l2_training_plot(self, visualization_service, sample_daily_df):
        """L2トレーニング時間のグラフ作成のテスト"""
        fig = visualization_service.create_l2_training_plot(sample_daily_df)
        
        # 結果がPlotlyのFigureオブジェクトであることを確認
        assert isinstance(fig, go.Figure)
        
        # グラフのタイトルが正しいことを確認
        assert "L2トレーニング時間の推移" in fig.layout.title.text
    
    def test_create_correlation_plot_daily(self, visualization_service, sample_daily_df):
        """日別データでの相関グラフ作成のテスト"""
        fig = visualization_service.create_correlation_plot(sample_daily_df)
        
        # 結果がPlotlyのFigureオブジェクトであることを確認
        assert isinstance(fig, go.Figure)
    
    def test_create_correlation_plot_weekly(self, visualization_service, sample_weekly_df):
        """週別データでの相関グラフ作成のテスト"""
        fig = visualization_service.create_correlation_plot(sample_weekly_df)
        
        # 結果がPlotlyのFigureオブジェクトであることを確認
        assert isinstance(fig, go.Figure)
    
    def test_create_stacked_bar_chart(self, visualization_service, sample_weekly_df):
        """積み上げ棒グラフ作成のテスト"""
        fig = visualization_service.create_stacked_bar_chart(sample_weekly_df)
        
        # 結果がPlotlyのFigureオブジェクトであることを確認
        assert isinstance(fig, go.Figure)
        
        # グラフのタイトルが正しいことを確認
        assert "週別トレーニング時間の内訳" in fig.layout.title.text
    
    def test_create_l2_percentage_plot(self, visualization_service, sample_weekly_df):
        """L2トレーニング割合のグラフ作成のテスト"""
        fig = visualization_service.create_l2_percentage_plot(sample_weekly_df)
        
        # 結果がPlotlyのFigureオブジェクトであることを確認
        assert isinstance(fig, go.Figure)
        
        # グラフのタイトルが正しいことを確認
        assert "週別L2トレーニング割合" in fig.layout.title.text
    
    def test_create_heatmap(self, visualization_service, sample_weekly_df):
        """ヒートマップ作成のテスト"""
        fig = visualization_service.create_heatmap(sample_weekly_df)
        
        # 結果がPlotlyのFigureオブジェクトであることを確認
        assert isinstance(fig, go.Figure)
        
        # グラフのタイトルが正しいことを確認
        assert "L2トレーニング時間とHRVの関係ヒートマップ" in fig.layout.title.text
    
    def test_missing_data_handling(self, visualization_service):
        """データが不足している場合の処理テスト"""
        # 空のデータフレーム
        empty_df = pd.DataFrame()
        
        # 各メソッドが例外を発生させずに動作することを確認
        fig1 = visualization_service.create_hrv_rhr_trend_plot(empty_df)
        fig2 = visualization_service.create_l2_training_plot(empty_df)
        fig3 = visualization_service.create_correlation_plot(empty_df)
        fig4 = visualization_service.create_stacked_bar_chart(empty_df)
        fig5 = visualization_service.create_l2_percentage_plot(empty_df)
        fig6 = visualization_service.create_heatmap(empty_df)
        
        # すべての結果がPlotlyのFigureオブジェクトであることを確認
        assert isinstance(fig1, go.Figure)
        assert isinstance(fig2, go.Figure)
        assert isinstance(fig3, go.Figure)
        assert isinstance(fig4, go.Figure)
        assert isinstance(fig5, go.Figure)
        assert isinstance(fig6, go.Figure)