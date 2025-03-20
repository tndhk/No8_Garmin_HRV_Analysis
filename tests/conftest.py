import pytest
import sys
import os
from pathlib import Path

# プロジェクトのルートディレクトリをPATHに追加
project_root = str(Path(__file__).parent.parent)
sys.path.insert(0, project_root)

# テスト実行時に環境変数を設定
@pytest.fixture(scope="session", autouse=True)
def setup_test_env():
    """テスト環境のセットアップ"""
    # テスト用の環境変数を設定
    os.environ['DATA_SOURCE_TYPE'] = 'mock'
    os.environ['GARMIN_USERNAME'] = 'test_user'
    os.environ['GARMIN_PASSWORD'] = 'test_pass'
    
    yield
    
    # テスト後のクリーンアップ（必要に応じて）
    pass