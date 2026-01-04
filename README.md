# gigs-in-tokyo-bot

Instagram の特定アカウントの新規投稿を検出して Discord に通知する簡易ボット（ポーリング方式）

## 使い方

1. Python 3.8+ を用意
2. 依存パッケージをインストール

   pip install -r requirements.txt

   この `requirements.txt` に `python-dotenv` が含まれており、`.env` の自動読み込みを提供します。

3. `.env` を作成して環境変数を配置
   - コピーして編集:
     ```
     cp .env.example .env
     # または Windows:
     copy .env.example .env
     ```
   - 主要な環境変数:
     - `DISCORD_WEBHOOK_URL`（必須）
     - `INSTAGRAM_USERNAME`, `STATE_FILE`, `POST_FETCH_LIMIT`（任意）

   スクリプトは起動時に `.env` を自動で読み込みます（`python-dotenv` を使用）。手動で環境変数を設定しても問題ありません（例: PowerShell `$env:DISCORD_WEBHOOK_URL = '...'`）。

4. 動作確認

   python notify_instagram.py

5. スケジュール（例）
   - Windows タスクスケジューラ: 10 分毎に `python C:\path\to\notify_instagram.py` を実行
   - Linux cron: `*/10 * * * * /usr/bin/python3 /path/to/notify_instagram.py`
   - 代替: GitHub Actions の schedule を使ってホスティング不要にすることも可能です

## 注意点
- この方法は公式 API を使わないスクレイピング系の取得を行います。利用規約やレート制限に注意してください。
- `DISCORD_WEBHOOK_URL` は秘匿してください（公開レポジトリに直接置かない）。
- このバージョンは投稿の URL に加えて最初の画像を Embed として Discord に送信します（Instagram の画像URL が外部からフェッチ可能である必要があります）。
- 必要ならリトライやエラー通知、キャプションを一緒に送る拡張を追加できます。
