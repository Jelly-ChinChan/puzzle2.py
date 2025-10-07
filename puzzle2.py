# streamlit_app.py —— 上傳/連結讀題庫 + 三模式 + 回合制（CSV errors 修正）
import io
import re
import requests
import pandas as pd
import streamlit as st
import random

st.set_page_config(page_title="Cloze Test Practice (3 modes, rounds)", page_icon="📝", layout="centered")

# ===================== 全域樣式 =====================
st.markdown("""
<style>
html, body, [class*="css"]  { font-size: 22px !important; }
h2 { font-size: 26px !important; margin-top: 0.22em !important; margin-bottom: 0.22em !important; }
.block-container { padding-top: 0.4rem !important; padding-bottom: 0.9rem !important; max-width: 1000px; }
.progress-card { margin-bottom: 0.22rem !important; }
.stRadio { margin-top: 0 !important; }
div[data-testid="stVerticalBlock"] > div:has(> div[data-testid="stRadio"]) { margin-top: 0 !important; }
.stButton>button{ height: 44px; padding: 0 18px; }
.feedback-small { font-size: 17px !important; line-height: 1.4; margin: 6px 0 2px 0; }
.feedback-correct { color: #1a7f37; font-weight: 700; }
.feedback-wrong { color: #c62828; font-weight: 700; }
.zh-blue { color: #1e88e5; }
.subtle-callout { margin-top: 1.2rem; padding: 12px 14px; border-radius: 10px; background: #fafafa; border: 1px dashed #ddd; }
.stSidebar, .block-container { overflow: visible !important; }
label, .stText, .stMarkdown, .stCaption { line-height: 1.5; }
.sidebar-spacer { height: 10px; }
</style>
""", unsafe_allow_html=True)

# ===================== 常數 =====================
MAX_ROUNDS = 3
QUESTIONS_PER_ROUND = 10

MODE_1 = "模式一｜手寫輸入（含中譯）"        # 題幹：Cloze；下方顯示中文；作答：輸入英文（比對 Answer）
MODE_2 = "模式二｜英文題目（中文選項）"      # 題幹：Cloze；選項：Meaning(Chinese)；比對 Answer
MODE_3 = "模式三｜中文題目（英文選項）"      # 題幹：Sentence Translation (Chinese)；選項：Answer

# ===================== 解析 & 下載（支援 Drive / Sheets） =====================
def parse_gdoc_or_drive(url: str):
    url = url.strip()
    m = re.search(r"docs\.google\.com\/spreadsheets\/d\/([a-zA-Z0-9-_]+)", url)
    if m:
        fid = m.group(1)
        export_url = f"https://docs.google.com/spreadsheets/d/{fid}/export?format=xlsx"
        return {"kind": "sheets", "id": fid, "export_url": export_url}
    patterns = [
        r"drive\.google\.com\/file\/d\/([a-zA-Z0-9_-]+)",
        r"drive\.google\.com\/open\?id=([a-zA-Z0-9_-]+)",
        r"drive\.google\.com\/uc\?id=([a-zA-Z0-9_-]+)",
        r"drive\.google\.com\/.*?[?&]id=([a-zA-Z0-9_-]+)",
    ]
    for p in patterns:
        m = re.search(p, url)
        if m:
            fid = m.group(1)
            export_url = f"https://drive.google.com/uc?export=download&id={fid}"
            return {"kind": "drive_file", "id": fid, "export_url": export_url}
    return None

def download_bytes_by_url(export_url: str) -> bytes:
    r = requests.get(export_url, timeout=45)
    r.raise_for_status()
    return r.content

def load_table_from_bytes(raw: bytes) -> pd.DataFrame:
    """
    先嘗試以 Excel 讀；若失敗再嘗試 CSV（UTF-8 / Big5 / Latin-1，忽略壞字元）。
    """
    # Excel
    try:
        return pd.read_excel(io.BytesIO(raw))
    except Exception:
        pass
    # CSV UTF-8
    try:
        return pd.read_csv(io.BytesIO(raw), encoding="utf-8", encoding_errors="ignore")
    except Exception:
        pass
    # CSV Big5
    try:
        return pd.read_csv(io.BytesIO(raw), encoding="big5", encoding_errors="ignore")
    except Exception:
        pass
    # CSV Latin-1（最後一層）
    try:
        return pd.read_csv(io.BytesIO(raw), encoding="latin-1", encoding_errors="ignore")
    except Exception as e:
        raise e

