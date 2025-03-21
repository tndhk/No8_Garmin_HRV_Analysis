#!/usr/bin/env python3
"""
Garmin Connect APIの診断ツール
APIの応答を分析し、どのエンドポイントからRHRとHRVデータを取得できるかを調査します
"""
import sys
import os
import json
import logging
from datetime import date, datetime, timedelta
from pathlib import Path

# プロジェクトのルートディレクトリをPATHに追加
project_root = str(Path(__file__).parent)
sys.path.insert(0, project_root)

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 必要なライブラリとモジュールをインポート
try:
    from garminconnect import Garmin
except ImportError:
    logger.error("garminconnect パッケージがインストールされていません。以下のコマンドでインストールしてください：")
    logger.error("pip install garmin-connect")
    sys.exit(1)

def print_header(text):
    """ヘッダーを出力"""
    print("\n" + "=" * 70)
    print(text)
    print("=" * 70)

def dump_json(obj, indent=2):
    """オブジェクトをJSON形式で出力"""
    if obj is None:
        return "None"
    
    try:
        return json.dumps(obj, indent=indent, ensure_ascii=False)
    except:
        return str(obj)

def explore_response(response, max_depth=3, prefix="", current_depth=0):
    """レスポンスの構造を再帰的に探索"""
    if current_depth > max_depth:
        return "... (max depth reached)"
    
    if response is None:
        return "None"
    
    if isinstance(response, dict):
        result = "{\n"
        for key, value in response.items():
            result += f"{prefix}  '{key}': "
            if isinstance(value, (dict, list)) and len(str(value)) > 100:
                result += explore_response(value, max_depth, prefix + "  ", current_depth + 1)
            else:
                result += str(value)
            result += ",\n"
        result += prefix + "}"
        return result
    
    if isinstance(response, list):
        if len(response) == 0:
            return "[]"
        
        if len(response) > 3:
            sample = response[:3]
            result = f"[/* {len(response)} items, showing first 3 */ \n"
        else:
            sample = response
            result = "[\n"
        
        for item in sample:
            result += prefix + "  "
            if isinstance(item, (dict, list)):
                result += explore_response(item, max_depth, prefix + "  ", current_depth + 1)
            else:
                result += str(item)
            result += ",\n"
        
        if len(response) > 3:
            result += prefix + "  ... (more items)"
        
        result += prefix + "]"
        return result
    
    return str(response)

