import os
import logging
from app.repository.repository_interface import RepositoryInterface
from app.repository.sqlite_repository import SQLiteRepository
from app.models.database_models import init_db

logger = logging.getLogger(__name__)

class RepositoryFactory:
    """
    リポジトリを生成するファクトリークラス
    """
    
    @staticmethod
    def create_repository() -> RepositoryInterface:
        """
        環境設定に基づいて適切なリポジトリを作成する
        
        Returns:
            RepositoryInterface: 作成されたリポジトリインスタンス
        """
        # データベースパスの取得（デフォルトはSQLite）
        db_path = os.environ.get('DATABASE_PATH', 'sqlite:///data/garmin_data.db')
        
        logger.info(f"リポジトリを作成します: {db_path}")
        
        # SQLiteリポジトリを作成
        _, Session = init_db(db_path)
        return SQLiteRepository(Session)