def read_question_bank(uploaded_file, url_input):
    """
    二選一：上傳檔案或貼連結。成功回傳 DataFrame，否則 None。
    """
    if uploaded_file is None and not url_input.strip():
        st.warning("請先上傳檔案，或貼上 Google Drive / Google Sheets 連結。")
        return None

    # A) 直接上傳
    if uploaded_file is not None:
        name = uploaded_file.name.lower()
        try:
            if name.endswith(".csv"):
                # 預設 → UTF-8 → Big5 → Latin-1（均忽略壞字元）
                try:
                    return pd.read_csv(uploaded_file)
                except Exception:
                    uploaded_file.seek(0)
                    try:
                        return pd.read_csv(uploaded_file, encoding="utf-8", encoding_errors="ignore")
                    except Exception:
                        uploaded_file.seek(0)
                        try:
                            return pd.read_csv(uploaded_file, encoding="big5", encoding_errors="ignore")
                        except Exception:
                            uploaded_file.seek(0)
                            return pd.read_csv(uploaded_file, encoding="latin-1", encoding_errors="ignore")
            else:
                return pd.read_excel(uploaded_file)
        except Exception as e:
            st.error(f"讀取上傳檔案失敗：{e}")
            return None

    # B) 連結下載
    parsed = parse_gdoc_or_drive(url_input)
    if not parsed:
        st.error(
            "這不是可辨識的 Google Drive/Sheets 連結。請用：\n"
            "• Drive 檔案：drive.google.com/file/d/<ID>/...\n"
            "• 試算表：docs.google.com/spreadsheets/d/<ID>/...（會自動轉成 xlsx）"
        )
        return None

    try:
        raw = download_bytes_by_url(parsed["export_url"])
        df = load_table_from_bytes(raw)
        return df
    except requests.exceptions.RequestException:
        st.error("下載連結時發生網路錯誤。請確認公開權限或稍候再試，或改用 Safari / Firefox。")
    except Exception as e:
        st.error(f"解析連結內容失敗：{e}")
    return None

# ===================== 欄位推斷 & 題庫建置 =====================
def infer_columns(df: pd.DataFrame):
    def norm_map(cols):
        return {c.strip().lower(): c for c in cols}
    n = norm_map(df.columns)

    def get(*cands):
        for c in cands:
            key = c.strip().lower()
            if key in n:
                return n[key]
        return None

    cloze_en = get("cloze sentence", "cloze_sentence", "cloze", "english_sentence", "sentence_en", "english")
    sent_zh  = get("sentence translation (chinese)", "sentence_translation_(chinese)",
                   "sentence translation ( chinese )", "sentence_translation", "sentence_zh",
                   "chinese_sentence", "zh_sentence", "translation_chinese")
    answer_en = get("answer", "word", "term", "english_word")
    meaning_zh = get("meaning (chinese)", "meaning", "chinese meaning", "meaning_zh", "definition_zh", "chinese")

    return answer_en, cloze_en, sent_zh, meaning_zh

def build_question_bank_from_df(df: pd.DataFrame, mapping=None):
    a_ans, a_en, a_zh, a_mean = infer_columns(df)
    if mapping:
        a_ans  = mapping.get("answer_en") or a_ans
        a_en   = mapping.get("cloze_en") or a_en
        a_zh   = mapping.get("sent_zh") if mapping.get("sent_zh") != "(無)" else None
        a_mean = mapping.get("meaning_zh") if mapping.get("meaning_zh") != "(無)" else None

    def pick(row, col):
        if col and col in row and pd.notna(row[col]):
            return str(row[col]).strip()
        return ""

    bank = []
    for _, row in df.iterrows():
        item = {
            "answer_en":  pick(row, a_ans),
            "cloze_en":   pick(row, a_en),
            "sent_zh":    pick(row, a_zh),
            "meaning_zh": pick(row, a_mean),
        }
        if item["cloze_en"] and item["answer_en"]:
            bank.append(item)

    # 去重
    uniq = {}
    for it in bank:
        uniq[(it["cloze_en"], it["answer_en"])] = it
    return list(uniq.values()), (a_ans, a_en, a_zh, a_mean)

