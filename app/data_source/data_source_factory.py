from typing import Optional
import os
import logging

from app.data_source.data_source_interface import DataSourceInterface
from app.data_source.garmin_data_source import GarminDataSource
from app.data_source.mock_data_source import MockDataSource

logger = logging.getLogger(__name__)

class DataSourceFactory:
    """
    データソースを生成するファクトリークラス
    環境設定や設定ファイルに基づいて適切なデータソースを提供する
    """
    
    @staticmethod
    def create_data_source(source_type: str = None) -> DataSourceInterface:
        """
        指定されたタイプのデータソースを生成する
        
        Args:
            source_type: データソースの種類 ('garmin' or 'mock')
                        Noneの場合は環境変数から判断
        
        Returns:
            DataSourceInterface: 生成されたデータソースインスタンス
        """
        # 環境変数からデータソースタイプを取得（デフォルトはgarmin）
        if source_type is None:
            source_type = os.environ.get('DATA_SOURCE_TYPE', 'garmin').lower()
        
        logger.info(f"データソースタイプ '{source_type}' を使用します")
        
        if source_type == 'mock':
            return MockDataSource()
        elif source_type == 'garmin':
            return GarminDataSource()
        else:
            logger.warning(f"不明なデータソースタイプ '{source_type}'。デフォルトのGarminデータソースを使用します")
            return GarminDataSource()