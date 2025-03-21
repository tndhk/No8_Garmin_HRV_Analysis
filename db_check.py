#!/usr/bin/env python3
"""
SQLiteデータベース内のデータを確認するスクリプト
"""
import sys
import os
from pathlib import Path
import sqlite3
from datetime import datetime, timedelta

# プロジェクトのルートディレクトリをPATHに追加
project_root = str(Path(__file__).parent)
sys.path.insert(0, project_root)

def print_header(text):
    """ヘッダーを出力"""
    print("\n" + "=" * 50)
    print(text)
    print("=" * 50)

def format_value(value):
    """値を文字列に変換（Noneの場合は'NULL'）"""
    if value is None:
        return 'NULL'
    return str(value)

def check_database(db_path='data/garmin_data.db'):
    """データベースの内容を確認"""
    try:
        # データベースに接続
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # テーブル一覧を取得
        print_header("テーブル一覧")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        for table in tables:
            print(f"- {table[0]}")
        
        # 各テーブルの行数を確認
        print_header("テーブル内のレコード数")
        for table in tables:
            table_name = table[0]
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"{table_name}: {count}行")
        
        # RHRデータのサンプルを表示
        print_header("RHRデータのサンプル (最新5件)")
        try:
            cursor.execute("SELECT id, date, rhr FROM rhr_records ORDER BY date DESC LIMIT 5")
            rows = cursor.fetchall()
            if rows:
                print(f"{'ID':<5} {'日付':<12} {'RHR':<5}")
                print("-" * 25)
                for row in rows:
                    id_val = format_value(row[0])
                    date_val = format_value(row[1])
                    rhr_val = format_value(row[2])
                    print(f"{id_val:<5} {date_val:<12} {rhr_val:<5}")
            else:
                print("RHRデータはありません")
        except sqlite3.Error as e:
            print(f"RHRデータ取得エラー: {e}")
        
        # HRVデータのサンプルを表示
        print_header("HRVデータのサンプル (最新5件)")
        try:
            cursor.execute("SELECT id, date, hrv FROM hrv_records ORDER BY date DESC LIMIT 5")
            rows = cursor.fetchall()
            if rows:
                print(f"{'ID':<5} {'日付':<12} {'HRV':<5}")
                print("-" * 25)
                for row in rows:
                    id_val = format_value(row[0])
                    date_val = format_value(row[1])
                    hrv_val = format_value(row[2])
                    print(f"{id_val:<5} {date_val:<12} {hrv_val:<5}")
            else:
                print("HRVデータはありません")
        except sqlite3.Error as e:
            print(f"HRVデータ取得エラー: {e}")
        
        # アクティビティデータのサンプルを表示
        print_header("アクティビティデータのサンプル (最新5件)")
        try:
            cursor.execute("SELECT id, date, activity_type, is_l2_training FROM activity_records ORDER BY date DESC LIMIT 5")
            rows = cursor.fetchall()
            if rows:
                print(f"{'ID':<5} {'日付':<12} {'タイプ':<10} {'L2':<5}")
                print("-" * 35)
                for row in rows:
                    id_val = format_value(row[0])
                    date_val = format_value(row[1])
                    type_val = format_value(row[2])
                    l2_val = 'Yes' if row[3] else 'No'
                    print(f"{id_val:<5} {date_val:<12} {type_val:<10} {l2_val:<5}")
            else:
                print("アクティビティデータはありません")
        except sqlite3.Error as e:
            print(f"アクティビティデータ取得エラー: {e}")
        
        # テーブル構造の表示を追加
        print_header("テーブル構造")
        for table in tables:
            table_name = table[0]
            try:
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                print(f"\n{table_name}テーブルの構造:")
                print(f"{'カラム名':<15} {'型':<10} {'NULL許可':<10} {'デフォルト値':<15}")
                print("-" * 50)
                for col in columns:
                    col_name = col[1]
                    col_type = col[2]
                    not_null = "No" if col[3] == 0 else "Yes"
                    default_val = format_value(col[4])
                    print(f"{col_name:<15} {col_type:<10} {not_null:<10} {default_val:<15}")
            except sqlite3.Error as e:
                print(f"{table_name}テーブルの構造取得エラー: {e}")
        
        # 最近のデータを確認（NULL値を含むかどうか）
        print_header("NULL値の確認")
        try:
            cursor.execute("SELECT COUNT(*) FROM rhr_records WHERE rhr IS NULL")
            null_rhr_count = cursor.fetchone()[0]
            print(f"RHRがNULLのレコード数: {null_rhr_count}")
            
            cursor.execute("SELECT COUNT(*) FROM hrv_records WHERE hrv IS NULL")
            null_hrv_count = cursor.fetchone()[0]
            print(f"HRVがNULLのレコード数: {null_hrv_count}")
            
            # NULLの具体例を表示
            if null_rhr_count > 0:
                cursor.execute("SELECT id, date FROM rhr_records WHERE rhr IS NULL LIMIT 3")
                rows = cursor.fetchall()
                print("\nRHRがNULLの例:")
                for row in rows:
                    print(f"ID: {row[0]}, 日付: {row[1]}")
            
            if null_hrv_count > 0:
                cursor.execute("SELECT id, date FROM hrv_records WHERE hrv IS NULL LIMIT 3")
                rows = cursor.fetchall()
                print("\nHRVがNULLの例:")
                for row in rows:
                    print(f"ID: {row[0]}, 日付: {row[1]}")
                    
        except sqlite3.Error as e:
            print(f"NULL値確認エラー: {e}")
        
        # 日付範囲の確認
        print_header("データの日付範囲")
        try:
            cursor.execute("SELECT MIN(date), MAX(date) FROM rhr_records")
            rhr_range = cursor.fetchone()
            print(f"RHRデータ日付範囲: {rhr_range[0]} から {rhr_range[1]}")
            
            cursor.execute("SELECT MIN(date), MAX(date) FROM hrv_records")
            hrv_range = cursor.fetchone()
            print(f"HRVデータ日付範囲: {hrv_range[0]} から {hrv_range[1]}")
            
            cursor.execute("SELECT MIN(date), MAX(date) FROM activity_records")
            activity_range = cursor.fetchone()
            print(f"アクティビティデータ日付範囲: {activity_range[0]} から {activity_range[1]}")
        except sqlite3.Error as e:
            print(f"日付範囲確認エラー: {e}")
        
        # 接続を閉じる
        conn.close()
        
    except sqlite3.Error as e:
        print(f"データベース接続エラー: {e}")
    except Exception as e:
        print(f"予期せぬエラー: {e}")

if __name__ == "__main__":
    # コマンドライン引数からDBパスを取得するか、デフォルト値を使用
    db_path = sys.argv[1] if len(sys.argv) > 1 else 'data/garmin_data.db'
    check_database(db_path)