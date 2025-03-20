import logging
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import date, datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple

from app.models.models import DailyData, WeeklyData

logger = logging.getLogger(__name__)

class VisualizationService:
    """
    データ可視化サービスクラス
    HRV/RHRとL2トレーニングの関係などを可視化する
    """
    
    def create_hrv_rhr_trend_plot(self, df: pd.DataFrame) -> go.Figure:
        """
        HRVとRHRの時系列トレンドグラフを作成する
        
        Args:
            df: 日別または週別データフレーム
            
        Returns:
            go.Figure: Plotlyグラフオブジェクト
        """
        # サブプロット（2行1列）を作成
        fig = make_subplots(rows=2, cols=1, 
                           shared_xaxes=True,
                           vertical_spacing=0.1,
                           subplot_titles=("心拍変動（HRV）トレンド", "安静時心拍数（RHR）トレンド"))
        
        # HRVのプロット
        if 'hrv' in df.columns and not df['hrv'].isna().all():
            fig.add_trace(
                go.Scatter(x=df.index, y=df['hrv'], mode='lines+markers', 
                          name='HRV', line=dict(color='green')),
                row=1, col=1
            )
            
            # 移動平均線を追加（7日間）
            if len(df) >= 7:
                ma7 = df['hrv'].rolling(window=7).mean()
                fig.add_trace(
                    go.Scatter(x=df.index, y=ma7, mode='lines', 
                              name='HRV 7日移動平均', line=dict(color='darkgreen', dash='dash')),
                    row=1, col=1
                )
        
        # RHRのプロット
        if 'rhr' in df.columns and not df['rhr'].isna().all():
            fig.add_trace(
                go.Scatter(x=df.index, y=df['rhr'], mode='lines+markers', 
                          name='RHR', line=dict(color='red')),
                row=2, col=1
            )
            
            # 移動平均線を追加（7日間）
            if len(df) >= 7:
                ma7 = df['rhr'].rolling(window=7).mean()
                fig.add_trace(
                    go.Scatter(x=df.index, y=ma7, mode='lines', 
                              name='RHR 7日移動平均', line=dict(color='darkred', dash='dash')),
                    row=2, col=1
                )
        
        # レイアウトの調整
        fig.update_layout(
            height=600,
            title_text="HRVとRHRの長期トレンド",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        # Y軸のタイトル
        fig.update_yaxes(title_text="HRV (ms)", row=1, col=1)
        fig.update_yaxes(title_text="RHR (bpm)", row=2, col=1)
        
        # X軸のタイトル
        fig.update_xaxes(title_text="日付", row=2, col=1)
        
        return fig
    
    def create_l2_training_plot(self, df: pd.DataFrame) -> go.Figure:
        """
        L2トレーニング時間の時系列グラフを作成する
        
        Args:
            df: 日別または週別データフレーム
            
        Returns:
            go.Figure: Plotlyグラフオブジェクト
        """
        # L2とHRVの両方のデータがあるか確認
        has_l2 = 'l2_duration' in df.columns or 'l2_hours' in df.columns
        if not has_l2:
            fig = go.Figure()
            fig.add_annotation(text="L2トレーニングデータがありません", 
                             xref="paper", yref="paper",
                             x=0.5, y=0.5, showarrow=False)
            return fig
        
        # L2トレーニング時間のカラム名を特定
        l2_col = 'l2_hours' if 'l2_hours' in df.columns else 'l2_duration'
        
        # グラフの作成
        fig = go.Figure()
        
        # L2トレーニング時間の棒グラフ
        fig.add_trace(
            go.Bar(x=df.index, y=df[l2_col], name='L2トレーニング時間',
                 marker_color='blue')
        )
        
        # 移動平均線を追加（週単位のデータでは不要）
        if 'l2_duration' in df.columns and len(df) >= 7:
            ma7 = df[l2_col].rolling(window=7).mean()
            fig.add_trace(
                go.Scatter(x=df.index, y=ma7, mode='lines', 
                          name='7日移動平均', line=dict(color='darkblue', width=2))
            )
        
        # レイアウトの調整
        fig.update_layout(
            title="L2トレーニング時間の推移",
            xaxis_title="日付",
            yaxis_title="トレーニング時間（時間）",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            height=400
        )
        
        return fig
    
    def create_correlation_plot(self, df: pd.DataFrame) -> go.Figure:
        """
        L2トレーニング時間とHRV/RHRの相関散布図を作成する
        
        Args:
            df: 日別または週別データフレーム
            
        Returns:
            go.Figure: Plotlyグラフオブジェクト
        """
        # データの準備
        l2_col = 'l2_hours' if 'l2_hours' in df.columns else 'l2_duration'
        hrv_col = 'avg_hrv' if 'avg_hrv' in df.columns else 'hrv'
        rhr_col = 'avg_rhr' if 'avg_rhr' in df.columns else 'rhr'
        
        # 必要なデータがあるか確認
        has_l2 = l2_col in df.columns and not df[l2_col].isna().all()
        has_hrv = hrv_col in df.columns and not df[hrv_col].isna().all()
        has_rhr = rhr_col in df.columns and not df[rhr_col].isna().all()
        
        if not (has_l2 and (has_hrv or has_rhr)):
            fig = go.Figure()
            fig.add_annotation(text="相関分析に必要なデータがありません", 
                             xref="paper", yref="paper",
                             x=0.5, y=0.5, showarrow=False)
            return fig
        
        # サブプロットの作成（HRVとRHRの両方があれば2行、どちらかだけなら1行）
        if has_hrv and has_rhr:
            fig = make_subplots(rows=2, cols=1, 
                               shared_xaxes=True,
                               vertical_spacing=0.1,
                               subplot_titles=("L2トレーニング時間 vs HRV", "L2トレーニング時間 vs RHR"))
            
            # HRV相関散布図
            fig.add_trace(
                go.Scatter(x=df[l2_col], y=df[hrv_col], mode='markers', 
                          name='HRV相関', marker=dict(color='green', size=8)),
                row=1, col=1
            )
            
            # 回帰線の追加（HRV）
            if len(df.dropna(subset=[l2_col, hrv_col])) >= 2:
                df_clean = df.dropna(subset=[l2_col, hrv_col])
                # 最小二乗法で回帰直線を計算
                from scipy import stats
                slope, intercept, r_value, p_value, std_err = stats.linregress(df_clean[l2_col], df_clean[hrv_col])
                
                x_range = pd.Series([df_clean[l2_col].min(), df_clean[l2_col].max()])
                y_pred = intercept + slope * x_range
                
                fig.add_trace(
                    go.Scatter(x=x_range, y=y_pred, mode='lines', 
                              name=f'相関係数: {r_value:.3f}', line=dict(color='darkgreen')),
                    row=1, col=1
                )
            
            # RHR相関散布図
            fig.add_trace(
                go.Scatter(x=df[l2_col], y=df[rhr_col], mode='markers', 
                          name='RHR相関', marker=dict(color='red', size=8)),
                row=2, col=1
            )
            
            # 回帰線の追加（RHR）
            if len(df.dropna(subset=[l2_col, rhr_col])) >= 2:
                df_clean = df.dropna(subset=[l2_col, rhr_col])
                # 最小二乗法で回帰直線を計算
                slope, intercept, r_value, p_value, std_err = stats.linregress(df_clean[l2_col], df_clean[rhr_col])
                
                x_range = pd.Series([df_clean[l2_col].min(), df_clean[l2_col].max()])
                y_pred = intercept + slope * x_range
                
                fig.add_trace(
                    go.Scatter(x=x_range, y=y_pred, mode='lines', 
                              name=f'相関係数: {r_value:.3f}', line=dict(color='darkred')),
                    row=2, col=1
                )
            
            # Y軸のタイトル
            fig.update_yaxes(title_text="HRV (ms)", row=1, col=1)
            fig.update_yaxes(title_text="RHR (bpm)", row=2, col=1)
            
            # X軸のタイトル
            fig.update_xaxes(title_text="L2トレーニング時間（時間）", row=2, col=1)
            
        elif has_hrv:
            fig = go.Figure()
            
            # HRV相関散布図
            fig.add_trace(
                go.Scatter(x=df[l2_col], y=df[hrv_col], mode='markers', 
                          name='データポイント', marker=dict(color='green', size=8))
            )
            
            # 回帰線の追加
            if len(df.dropna(subset=[l2_col, hrv_col])) >= 2:
                df_clean = df.dropna(subset=[l2_col, hrv_col])
                # 最小二乗法で回帰直線を計算
                from scipy import stats
                slope, intercept, r_value, p_value, std_err = stats.linregress(df_clean[l2_col], df_clean[hrv_col])
                
                x_range = pd.Series([df_clean[l2_col].min(), df_clean[l2_col].max()])
                y_pred = intercept + slope * x_range
                
                fig.add_trace(
                    go.Scatter(x=x_range, y=y_pred, mode='lines', 
                              name=f'相関係数: {r_value:.3f}', line=dict(color='darkgreen'))
                )
            
            fig.update_layout(
                title="L2トレーニング時間 vs HRV",
                xaxis_title="L2トレーニング時間（時間）",
                yaxis_title="HRV (ms)"
            )
            
        elif has_rhr:
            fig = go.Figure()
            
            # RHR相関散布図
            fig.add_trace(
                go.Scatter(x=df[l2_col], y=df[rhr_col], mode='markers', 
                          name='データポイント', marker=dict(color='red', size=8))
            )
            
            # 回帰線の追加
            if len(df.dropna(subset=[l2_col, rhr_col])) >= 2:
                df_clean = df.dropna(subset=[l2_col, rhr_col])
                # 最小二乗法で回帰直線を計算
                from scipy import stats
                slope, intercept, r_value, p_value, std_err = stats.linregress(df_clean[l2_col], df_clean[rhr_col])
                
                x_range = pd.Series([df_clean[l2_col].min(), df_clean[l2_col].max()])
                y_pred = intercept + slope * x_range
                
                fig.add_trace(
                    go.Scatter(x=x_range, y=y_pred, mode='lines', 
                              name=f'相関係数: {r_value:.3f}', line=dict(color='darkred'))
                )
            
            fig.update_layout(
                title="L2トレーニング時間 vs RHR",
                xaxis_title="L2トレーニング時間（時間）",
                yaxis_title="RHR (bpm)"
            )
        
        # 共通のレイアウト設定
        fig.update_layout(
            height=600,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        return fig
    
    def create_stacked_bar_chart(self, weekly_df: pd.DataFrame) -> go.Figure:
        """
        週別のトレーニング時間積み上げグラフを作成する
        
        Args:
            weekly_df: 週別データフレーム
            
        Returns:
            go.Figure: Plotlyグラフオブジェクト
        """
        if 'l2_hours' not in weekly_df.columns or 'total_training_hours' not in weekly_df.columns:
            fig = go.Figure()
            fig.add_annotation(text="トレーニング時間データがありません", 
                             xref="paper", yref="paper",
                             x=0.5, y=0.5, showarrow=False)
            return fig
        
        # その他のトレーニング時間を計算
        weekly_df['other_hours'] = weekly_df['total_training_hours'] - weekly_df['l2_hours']
        
        # 日付をフォーマット
        date_labels = [f"{d.strftime('%m/%d')}週" for d in weekly_df.index]
        
        # グラフの作成
        fig = go.Figure()
        
        # L2トレーニング（下段）
        fig.add_trace(
            go.Bar(x=date_labels, y=weekly_df['l2_hours'], name='L2トレーニング',
                 marker_color='blue')
        )
        
        # その他のトレーニング（上段）
        fig.add_trace(
            go.Bar(x=date_labels, y=weekly_df['other_hours'], name='その他のトレーニング',
                 marker_color='gray')
        )
        
        # 積み上げバーに設定
        fig.update_layout(barmode='stack')
        
        # レイアウトの調整
        fig.update_layout(
            title="週別トレーニング時間の内訳",
            xaxis_title="週",
            yaxis_title="トレーニング時間（時間）",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            height=400
        )
        
        return fig
    
    def create_l2_percentage_plot(self, weekly_df: pd.DataFrame) -> go.Figure:
        """
        L2トレーニング割合の時系列グラフを作成する
        
        Args:
            weekly_df: 週別データフレーム
            
        Returns:
            go.Figure: Plotlyグラフオブジェクト
        """
        if 'l2_percentage' not in weekly_df.columns:
            fig = go.Figure()
            fig.add_annotation(text="L2トレーニング割合データがありません", 
                             xref="paper", yref="paper",
                             x=0.5, y=0.5, showarrow=False)
            return fig
        
        # 日付をフォーマット
        date_labels = [f"{d.strftime('%m/%d')}週" for d in weekly_df.index]
        
        # グラフの作成
        fig = go.Figure()
        
        # L2割合の折れ線グラフ
        fig.add_trace(
            go.Scatter(x=date_labels, y=weekly_df['l2_percentage'], mode='lines+markers',
                     name='L2トレーニング割合', marker_color='purple', line_width=2)
        )
        
        # レイアウトの調整
        fig.update_layout(
            title="週別L2トレーニング割合",
            xaxis_title="週",
            yaxis_title="L2トレーニング割合（%）",
            height=400,
            yaxis=dict(
                range=[0, 100]
            )
        )
        
        return fig
    
    def create_heatmap(self, weekly_df: pd.DataFrame, hrv_col: str = 'avg_hrv', l2_col: str = 'l2_hours') -> go.Figure:
        """
        HRVとL2トレーニングのヒートマップを作成する
        
        Args:
            weekly_df: 週別データフレーム
            hrv_col: HRVのカラム名
            l2_col: L2トレーニング時間のカラム名
            
        Returns:
            go.Figure: Plotlyグラフオブジェクト
        """
        if hrv_col not in weekly_df.columns or l2_col not in weekly_df.columns:
            fig = go.Figure()
            fig.add_annotation(text="ヒートマップ作成に必要なデータがありません", 
                             xref="paper", yref="paper",
                             x=0.5, y=0.5, showarrow=False)
            return fig
        
        # データ前処理
        data = weekly_df.dropna(subset=[hrv_col, l2_col]).copy()
        
        if len(data) < 4:  # 少なくとも4週間のデータが必要
            fig = go.Figure()
            fig.add_annotation(text="ヒートマップ作成には少なくとも4週間のデータが必要です", 
                             xref="paper", yref="paper",
                             x=0.5, y=0.5, showarrow=False)
            return fig
        
        # L2時間を5つのビンに分類
        data['l2_bin'] = pd.qcut(data[l2_col], 5, labels=False)
        
        # HRVを5つのビンに分類
        data['hrv_bin'] = pd.qcut(data[hrv_col], 5, labels=False)
        
        # ビンごとの集計
        heatmap_data = pd.crosstab(data['l2_bin'], data['hrv_bin'])
        
        # L2時間の実際の範囲を計算
        l2_ranges = pd.qcut(data[l2_col], 5).unique().categories
        l2_labels = [f"{r.left:.1f}-{r.right:.1f}" for r in l2_ranges]
        
        # HRVの実際の範囲を計算
        hrv_ranges = pd.qcut(data[hrv_col], 5).unique().categories
        hrv_labels = [f"{r.left:.1f}-{r.right:.1f}" for r in hrv_ranges]
        
        # ヒートマップの作成
        fig = go.Figure(data=go.Heatmap(
            z=heatmap_data.values,
            x=hrv_labels,
            y=l2_labels,
            colorscale='Blues',
            colorbar=dict(title='週数')
        ))
        
        # レイアウトの調整
        fig.update_layout(
            title="L2トレーニング時間とHRVの関係ヒートマップ",
            xaxis_title="HRV範囲 (ms)",
            yaxis_title="L2トレーニング時間範囲 (時間/週)",
            height=500
        )
        
        return fig