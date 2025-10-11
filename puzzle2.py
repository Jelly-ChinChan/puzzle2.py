# streamlit_app.py — 3 modes + Summary + 力量模式 + 終極力量回合 + 作答蒐集/儀表板
# 變更摘要：
# 1) 題庫改為 11 題「簡易理化」問題。
# 2) 新增「作答者資訊」欄位（姓名/班級/座號）。
# 3) 以兩種方式寫出作答紀錄：
#    - A. 若設定 Google Sheet（建議）：自動 Append 到試算表（雲端長期保存，可分享連結）
#    - B. 若未設定 Google Sheet：落地到本機 responses.csv，並提供內建儀表板（?view=dashboard）查看。
# 4) 新增「儀表板」頁（?view=dashboard）可即時查看彙整資料（Google Sheet 或本機 CSV）。
# 5) 維持原有 3 模式、Summary、力量模式與終極力量回合，但將本回合題數改為 11。

import os
import csv
import uuid
import random
import datetime as dt
from urllib.parse import urlencode

import streamlit as st

# ===============（可選）Google Sheet 連線設定=================
# 若要寫入 Google 試算表：
# 1) 建立一個 Google Cloud 專案與 Service Account，下載 JSON 憑證
# 2) 在你的 Streamlit Cloud 專案的「Secrets」加入：
#    [gsheets]
#    spreadsheet_id = "你的Sheet ID"  # URL 中 /d/ 後面那段
#    service_account_json = "{""type"":""service_account"",...}"  # 直接貼上整個 JSON 內容（用雙引號跳脫）
# 3) 到該試算表，將共享權限加入 Service Account 的 email（可編輯）
# 4) 需要相依套件：gspread、google-auth

_GS_OK = False
_gs_client = None
_gs_worksheet = None

try:
    from google.oauth2.service_account import Credentials  # type: ignore
    import gspread  # type: ignore
    def _try_init_gsheet():
        global _GS_OK, _gs_client, _gs_worksheet
        conf = st.secrets.get("gsheets", {}) if hasattr(st, "secrets") else {}
        sid = conf.get("spreadsheet_id")
        saj = conf.get("service_account_json")
        if not sid or not saj:
            _GS_OK = False
            return
        creds = Credentials.from_service_account_info(json.loads(saj), scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ])
        _gs_client = gspread.authorize(creds)
        sh = _gs_client.open_by_key(sid)
        try:
            _gs_worksheet = sh.worksheet("responses")
        except Exception:
            _gs_worksheet = sh.add_worksheet(title="responses", rows=1000, cols=30)
            _gs_worksheet.append_row([
                "timestamp", "session_id", "name", "class", "seat",
                "phase", "mode", "q_label", "q_id", "prompt",
                "answer_en", "user_answer", "is_correct"
            ])
        _GS_OK = True
    _try_init_gsheet()
except Exception:
    _GS_OK = False

# ===================== 共用設定 =====================
st.set_page_config(page_title="Cloze Test (3 modes) + Logging", page_icon="📝", layout="centered")

# 儀表板切換（同一 URL 加上 ?view=dashboard）
params = st.experimental_get_query_params() if hasattr(st, "experimental_get_query_params") else {}
VIEW_DASHBOARD = (params.get("view", [""])[0].lower() == "dashboard")

# ===================== 題庫（11 題簡易理化） =====================
# 欄位定義：answer_en（標準答案，英文字或符號）、cloze_en（英語題幹/填空）、sent_zh（中文提示/題幹）、meaning_zh（中文釋義/答案說明）
QUESTION_BANK = [
    {"answer_en": "gravity", "cloze_en": "The force that pulls objects toward Earth is called g_____y.", "sent_zh": "把物體往地球拉的力叫做什麼？", "meaning_zh": "重力"},
    {"answer_en": "evaporation", "cloze_en": "Water turns into vapor through e__________n.", "sent_zh": "水變成水蒸氣的過程叫？", "meaning_zh": "蒸發"},
    {"answer_en": "freezing", "cloze_en": "Water f_______g at 0°C.", "sent_zh": "水在 0°C 會發生什麼相變？", "meaning_zh": "凝固/結冰"},
    {"answer_en": "density", "cloze_en": "Mass divided by volume is d_____y.", "sent_zh": "質量除以體積稱為？", "meaning_zh": "密度"},
    {"answer_en": "voltage", "cloze_en": "The electrical potential difference is called v_____e.", "sent_zh": "電位差又稱？", "meaning_zh": "電壓"},
    {"answer_en": "current", "cloze_en": "The rate of flow of charge is c_____t.", "sent_zh": "單位時間內通過導體截面的電荷量稱為？", "meaning_zh": "電流"},
    {"answer_en": "resistance", "cloze_en": "Opposition to current flow is r________e.", "sent_zh": "阻礙電流通過的性質稱？", "meaning_zh": "電阻"},
    {"answer_en": "acid", "cloze_en": "A substance with pH less than 7 is an a____d.", "sent_zh": "pH 小於 7 的物質稱為？", "meaning_zh": "酸"},
    {"answer_en": "base", "cloze_en": "A substance with pH greater than 7 is a b___e.", "sent_zh": "pH 大於 7 的物質稱為？", "meaning_zh": "鹼/鹼性物質"},
    {"answer_en": "neutralization", "cloze_en": "Acid reacts with base to form salt and water. This is n____________n.", "sent_zh": "酸和鹼反應生成鹽與水的反應叫？", "meaning_zh": "中和"},
    {"answer_en": "photosynthesis", "cloze_en": "Plants make food using light in p____________s.", "sent_zh": "植物利用光能製造養分的作用？", "meaning_zh": "光合作用"},
]

