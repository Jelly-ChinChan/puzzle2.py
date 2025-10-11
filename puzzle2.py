# streamlit_app.py — 內建題庫 + GSheet 紀錄（即時寫入版）
import streamlit as st
import random
import datetime as dt
import uuid
import json

# ====== Google Sheet ======
_GS_OK = False
_gs_worksheet = None
_SHEET_NAME = "responses"

def _now_ts():
    return dt.datetime.now().isoformat(timespec="seconds")

def _connect_gsheet():
    """讀取 st.secrets['gsheets']，建立 worksheet 連線（若沒設就回 False）"""
    global _GS_OK, _gs_worksheet
    try:
        conf = st.secrets.get("gsheets", {})
        sid = conf.get("spreadsheet_id")
        saj = conf.get("service_account_json")
        if not (sid and saj):
            _GS_OK = False
            return False, "Secrets 未設定 gsheets"
        from google.oauth2.service_account import Credentials
        import gspread

        creds = Credentials.from_service_account_info(json.loads(saj), scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ])
        gc = gspread.authorize(creds)
        sh = gc.open_by_key(sid)
        # 取工作表；沒有就建立
        try:
            ws = sh.worksheet(_SHEET_NAME)
        except Exception:
            ws = sh.add_worksheet(title=_SHEET_NAME, rows=1000, cols=20)
            ws.append_row([
                "timestamp","session_id","name","class","seat",
                "phase","mode","round","q_index",
                "prompt","correct_en","chosen","is_correct"
            ])
        _gs_worksheet = ws
        _GS_OK = True
        return True, "OK"
    except Exception as e:
        _GS_OK = False
        return False, str(e)

def _clean_mode(mode_obj) -> str:
    return str(mode_obj).replace("\n", " ")

def append_to_gsheet(rows):
    """rows: List[List]"""
    if not _GS_OK or not _gs_worksheet:
        ok, msg = _connect_gsheet()
        if not ok:
            return False, msg
    try:
        _gs_worksheet.append_rows(rows, value_input_option="RAW")
        return True, "OK"
    except Exception as e:
        return False, str(e)

def append_to_local_csv(rows, path="responses.csv"):
    import csv, os
    header = [
        "timestamp","session_id","name","class","seat",
        "phase","mode","round","q_index",
        "prompt","correct_en","chosen","is_correct"
    ]
    exists = os.path.exists(path)
    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if not exists:
            w.writerow(header)
        w.writerows(rows)

# ====== App 基本設定 ======
st.set_page_config(page_title="Cloze Test Practice (3 modes, rounds)", page_icon="📝", layout="centered")

