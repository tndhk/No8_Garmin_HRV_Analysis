# Garmin HRV/RHR 長期トレンド分析アプリ

## 概要

このアプリケーションは、Garmin Connectから取得した心拍変動（HRV）および安静時心拍数（RHR）データの長期トレンドを分析し、L2（低強度）トレーニングとの関係性を可視化します。特にL2トレーニングの増加がHRV/RHRの改善にどのように寄与するかを定量的に評価することができます。

## 主な機能

- **データ取得**: Garmin Connect APIを用いて過去2年分までのHRV/RHRデータを取得
- **データ可視化**: 日別・週別のHRV/RHRトレンドをグラフ表示
- **L2トレーニング分析**: L2トレーニング時間の推移と割合を分析
- **相関分析**: L2トレーニング時間とHRV/RHRの相関関係を算出
- **時間差効果分析**: 前週のL2トレーニングが現在のHRV/RHRに与える影響を分析
- **レポート生成**: 分析結果のサマリーレポートを生成・ダウンロード

## 技術スタック

- **バックエンド**: Python 3.10
- **データ取得**: `python-garminconnect`
- **データ解析**: pandas, numpy, scipy
- **データ可視化**: Streamlit, Plotly
- **データ保存**: SQLite
- **開発環境**: Docker, GitHub

## アーキテクチャ

本アプリケーションは、クリーンアーキテクチャとSPID（ソリッド、ポリシー、インターフェース、データ）パターンに基づいて設計されています：

- **データソース層**: 外部API（Garmin Connect）との連携を抽象化
- **リポジトリ層**: データの永続化と取得を担当
- **サービス層**: ビジネスロジックと分析処理を実装
- **プレゼンテーション層**: Streamlitを使用したユーザーインターフェース

## 環境設定

### 必要条件

- Python 3.10以上
- Docker（推奨）
- Garmin Connectアカウント

### インストール方法

1. リポジトリをクローン
```bash
git clone https://github.com/yourusername/garmin-hrv-analysis.git
cd garmin-hrv-analysis
```

2. 環境変数の設定
`.env`ファイルを作成し、以下の内容を設定
```
GARMIN_USERNAME=your_garmin_username
GARMIN_PASSWORD=your_garmin_password
DATA_SOURCE_TYPE=garmin  # または 'mock' (テスト用)
```

3. Dockerを使用する場合
```bash
docker-compose up -d
```

4. ローカル環境で直接実行する場合
```bash
pip install -r requirements.txt
python main.py
```

5. ブラウザで以下のURLにアクセス
```
http://localhost:8501
```

## 開発者向け情報

### プロジェクト構造
```
garmin-hrv-analysis/
├── app/
│   ├── data_source/    # データソース層
│   ├── repository/     # リポジトリ層
│   ├── service/        # サービス層
│   ├── analysis/       # 分析処理
│   ├── visualization/  # 可視化処理
│   ├── models/         # データモデル
│   └── main.py         # Streamlitアプリ
├── tests/
│   ├── unit/           # 単体テスト
│   └── integration/    # 統合テスト
├── data/               # データベースファイル
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── main.py             # エントリーポイント
└── README.md
```

### テスト実行方法
```bash
# 単体テスト
pytest tests/unit

# 統合テスト
pytest tests/integration

# すべてのテスト
pytest
```

### TDD開発フロー
このプロジェクトはTDD（テスト駆動開発）で開発されています。新機能を追加する際は以下のフローに従ってください：

1. 失敗するテストを書く
2. テストが通るように実装する
3. リファクタリングする
4. 繰り返す

## 使用方法

1. アプリを起動してGarmin Connectにログイン
2. データ取得期間を設定して「データ取得開始」をクリック
3. 各タブで分析結果を確認
   - HRV/RHRトレンド: 時系列での変化を確認
   - トレーニング分析: L2トレーニングの推移を分析
   - 相関分析: L2トレーニングとHRV/RHRの関係を分析
   - レポート: 総合的な分析結果とレコメンデーションを確認

## 注意事項

- Garmin Connect APIは非公式であるため、Garminの仕様変更により動作しなくなる可能性があります
- HRVデータは全てのGarminデバイスで記録されるわけではありません
- APIリクエストには制限があるため、大量のデータを取得する際は時間がかかる場合があります

## ライセンス

MIT License

## 開発者

あなたの名前