# 題目數：本回合 11 題
QUESTIONS_PER_ROUND = 11

# ===================== 外觀（保留前版風格重點） =====================
BASE_CSS = """
<style>
  html, body, [class*="css"] { font-size: 22px !important; }
  .block-container { padding-top: .28rem !important; padding-bottom: .6rem !important; max-width: 1000px; }
  h2 { font-size: 26px !important; margin-top: .10rem !important; margin-bottom: .40rem !important; }
  .progress-card-normal { margin: 0 0 .30rem 0 !important; }
  .progress-card-normal progress { width:100%; height:8px; -webkit-appearance:none; appearance:none; }
  .progress-card-normal progress::-webkit-progress-bar { background:#e9e9ee; border-radius:6px; }
  .progress-card-normal progress::-webkit-progress-value { background:#5a67d8; border-radius:6px; box-shadow:none; }
  .stRadio [role="radiogroup"] > label:hover { filter: drop-shadow(0 0 4px rgba(90,103,216,.25)); }
  .stRadio input[type="radio"]:checked { accent-color: #5a67d8; }
  @media (max-width: 480px){ .block-container { padding-top: .26rem !important; } h2 { margin-top: .06rem !important; margin-bottom: .34rem !important; } }
</style>
"""

NEON_BLACK_CSS = """
<style>
  :root { --bg:#000; --txt:#ffffff; --pink:#ff3d81; }
  html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"], [data-testid="stSidebar"] { background-color:#000 !important; color:var(--txt) !important; }
  section.main, .block-container { background:transparent !important; color:var(--txt) !important; padding-top: 1.45rem !important; }
  .progress-card-power { margin: .10rem 0 .10rem 0 !important; }
  .progress-card-power progress { width:100%; height:14px; -webkit-appearance:none; appearance:none; }
  .progress-card-power progress::-webkit-progress-bar { background:#0f0f0f; border-radius:10px; }
  .progress-card-power progress::-webkit-progress-value { background: linear-gradient(90deg, #ff3468, #ff7a90); border-radius:10px; box-shadow:0 0 14px rgba(255,52,104,.85), 0 0 30px rgba(255,52,104,.45); }
  h2 { color:#fff !important; margin-top:.06rem !important; margin-bottom:.28rem !important; }
  .stButton>button{ background:#060606; color:#fff; border:1px solid rgba(255,255,255,.15); border-radius:12px; }
  .stButton>button:hover{ box-shadow:0 0 12px rgba(255,61,129,.45), inset 0 0 6px rgba(255,255,255,.15); }
  .stRadio [role="radiogroup"] > label{ color:#fff !important; border-radius:12px; padding:6px 8px; transition: filter .12s ease, box-shadow .12s ease; }
  .stRadio [role="radiogroup"] label, .stRadio [role="radiogroup"] label * { color:#fff !important; opacity:1 !important; }
  .stRadio [role="radiogroup"] > label:hover{ filter: drop-shadow(0 0 10px rgba(255,61,129,.6)); box-shadow: 0 0 8px rgba(255,61,129,.35) inset, 0 0 8px rgba(255,61,129,.35); }
  .stRadio [role="radiogroup"] > label:has(input[type="radio"]:checked){ filter: drop-shadow(0 0 12px rgba(255,61,129,.85)); box-shadow: 0 0 10px rgba(255,61,129,.45) inset, 0 0 10px rgba(255,61,129,.45); }
  .stRadio input[type="radio"]:checked { accent-color:#ff3d81; }
  .explain { background:#0b0b0b; border:1px solid rgba(255,255,255,.12); border-radius:12px; padding:10px 14px; }
  .badge { display:inline-block; padding:2px 10px; border-radius:999px; font-weight:700; font-size:16px; margin-right:6px; }
  .ok{ background:#103a22; color:#7ae582; border:1px solid #255f3d; }
  .bad{ background:#2a0b0b; color:#ff6b6b; border:1px solid #7a2d2d; }
  .gameover { font-size:48px; font-weight:900; letter-spacing:.12em; color:#ff3d81; text-align:center; margin:18px 0 8px; text-shadow:0 0 10px rgba(255,61,129,.85), 0 0 22px rgba(255,255,255,.25); }
  .devil { font-size:64px; text-align:center; filter: drop-shadow(0 0 14px rgba(255,61,129,.75)); }
  @media (max-width: 480px){ .block-container { padding-top: 1.42rem !important; } .progress-card-power { margin: .10rem 0 .10rem 0 !important; } h2 { margin-top:.04rem !important; margin-bottom:.26rem !important; } }
</style>
"""

