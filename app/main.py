import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os
import logging
from datetime import date, datetime, timedelta
import time

from app.service.data_service import DataService
from app.analysis.analysis_service import AnalysisService
from app.visualization.visualization_service import VisualizationService

# ロギングの設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# サービスのインスタンス化
data_service = DataService()
analysis_service = AnalysisService()
viz_service = VisualizationService()

# アプリケーションの状態管理
if 'is_authenticated' not in st.session_state:
    st.session_state.is_authenticated = False

if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False

if 'daily_data' not in st.session_state:
    st.session_state.daily_data = None

if 'weekly_data' not in st.session_state:
    st.session_state.weekly_data = None

if 'daily_df' not in st.session_state:
    st.session_state.daily_df = None

if 'weekly_df' not in st.session_state:
    st.session_state.weekly_df = None

def authenticate():
    """ユーザー認証とデータソース接続を行う"""
    st.subheader("Garmin Connect認証")
    
    with st.form("auth_form"):
        username = st.text_input("Garminユーザー名", key="username")
        password = st.text_input("Garminパスワード", type="password", key="password")
        submit = st.form_submit_button("接続")
        
        if submit:
            # 環境変数に設定
            os.environ['GARMIN_USERNAME'] = username
            os.environ['GARMIN_PASSWORD'] = password
            
            with st.spinner("Garmin Connectに接続中..."):
                success = data_service.connect()
                
                if success:
                    st.session_state.is_authenticated = True
                    st.success("Garmin Connectに接続しました")
                    time.sleep(1)
                    st.experimental_rerun()
                else:
                    st.error("Garmin Connectへの接続に失敗しました。ユーザー名とパスワードを確認してください。")

def fetch_data():
    """データ取得と保存を行う"""
    st.subheader("データ取得")
    
    # 期間の選択
    col1, col2 = st.columns(2)
    with col1:
        end_date = st.date_input("終了日", value=date.today())
    with col2:
        days = st.slider("取得日数", min_value=30, max_value=730, value=180, step=30)
    
    start_date = end_date - timedelta(days=days-1)
    st.info(f"取得期間: {start_date} から {end_date} ({days}日間)")
    
    if st.button("データ取得開始"):
        with st.spinner(f"{days}日分のデータを取得しています..."):
            success = data_service.fetch_and_save_data(start_date, end_date)
            
            if success:
                st.success("データの取得・保存が完了しました")
                st.session_state.data_loaded = True
                load_and_analyze_data(start_date, end_date)
                st.experimental_rerun()
            else:
                st.error("データの取得・保存中にエラーが発生しました")

def load_and_analyze_data(start_date, end_date):
    """データの読み込みと分析を行う"""
    # 日別データの取得
    st.session_state.daily_data = data_service.get_daily_data(start_date, end_date)
    
    # 週別データの取得
    st.session_state.weekly_data = data_service.get_weekly_data(start_date, end_date)
    
    # 分析用データフレームの作成
    if st.session_state.daily_data:
        st.session_state.daily_df = analysis_service.create_time_series_dataframe(
            st.session_state.daily_data
        )
    
    if st.session_state.weekly_data:
        st.session_state.weekly_df = analysis_service.create_weekly_dataframe(
            st.session_state.weekly_data
        )

