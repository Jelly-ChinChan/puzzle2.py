# streamlit_app.py —— 需上傳 Excel 題庫版（移除藍色框、更新模式名稱）
import streamlit as st
import pandas as pd
import random
import pathlib

st.set_page_config(page_title="Cloze Test Practice (3 modes, rounds)", page_icon="📝", layout="centered")

# ===================== 樣式 =====================
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
</style>
""", unsafe_allow_html=True)

# ===================== 常數 =====================
MAX_ROUNDS = 3
QUESTIONS_PER_ROUND = 10

# ✅ 依你的文字更新模式名稱
MODE_1 = "模式一｜手寫輸入（含中譯）"        # 題幹：Cloze；下方顯示中文；作答：輸入英文（比對 Answer）
MODE_2 = "模式二｜英文題目（中文選項）"      # 題幹：Cloze；選項：Meaning(Chinese)；比對 Answer
MODE_3 = "模式三｜中文題目（英文選項）"      # 題幹：Sentence Translation (Chinese)；選項：Answer

# ===================== 欄位推斷 & 載入 =====================
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

@st.cache_data(show_spinner=False)
def load_question_bank(excel_file, mapping=None):
    df = pd.read_excel(excel_file)
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

    uniq = {}
    for it in bank:
        uniq[(it["cloze_en"], it["answer_en"])] = it
    return list(uniq.values()), (a_ans, a_en, a_zh, a_mean)

# ===================== 上傳檔案 =====================
with st.sidebar:
    st.markdown("### 題庫檔案（必填）")
    uploaded = st.file_uploader("上傳 Excel 題庫（.xlsx）", type=["xlsx"])

# ❌ 刪除原本的 st.info 藍色框；✅ 改為純文字提示
if not uploaded:
    st.markdown("<div class='subtle-callout'>請先上傳你的字庫Excel檔</div>", unsafe_allow_html=True)
    st.stop()

# 欄位映射（可選）
_tmp_df = pd.read_excel(uploaded)
detected_cols = infer_columns(_tmp_df)

with st.sidebar:
    st.markdown("### 欄位對應（若自動偵測錯誤可手動指定）")
    cols = list(_tmp_df.columns)
    answer_en = st.selectbox("正解英文（Answer）", options=cols, index=cols.index(detected_cols[0]) if detected_cols[0] in cols else 0)
    cloze_en  = st.selectbox("題幹英文（Cloze Sentence）", options=cols, index=cols.index(detected_cols[1]) if detected_cols[1] in cols else 0)
    sent_zh   = st.selectbox("題幹中文（Sentence Translation (Chinese)）", options=["(無)"] + cols,
                             index=(cols.index(detected_cols[2])+1) if detected_cols[2] in cols else 0)
    meaning_zh= st.selectbox("中文義（Meaning (Chinese)）", options=["(無)"] + cols,
                             index=(cols.index(detected_cols[3])+1) if detected_cols[3] in cols else 0)
    mapping = {"answer_en": answer_en, "cloze_en": cloze_en, "sent_zh": sent_zh, "meaning_zh": meaning_zh}

QUESTION_BANK, _ = load_question_bank(uploaded, mapping=mapping)
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

# ===================== 側邊欄 =====================
with st.sidebar:
    st.markdown("### 設定")
    can_change_mode = (
        st.session_state.cur_idx_in_round == 0 and
        not st.session_state.submitted and
        st.session_state.round == 1 and
        len(st.session_state.records) == 0
    )
    st.session_state.mode = st.radio("選擇練習模式", [MODE_1, MODE_2, MODE_3], index=0, disabled=not can_change_mode)

    if st.button("🔄 重新開始"):
        init_state()
        start_new_round()
        st.rerun()

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