def diagnose_garmin_api(username, password):
    """Garmin Connect APIの診断"""
    try:
        print_header("Garmin Connect API診断")
        
        # Garmin Connect APIに接続
        print("\n接続中...")
        client = Garmin(username, password)
        client.login()
        print("接続成功！")
        
        # 日付範囲の設定
        today = date.today()
        yesterday = today - timedelta(days=1)
        last_week = today - timedelta(days=7)
        
        # 利用可能なメソッドのリスト
        api_methods = [
            ("ユーザープロファイル", client.get_user_profile),
            ("安静時心拍数 (今日)", lambda: client.get_rhr_day(today.isoformat())),
            ("安静時心拍数 (昨日)", lambda: client.get_rhr_day(yesterday.isoformat())),
            ("統計データ (今日)", lambda: client.get_stats(today.isoformat())),
            ("統計データ (昨日)", lambda: client.get_stats(yesterday.isoformat())),
            ("睡眠データ (昨日)", lambda: client.get_sleep_data(yesterday.isoformat())),
            ("体重データ", lambda: client.get_body_composition(today.isoformat())),
            ("アクティビティリスト", lambda: client.get_activities(0, 10)),
            ("ランニングHRVデータ", lambda: client.get_hrv_data()),
            ("先週のアクティビティ心拍数", lambda: client.get_heart_rates(last_week.isoformat(), today.isoformat())),
            ("先週のストレスデータ", lambda: client.get_stress_data(last_week.isoformat())),
            ("最近の最大酸素摂取量", lambda: client.get_max_metrics(10)),
            ("先週の日別統計", lambda: client.get_user_summary(last_week.isoformat(), today.isoformat())),
        ]
        
        # 各APIメソッドを実行
        for name, method in api_methods:
            print_header(f"テスト: {name}")
            try:
                response = method()
                
                # レスポンスの種類を判定
                if isinstance(response, dict):
                    print(f"レスポンスタイプ: 辞書 ({len(response)} キー)")
                    print(f"キー一覧: {list(response.keys())}")
                    
                    # RHRとHRVに関連するキーを探す
                    rhr_keys = [k for k in response.keys() if 'heart' in k.lower() or 'rhr' in k.lower() or 'rest' in k.lower()]
                    hrv_keys = [k for k in response.keys() if 'hrv' in k.lower() or 'variability' in k.lower()]
                    
                    if rhr_keys:
                        print(f"\n安静時心拍数に関連する可能性があるキー: {rhr_keys}")
                        for key in rhr_keys:
                            print(f"  {key}: {response.get(key)}")
                    
                    if hrv_keys:
                        print(f"\n心拍変動に関連する可能性があるキー: {hrv_keys}")
                        for key in hrv_keys:
                            print(f"  {key}: {response.get(key)}")
                    
                    # 特に調査したいキー
                    special_keys = ['restingHeartRate', 'hrv', 'heartRateVariability', 'avgHRV']
                    for key in special_keys:
                        if key in response:
                            print(f"\n{key}: {response[key]}")
                        elif '.' in key:
                            parts = key.split('.')
                            sub_data = response
                            found = True
                            for part in parts:
                                if isinstance(sub_data, dict) and part in sub_data:
                                    sub_data = sub_data[part]
                                else:
                                    found = False
                                    break
                            if found:
                                print(f"\n{key}: {sub_data}")
                    
                    # 特定のデータ構造の詳細探索
                    if 'allMetrics' in response:
                        print("\nallMetrics 構造:")
                        metrics = response['allMetrics']
                        if isinstance(metrics, dict):
                            for key, value in metrics.items():
                                print(f"  {key}: {type(value)}")
                                if isinstance(value, list) and len(value) > 0:
                                    print(f"    First item: {value[0]}")
                    
                    if 'heartRateValues' in response:
                        print("\nheartRateValues サンプル:")
                        hr_values = response['heartRateValues']
                        if isinstance(hr_values, list) and len(hr_values) > 0:
                            for i, item in enumerate(hr_values[:3]):
                                print(f"  {i}: {item}")
                    
                elif isinstance(response, list):
                    print(f"レスポンスタイプ: リスト ({len(response)} アイテム)")
                    if len(response) > 0:
                        print("\n最初のアイテム:")
                        first_item = response[0]
                        if isinstance(first_item, dict):
                            print(f"キー一覧: {list(first_item.keys())}")
                            
                            # RHRとHRVに関連するキーを探す
                            rhr_keys = [k for k in first_item.keys() if 'heart' in k.lower() or 'rhr' in k.lower() or 'rest' in k.lower()]
                            hrv_keys = [k for k in first_item.keys() if 'hrv' in k.lower() or 'variability' in k.lower()]
                            
                            if rhr_keys:
                                print(f"\n安静時心拍数に関連する可能性があるキー: {rhr_keys}")
                                for key in rhr_keys:
                                    print(f"  {key}: {first_item.get(key)}")
                            
                            if hrv_keys:
                                print(f"\n心拍変動に関連する可能性があるキー: {hrv_keys}")
                                for key in hrv_keys:
                                    print(f"  {key}: {first_item.get(key)}")
                
                # 完全なレスポンスの出力
                print("\n詳細なレスポンス構造:")
                print(explore_response(response))
                
            except Exception as e:
                print(f"エラー: {str(e)}")
                continue
        
    except Exception as e:
        print(f"診断中にエラーが発生しました: {str(e)}")

if __name__ == "__main__":
    print("Garmin Connect API診断ツール")
    
    # 環境変数からユーザー名とパスワードを取得、またはコマンドラインから入力
    username = os.environ.get('GARMIN_USERNAME')
    password = os.environ.get('GARMIN_PASSWORD')
    
    if not username:
        username = input("Garmin Connectユーザー名: ")
    
    if not password:
        password = input("Garmin Connectパスワード: ")
    
    diagnose_garmin_api(username, password)