# ===================== 側欄：I/O UI（上傳或貼連結） =====================
with st.sidebar:
    st.header("題庫檔案（必填）")
    st.markdown("<div class='sidebar-spacer'></div>", unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
        "上傳 Excel 題庫（.xlsx / .xls / .csv）",
        type=["xlsx", "xls", "csv"]
    )
    st.caption("請先從>>處 上傳你的字庫Excel檔")

    url_input = st.text_input(
        "或貼上 Google Drive / Google Sheets 連結（公開可讀）",
        placeholder="https://docs.google.com/spreadsheets/d/xxxxxxxxxxxxxxxxxxxx/edit"
    )
    st.caption("⚠️ 若手機上傳出現 Network/Axios 錯誤，建議改貼公開分享連結，或換 Safari / Firefox。")

    if st.button("讀取題庫"):
        df = read_question_bank(uploaded_file, url_input)
        if df is not None:
            st.success("題庫讀取成功！下方預覽前 20 列。")
            st.dataframe(df.head(20), use_container_width=True)
            st.session_state["question_bank_df"] = df

# 沒有資料時：顯示灰底提示（取代原本藍色框）
if "question_bank_df" not in st.session_state:
    st.markdown("<div class='subtle-callout'>請先在&gt;&gt;上傳你的字庫Excel檔</div>", unsafe_allow_html=True)
    st.stop()

# ===================== 欄位對應（有資料後才顯示） =====================
_df = st.session_state["question_bank_df"]
detected_cols = infer_columns(_df)

with st.sidebar:
    st.markdown("### 欄位對應（若自動偵測錯誤可手動指定）")
    cols = list(_df.columns)
    answer_en = st.selectbox("正解英文（Answer）", options=cols, index=cols.index(detected_cols[0]) if detected_cols[0] in cols else 0)
    cloze_en  = st.selectbox("題幹英文（Cloze Sentence）", options=cols, index=cols.index(detected_cols[1]) if detected_cols[1] in cols else 0)
    sent_zh   = st.selectbox("題幹中文（Sentence Translation (Chinese)）", options=["(無)"] + cols,
                             index=(cols.index(detected_cols[2])+1) if detected_cols[2] in cols else 0)
    meaning_zh= st.selectbox("中文義（Meaning (Chinese)）", options=["(無)"] + cols,
                             index=(cols.index(detected_cols[3])+1) if detected_cols[3] in cols else 0)
    mapping = {"answer_en": answer_en, "cloze_en": cloze_en, "sent_zh": sent_zh, "meaning_zh": meaning_zh}

QUESTION_BANK, _ = build_question_bank_from_df(_df, mapping=mapping)

if len(QUESTION_BANK) < 10:
    st.error("題庫少於 10 題，無法進行回合制。請檢查檔案內容。")
    st.stop()

# ===================== 狀態 =====================
def init_state():
    st.session_state.mode = MODE_1
    st.session_state.round = 1
    st.session_state.used_answers = set()
    st.session_state.cur_round_qidx = []
    st.session_state.cur_idx_in_round = 0
    st.session_state.records = []   # (round, prompt, chosen, correct_en, is_correct, opts_disp, opts_val)
    st.session_state.score_this_round = 0
    st.session_state.submitted = False
    st.session_state.last_feedback = ""
    st.session_state.options_cache = {}
    st.session_state.text_input_cache = ""

def start_new_round():
    available = [i for i, it in enumerate(QUESTION_BANK) if it["answer_en"] not in st.session_state.used_answers]
    chosen = available if len(available) < QUESTIONS_PER_ROUND else random.sample(available, QUESTIONS_PER_ROUND)
    st.session_state.cur_round_qidx = chosen
    st.session_state.cur_idx_in_round = 0
    st.session_state.score_this_round = 0
    st.session_state.submitted = False
    st.session_state.last_feedback = ""
    st.session_state.options_cache = {}
    st.session_state.text_input_cache = ""

if "round" not in st.session_state:
    init_state()
    start_new_round()