def visualize_data():
    """データの可視化を行う"""
    st.title("Garmin HRV/RHR 長期トレンド分析")
    
    # 期間の選択
    st.sidebar.header("データ範囲設定")
    
    # 日付範囲が有効かチェック
    if st.session_state.daily_df is not None and not st.session_state.daily_df.empty:
        min_date = st.session_state.daily_df.index.min().date()
        max_date = st.session_state.daily_df.index.max().date()
        
        start_date = st.sidebar.date_input(
            "開始日", 
            value=min_date,
            min_value=min_date,
            max_value=max_date
        )
        
        end_date = st.sidebar.date_input(
            "終了日", 
            value=max_date,
            min_value=start_date,
            max_value=max_date
        )
        
        # データをフィルタリング
        mask = (st.session_state.daily_df.index.date >= start_date) & \
               (st.session_state.daily_df.index.date <= end_date)
        filtered_daily_df = st.session_state.daily_df[mask]
        
        # 週別データもフィルタリング
        if st.session_state.weekly_df is not None and not st.session_state.weekly_df.empty:
            mask = (st.session_state.weekly_df.index.date >= start_date) & \
                   (st.session_state.weekly_df.index.date <= end_date)
            filtered_weekly_df = st.session_state.weekly_df[mask]
        else:
            filtered_weekly_df = pd.DataFrame()
        
        # タブの作成
        tab1, tab2, tab3, tab4 = st.tabs([
            "HRV/RHRトレンド", "トレーニング分析", "相関分析", "レポート"
        ])
        
        with tab1:
            st.subheader("HRVとRHRの長期トレンド")
            
            # HRV/RHRトレンドグラフ
            if not filtered_daily_df.empty:
                fig = viz_service.create_hrv_rhr_trend_plot(filtered_daily_df)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("表示するデータがありません")
        
        with tab2:
            st.subheader("L2トレーニング分析")
            
            # L2トレーニング時間の推移
            if not filtered_daily_df.empty:
                fig = viz_service.create_l2_training_plot(filtered_daily_df)
                st.plotly_chart(fig, use_container_width=True)
            
            # 週別トレーニング内訳
            if not filtered_weekly_df.empty:
                col1, col2 = st.columns(2)
                
                with col1:
                    fig = viz_service.create_stacked_bar_chart(filtered_weekly_df)
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    fig = viz_service.create_l2_percentage_plot(filtered_weekly_df)
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("表示する週別データがありません")
        
        with tab3:
            st.subheader("相関分析")
            
            # 分析期間の選択
            analysis_period = st.radio(
                "分析単位",
                ["日別データ", "週別データ"],
                horizontal=True
            )
            
            if analysis_period == "日別データ":
                if not filtered_daily_df.empty:
                    fig = viz_service.create_correlation_plot(filtered_daily_df)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("表示するデータがありません")
            else:  # 週別データ
                if not filtered_weekly_df.empty:
                    fig = viz_service.create_correlation_plot(filtered_weekly_df)
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # ヒートマップも表示
                    fig = viz_service.create_heatmap(filtered_weekly_df)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("表示する週別データがありません")
            
            # 相関係数の計算と表示
            if not filtered_weekly_df.empty:
                st.subheader("相関分析結果")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    hrv_corr = analysis_service.calculate_l2_hrv_correlation(filtered_weekly_df)
                    if hrv_corr['correlation'] is not None:
                        st.metric(
                            "L2トレーニングとHRVの相関係数", 
                            f"{hrv_corr['correlation']:.3f}",
                            delta=None
                        )
                        st.write(f"p値: {hrv_corr['p_value']:.3f}")
                        st.write(hrv_corr['message'])
                
                with col2:
                    rhr_corr = analysis_service.calculate_l2_rhr_correlation(filtered_weekly_df)
                    if rhr_corr['correlation'] is not None:
                        st.metric(
                            "L2トレーニングとRHRの相関係数", 
                            f"{rhr_corr['correlation']:.3f}",
                            delta=None
                        )
                        st.write(f"p値: {rhr_corr['p_value']:.3f}")
                        st.write(rhr_corr['message'])
                
                # 時間差相関
                st.subheader("時間差相関分析")
                lag_weeks = st.slider("遅延週数", min_value=1, max_value=4, value=1)
                
                lagged_corr = analysis_service.calculate_time_lagged_correlation(
                    filtered_weekly_df, lag_weeks=lag_weeks
                )
                
                if lagged_corr['hrv_correlation'] is not None:
                    st.write(lagged_corr['message'])
        
        with tab4:
            st.subheader("分析レポート")
            
            if not filtered_weekly_df.empty:
                report = analysis_service.generate_summary_report(filtered_weekly_df)
                st.markdown(report)
                
                # レポートのダウンロードボタン
                st.download_button(
                    "レポートをダウンロード",
                    report,
                    file_name=f"hrv_analysis_report_{start_date}_to_{end_date}.md",
                    mime="text/markdown"
                )
            else:
                st.info("レポート生成に十分なデータがありません")
    else:
        st.info("分析するデータがありません。「データ取得」を行ってください。")
    
    # データ更新ボタン
    st.sidebar.subheader("データ管理")
    if st.sidebar.button("データを再取得"):
        st.session_state.data_loaded = False
        st.experimental_rerun()

def main():
    """メイン関数"""
    st.set_page_config(
        page_title="Garmin HRV/RHR分析",
        page_icon="❤️",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # サイドバーにタイトルを表示
    st.sidebar.title("Garmin HRV/RHR分析")
    
    # 認証状態に応じて表示を切り替え
    if not st.session_state.is_authenticated:
        authenticate()
        
    elif not st.session_state.data_loaded:
        fetch_data()
        
    else:
        visualize_data()

if __name__ == "__main__":
    main()