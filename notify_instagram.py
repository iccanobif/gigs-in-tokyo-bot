"""
notify_instagram.py

概要: 指定Instagramユーザの新規投稿を検出してDiscord Webhookへ通知するスクリプト（instaloader使用・ポーリング向け）
使い方: 環境変数 `DISCORD_WEBHOOK_URL` を設定して実行します。
"""

import os
import json
import time
import logging
from typing import List, Dict, Optional

import requests
import instaloader
from pathlib import Path
from dotenv import load_dotenv

# dotenv の読み込み（存在する .env をロード）
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

# --- 設定 ------------------------------------------------------------------
INSTAGRAM_USERNAME = os.environ.get("INSTAGRAM_USERNAME", "gigsintokyo")
STATE_FILE = os.environ.get("STATE_FILE", "last_seen.json")
WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
POST_FETCH_LIMIT = int(os.environ.get("POST_FETCH_LIMIT", "10"))

# --- ロギング ---------------------------------------------------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# --- 状態管理 ---------------------------------------------------------------
def load_state() -> Dict[str, Optional[str]]:
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            logger.exception("状態ファイルの読み込みに失敗しました。初期化します。")
    return {"last_shortcode": None}


def save_state(state: Dict[str, Optional[str]]) -> None:
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f)


# --- Instagram 取得 ---------------------------------------------------------
def get_latest_posts(limit: int = 5) -> List[Dict[str, str]]:
    L = instaloader.Instaloader()
    try:
        profile = instaloader.Profile.from_username(L.context, INSTAGRAM_USERNAME)
    except Exception:
        logger.exception("Instagramプロフィールの取得に失敗しました")
        return []

    posts = []
    try:
        for post in profile.get_posts():
            image_url = None
            try:
                # カルーセル（複数メディア）の場合、最初のノードの display_url を使う
                nodes = list(post.get_sidecar_nodes())
                if nodes:
                    first = nodes[0]
                    image_url = getattr(first, 'display_url', None)
                    if image_url is None and isinstance(first, dict):
                        image_url = first.get('display_url')
            except Exception:
                # sidecar が無い・例外の場合はポスト自体の display_url/thumbnail を試す
                image_url = getattr(post, 'display_url', None) or getattr(post, 'url', None) or getattr(post, 'thumbnail_url', None)

            posts.append({
                "shortcode": post.shortcode,
                "url": f"https://www.instagram.com/p/{post.shortcode}/",
                "date": post.date_utc.isoformat(),
                "image_url": image_url,
            })
            if len(posts) >= limit:
                break
    except Exception:
        logger.exception("投稿の取得中にエラーが発生しました")
    return posts


# --- Discord 通知 -----------------------------------------------------------
def notify_discord(message: str, image_url: Optional[str] = None) -> bool:
    if not WEBHOOK_URL:
        logger.error("DISCORD_WEBHOOK_URL が設定されていません。通知をスキップします。")
        return False
    payload = {"content": message}
    # 画像が指定されていれば Embed に載せる（Discord が外部URLをフェッチできることが前提）
    if image_url:
        payload["embeds"] = [{"image": {"url": image_url}}]
    try:
        r = requests.post(WEBHOOK_URL, json=payload, timeout=10)
        if 200 <= r.status_code < 300:
            return True
        logger.error("Discord通知失敗: %s %s", r.status_code, r.text)
    except Exception:
        logger.exception("Discord通知中に例外が発生しました")
    return False


# --- メイン処理 -------------------------------------------------------------
def main() -> None:
    state = load_state()
    posts = get_latest_posts(limit=POST_FETCH_LIMIT)
    if not posts:
        logger.info("投稿が取得できませんでした。終了します。")
        return

    # 最新から過去へ並んでいるので、保存されている last_shortcode に当たるまで集める
    new_posts = []
    for p in posts:
        if p["shortcode"] == state.get("last_shortcode"):
            break
        new_posts.append(p)

    if not new_posts:
        logger.info("新着投稿はありませんでした。")
        return

    # 古い順に通知（同じ順序で Discord に流す）
    new_posts.reverse()
    for p in new_posts:
        msg = p['url']
        logger.info("通知: %s", msg)
        success = notify_discord(msg, p.get('image_url'))
        if not success:
            logger.error("通知に失敗しました。処理を中断します。")
            break
        state["last_shortcode"] = p["shortcode"]
        save_state(state)
        time.sleep(1)

    logger.info("処理完了")


if __name__ == "__main__":
    main()