st.markdown(BASE_CSS, unsafe_allow_html=True)

# ===================== 模式名稱 =====================
MODE_1 = "模式一\n-   【手寫輸入】"
MODE_2 = "模式二\n-   【中文選擇】"
MODE_3 = "模式三\n-   【英文選擇】"

# ===================== 判分（彈性） =====================

def _norm(s: str) -> str:
    return (s or "").strip().lower()


def _variants(correct: str):
    c = _norm(correct)
    vs = {c, c + "s", c + "es"}
    if c.endswith("y"):
        vs.add(c[:-1] + "ies")
    vs.add(c + "ed")
    if c.endswith("y"):
        vs.add(c[:-1] + "ied")
    if c.endswith("e") and not c.endswith("ee"):
        vs.add(c[:-1] + "ing")
    else:
        vs.add(c + "ing")
    if c.endswith("y"):
        vs.add(c[:-1] + "ying")
    return vs


def is_free_text_correct(user_ans: str, correct_en: str) -> bool:
    u = _norm(user_ans)
    c = _norm(correct_en)
    if not u:
        return False
    if u == c or u in _variants(c):
        return True
    if u.endswith("s") and u[:-1] == c:
        return True
    if u.endswith("es") and (u[:-2] == c or c + "e" == u[:-1]):
        return True
    if u.endswith("ies") and c.endswith("y") and u[:-3] + "y" == c:
        return True
    return False

# ===================== 狀態 =====================

def init_state():
    # 作答者資訊
    st.session_state.user_name = ""
    st.session_state.user_class = ""
    st.session_state.user_seat = ""

    st.session_state.session_id = str(uuid.uuid4())

    # 回合/題目
    st.session_state.mode = MODE_1
    st.session_state.round_active = True
    st.session_state.cur_round_qidx = []
    st.session_state.cur_ptr = 0
    st.session_state.records = []  # 暫存（本回合）
    st.session_state.submitted = False
    st.session_state.options_cache = {}
    st.session_state.text_input_cache = ""

    # 力量模式
    st.session_state.summary_records = None
    st.session_state.power_mode = False
    st.session_state.power_qidx = []
    st.session_state.power_ptr = 0
    st.session_state.power_failed = False

    # 終極力量回合
    st.session_state.ultimate_mode = False
    st.session_state.ultimate_qidx = []
    st.session_state.ultimate_ptr = 0
    st.session_state.ultimate_failed = False

    # 結束頁
    st.session_state.ended = False


def start_round():
    all_idx = list(range(len(QUESTION_BANK)))
    chosen = random.sample(all_idx, k=min(QUESTIONS_PER_ROUND, len(all_idx)))
    st.session_state.cur_round_qidx = chosen
    st.session_state.cur_ptr = 0
    st.session_state.submitted = False
    st.session_state.options_cache = {}
    st.session_state.text_input_cache = ""
    st.session_state.records = []


if "session_id" not in st.session_state:
    init_state()
    start_round()

# ===================== 寫出紀錄 =====================

CSV_PATH = "responses.csv"  # 本機 CSV 路徑


def _now_ts():
    return dt.datetime.now().isoformat(timespec="seconds")