# ===================== 選項產生 =====================
def get_options_for_q(qidx, mode):
    key = (qidx, mode)
    if key in st.session_state.options_cache:
        return st.session_state.options_cache[key]

    item = QUESTION_BANK[qidx]
    correct_en = item["answer_en"].strip()
    correct_zh = item.get("meaning_zh", "").strip()
    payload = {"display": [], "value": []}

    if mode == MODE_2:
        # 中文選項（值＝英文）
        pool = list({it.get("meaning_zh","").strip() for it in QUESTION_BANK
                     if it.get("meaning_zh") and it.get("meaning_zh").strip() and it.get("meaning_zh").strip()!=correct_zh})
        distractors = random.sample(pool, k=min(3, len(pool)))
        display = list(dict.fromkeys([correct_zh] + distractors))
        random.shuffle(display)
        value = []
        for zh in display:
            en = next((it["answer_en"] for it in QUESTION_BANK
                       if str(it.get("meaning_zh","")).strip() == zh), "")
            value.append(str(en).strip())
        payload = {"display": display, "value": value}

    elif mode == MODE_3:
        # 英文選項（值＝英文）
        pool = list({it["answer_en"].strip() for it in QUESTION_BANK
                     if it.get("answer_en") and it["answer_en"].strip() and it["answer_en"].strip()!=correct_en})
        distractors = random.sample(pool, k=min(3, len(pool)))
        display = list(dict.fromkeys([correct_en] + distractors))
        random.shuffle(display)
        payload = {"display": display, "value": display[:]}

    st.session_state.options_cache[key] = payload
    return payload

# ===================== UI 元件 =====================
def render_top_card():
    r = st.session_state.round
    i = st.session_state.cur_idx_in_round + 1
    n = len(st.session_state.cur_round_qidx)
    percent = int(i / n * 100) if n else 0
    st.markdown(
        f"""
        <div class="progress-card" style='background-color:#f5f5f5; padding:9px 14px; border-radius:12px;'>
            <div style='display:flex; align-items:center; justify-content:space-between; margin-bottom:4px;'>
                <div style='font-size:18px;'>🎯 第 {r} 回合｜進度：{i} / {n}</div>
                <div style='font-size:16px; color:#555;'>{percent}%</div>
            </div>
            <progress value='{i}' max='{n if n else 1}' style='width:100%; height:14px;'></progress>
        </div>
        """,
        unsafe_allow_html=True
    )

def render_question():
    cur_pos = st.session_state.cur_idx_in_round
    qidx = st.session_state.cur_round_qidx[cur_pos]
    q = QUESTION_BANK[qidx]
    mode = st.session_state.mode

    # 題幹
    if mode == MODE_3:
        prompt = (q.get("sent_zh") or "").strip()
        st.markdown(f"<h2>Q{cur_pos + 1}. {prompt if prompt else '（此題缺少中文題幹）'}</h2>", unsafe_allow_html=True)
    else:
        st.markdown(f"<h2>Q{cur_pos + 1}. {q['cloze_en']}</h2>", unsafe_allow_html=True)
        if mode == MODE_1 and q.get("sent_zh"):
            st.markdown(f"<div class='zh-blue'>📘 {q['sent_zh']}</div>", unsafe_allow_html=True)

    # 作答介面
    if mode == MODE_1:
        user_text = st.text_input("請輸入英文答案：", key=f"ti_{qidx}", value=st.session_state.text_input_cache)
        return qidx, q, user_text
    else:
        payload = get_options_for_q(qidx, mode)
        options_disp = payload["display"]
        if not options_disp:
            st.markdown("<div class='subtle-callout'>此題沒有可用選項，請檢查題庫欄位內容。</div>", unsafe_allow_html=True)
            user_choice_disp = None
        else:
            user_choice_disp = st.radio("", options_disp, key=f"mc_{qidx}", label_visibility="collapsed")
        return qidx, q, (user_choice_disp, payload)

