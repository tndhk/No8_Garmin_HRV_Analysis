import logging
import numpy as np
import pandas as pd
from datetime import date, datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple

from app.models.models import DailyData, WeeklyData

logger = logging.getLogger(__name__)

class AnalysisService:
    """
    データ分析サービスクラス
    HRV/RHRとL2トレーニングの関係などを分析する
    """
    
    def create_time_series_dataframe(self, daily_data: List[DailyData]) -> pd.DataFrame:
        """
        日別データからPandasデータフレームを作成する
        
        Args:
            daily_data: 日別データのリスト
            
        Returns:
            pd.DataFrame: 分析用データフレーム
        """
        data = []
        
        for daily in daily_data:
            row = {
                'date': daily.date,
                'rhr': daily.rhr,
                'hrv': daily.hrv,
                'total_duration': daily.total_duration / 3600,  # 時間単位に変換
                'l2_duration': daily.l2_duration / 3600,  # 時間単位に変換
                'l2_percentage': daily.l2_percentage
            }
            data.append(row)
        
        df = pd.DataFrame(data)
        df.set_index('date', inplace=True)
        return df
    
    def create_weekly_dataframe(self, weekly_data: List[WeeklyData]) -> pd.DataFrame:
        """
        週別データからPandasデータフレームを作成する
        
        Args:
            weekly_data: 週別データのリスト
            
        Returns:
            pd.DataFrame: 週別分析用データフレーム
        """
        data = []
        
        for weekly in weekly_data:
            row = {
                'week_start': weekly.start_date,
                'week_end': weekly.end_date,
                'avg_rhr': weekly.avg_rhr,
                'avg_hrv': weekly.avg_hrv,
                'total_training_hours': weekly.total_training_hours,
                'l2_hours': weekly.total_l2_hours,
                'l2_percentage': weekly.l2_percentage
            }
            data.append(row)
        
        df = pd.DataFrame(data)
        df.set_index('week_start', inplace=True)
        return df
    
    def calculate_l2_hrv_correlation(self, weekly_df: pd.DataFrame) -> Dict[str, Any]:
        """
        L2トレーニング時間とHRVの相関関係を計算する
        
        Args:
            weekly_df: 週別データフレーム
            
        Returns:
            Dict[str, Any]: 相関関係の分析結果
        """
        # NaNを除外したデータで相関を計算
        data = weekly_df.dropna(subset=['avg_hrv', 'l2_hours'])
        
        if len(data) < 2:
            logger.warning("相関計算に十分なデータがありません")
            return {
                'correlation': None,
                'p_value': None,
                'has_significant_correlation': False,
                'weeks_analyzed': len(data),
                'message': "相関分析に十分なデータがありません（週数: {})".format(len(data))
            }
        
        try:
            # L2時間とHRVの相関係数を計算
            correlation = data['l2_hours'].corr(data['avg_hrv'])
            
            # 統計的有意性（p値）を計算
            from scipy import stats
            r, p_value = stats.pearsonr(data['l2_hours'], data['avg_hrv'])
            
            significant = p_value < 0.05
            
            message = f"L2トレーニング時間とHRVの相関係数: {correlation:.3f} (p値: {p_value:.3f})"
            if significant:
                if correlation > 0:
                    message += "\nL2トレーニングの増加はHRVの向上と有意に関連しています。"
                else:
                    message += "\nL2トレーニングの増加はHRVの低下と有意に関連しています。"
            else:
                message += "\n統計的に有意な相関関係は見られませんでした。"
            
            return {
                'correlation': correlation,
                'p_value': p_value,
                'has_significant_correlation': significant,
                'weeks_analyzed': len(data),
                'message': message
            }
            
        except Exception as e:
            logger.error(f"相関計算中にエラーが発生しました: {str(e)}")
            return {
                'correlation': None,
                'p_value': None,
                'has_significant_correlation': False,
                'weeks_analyzed': len(data),
                'message': f"相関計算中にエラーが発生しました: {str(e)}"
            }
    
    def calculate_l2_rhr_correlation(self, weekly_df: pd.DataFrame) -> Dict[str, Any]:
        """
        L2トレーニング時間とRHRの相関関係を計算する
        
        Args:
            weekly_df: 週別データフレーム
            
        Returns:
            Dict[str, Any]: 相関関係の分析結果
        """
        # NaNを除外したデータで相関を計算
        data = weekly_df.dropna(subset=['avg_rhr', 'l2_hours'])
        
        if len(data) < 2:
            logger.warning("相関計算に十分なデータがありません")
            return {
                'correlation': None,
                'p_value': None,
                'has_significant_correlation': False,
                'weeks_analyzed': len(data),
                'message': "相関分析に十分なデータがありません（週数: {})".format(len(data))
            }
        
        try:
            # L2時間とRHRの相関係数を計算
            correlation = data['l2_hours'].corr(data['avg_rhr'])
            
            # 統計的有意性（p値）を計算
            from scipy import stats
            r, p_value = stats.pearsonr(data['l2_hours'], data['avg_rhr'])
            
            significant = p_value < 0.05
            
            message = f"L2トレーニング時間とRHRの相関係数: {correlation:.3f} (p値: {p_value:.3f})"
            if significant:
                if correlation < 0:
                    message += "\nL2トレーニングの増加はRHRの低下（改善）と有意に関連しています。"
                else:
                    message += "\nL2トレーニングの増加はRHRの上昇と有意に関連しています。"
            else:
                message += "\n統計的に有意な相関関係は見られませんでした。"
            
            return {
                'correlation': correlation,
                'p_value': p_value,
                'has_significant_correlation': significant,
                'weeks_analyzed': len(data),
                'message': message
            }
            
        except Exception as e:
            logger.error(f"相関計算中にエラーが発生しました: {str(e)}")
            return {
                'correlation': None,
                'p_value': None,
                'has_significant_correlation': False,
                'weeks_analyzed': len(data),
                'message': f"相関計算中にエラーが発生しました: {str(e)}"
            }
    
    def calculate_time_lagged_correlation(self, weekly_df: pd.DataFrame, lag_weeks: int = 1) -> Dict[str, Any]:
        """
        L2トレーニングとその後のHRV/RHRの時間差相関を計算する
        
        Args:
            weekly_df: 週別データフレーム
            lag_weeks: 遅延させる週数
            
        Returns:
            Dict[str, Any]: 時間差相関の分析結果
        """
        # L2時間を遅延させる
        shifted_df = weekly_df.copy()
        shifted_df['l2_hours_lagged'] = shifted_df['l2_hours'].shift(lag_weeks)
        
        # NaNを除外
        clean_df = shifted_df.dropna(subset=['avg_hrv', 'avg_rhr', 'l2_hours_lagged'])
        
        if len(clean_df) < 2:
            return {
                'hrv_correlation': None,
                'hrv_p_value': None,
                'rhr_correlation': None,
                'rhr_p_value': None,
                'weeks_analyzed': len(clean_df),
                'message': f"時間差相関分析（{lag_weeks}週遅延）に十分なデータがありません"
            }
        
        try:
            from scipy import stats
            
            # HRVとの時間差相関
            hrv_r, hrv_p = stats.pearsonr(clean_df['l2_hours_lagged'], clean_df['avg_hrv'])
            
            # RHRとの時間差相関
            rhr_r, rhr_p = stats.pearsonr(clean_df['l2_hours_lagged'], clean_df['avg_rhr'])
            
            hrv_significant = hrv_p < 0.05
            rhr_significant = rhr_p < 0.05
            
            message = f"{lag_weeks}週前のL2トレーニングと現在のHRV/RHRの相関分析:\n"
            
            message += f"HRV相関: {hrv_r:.3f} (p値: {hrv_p:.3f}) - "
            if hrv_significant:
                if hrv_r > 0:
                    message += "過去のL2トレーニングは現在のHRV向上と有意に関連\n"
                else:
                    message += "過去のL2トレーニングは現在のHRV低下と有意に関連\n"
            else:
                message += "有意な関連なし\n"
            
            message += f"RHR相関: {rhr_r:.3f} (p値: {rhr_p:.3f}) - "
            if rhr_significant:
                if rhr_r < 0:
                    message += "過去のL2トレーニングは現在のRHR低下（改善）と有意に関連"
                else:
                    message += "過去のL2トレーニングは現在のRHR上昇と有意に関連"
            else:
                message += "有意な関連なし"
            
            return {
                'hrv_correlation': hrv_r,
                'hrv_p_value': hrv_p,
                'hrv_significant': hrv_significant,
                'rhr_correlation': rhr_r,
                'rhr_p_value': rhr_p,
                'rhr_significant': rhr_significant,
                'weeks_analyzed': len(clean_df),
                'message': message
            }
            
        except Exception as e:
            logger.error(f"時間差相関計算中にエラーが発生しました: {str(e)}")
            return {
                'hrv_correlation': None,
                'hrv_p_value': None,
                'rhr_correlation': None,
                'rhr_p_value': None,
                'weeks_analyzed': 0,
                'message': f"時間差相関計算中にエラーが発生しました: {str(e)}"
            }
    
    def generate_trend_analysis(self, weekly_df: pd.DataFrame) -> Dict[str, Any]:
        """
        長期的なトレンド分析を行う
        
        Args:
            weekly_df: 週別データフレーム
            
        Returns:
            Dict[str, Any]: トレンド分析の結果
        """
        if len(weekly_df) < 4:  # 少なくとも1ヶ月のデータが必要
            return {
                'message': f"長期トレンド分析には少なくとも4週間のデータが必要です（現在: {len(weekly_df)}週間）"
            }
        
        # 4週間移動平均を計算
        smoothed_df = weekly_df.copy()
        smoothed_df['hrv_ma4'] = smoothed_df['avg_hrv'].rolling(window=4).mean()
        smoothed_df['rhr_ma4'] = smoothed_df['avg_rhr'].rolling(window=4).mean()
        smoothed_df['l2_hours_ma4'] = smoothed_df['l2_hours'].rolling(window=4).mean()
        
        # 前半と後半に分割して比較
        mid_point = len(weekly_df) // 2
        if mid_point < 2:
            return {
                'message': "トレンド分析には十分なデータ量がありません"
            }
        
        first_half = weekly_df.iloc[:mid_point]
        second_half = weekly_df.iloc[mid_point:]
        
        results = {}
        
        # HRVの変化
        if not first_half['avg_hrv'].isna().all() and not second_half['avg_hrv'].isna().all():
            first_half_hrv = first_half['avg_hrv'].mean(skipna=True)
            second_half_hrv = second_half['avg_hrv'].mean(skipna=True)
            hrv_change = second_half_hrv - first_half_hrv
            hrv_change_pct = (hrv_change / first_half_hrv) * 100 if first_half_hrv else 0
            
            results['hrv_first_half_avg'] = first_half_hrv
            results['hrv_second_half_avg'] = second_half_hrv
            results['hrv_change'] = hrv_change
            results['hrv_change_pct'] = hrv_change_pct
        
        # RHRの変化
        if not first_half['avg_rhr'].isna().all() and not second_half['avg_rhr'].isna().all():
            first_half_rhr = first_half['avg_rhr'].mean(skipna=True)
            second_half_rhr = second_half['avg_rhr'].mean(skipna=True)
            rhr_change = second_half_rhr - first_half_rhr
            rhr_change_pct = (rhr_change / first_half_rhr) * 100 if first_half_rhr else 0
            
            results['rhr_first_half_avg'] = first_half_rhr
            results['rhr_second_half_avg'] = second_half_rhr
            results['rhr_change'] = rhr_change
            results['rhr_change_pct'] = rhr_change_pct
        
        # L2トレーニング時間の変化
        if not first_half['l2_hours'].isna().all() and not second_half['l2_hours'].isna().all():
            first_half_l2 = first_half['l2_hours'].mean(skipna=True)
            second_half_l2 = second_half['l2_hours'].mean(skipna=True)
            l2_change = second_half_l2 - first_half_l2
            l2_change_pct = (l2_change / first_half_l2) * 100 if first_half_l2 else 0
            
            results['l2_first_half_avg'] = first_half_l2
            results['l2_second_half_avg'] = second_half_l2
            results['l2_change'] = l2_change
            results['l2_change_pct'] = l2_change_pct
        
        # 分析メッセージの生成
        message = "長期トレンド分析（前半vs後半）:\n"
        
        if 'hrv_change' in results:
            message += f"HRV: {results['hrv_first_half_avg']:.1f} → {results['hrv_second_half_avg']:.1f} "
            if results['hrv_change'] > 0:
                message += f"(+{results['hrv_change']:.1f}, +{results['hrv_change_pct']:.1f}%)\n"
            else:
                message += f"({results['hrv_change']:.1f}, {results['hrv_change_pct']:.1f}%)\n"
        
        if 'rhr_change' in results:
            message += f"RHR: {results['rhr_first_half_avg']:.1f} → {results['rhr_second_half_avg']:.1f} "
            if results['rhr_change'] < 0:
                message += f"({results['rhr_change']:.1f}, {results['rhr_change_pct']:.1f}%) - 改善\n"
            else:
                message += f"(+{results['rhr_change']:.1f}, +{results['rhr_change_pct']:.1f}%)\n"
        
        if 'l2_change' in results:
            message += f"週平均L2時間: {results['l2_first_half_avg']:.1f}時間 → {results['l2_second_half_avg']:.1f}時間 "
            if results['l2_change'] > 0:
                message += f"(+{results['l2_change']:.1f}, +{results['l2_change_pct']:.1f}%)\n"
            else:
                message += f"({results['l2_change']:.1f}, {results['l2_change_pct']:.1f}%)\n"
        
        # 総合的な結論
        if 'hrv_change' in results and 'rhr_change' in results and 'l2_change' in results:
            message += "\n総合的な傾向: "
            
            # 改善判定
            hrv_improved = results['hrv_change'] > 0
            rhr_improved = results['rhr_change'] < 0
            l2_increased = results['l2_change'] > 0
            
            if hrv_improved and rhr_improved:
                message += "心臓の健康状態が改善しています。"
                if l2_increased:
                    message += " L2トレーニングの増加が効果をもたらしている可能性があります。"
                else:
                    message += " ただし、L2トレーニング量は減少しているため、他の要因が影響している可能性があります。"
            elif hrv_improved or rhr_improved:
                message += "一部の指標に改善が見られます。"
                if l2_increased:
                    message += " L2トレーニングの増加が部分的に効果をもたらしている可能性があります。"
            else:
                message += "心臓の健康指標に改善が見られません。"
                if l2_increased:
                    message += " L2トレーニングを増やしていますが、まだ効果が現れていないか、別の要因が影響している可能性があります。"
                else:
                    message += " L2トレーニングも減少しているため、トレーニング計画の見直しが必要かもしれません。"
        
        results['message'] = message
        return results
    
    def generate_summary_report(self, weekly_df: pd.DataFrame) -> str:
        """
        総合的な分析レポートを生成する
        
        Args:
            weekly_df: 週別データフレーム
            
        Returns:
            str: 分析レポート
        """
        if len(weekly_df) < 2:
            return "レポート生成に十分なデータがありません。少なくとも2週間分のデータを収集してください。"
        
        # 各種分析を実行
        correlation = self.calculate_l2_hrv_correlation(weekly_df)
        rhr_correlation = self.calculate_l2_rhr_correlation(weekly_df)
        lagged_correlation = self.calculate_time_lagged_correlation(weekly_df, lag_weeks=1)
        trend_analysis = self.generate_trend_analysis(weekly_df)
        
        # レポートの組み立て
        report = "# HRV/RHR長期トレンド分析レポート\n\n"
        
        # 分析期間
        report += f"## 分析期間\n"
        report += f"開始: {weekly_df.index.min().strftime('%Y年%m月%d日')}\n"
        report += f"終了: {weekly_df.index.max().strftime('%Y年%m月%d日')}\n"
        report += f"データ週数: {len(weekly_df)}週間\n\n"
        
        # トレンド分析
        report += f"## 長期トレンド\n"
        if 'message' in trend_analysis:
            report += trend_analysis['message'] + "\n\n"
        
        # 相関分析
        report += f"## 相関分析\n"
        
        report += "### L2トレーニングとHRVの関係\n"
        if 'message' in correlation:
            report += correlation['message'] + "\n\n"
        
        report += "### L2トレーニングとRHRの関係\n"
        if 'message' in rhr_correlation:
            report += rhr_correlation['message'] + "\n\n"
        
        report += "### 時間差相関（1週間遅延）\n"
        if 'message' in lagged_correlation:
            report += lagged_correlation['message'] + "\n\n"
        
        # 推奨事項
        report += "## 推奨事項\n"
        
        # 推奨事項のロジック
        recommendations = []
        
        # HRVが改善している場合
        if 'hrv_change' in trend_analysis and trend_analysis['hrv_change'] > 0:
            recommendations.append("現在のトレーニングアプローチが効果的に機能しています。同様のアプローチを継続することをお勧めします。")
        
        # L2トレーニングとHRVに正の相関がある場合
        if 'correlation' in correlation and correlation['correlation'] is not None and correlation['correlation'] > 0 and correlation['has_significant_correlation']:
            recommendations.append("L2トレーニング（低強度持久トレーニング）の時間をさらに増やすことで、HRVのさらなる向上が期待できます。")
        
        # RHRが高い（悪化）場合
        if 'rhr_second_half_avg' in trend_analysis and trend_analysis['rhr_second_half_avg'] > 60:
            recommendations.append("安静時心拍数（RHR）が高めです。リカバリーとストレス管理を強化し、睡眠の質を向上させることを検討してください。")
        
        # HRVが低下している場合
        if 'hrv_change' in trend_analysis and trend_analysis['hrv_change'] < 0:
            recommendations.append("HRVが低下傾向にあります。オーバートレーニングやストレスなどの影響が考えられます。休息とリカバリーの時間を増やし、トレーニング強度を一時的に下げることを検討してください。")
        
        # L2トレーニングが少ない場合
        if 'l2_second_half_avg' in trend_analysis and trend_analysis['l2_second_half_avg'] < 3:
            recommendations.append("週あたりのL2トレーニング時間が比較的少ないです。有酸素能力と心臓の健康を向上させるため、週に少なくとも3-5時間のL2トレーニングを目指しましょう。")
        
        # デフォルトの推奨事項
        if not recommendations:
            recommendations.append("十分なデータが収集されていないか、明確なパターンが見られません。引き続きデータを収集し、トレーニングと回復のバランスを意識してください。")
        
        for i, rec in enumerate(recommendations, 1):
            report += f"{i}. {rec}\n"
        
        return report