# streamlit_app.py —— 模式選擇移到側邊欄
import io
import re
import requests
import pandas as pd
import streamlit as st
import random

st.set_page_config(page_title="Cloze Test Practice (3 modes, rounds)", page_icon="📝", layout="centered")

# ===================== 樣式 =====================
st.markdown("""
<style>
html, body, [class*="css"]  { font-size: 22px !important; }
h2 { font-size: 26px !important; margin-top: 0.22em !important; margin-bottom: 0.22em !important; }
.block-container { padding-top: 0.4rem !important; padding-bottom: 0.9rem !important; max-width: 1000px; }
.progress-card { margin-bottom: 0.22rem !important; }
.stRadio { margin-top: 0 !important; }
.stButton>button{ height: 44px; padding: 0 18px; }
.feedback-small { font-size: 17px !important; line-height: 1.4; margin: 6px 0 2px 0; }
.feedback-correct { color: #1a7f37; font-weight: 700; }
.feedback-wrong { color: #c62828; font-weight: 700; }
.zh-blue { color: #1e88e5; }
.subtle-callout { padding: 12px 14px; border-radius: 10px; background: #fafafa; border: 1px dashed #ddd; }
.sidebar-spacer { height: 10px; }
</style>
""", unsafe_allow_html=True)

# ===================== 常數 =====================
MAX_ROUNDS = 3
QUESTIONS_PER_ROUND = 10
MODE_1 = "模式一｜手寫輸入（含中譯）"
MODE_2 = "模式二｜英文題目（中文選項）"
MODE_3 = "模式三｜中文題目（英文選項）"

# ===================== Google Drive / Sheets 解析 =====================
def parse_gdoc_or_drive(url: str):
    url = url.strip()
    m = re.search(r"docs\.google\.com\/spreadsheets\/d\/([a-zA-Z0-9-_]+)", url)
    if m:
        fid = m.group(1)
        return {"export_url": f"https://docs.google.com/spreadsheets/d/{fid}/export?format=xlsx"}
    m = re.search(r"drive\.google\.com\/.*?[?&]id=([a-zA-Z0-9_-]+)", url)
    if m:
        fid = m.group(1)
        return {"export_url": f"https://drive.google.com/uc?export=download&id={fid}"}
    return None

def download_bytes_by_url(export_url: str) -> bytes:
    r = requests.get(export_url, timeout=45)
    r.raise_for_status()
    return r.content

def load_table_from_bytes(raw: bytes) -> pd.DataFrame:
    try:
        return pd.read_excel(io.BytesIO(raw))
    except Exception:
        pass
    try:
        return pd.read_csv(io.BytesIO(raw), encoding="utf-8", encoding_errors="ignore")
    except Exception:
        pass
    try:
        return pd.read_csv(io.BytesIO(raw), encoding="big5", encoding_errors="ignore")
    except Exception:
        pass
    return pd.read_csv(io.BytesIO(raw), encoding="latin-1", encoding_errors="ignore")

def read_question_bank(url_input):
    if not url_input.strip():
        st.warning("請貼上 Google Drive / Google Sheets 連結")
        return None
    parsed = parse_gdoc_or_drive(url_input)
    if not parsed:
        st.error("連結格式錯誤，請確認是否為 Google Drive / Sheets")
        return None
    try:
        raw = download_bytes_by_url(parsed["export_url"])
        return load_table_from_bytes(raw)
    except Exception as e:
        st.error(f"讀取失敗：{e}")
        return None

# ===================== 欄位推斷 =====================
def infer_columns(df: pd.DataFrame):
    def norm_map(cols):
        return {c.strip().lower(): c for c in cols}
    n = norm_map(df.columns)

    def get(*cands):
        for c in cands:
            if c.lower() in n:
                return n[c.lower()]
        return None

    return (
        get("answer", "word"),
        get("cloze sentence", "english"),
        get("sentence translation (chinese)", "chinese"),
        get("meaning (chinese)", "meaning")
    )

def build_question_bank_from_df(df: pd.DataFrame, mapping=None):
    a_ans, a_en, a_zh, a_mean = infer_columns(df)
    if mapping:
        a_ans = mapping.get("answer_en") or a_ans
        a_en = mapping.get("cloze_en") or a_en
        a_zh = mapping.get("sent_zh") if mapping.get("sent_zh") != "(無)" else None
        a_mean = mapping.get("meaning_zh") if mapping.get("meaning_zh") != "(無)" else None

    def pick(row, col):
        if col and col in row and pd.notna(row[col]):
            return str(row[col]).strip()
        return ""

    bank = []
    for _, row in df.iterrows():
        item = {
            "answer_en": pick(row, a_ans),
            "cloze_en": pick(row, a_en),
            "sent_zh": pick(row, a_zh),
            "meaning_zh": pick(row, a_mean),
        }
        if item["cloze_en"] and item["answer_en"]:
            bank.append(item)

    uniq = {}
    for it in bank:
        uniq[(it["cloze_en"], it["answer_en"])] = it
    return list(uniq.values())

# ===================== 側邊欄 =====================
with st.sidebar:
    st.header("題庫連結（必填）")
    url_input = st.text_input(
        "貼上 Google Drive / Google Sheets 連結（公開可讀）",
        placeholder="https://docs.google.com/spreadsheets/d/xxxxxxxxxxxxxxxxxxxx/edit"
    )
    if st.button("讀取題庫", use_container_width=True):
        df = read_question_bank(url_input)
        if df is not None:
            st.success("題庫讀取成功！下方預覽前 20 列")
            st.dataframe(df.head(20), use_container_width=True)
            st.session_state["question_bank_df"] = df

    # 模式選擇移到這裡
    st.markdown("### 練習模式")
    if "mode" not in st.session_state:
        st.session_state.mode = MODE_1
    st.session_state.mode = st.radio(
        "選擇練習模式：",
        [MODE_1, MODE_2, MODE_3],
        index=[MODE_1, MODE_2, MODE_3].index(st.session_state.get("mode", MODE_1))
    )

# ===================== 主畫面提示 =====================
if "question_bank_df" not in st.session_state:
    st.markdown(
        "<div class='subtle-callout' style='margin-top: 48px;'>請先在&gt;&gt;貼上 Google Sheets/Drive 連結</div>",
        unsafe_allow_html=True
    )
    st.stop()

# (後續出題邏輯與上一版相同，讀取題庫 → init_state → start_new_round → render_question → handle_action)
# 只要保留原本的出題與答題流程即可，不需要再放一個主畫面的模式選單。
