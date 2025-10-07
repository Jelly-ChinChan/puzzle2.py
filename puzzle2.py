# app.py
import io
import re
import requests
import pandas as pd
import streamlit as st

# -------- Page 基本設定 --------
st.set_page_config(page_title="Cloze Test Practice", layout="wide")

# -------- CSS：避免窄螢幕裁切、提升可讀性 --------
st.markdown("""
<style>
/* 讓窄螢幕下的側欄與內容不被裁切，並拉高行距 */
.stSidebar, .block-container { overflow: visible !important; }
label, .stText, .stMarkdown, .stCaption { line-height: 1.5; }
/* 讓手機上方不要貼太近 */
.sidebar-spacer { height: 10px; }
</style>
""", unsafe_allow_html=True)

# -------- 模式字串（換行顯示）--------
MODE_1 = "模式一\n-【手寫輸入】"
MODE_2 = "模式二\n-【中文選擇】"
MODE_3 = "模式三\n-【英文選擇】"
MODE_OPTIONS = [MODE_1, MODE_2, MODE_3]

# -------- Google Drive 下載工具 --------
def extract_drive_file_id(url: str) -> str | None:
    """支援多種 Google Drive 連結格式，回傳 file id 或 None"""
    patterns = [
        r"drive\.google\.com\/file\/d\/([a-zA-Z0-9_-]+)",
        r"drive\.google\.com\/open\?id=([a-zA-Z0-9_-]+)",
        r"drive\.google\.com\/uc\?id=([a-zA-Z0-9_-]+)",
        r"drive\.google\.com\/.*?id=([a-zA-Z0-9_-]+)",
    ]
    for p in patterns:
        m = re.search(p, url)
        if m:
            return m.group(1)
    return None

def download_drive_file_as_bytes(file_id: str) -> bytes:
    """用公開分享的 file id 下載內容"""
    url = f"https://drive.google.com/uc?export=download&id={file_id}"
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return r.content

# -------- 題庫讀取主函式 --------
def read_question_bank(uploaded_file, gdrive_url):
    """回傳 pandas.DataFrame（從上傳或 Google Drive 擇一）"""
    if uploaded_file is None and not gdrive_url.strip():
        st.warning("請先上傳檔案，或貼上 Google Drive 連結。")
        return None

    try:
        # 1) 直接上傳
        if uploaded_file is not None:
            name = uploaded_file.name.lower()
            if name.endswith(".csv"):
                df = pd.read_csv(uploaded_file)
            else:  # .xlsx / .xls
                df = pd.read_excel(uploaded_file)
            return df

        # 2) Google Drive 連結
        fid = extract_drive_file_id(gdrive_url.strip())
        if not fid:
            st.error("看起來這不是有效的 Google Drive 連結。請確認分享權限為『知道連結的任何人可檢視』。")
            return None

        raw = download_drive_file_as_bytes(fid)

        # 嘗試以 Excel 讀取；失敗再試 CSV
        try:
            df = pd.read_excel(io.BytesIO(raw))
            return df
        except Exception:
            df = pd.read_csv(io.BytesIO(raw))
            return df

    except requests.exceptions.RequestException:
        st.error("下載連結時發生網路錯誤。請檢查網路、改用其他瀏覽器（Safari/Firefox），或改用電腦上傳。")
    except Exception as e:
        st.error(
            f"讀取題庫失敗：{e}\n\n建議：1) 改用 Safari/Firefox，"
            "2) 改貼公開的 Google Drive 連結，3) 確認檔案為 .xlsx/.xls/.csv"
        )
    return None

# ================== UI：側欄 ==================
with st.sidebar:
    st.header("題庫檔案（必填）")
    st.markdown("<div class='sidebar-spacer'></div>", unsafe_allow_html=True)

    # 上傳元件（允許多副檔名，手機較不易誤判）
    uploaded_file = st.file_uploader(
        "上傳 Excel 題庫（.xlsx / .xls / .csv）",
        type=["xlsx", "xls", "csv"]
    )
    # 你的指定文案
    st.caption("請先從>>處 上傳你的字庫Excel檔")

    # 手機備案：Google Drive 連結
    gdrive_url = st.text_input("或貼上 Google Drive 連結（公開可讀）")
    st.caption("⚠️ 若手機上傳出現 Network/Axios 錯誤，請改貼公開分享連結，或換 Safari / Firefox。")

    # 讀取按鈕
    read_btn = st.button("讀取題庫")

    st.divider()

    # 模式選擇（換行樣式）
    mode = st.radio(
        "選擇練習模式",
        MODE_OPTIONS,
        index=0,
        help="手機上以換行顯示：\n模式一 ↵\n-【手寫輸入】"
    )

# ================== 主區塊 ==================
st.title("Cloze Test Practice (3 modes)")
st.write("目前模式：", mode.replace("\n", " "))  # 顯示為單行說明即可

if read_btn:
    df = read_question_bank(uploaded_file, gdrive_url)
    if df is not None:
        st.success("題庫讀取成功！以下為前 20 列預覽：")
        st.dataframe(df.head(20), use_container_width=True)
        st.session_state["question_bank"] = df

# 之後你的練習邏輯可直接使用：
# df = st.session_state.get("question_bank")
# if df is not None:
#     ...  # 依模式 mode 進行練習流程
