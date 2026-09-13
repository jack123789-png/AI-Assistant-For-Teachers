"""中央 AI 呼叫：金鑰從側欄輸入 / 環境變數 / .env 讀取，沒金鑰也能開程式。"""
import os
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

MODEL = os.getenv("OPENAI_MODEL", "gpt-5-mini")
NO_KEY_MSG = (
    "尚未設定 OpenAI API 金鑰。請在左側欄位輸入金鑰，"
    "或在 .env 檔設定 OPENAI_API_KEY 後重啟。"
)


def get_api_key() -> str:
    try:
        key = st.session_state.get("openai_api_key", "")
        if key:
            return key
    except Exception:
        pass
    return os.getenv("OPENAI_API_KEY", "")


def get_client():
    key = get_api_key()
    if not key:
        return None
    from openai import OpenAI
    return OpenAI(api_key=key)


def ask_ai(system_prompt: str, user_prompt: str) -> str:
    """全站共用：系統提示自動加繁中要求，沒金鑰回中文說明。"""
    client = get_client()
    if client is None:
        return "warning: " + NO_KEY_MSG
    system_prompt = system_prompt + "\n請一律使用繁體中文（台灣用語）回答。"
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"warning: AI 發生錯誤：{e}"