def append_to_local_csv(rows):
    exists = os.path.exists(CSV_PATH)
    with open(CSV_PATH, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if not exists:
            w.writerow([
                "timestamp", "session_id", "name", "class", "seat",
                "phase", "mode", "q_label", "q_id", "prompt",
                "answer_en", "user_answer", "is_correct",
            ])
        for r in rows:
            w.writerow(r)


def append_to_gsheet(rows):
    if not _GS_OK:
        return False, "GS not configured"
    try:
        _gs_worksheet.append_rows(rows, value_input_option="RAW")
        return True, "OK"
    except Exception as e:
        return False, str(e)


def test_ping_gsheet():
    """寫入一行 PING 以測試 Google Sheet 連線。"""
    sid = st.session_state.get("session_id", str(uuid.uuid4()))
    row = [[
        _now_ts(), sid, "PING", "-", "-",
        "Test", "-", "-", "-",
        "(Connectivity test)", "-", "-", "True"
    ]]
    if _GS_OK:
        ok, msg = append_to_gsheet(row)
        return ok, msg
    else:
        return False, "GS not configured"


def persist_records(phase: str):
    """將本回合累積的 records 一次寫出。"""
    name = st.session_state.get("user_name", "")
    klass = st.session_state.get("user_class", "")
    seat = st.session_state.get("user_seat", "")
    sid = st.session_state.get("session_id", "")
    rows = []
    for rec in st.session_state.records:
        # rec = (idx_label, prompt, chosen_label, correct_en, is_correct, mode, qidx_cache)
        idx_label, prompt, chosen, correct_en, is_correct, mode, qidx = rec
        rows.append([
            _now_ts(), sid, name, klass, seat,
            phase, str(mode).replace("
", " "), idx_label, qidx,
            prompt, correct_en, chosen, str(bool(is_correct))
        ])

    ok, msg = (True, "SKIP")
    if _GS_OK:
        ok, msg = append_to_gsheet(rows)
    if not ok:
        append_to_local_csv(rows)
    return ok, msg


def persist_last_record(phase: str):
    """只把最後一筆 st.session_state.records[-1] 立即寫出（每題提交時用）。"""
    if not st.session_state.records:
        return False, "no-record"
    name = st.session_state.get("user_name", "")
    klass = st.session_state.get("user_class", "")
    seat = st.session_state.get("user_seat", "")
    sid = st.session_state.get("session_id", "")
    idx_label, prompt, chosen, correct_en, is_correct, mode, qidx = st.session_state.records[-1]
    row = [[
        _now_ts(), sid, name, klass, seat,
        phase, str(mode).replace("
", " "), idx_label, qidx,
        prompt, correct_en, chosen, str(bool(is_correct))
    ]]
    ok, msg = (True, "SKIP")
    if _GS_OK:
        ok, msg = append_to_gsheet(row)
    if not ok:
        append_to_local_csv(row)
    return ok, msg


def persist_last_record(phase: str):
    """只把最後一筆 st.session_state.records[-1] 立即寫出（每題提交時用）。"""
    if not st.session_state.records:
        return False, "no-record"
    name = st.session_state.get("user_name", "")
    klass = st.session_state.get("user_class", "")
    seat = st.session_state.get("user_seat", "")
    sid = st.session_state.get("session_id", "")
    idx_label, prompt, chosen, correct_en, is_correct, mode, qidx = st.session_state.records[-1]
    row = [[
        _now_ts(), sid, name, klass, seat,
        phase, str(mode).replace("
", " "), idx_label, qidx,
        prompt, correct_en, chosen, str(bool(is_correct))
    ]]
    ok, msg = (True, "SKIP")
    if _GS_OK:
        ok, msg = append_to_gsheet(row)
    if not ok:
        append_to_local_csv(row)
    return ok, msg

# ===================== 側欄 =====================
with st.sidebar:
    st.markdown("### 設定 / 身分")
    st.session_state.user_name = st.text_input("姓名", st.session_state.get("user_name", ""))
    st.session_state.user_class = st.text_input("班級", st.session_state.get("user_class", ""))
    st.session_state.user_seat = st.text_input("座號", st.session_state.get("user_seat", ""))

    can_change_mode = (
        st.session_state.cur_ptr == 0 and
        not st.session_state.submitted and
        st.session_state.round_active and
        len(st.session_state.records) == 0 and
        not st.session_state.power_mode and
        not st.session_state.ultimate_mode and
        not st.session_state.ended
    )
    st.session_state.mode = st.radio("選擇練習模式", [MODE_1, MODE_2, MODE_3], index=0, disabled=not can_change_mode)

    # 儀表板連結 + 測試寫入
    base_url = "?" + urlencode({"view": "dashboard"})
    st.markdown(f"[📈 查看作答情況（儀表板）]({base_url})")
    if st.button("🧪 測試寫入（Google Sheet）"):
        ok, msg = test_ping_gsheet()
        if ok:
            st.success("已測試寫入：請到 responses 工作表查看最新一列 `PING` 記錄。")
        else:
            if msg == "GS not configured":
                st.warning("尚未正確設定 Google Sheet（或未授權）。請檢查 Secrets 與試算表分享權限。")
            else:
                st.error(f"寫入失敗：{msg}")

    if st.button("🔄 重新開始"):
        init_state(); start_round(); st.experimental_rerun()

# ===================== 選項產生 =====================

def get_options_for_q(qidx, mode):
    key = (qidx, mode)
    if key in st.session_state.options_cache:
        return st.session_state.options_cache[key]
    item = QUESTION_BANK[qidx]
    correct_en = item["answer_en"].strip()
    correct_zh = (item.get("meaning_zh") or "").strip()
    if mode == MODE_2:
        pool = list({(it.get("meaning_zh") or "").strip()
                     for it in QUESTION_BANK
                     if (it.get("meaning_zh") or "").strip() and (it.get("meaning_zh") or "").strip() != correct_zh})
        distractors = random.sample(pool, k=min(3, len(pool)))
        display = list(dict.fromkeys([correct_zh] + distractors)); random.shuffle(display)
        payload = {"display": display}
    elif mode == MODE_3:
        pool = list({it["answer_en"].strip()
                     for it in QUESTION_BANK if it["answer_en"].strip() and it["answer_en"].strip() != correct_en})
        distractors = random.sample(pool, k=min(3, len(pool)))
        display = list(dict.fromkeys([correct_en] + distractors)); random.shuffle(display)
        payload = {"display": display}
    else:
        payload = {"display": []}
    st.session_state.options_cache[key] = payload
    return payload

# ===================== UI 共用 =====================

def render_progress(i, n, power=False):
    klass = "progress-card-power" if power else "progress-card-normal"
    st.markdown(f"""
        <div class="{klass}">
          <progress value='{i}' max='{n if n else 1}'></progress>
        </div>
        """, unsafe_allow_html=True)


def render_question(global_idx, label_no, power=False):
    if power:
        st.markdown(NEON_BLACK_CSS, unsafe_allow_html=True)
    q = QUESTION_BANK[global_idx]
    mode = st.session_state.mode

    # 題目
    if mode == MODE_3:
        prompt = q.get("sent_zh", "").strip()
        st.markdown(f"<h2>Q{label_no}. {prompt if prompt else '（此題缺少中文題幹）'}</h2>", unsafe_allow_html=True)
    else:
        st.markdown(f"<h2>Q{label_no}. {q['cloze_en']}</h2>", unsafe_allow_html=True)
        if mode == MODE_1 and q.get("sent_zh"):
            st.caption(q['sent_zh'])

    # 輸入/選項
    if mode == MODE_1:
        user_text = st.text_input("", key=f"ti_{global_idx}_{label_no}",
                                  value=st.session_state.text_input_cache,
                                  label_visibility="collapsed")
        return q, ("TEXT", user_text)
    else:
        payload = get_options_for_q(global_idx, mode)
        options = payload["display"]
        choice = st.radio("", options if options else [],
                          key=f"mc_{global_idx}_{label_no}",
                          label_visibility="collapsed") if options else None
        if not options:
            st.info("No options to select.")
        return q, ("MC", (choice, payload))


def record(idx_label, q, chosen_label, is_correct, qidx_cache):
    st.session_state.records.append((
        idx_label,
        q["cloze_en"] if st.session_state.mode != MODE_3 else q.get("sent_zh", ""),
        chosen_label,
        q["answer_en"].strip(),
        is_correct,
        st.session_state.mode,
        qidx_cache
    ))


def explain_block(q, mode, is_correct, payload=None):
    en = q["answer_en"].strip()
    zh = (q.get("meaning_zh") or "").strip()
    if mode == MODE_2:
        badge = "<span class='badge ok'>✅ 答對</span>" if is_correct else "<span class='badge bad'>❌ 答錯</span>"
        body = f"{zh}（{en}）"
        st.markdown(f"<div class='explain'>{badge}{body}</div>", unsafe_allow_html=True)
    elif mode == MODE_3:
        en2zh = {it['answer_en'].strip(): (it.get('meaning_zh') or '').strip() for it in QUESTION_BANK}
        opts = (payload or {}).get("display", [])
        lines = []
        for e in opts:
            e_s = str(e).strip()
            tag = " ✅" if _norm(e_s) == _norm(en) else ""
            lines.append(f"- {e_s}（{en2zh.get(e_s, '')}）{tag}")
        st.markdown(f"<div class='explain'><div class='opt-list'>{'<br/>'.join(lines)}</div></div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='explain'><span class='badge {'ok' if is_correct else 'bad'}'>{'✅ 答對' if is_correct else '❌ 答錯'}</span>{en}（{zh}）</div>", unsafe_allow_html=True)

# ===================== 一般模式頁 =====================

def normal_mode_page():
    cur_ptr = st.session_state.cur_ptr
    show_qidx = st.session_state.cur_round_qidx[cur_ptr]
    label_no = cur_ptr + 1

    render_progress(cur_ptr + 1, len(st.session_state.cur_round_qidx), power=False)
    q, uinput = render_question(show_qidx, label_no, power=False)

    if not st.session_state.submitted:
        if st.button("送出答案", key="submit_normal", use_container_width=True):
            correct_en = q["answer_en"].strip()
            correct_zh = (q.get("meaning_zh") or "").strip()
            mode = st.session_state.mode

            if uinput[0] == "TEXT":
                ans = (uinput[1] or "").strip()
                is_correct = is_free_text_correct(ans, correct_en)
                record(label_no, q, ans, is_correct, show_qidx)
            # 立即寫出單題紀錄
            persist_last_record("Normal")
        else:
            chosen_disp, _ = uinput[1]
                if chosen_disp is None:
                    st.warning("請先選擇一個選項。"); st.stop()
                is_correct = (_norm(chosen_disp) == _norm(correct_zh)) if mode == MODE_2 else (_norm(chosen_disp) == _norm(correct_en))
                record(label_no, q, chosen_disp, is_correct, show_qidx)
            # 立即寫出單題紀錄
            persist_last_record("Normal")

            st.session_state.submitted = True
            st.experimental_rerun()
    else:
        payload = uinput[1][1] if (uinput[0] == "MC") else None
        last_correct = st.session_state.records[-1][4]
        explain_block(q, st.session_state.mode, last_correct, payload)

        if st.button("下一題", key="next_normal", use_container_width=True):
            st.session_state.submitted = False
            st.session_state.text_input_cache = ""
            st.session_state.cur_ptr += 1
            if st.session_state.cur_ptr >= len(st.session_state.cur_round_qidx):
                st.session_state.round_active = False
                st.session_state.summary_records = st.session_state.records[:]
                # 回合結束，寫出作答紀錄（phase = Normal）
                ok, msg = persist_records("Normal")
                if _GS_OK and not ok:
                    st.warning(f"寫入 Google Sheet 失敗，已改存本機 CSV：{msg}")
            st.experimental_rerun()

# ===================== Summary =====================

def summary_page():
    st.session_state.submitted = False

    recs = st.session_state.summary_records or []
    total = len(recs); correct = sum(1 for r in recs if r[4])
    acc = (correct / total * 100) if total else 0.0

    st.subheader("📊 總結")
    st.markdown(f"**Total Answered:** {total}")
    st.markdown(f"**Total Correct:** {correct}")
    st.markdown(f"**Accuracy:** {acc:.1f}%")

    wrongs = [r for r in recs if not r[4]]
    st.markdown("### ❌ 錯題總覽")
    if not wrongs:
        st.info("本回合無錯題！")
    else:
        for idx_label, prompt, chosen, correct_en, _, _, _ in wrongs:
            en2zh = {it["answer_en"].strip(): (it.get("meaning_zh") or "").strip() for it in QUESTION_BANK}
            st.markdown(f"- **Q{idx_label}**：{prompt}")
            st.markdown(f"　你的答案：`{chosen}`")
            st.markdown(f"　正確答案：`{correct_en}`（{en2zh.get(correct_en, '')}）")

    c1, c2 = st.columns(2)
    with c1:
        if st.button("🔁 再玩一次", use_container_width=True):
            init_state(); start_round(); st.experimental_rerun()
    with c2:
        if correct == total and total == QUESTIONS_PER_ROUND:
            if st.button("⚡ 你渴望力量嗎", use_container_width=True):
                used_answers = {QUESTION_BANK[i]["answer_en"] for i in st.session_state.cur_round_qidx}
                remain_idx = [i for i, it in enumerate(QUESTION_BANK) if it["answer_en"] not in used_answers]
                pick_n = min(20, len(remain_idx))   # Q11~Q30 20題（本題庫 11 題，通常為 0）
                st.session_state.power_qidx = random.sample(remain_idx, k=pick_n) if pick_n > 0 else []
                st.session_state.power_ptr = 0
                st.session_state.power_failed = False
                st.session_state.power_mode = True
                st.session_state.submitted = False
                st.experimental_rerun()

# ===================== 力量模式 =====================

def power_mode_page():
    st.markdown(NEON_BLACK_CSS, unsafe_allow_html=True)
    total = len(st.session_state.power_qidx)

    # 結束/失敗
    if st.session_state.power_ptr >= total or (st.session_state.power_failed and not st.session_state.submitted):
        if st.session_state.power_failed:
            st.markdown("<div class='gameover'>GAME OVER</div>", unsafe_allow_html=True)
            st.markdown("<div class='devil'>😈</div>", unsafe_allow_html=True)
            st.caption("力量模式：答錯即止。再接再厲！")
        else:
            st.markdown("<h2 style='color:#fff;'>🎉 你征服了力量模式！</h2>", unsafe_allow_html=True)
            st.write(f"你通過了 **{total} / {total}** 題。")
        # 寫出力量模式紀錄
        if total > 0:
            ok, msg = persist_records("Power")
            if _GS_OK and not ok:
                st.warning(f"寫入 Google Sheet 失敗，已改存本機 CSV：{msg}")

        c1, c2 = st.columns(2)
        with c1:
            if st.button("🔁 回到一般模式再來", use_container_width=True):
                init_state(); start_round(); st.experimental_rerun()
        with c2:
            if st.button("💥 終極力量回合", use_container_width=True):
                used = {QUESTION_BANK[i]["answer_en"] for i in st.session_state.cur_round_qidx} \
                       | {QUESTION_BANK[i]["answer_en"] for i in st.session_state.power_qidx}
                remain_idx = [i for i, it in enumerate(QUESTION_BANK) if it["answer_en"] not in used]
                max_n = min(30, len(remain_idx))
                if max_n == 0:
                    st.session_state.ended = True
                    st.session_state.power_mode = False
                    st.experimental_rerun()
                st.session_state.ultimate_qidx = random.sample(remain_idx, k=max_n) if max_n > 0 else []
                st.session_state.ultimate_ptr = 0
                st.session_state.ultimate_failed = False
                st.session_state.ultimate_mode = True
                st.session_state.power_mode = False
                st.session_state.submitted = False
                st.experimental_rerun()
        st.stop()

    cur = st.session_state.power_ptr
    show_qidx = st.session_state.power_qidx[cur]
    label_no = 11 + cur

    render_progress(cur + 1, total, power=True)
    q, uinput = render_question(show_qidx, label_no, power=True)

    if not st.session_state.submitted:
        if st.button("送出答案", key="submit_power", use_container_width=True):
            correct_en = q["answer_en"].strip()
            correct_zh = (q.get("meaning_zh") or "").strip()
            mode = st.session_state.mode

            if uinput[0] == "TEXT":
                ans = (uinput[1] or "").strip()
                is_correct = is_free_text_correct(ans, correct_en)
            else:
                chosen_disp, _ = uinput[1]
                if chosen_disp is None:
                    st.warning("請先選擇一個選項。"); st.stop()
                is_correct = (_norm(chosen_disp) == _norm(correct_zh)) if mode == MODE_2 else (_norm(chosen_disp) == _norm(correct_en))

            st.session_state.submitted = True
            # 每題提交就寫出（力量模式）
            persist_last_record("Power")
            if not is_correct:
                st.session_state.power_failed = True
            st.experimental_rerun()
    else:
        payload = uinput[1][1] if (uinput[0] == "MC") else None
        mode = st.session_state.mode
        en = q["answer_en"].strip(); zh = (q.get("meaning_zh") or "").strip()
        if uinput[0] == "TEXT":
            was_correct = is_free_text_correct(uinput[1] or "", en)
        else:
            chosen_disp, _ = uinput[1]
            was_correct = (_norm(chosen_disp) == _norm(zh)) if mode == MODE_2 else (_norm(chosen_disp) == _norm(en))
        explain_block(q, mode, was_correct, payload)

        if st.button("下一題", key="next_power", use_container_width=True):
            st.session_state.submitted = False
            if not st.session_state.power_failed:
                st.session_state.power_ptr += 1
            st.experimental_rerun()

# ===================== 終極力量回合 =====================

def ultimate_mode_page():
    st.markdown(NEON_BLACK_CSS, unsafe_allow_html=True)
    total = len(st.session_state.ultimate_qidx)

    if st.session_state.ultimate_ptr >= total or (st.session_state.ultimate_failed and not st.session_state.submitted):
        if st.session_state.ultimate_failed:
            st.markdown("<div class='gameover'>GAME OVER</div>", unsafe_allow_html=True)
            st.markdown("<div class='devil'>😈</div>", unsafe_allow_html=True)
            st.caption("終極力量回合：答錯即止。")
        else:
            st.markdown("<h2 style='color:#fff;'>🏆 你征服了終極力量回合！</h2>", unsafe_allow_html=True)
            st.write(f"你通過了 **{total} / {total}** 題。")
        # 寫出紀錄
        if total > 0:
            ok, msg = persist_records("Ultimate")
            if _GS_OK and not ok:
                st.warning(f"寫入 Google Sheet 失敗，已改存本機 CSV：{msg}")

        c1, c2 = st.columns(2)
        with c1:
            if st.button("🔁 回到一般模式再來", use_container_width=True):
                init_state(); start_round(); st.experimental_rerun()
        with c2:
            if st.button("🏁 結束", use_container_width=True):
                st.session_state.ended = True
                st.session_state.ultimate_mode = False
                st.experimental_rerun()
        st.stop()

    cur = st.session_state.ultimate_ptr
    show_qidx = st.session_state.ultimate_qidx[cur]
    label_no = 31 + cur  # Q31 起

    render_progress(cur + 1, total, power=True)
    q, uinput = render_question(show_qidx, label_no, power=True)

    if not st.session_state.submitted:
        if st.button("送出答案", key="submit_ultimate", use_container_width=True):
            correct_en = q["answer_en"].strip()
            correct_zh = (q.get("meaning_zh") or "").strip()
            mode = st.session_state.mode

            if uinput[0] == "TEXT":
                ans = (uinput[1] or "").strip()
                is_correct = is_free_text_correct(ans, correct_en)
            else:
                chosen_disp, _ = uinput[1]
                if chosen_disp is None:
                    st.warning("請先選擇一個選項。"); st.stop()
                is_correct = (_norm(chosen_disp) == _norm(correct_zh)) if mode == MODE_2 else (_norm(chosen_disp) == _norm(correct_en))

            st.session_state.submitted = True
            # 每題提交就寫出（終極力量回合）
            persist_last_record("Ultimate")
            if not is_correct:
                st.session_state.ultimate_failed = True
            st.experimental_rerun()
    else:
        payload = uinput[1][1] if (uinput[0] == "MC") else None
        mode = st.session_state.mode
        en = q["answer_en"].strip(); zh = (q.get("meaning_zh") or "").strip()
        if uinput[0] == "TEXT":
            was_correct = is_free_text_correct(uinput[1] or "", en)
        else:
            chosen_disp, _ = uinput[1]
            was_correct = (_norm(chosen_disp) == _norm(zh)) if mode == MODE_2 else (_norm(chosen_disp) == _norm(en))
        explain_block(q, mode, was_correct, payload)

        if st.button("下一題", key="next_ultimate", use_container_width=True):
            st.session_state.submitted = False
            if not st.session_state.ultimate_failed:
                st.session_state.ultimate_ptr += 1
            st.experimental_rerun()

# ===================== 結束頁 =====================

def end_page():
    st.markdown(NEON_BLACK_CSS, unsafe_allow_html=True)
    st.markdown("""
    <div style="text-align:center; margin-top:2.2rem; color:#fff;">
      <h1 style="color:#ff3d81; text-shadow:0 0 14px rgba(255,61,129,.7);">SEE YOU AGAIN</h1>
      <p style="font-size:22px; opacity:.92;">期待你再來挑戰，否則你將永遠被困在題庫之中，哇哈哈哈哈 👹</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("🔁 回到首頁", use_container_width=True):
        init_state(); start_round(); st.experimental_rerun()

# ===================== 儀表板（查看作答情況） =====================

def dashboard_page():
    st.title("📈 作答情況儀表板")
    st.caption("若已設定 Google Sheet，資料會寫入該 Sheet 的 responses 工作表；否則讀取本機 responses.csv。")

    # 顯示連結（若為 Google Sheet）
    if _GS_OK:
        sid = st.secrets["gsheets"]["spreadsheet_id"]
        sheet_url = f"https://docs.google.com/spreadsheets/d/{sid}"
        st.markdown(f"**Google Sheet：** [{sheet_url}]({sheet_url})")

    # 讀取資料顯示（表格）
    import pandas as pd
    df = None
    if _GS_OK:
        try:
            ws = _gs_worksheet.get_all_values()
            if ws and len(ws) > 1:
                header, data = ws[0], ws[1:]
                df = pd.DataFrame(data, columns=header)
        except Exception as e:
            st.warning(f"讀取 Google Sheet 失敗：{e}")
    if df is None and os.path.exists(CSV_PATH):
        df = pd.read_csv(CSV_PATH)

    if df is None or df.empty:
        st.info("目前尚無資料。先讓同學完成一回合作答再回來看吧！")
        return

    # 簡要統計
    st.markdown("### 概覽")
    total = len(df)
    acc = (df["is_correct"].astype(str).str.lower() == "true").mean() * 100 if total else 0
    st.write(f"總作答筆數：**{total}**，整體正確率：約 **{acc:.1f}%**")

    # 篩選器
    cols = st.columns(4)
    with cols[0]:
        name_f = st.text_input("依姓名篩選")
    with cols[1]:
        class_f = st.text_input("依班級篩選")
    with cols[2]:
        mode_f = st.selectbox("模式", options=["", MODE_1, MODE_2, MODE_3])
    with cols[3]:
        phase_f = st.selectbox("回合", options=["", "Normal", "Power", "Ultimate"])

    if name_f:
        df = df[df["name"].astype(str).str.contains(name_f, case=False, na=False)]
    if class_f:
        df = df[df["class"].astype(str).str.contains(class_f, case=False, na=False)]
    if mode_f:
        df = df[df["mode"] == mode_f.replace("\n", " ")]
    if phase_f:
        df = df[df["phase"] == phase_f]

    st.dataframe(df, use_container_width=True)

    # 提供本機 CSV 下載（若存在）
    if os.path.exists(CSV_PATH):
        with open(CSV_PATH, "rb") as f:
            st.download_button("⬇️ 下載本機 CSV（備份）", data=f, file_name="responses.csv", mime="text/csv")

# ===================== 路由 =====================

if VIEW_DASHBOARD:
    dashboard_page()
else:
    if st.session_state.ended:
        end_page()
    else:
        if st.session_state.round_active:
            normal_mode_page()
        elif st.session_state.power_mode:
            power_mode_page()
        elif st.session_state.ultimate_mode:
            ultimate_mode_page()
        else:
            summary_page()