# ===================== 交互 =====================
def handle_action(qidx, q, user_input):
    mode = st.session_state.mode
    correct_en = (q.get("answer_en") or "").strip()

    if mode == MODE_1:
        user_ans = (user_input or "").strip()
        is_correct = (user_ans.lower() == correct_en.lower()) if correct_en else False
        chosen_label = user_ans
        opts_disp, opts_val = [], []
    else:
        chosen_disp, payload = user_input
        if chosen_disp is None:
            st.warning("請先選擇一個選項。")
            return
        options_disp = payload["display"]
        options_val  = payload["value"]

        try:
            idx = options_disp.index(chosen_disp)
            chosen_value = options_val[idx] if idx < len(options_val) else ""
        except ValueError:
            chosen_value = ""

        if mode == MODE_2:
            is_correct = (chosen_value.strip().lower() == correct_en.lower())
            chosen_label = chosen_disp  # 顯示中文
        else:
            is_correct = (chosen_disp.strip().lower() == correct_en.lower())
            chosen_label = chosen_disp  # 顯示英文

        opts_disp, opts_val = options_disp, options_val

    # 第一次按：送出並判題
    if not st.session_state.submitted:
        st.session_state.submitted = True
        st.session_state.records.append((
            st.session_state.round,
            q["cloze_en"] if mode != MODE_3 else (q.get("sent_zh") or ""),
            chosen_label,
            correct_en,
            is_correct,
            opts_disp,
            opts_val,
        ))
        if is_correct:
            st.session_state.last_feedback = "<div class='feedback-small feedback-correct'>✅ 回答正確</div>"
            st.session_state.score_this_round += 1
        else:
            st.session_state.last_feedback = f"<div class='feedback-small feedback-wrong'>❌ Incorrect. 正確答案：{correct_en}</div>"
        st.rerun()
    else:
        # 第二次按：下一題／下一回合／結束
        st.session_state.used_answers.add(correct_en)
        st.session_state.cur_idx_in_round += 1
        st.session_state.submitted = False
        st.session_state.last_feedback = ""
        st.session_state.text_input_cache = ""
        if st.session_state.cur_idx_in_round >= len(st.session_state.cur_round_qidx):
            if (st.session_state.score_this_round == len(st.session_state.cur_round_qidx)) and (st.session_state.round < MAX_ROUNDS):
                st.session_state.round += 1
                start_new_round()
            else:
                st.session_state.round = None
        st.rerun()

# ===================== 主畫面 =====================
if st.session_state.round:
    render_top_card()
    qidx, q, user_input = render_question()

    # 上方即時回饋
    if st.session_state.submitted and st.session_state.last_feedback:
        st.markdown(st.session_state.last_feedback, unsafe_allow_html=True)

    # 送出／下一題
    action_label = "下一題" if st.session_state.submitted else "送出答案"
    if st.button(action_label, key="action_btn"):
        handle_action(qidx, q, user_input)

    # 提交後：固定顯示 正確答案（英＋中） + 選項配對（依模式）
    if st.session_state.submitted and st.session_state.records:
        last = st.session_state.records[-1]
        _, _, _, correct_en, _, opts_disp, opts_val = last

        en2zh = { (it.get("answer_en") or "").strip(): (it.get("meaning_zh") or "").strip()
                  for it in QUESTION_BANK }

        correct_zh = en2zh.get(correct_en, "")
        st.markdown("---")
        st.markdown(f"**正確答案：{correct_en}**　({correct_zh})")

        # 模式2：中文：英文
        if st.session_state.mode == MODE_2 and opts_disp:
            pairs = []
            for zh, en in zip(opts_disp, (opts_val or [])):
                zh_s, en_s = str(zh).strip(), str(en).strip()
                if zh_s and en_s:
                    pairs.append(f"{zh_s}：{en_s}")
            if pairs:
                st.markdown("**本題所有選項的選項：**  ")
                st.markdown("、".join(pairs))

        # 模式3：英文：中文
        if st.session_state.mode == MODE_3 and opts_disp:
            pairs = []
            for en in opts_disp:
                en_s = str(en).strip()
                if not en_s:
                    continue
                zh_s = en2zh.get(en_s, "")
                pairs.append(f"{en_s}：{zh_s if zh_s else '(無中文)'}")
            if pairs:
                st.markdown("**本題所有選項的選項：**  ")
                st.markdown("、".join(pairs))

else:
    # 結果頁
    total_answered = len(st.session_state.records)
    total_correct = sum(1 for rec in st.session_state.records if rec[4])
    st.subheader("📊 總結")
    st.markdown(f"<h3>Total Answered: {total_answered}</h3>", unsafe_allow_html=True)
    st.markdown(f"<h3>Total Correct: {total_correct}</h3>", unsafe_allow_html=True)
    acc = (total_correct / total_answered * 100) if total_answered else 0.0
    st.markdown(f"<h3>Accuracy: {acc:.1f}%</h3>", unsafe_allow_html=True)
    st.button("🔄 再玩一次", on_click=lambda: (init_state(), start_new_round()))
