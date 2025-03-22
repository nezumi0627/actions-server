# LINE WORKS Bot Server with GitHub Actions

このリポジトリはGitHub Actionsを使用してLINE WORKSのボットをサーバーレスで実行するプロジェクトです。

### コンポーネント詳細

1. **GitHub Actions Workflow**
   - **定期実行**: 毎5分ごとに自動実行
   - **環境セットアップ**: Python 3.11.11環境の構築
   - **依存関係管理**: 必要なパッケージのインストール
   - **実行管理**: ボットの実行と監視

2. **LineWorks Bot**
   - **メッセージング**: MQTTプロトコルを使用した通信
   - **コマンド処理**: 複数のコマンドをサポート
   - **状態管理**: ログ記録と統計収集

3. **ログシステム**
   - **データ収集**: 
     - 起動時間と最終受信時間
     - メッセージの総数
     - メッセージタイプ別の統計
     - コマンドの使用頻度
     - 時間帯別のメッセージ数
   - **データ可視化**: 
     - 時間帯別のメッセージ数グラフ
     - メッセージタイプ分布
     - コマンド使用頻度
   - **自動更新**: 定期的なログ更新とアーカイブ

## 機能

- GitHub Actionsによる自動化
- 毎5分ごとにボットを実行
- 自動的なREADME更新
- ログの定期的な更新とアーカイブ
- LINE WORKSとの連携
- MQTTプロトコルを使用したメッセージング
- テキストメッセージとFlexメッセージの送信

## ログシステム

### データ収集
- 起動時間と最終受信時間の記録
- メッセージの総数
- メッセージタイプ別の統計
- コマンドの総数
- 時間帯別のメッセージ数

### データ可視化
- 時間帯別のメッセージ数のグラフ
- メッセージタイプ別の分布
- コマンドの使用頻度

## GitHub Actionsの設定

- **ワークフロー**: `line_works.yml`
- 定期実行: 毎5分
- タスク:
  - Python環境のセットアップ
  - 依存関係のインストール
  - ボットの実行
  - ログのアーカイブ