# ===================== 內建題庫 =====================
QUESTION_BANK = [
    {'answer_en': 'adjust', 'cloze_en': 'He tried to a_____t his chair to be more comfortable.', 'sent_zh': '他試著調整椅子讓自己更舒服。', 'meaning_zh': '調整'},
    {'answer_en': 'adjustment', 'cloze_en': 'The teacher made an a_____t to the lesson plan.', 'sent_zh': '老師對課程計畫做了調整。', 'meaning_zh': '調整'},
    {'answer_en': 'architect', 'cloze_en': 'The city is famous for its modern a_____e.', 'sent_zh': '這座城市以其現代建築而聞名。', 'meaning_zh': '建築師；建築物'},
    {'answer_en': 'banishment', 'cloze_en': 'His crimes led to his b_____t from the country.', 'sent_zh': '他的罪行導致他的放逐。', 'meaning_zh': '放逐；驅逐'},
    {'answer_en': 'capable', 'cloze_en': 'She is c_____e of solving this problem.', 'sent_zh': '她有能力解決這個問題。', 'meaning_zh': '有能力的'},
    {'answer_en': 'capability', 'cloze_en': 'This device has the c_____y to store a large amount of data.', 'sent_zh': '這個裝置具有儲存大量資料的能力。', 'meaning_zh': '能力；容量'},
    {'answer_en': 'collapse', 'cloze_en': 'The building c_____d after the earthquake.', 'sent_zh': '地震後建築物倒塌了。', 'meaning_zh': '倒塌'},
    {'answer_en': 'comfort', 'cloze_en': 'A cup of hot tea gave her some c_____t.', 'sent_zh': '一杯熱茶給了她一些安慰。', 'meaning_zh': '安慰；舒適'},
    {'answer_en': 'commodity', 'cloze_en': 'Water is a precious c_____y in the desert.', 'sent_zh': '在沙漠中水是珍貴的商品。', 'meaning_zh': '商品；日用品'},
    {'answer_en': 'complicate', 'cloze_en': 'Do not c_____e the issue with too many details.', 'sent_zh': '不要用太多細節使問題複雜化。', 'meaning_zh': '使複雜'},
]

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
</style>
""", unsafe_allow_html=True)

MAX_ROUNDS = 3
QUESTIONS_PER_ROUND = 10

MODE_1 = "模式一\n-   【手寫輸入】"
MODE_2 = "模式二\n-   【中文選擇】"
MODE_3 = "模式三\n-   【英文選擇】"

# ===================== 工具：比對 =====================
def _norm(s: str) -> str:
    return (s or "").strip().lower()

def _variants(correct: str):
    c = _norm(correct)
    vs = {c, c+"s", c+"es"}
    if c.endswith("y"): vs.add(c[:-1]+"ies")
    vs.add(c+"ed")
    if c.endswith("y"): vs.add(c[:-1]+"ied")
    if c.endswith("e") and not c.endswith("ee"): vs.add(c[:-1]+"ing")
    else: vs.add(c+"ing")
    if c.endswith("y"): vs.add(c[:-1]+"ying")
    return vs

def is_free_text_correct(user_ans: str, correct_en: str) -> bool:
    u = _norm(user_ans); c = _norm(correct_en)
    if not u: return False
    if u == c or u in _variants(c): return True
    if u.endswith("s") and u[:-1] == c: return True
    if u.endswith("es") and (u[:-2] == c or c+"e" == u[:-1]): return True
    if u.endswith("ies") and c.endswith("y") and u[:-3]+"y" == c: return True
    return False

# ===================== 狀態 =====================
def init_state():
    st.session_state.mode = MODE_1
    st.session_state.round = 1
    st.session_state.used_answers = set()
    st.session_state.cur_round_qidx = []
    st.session_state.cur_idx_in_round = 0
    st.session_state.records = []  # (round, prompt, chosen, correct, is_correct, opts_disp, opts_val)
    st.session_state.score_this_round = 0
    st.session_state.submitted = False
    st.session_state.last_feedback = ""
    st.session_state.options_cache = {}
    st.session_state.text_input_cache = ""
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())

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

# ====== GSheet 寫入：每題立即 append ======
def persist_one(qidx:int, q:dict, chosen_label:str, is_correct:bool, phase:str):
    """把單題紀錄立即寫入 GSheet（失敗則落地 CSV）"""
    name = st.session_state.get("user_name","")
    klass = st.session_state.get("user_class","")
    seat = st.session_state.get("user_seat","")
    sid = st.session_state.get("session_id","")
    mode = _clean_mode(st.session_state.mode)
    rnd = st.session_state.get("round")
    prompt = q["cloze_en"] if st.session_state.mode != MODE_3 else (q.get("sent_zh","") or "")
    row = [[
        _now_ts(), sid, name, klass, seat,
        phase, mode, rnd, (st.session_state.cur_idx_in_round+1),
        prompt, q["answer_en"].strip(), chosen_label, str(bool(is_correct))
    ]]
    ok, msg = append_to_gsheet(row)
    if not ok:
        append_to_local_csv(row)

# ===================== 側邊欄（身分＋工具） =====================
with st.sidebar:
    st.markdown("### 設定 / 身分")
    st.session_state.user_name = st.text_input("姓名", st.session_state.get("user_name",""))
    st.session_state.user_class = st.text_input("班級", st.session_state.get("user_class",""))
    st.session_state.user_seat = st.text_input("座號", st.session_state.get("user_seat",""))

    can_change_mode = (
        st.session_state.cur_idx_in_round == 0 and
        not st.session_state.submitted and
        st.session_state.round == 1 and
        len(st.session_state.records) == 0
    )
    st.session_state.mode = st.radio("選擇練習模式", [MODE_1, MODE_2, MODE_3], index=0, disabled=not can_change_mode)

    if st.button("🔄 重新開始"):
        init_state(); start_new_round(); st.rerun()

    # 測試寫入 & 偵錯
    if st.button("🧪 測試寫入（Google Sheet）"):
        ok, msg = append_to_gsheet([[
            _now_ts(), st.session_state.get("session_id",""), "PING","-","-",
            "Test","-", st.session_state.get("round"), st.session_state.get("cur_idx_in_round",0)+1,
            "(Connectivity test)","-","-", "True"
        ]])
        st.success("已寫入 PING，請到 responses 工作表查看。") if ok else st.error(f"寫入失敗：{msg}")

    with st.expander("🔍 連線狀態 / 偵錯"):
        conf = st.secrets.get("gsheets", {}) if hasattr(st,"secrets") else {}
        sid = conf.get("spreadsheet_id","(未設)")
        saj = conf.get("service_account_json")
        client_email = "(未知)"
        try:
            if saj: client_email = json.loads(saj).get("client_email", client_email)
        except Exception:
            client_email = "(secrets JSON 無法解析)"
        st.write({"GS_configured": bool(conf), "spreadsheet_id": sid, "service_account": client_email})
        ok, msg = _connect_gsheet()
        st.write({"_connect_gsheet": ok, "msg": msg})

# ===================== 選項生成 =====================
def get_options_for_q(qidx, mode):
    key = (qidx, mode)
    if key in st.session_state.options_cache:
        return st.session_state.options_cache[key]
    item = QUESTION_BANK[qidx]
    correct_en = item["answer_en"].strip()
    correct_zh = (item.get("meaning_zh") or "").strip()

    if mode == MODE_2:  # 中文選項
        pool = list({(it.get("meaning_zh") or "").strip() for it in QUESTION_BANK if (it.get("meaning_zh") or "").strip() and (it.get("meaning_zh") or "").strip() != correct_zh})
        distractors = random.sample(pool, k=min(3, len(pool)))
        display = list(dict.fromkeys([correct_zh] + distractors)); random.shuffle(display)
        payload = {"display": display, "value": display[:]}

    elif mode == MODE_3:  # 英文選項
        pool = list({it["answer_en"].strip() for it in QUESTION_BANK if it["answer_en"].strip() and it["answer_en"].strip() != correct_en})
        distractors = random.sample(pool, k=min(3, len(pool)))
        display = list(dict.fromkeys([correct_en] + distractors)); random.shuffle(display)
        payload = {"display": display, "value": display[:]}

    else:
        payload = {"display": [], "value": []}

    st.session_state.options_cache[key] = payload
    return payload

# ===================== UI 區塊 =====================
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

    if mode == MODE_3:
        prompt = q.get("sent_zh", "").strip()
        st.markdown(f"<h2>Q{cur_pos + 1}. {prompt if prompt else '（此題缺少中文題幹）'}</h2>", unsafe_allow_html=True)
    else:
        st.markdown(f"<h2>Q{cur_pos + 1}. {q['cloze_en']}</h2>", unsafe_allow_html=True)
        if mode == MODE_1 and q.get("sent_zh"):
            st.markdown(f"<div class='zh-blue'>📘 {q['sent_zh']}</div>", unsafe_allow_html=True)

    if mode == MODE_1:
        user_text = st.text_input("請輸入英文答案：", key=f"ti_{qidx}", value=st.session_state.text_input_cache)
        return qidx, q, user_text
    else:
        payload = get_options_for_q(qidx, mode)
        options_disp = payload["display"]
        if not options_disp:
            st.info("No options to select.")
            user_choice_disp = None
        else:
            user_choice_disp = st.radio("", options_disp, key=f"mc_{qidx}", label_visibility="collapsed")
        return qidx, q, (user_choice_disp, payload)

def handle_action(qidx, q, user_input):
    mode = st.session_state.mode
    correct_en = q["answer_en"].strip()
    correct_zh = (q.get("meaning_zh") or "").strip()

    if mode == MODE_1:
        user_ans = (user_input or "").strip()
        is_correct = is_free_text_correct(user_ans, correct_en)
        chosen_label = user_ans
    else:
        chosen_disp, payload = user_input
        if chosen_disp is None:
            st.warning("請先選擇一個選項。")
            return
        if mode == MODE_2:
            is_correct = (_norm(chosen_disp) == _norm(correct_zh))  # 中文比對
            chosen_label = chosen_disp
        else:
            is_correct = (_norm(chosen_disp) == _norm(correct_en))  # 英文比對
            chosen_label = chosen_disp

    if not st.session_state.submitted:
        st.session_state.submitted = True
        st.session_state.records.append((
            st.session_state.round,
            q["cloze_en"] if mode != MODE_3 else q.get("sent_zh", ""),
            chosen_label,
            correct_en,
            is_correct,
            [], []
        ))
        # ✅ 立刻寫入一筆到 Google Sheet
        persist_one(qidx, q, chosen_label, is_correct, phase="Normal")

        if is_correct:
            st.session_state.last_feedback = "<div class='feedback-small feedback-correct'>✅ 回答正確</div>"
            st.session_state.score_this_round += 1
        else:
            st.session_state.last_feedback = f"<div class='feedback-small feedback-wrong'>❌ Incorrect. 正確答案：{correct_en}</div>"
        st.rerun()
    else:
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

    if st.session_state.submitted and st.session_state.last_feedback:
        st.markdown(st.session_state.last_feedback, unsafe_allow_html=True)

    action_label = "下一題" if st.session_state.submitted else "送出答案"
    if st.button(action_label, key="action_btn"):
        handle_action(qidx, q, user_input)

    if st.session_state.submitted and st.session_state.records:
        last = st.session_state.records[-1]
        _, _, _, correct_en, _, opts_disp, _ = last
        en2zh = { it["answer_en"].strip(): (it.get("meaning_zh") or "").strip() for it in QUESTION_BANK }
        correct_zh = en2zh.get(correct_en, "")
        st.markdown("---")
        st.markdown(f"**正確答案：{correct_en}**　({correct_zh})")
        if st.session_state.mode == MODE_2 and opts_disp:
            st.markdown("**本題所有選項：**  ")
            st.markdown("、".join([str(zh).strip() for zh in opts_disp if str(zh).strip()]))
        if st.session_state.mode == MODE_3 and opts_disp:
            pairs = []
            for en in opts_disp:
                en_s = str(en).strip()
                if not en_s: continue
                zh_s = en2zh.get(en_s, "")
                pairs.append(f"{en_s}：{zh_s if zh_s else '(無中文)'}")
            if pairs:
                st.markdown("**本題所有選項：**  ")
                st.markdown("、".join(pairs))

else:
    total_answered = len(st.session_state.records)
    total_correct = sum(1 for rec in st.session_state.records if rec[4])
    st.subheader("📊 總結")
    st.markdown(f"<h3>Total Answered: {total_answered}</h3>", unsafe_allow_html=True)
    st.markdown(f"<h3>Total Correct: {total_correct}</h3>", unsafe_allow_html=True)
    acc = (total_correct / total_answered * 100) if total_answered else 0.0
    st.markdown(f"<h3>Accuracy: {acc:.1f}%</h3>", unsafe_allow_html=True)
    st.button("🔄 再玩一次", on_click=lambda: (init_state(), start_new_round()))
