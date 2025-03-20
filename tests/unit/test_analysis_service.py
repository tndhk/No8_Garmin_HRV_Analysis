import pytest
import pandas as pd
import numpy as np
from datetime import date, datetime, timedelta

from app.analysis.analysis_service import AnalysisService
from app.models.models import DailyData, WeeklyData, Activity


class TestAnalysisService:
    """分析サービスのテストクラス"""
    
    @pytest.fixture
    def analysis_service(self):
        """分析サービスのインスタンスを作成"""
        return AnalysisService()
    
    @pytest.fixture
    def sample_daily_data(self):
        """テスト用の日別データを作成"""
        start_date = datetime(2023, 1, 1)
        daily_data = []
        
        for i in range(30):  # 30日分のデータ
            current_date = start_date + timedelta(days=i)
            
            # HRVとRHRのデータ（時間経過でHRVは向上、RHRは低下するトレンド）
            # ランダム性も加える
            hrv_base = 45 + (i / 10)  # 時間経過で少しずつ上昇
            hrv = hrv_base + np.random.normal(0, 2)  # ランダムノイズ
            
            rhr_base = 60 - (i / 15)  # 時間経過で少しずつ低下
            rhr = rhr_base + np.random.normal(0, 1.5)  # ランダムノイズ
            
            # 活動データ
            activities = []
            
            # 3日に1日はL2トレーニング
            if i % 3 == 0:
                l2_activity = Activity(
                    activity_id=f"l2_{i}",
                    date=current_date,
                    activity_type="cycling",
                    start_time=current_date.replace(hour=10),
                    duration=3600,  # 1時間
                    distance=30000,
                    is_l2_training=True,
                    intensity="L2"
                )
                activities.append(l2_activity)
            
            # 5日に1日は高強度トレーニング
            if i % 5 == 0:
                high_activity = Activity(
                    activity_id=f"high_{i}",
                    date=current_date,
                    activity_type="running",
                    start_time=current_date.replace(hour=18),
                    duration=1800,  # 30分
                    distance=5000,
                    is_l2_training=False,
                    intensity="High"
                )
                activities.append(high_activity)
            
            daily = DailyData(
                date=current_date,
                rhr=int(round(rhr)),
                hrv=round(hrv, 1),
                activities=activities
            )
            
            daily_data.append(daily)
        
        return daily_data
    
    @pytest.fixture
    def sample_weekly_data(self, sample_daily_data):
        """テスト用の週別データを作成（日別データから）"""
        # 週ごとにグループ化
        weekly_data = []
        
        # 4週間分のデータを作成
        for week in range(4):
            start_idx = week * 7
            end_idx = start_idx + 7
            
            if end_idx > len(sample_daily_data):
                end_idx = len(sample_daily_data)
            
            week_days = sample_daily_data[start_idx:end_idx]
            
            weekly = WeeklyData(
                start_date=week_days[0].date,
                end_date=week_days[-1].date,
                daily_data=week_days
            )
            
            weekly_data.append(weekly)
        
        return weekly_data
    
    def test_create_time_series_dataframe(self, analysis_service, sample_daily_data):
        """時系列データフレーム作成のテスト"""
        df = analysis_service.create_time_series_dataframe(sample_daily_data)
        
        # データフレームの形状をチェック
        assert len(df) == len(sample_daily_data)
        assert 'rhr' in df.columns
        assert 'hrv' in df.columns
        assert 'total_duration' in df.columns
        assert 'l2_duration' in df.columns
        assert 'l2_percentage' in df.columns
        
        # インデックスが日付型か
        assert isinstance(df.index, pd.DatetimeIndex)
        
        # 数値が正しく変換されているか
        for i, day in enumerate(sample_daily_data):
            assert df.iloc[i]['rhr'] == day.rhr
            assert df.iloc[i]['hrv'] == day.hrv
            
            # 活動時間の計算
            total_duration = sum(a.duration for a in day.activities) / 3600  # 時間単位
            l2_duration = sum(a.duration for a in day.activities if a.is_l2_training) / 3600
            
            assert pytest.approx(df.iloc[i]['total_duration']) == total_duration
            assert pytest.approx(df.iloc[i]['l2_duration']) == l2_duration
    
    def test_create_weekly_dataframe(self, analysis_service, sample_weekly_data):
        """週別データフレーム作成のテスト"""
        df = analysis_service.create_weekly_dataframe(sample_weekly_data)
        
        # データフレームの形状をチェック
        assert len(df) == len(sample_weekly_data)
        assert 'avg_rhr' in df.columns
        assert 'avg_hrv' in df.columns
        assert 'total_training_hours' in df.columns
        assert 'l2_hours' in df.columns
        assert 'l2_percentage' in df.columns
        
        # インデックスが日付型か
        assert isinstance(df.index, pd.DatetimeIndex)
        
        # 週ごとの集計が正しいか
        for i, week in enumerate(sample_weekly_data):
            # 平均RHR
            rhr_values = [d.rhr for d in week.daily_data if d.rhr is not None]
            expected_avg_rhr = sum(rhr_values) / len(rhr_values) if rhr_values else None
            if expected_avg_rhr is not None:
                assert pytest.approx(df.iloc[i]['avg_rhr']) == expected_avg_rhr
            
            # 平均HRV
            hrv_values = [d.hrv for d in week.daily_data if d.hrv is not None]
            expected_avg_hrv = sum(hrv_values) / len(hrv_values) if hrv_values else None
            if expected_avg_hrv is not None:
                assert pytest.approx(df.iloc[i]['avg_hrv']) == expected_avg_hrv
            
            # L2トレーニング時間
            expected_l2_hours = sum(d.l2_duration_hours for d in week.daily_data)
            assert pytest.approx(df.iloc[i]['l2_hours']) == expected_l2_hours
    
    def test_calculate_l2_hrv_correlation(self, analysis_service):
        """L2トレーニングとHRVの相関計算のテスト"""
        # テスト用データフレーム作成（正の相関を持つデータ）
        data = {
            'week_start': pd.date_range(start='2023-01-01', periods=10, freq='W'),
            'avg_hrv': [45, 46, 47, 48, 49, 50, 51, 52, 53, 54],  # 上昇トレンド
            'l2_hours': [1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5, 5.5]  # 上昇トレンド
        }
        df = pd.DataFrame(data)
        df.set_index('week_start', inplace=True)
        
        # 相関分析実行
        result = analysis_service.calculate_l2_hrv_correlation(df)
        
        # 結果の検証
        assert 'correlation' in result
        assert 'p_value' in result
        assert 'has_significant_correlation' in result
        assert 'message' in result
        
        # 正の強い相関があるはず
        assert result['correlation'] > 0.9
        assert result['p_value'] < 0.05
        assert result['has_significant_correlation'] == True
        
        # 負の相関のケースもテスト
        data['avg_hrv'] = [54, 53, 52, 51, 50, 49, 48, 47, 46, 45]  # 下降トレンド
        df = pd.DataFrame(data)
        df.set_index('week_start', inplace=True)
        
        result = analysis_service.calculate_l2_hrv_correlation(df)
        
        # 負の強い相関があるはず
        assert result['correlation'] < -0.9
        assert result['p_value'] < 0.05
        assert result['has_significant_correlation'] == True
    
    def test_calculate_time_lagged_correlation(self, analysis_service):
        """時間差相関分析のテスト"""
        # テスト用データフレーム作成（1週間遅れの効果を模擬）
        data = {
            'week_start': pd.date_range(start='2023-01-01', periods=12, freq='W'),
            'avg_hrv': [45, 45, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54],  # 遅延して上昇
            'avg_rhr': [60, 60, 60, 59, 58, 57, 56, 55, 54, 53, 52, 51],  # 遅延して下降
            'l2_hours': [1, 2, 3, 4, 5, 5, 5, 5, 5, 5, 5, 5]  # 最初に増加、その後一定
        }
        df = pd.DataFrame(data)
        df.set_index('week_start', inplace=True)
        
        # 時間差相関分析実行（1週間遅延）
        result = analysis_service.calculate_time_lagged_correlation(df, lag_weeks=1)
        
        # 結果の検証
        assert 'hrv_correlation' in result
        assert 'hrv_p_value' in result
        assert 'rhr_correlation' in result
        assert 'rhr_p_value' in result
        assert 'message' in result
        
        # 正のHRV相関と負のRHR相関があるはず
        assert result['hrv_correlation'] > 0
        assert result['rhr_correlation'] < 0
    
    def test_generate_trend_analysis(self, analysis_service):
        """トレンド分析のテスト"""
        # テスト用データフレーム作成（改善トレンドを持つデータ）
        data = {
            'week_start': pd.date_range(start='2023-01-01', periods=8, freq='W'),
            'avg_hrv': [45, 46, 47, 48, 49, 50, 51, 52],  # 上昇トレンド
            'avg_rhr': [60, 59, 58, 57, 56, 55, 54, 53],  # 下降トレンド
            'l2_hours': [1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5],  # 上昇トレンド
            'total_training_hours': [2, 3, 3, 4, 5, 6, 7, 8]  # 上昇トレンド
        }
        df = pd.DataFrame(data)
        df.set_index('week_start', inplace=True)
        
        # トレンド分析実行
        result = analysis_service.generate_trend_analysis(df)
        
        # 結果の検証
        assert 'hrv_change' in result
        assert 'rhr_change' in result
        assert 'l2_change' in result
        assert 'message' in result
        
        # 前半と後半で改善があるはず
        assert result['hrv_change'] > 0  # HRVは増加
        assert result['rhr_change'] < 0  # RHRは減少（改善）
        assert result['l2_change'] > 0   # L2トレーニングは増加
    
    def test_generate_summary_report(self, analysis_service):
        """サマリーレポート生成のテスト"""
        # テスト用データフレーム作成
        data = {
            'week_start': pd.date_range(start='2023-01-01', periods=8, freq='W'),
            'avg_hrv': [45, 46, 47, 48, 49, 50, 51, 52],  # 上昇トレンド
            'avg_rhr': [60, 59, 58, 57, 56, 55, 54, 53],  # 下降トレンド
            'l2_hours': [1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5],  # 上昇トレンド
            'total_training_hours': [2, 3, 3, 4, 5, 6, 7, 8]  # 上昇トレンド
        }
        df = pd.DataFrame(data)
        df.set_index('week_start', inplace=True)
        
        # レポート生成
        report = analysis_service.generate_summary_report(df)
        
        # 結果の検証
        assert isinstance(report, str)
        assert len(report) > 0
        
        # レポートに含まれるべきセクション
        assert "# HRV/RHR長期トレンド分析レポート" in report
        assert "## 分析期間" in report
        assert "## 長期トレンド" in report
        assert "## 相関分析" in report
        assert "## 推奨事項" in report