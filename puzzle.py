# streamlit_app.py —— 3 modes + 修正判分 + 回上一頁 + Summary + 突擊模式(Q11~Q30)
import streamlit as st
import random

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
    {'answer_en': 'complication', 'cloze_en': 'The surgery went well without any c_____n.', 'sent_zh': '手術很順利，沒有任何併發症。', 'meaning_zh': '複雜；併發症'},
    {'answer_en': 'compliment', 'cloze_en': 'He received a c_____t on his new haircut.', 'sent_zh': '他的髮型獲得了稱讚。', 'meaning_zh': '稱讚'},
    {'answer_en': 'confine', 'cloze_en': 'The sick child was c_____d to bed for a week.', 'sent_zh': '生病的孩子臥床一週。', 'meaning_zh': '限制；禁閉'},
    {'answer_en': 'confined', 'cloze_en': 'Owing to his leg surgery, Mike has been c_____d to bed for a whole week.', 'sent_zh': '由於腿部手術，麥克已經臥床一整週了。', 'meaning_zh': '被限制的；受限的'},
    {'answer_en': 'construction', 'cloze_en': 'That tall building is a famous c_____n.', 'sent_zh': '那棟高樓是著名的建築。', 'meaning_zh': '建築物；建造'},
    {'answer_en': 'constructive', 'cloze_en': 'Thanks for your c_____e suggestions.', 'sent_zh': '感謝你具有建設性的建議。', 'meaning_zh': '有建設性的'},
    {'answer_en': 'consume', 'cloze_en': 'Americans c_____e a lot of energy every day.', 'sent_zh': '美國人每天消耗大量能源。', 'meaning_zh': '消耗；吃喝'},
    {'answer_en': 'consumer', 'cloze_en': 'The company listens to c_____r feedback.', 'sent_zh': '公司重視消費者回饋。', 'meaning_zh': '消費者'},
    {'answer_en': 'consumption', 'cloze_en': 'The c_____n of sugar has increased.', 'sent_zh': '糖的消耗量增加了。', 'meaning_zh': '消耗；消費'},
    {'answer_en': 'container', 'cloze_en': 'Please put the food in a c_____r.', 'sent_zh': '請把食物放進容器裡。', 'meaning_zh': '容器'},
    {'answer_en': 'convey', 'cloze_en': 'Pictures can c_____y emotions better than words.', 'sent_zh': '圖片能比文字更好地傳達情感。', 'meaning_zh': '傳達；運送'},
    {'answer_en': 'criticism', 'cloze_en': 'He faced a lot of c_____m for his decisions.', 'sent_zh': '他的決定面臨許多批評。', 'meaning_zh': '批評'},
    {'answer_en': 'criticize', 'cloze_en': 'It is easy to c_____e but hard to create.', 'sent_zh': '批評很容易，創造很難。', 'meaning_zh': '批評'},
    {'answer_en': 'cruel', 'cloze_en': 'It is c_____l to hurt animals.', 'sent_zh': '傷害動物是殘忍的。', 'meaning_zh': '殘酷的'},
    {'answer_en': 'cruelty', 'cloze_en': 'Animal c_____y is a serious issue.', 'sent_zh': '虐待動物是嚴重的問題。', 'meaning_zh': '殘忍；虐待'},
    {'answer_en': 'delight', 'cloze_en': 'The children shouted with d_____t.', 'sent_zh': '孩子們高興地大叫。', 'meaning_zh': '高興；喜悅'},
    {'answer_en': 'delightful', 'cloze_en': 'We had a d_____l evening.', 'sent_zh': '我們度過了一個愉快的夜晚。', 'meaning_zh': '令人愉快的'},
    {'answer_en': 'dependent', 'cloze_en': 'He is d_____t on his parents for money.', 'sent_zh': '他在金錢上依賴父母。', 'meaning_zh': '依賴的'},
    {'answer_en': 'dependable', 'cloze_en': 'She is a d_____e friend.', 'sent_zh': '她是個可靠的朋友。', 'meaning_zh': '可信賴的'},
    {'answer_en': 'depend', 'cloze_en': 'It d_____ds on the weather.', 'sent_zh': '這取決於天氣。', 'meaning_zh': '依賴；取決於'},
    {'answer_en': 'dependence', 'cloze_en': 'He developed a d_____e on coffee.', 'sent_zh': '他對咖啡產生依賴。', 'meaning_zh': '依賴'},
    {'answer_en': 'dependent', 'cloze_en': 'Many children are still d_____t on their parents.', 'sent_zh': '許多孩子仍依賴父母。', 'meaning_zh': '依賴的'},
    {'answer_en': 'drowsy', 'cloze_en': 'It was so hot that the students felt d_____y.', 'sent_zh': '天氣太熱，學生感到昏昏欲睡。', 'meaning_zh': '昏昏欲睡的'},
    {'answer_en': 'element', 'cloze_en': 'The key e_____t of a good story is an interesting plot.', 'sent_zh': '好故事的關鍵要素是有趣的情節。', 'meaning_zh': '元素；要素'},
    {'answer_en': 'enable', 'cloze_en': 'The Internet e_____es people to exchange information easily.', 'sent_zh': '網際網路讓人們可以輕鬆交換資訊。', 'meaning_zh': '使能夠'},
    {'answer_en': 'enemy', 'cloze_en': 'He treated me like an e_____y.', 'sent_zh': '他把我當敵人看待。', 'meaning_zh': '敵人'},
    {'answer_en': 'enormous', 'cloze_en': 'The elephant is e_____s.', 'sent_zh': '大象非常巨大。', 'meaning_zh': '巨大的'},
    {'answer_en': 'enthusiasm', 'cloze_en': 'She showed great e_____m for the project.', 'sent_zh': '她對這個計畫充滿熱情。', 'meaning_zh': '熱忱；熱情'},
    {'answer_en': 'enthusiastic', 'cloze_en': 'They were e_____c supporters.', 'sent_zh': '他們是熱情的支持者。', 'meaning_zh': '熱情的'},
    {'answer_en': 'entire', 'cloze_en': 'She read the e_____e book in one day.', 'sent_zh': '她一天讀完整本書。', 'meaning_zh': '全部的'},
    {'answer_en': 'entirely', 'cloze_en': 'I e_____ly agree with you.', 'sent_zh': '我完全同意你。', 'meaning_zh': '完全地'},
    {'answer_en': 'exploration', 'cloze_en': 'The scientist went on an e_____n.', 'sent_zh': '這位科學家進行了一次探索。', 'meaning_zh': '探索；探究'},
    {'answer_en': 'extend', 'cloze_en': 'Please e_____d your hand.', 'sent_zh': '請伸出你的手。', 'meaning_zh': '延伸；延長'},
    {'answer_en': 'extension', 'cloze_en': 'You can request an e_____n for the deadline.', 'sent_zh': '你可以申請延長截止日期。', 'meaning_zh': '延長；擴展'},
    {'answer_en': 'extent', 'cloze_en': 'To what e_____t do you agree?', 'sent_zh': '你在多大程度上同意？', 'meaning_zh': '程度；範圍'},
    {'answer_en': 'freeze', 'cloze_en': 'Water f_____es at 0°C.', 'sent_zh': '水在0度結冰。', 'meaning_zh': '結冰；凍結'},
    {'answer_en': 'freezes', 'cloze_en': 'After the surface of the lake f_____s every winter, an ice-skating contest will be held.', 'sent_zh': '湖面每年冬天結冰後，將舉辦溜冰比賽。', 'meaning_zh': '結冰；凍結'},
    {'answer_en': 'frighten', 'cloze_en': 'The ghost story f_____ed us to death.', 'sent_zh': '那個鬼故事把我們嚇壞了。', 'meaning_zh': '使害怕'},
    {'answer_en': 'frightened', 'cloze_en': 'The ghost story Jeremy told us f_____ed us to death.', 'sent_zh': '傑里米講的鬼故事把我們嚇得要死。', 'meaning_zh': '受驚嚇的'},
    {'answer_en': 'generous', 'cloze_en': 'She is g_____s to everyone.', 'sent_zh': '她對每個人都很慷慨。', 'meaning_zh': '慷慨的'},
    {'answer_en': 'humankind', 'cloze_en': 'Peace is important for all h_____d.', 'sent_zh': '和平對全人類都很重要。', 'meaning_zh': '人類'},
    {'answer_en': 'laughter', 'cloze_en': 'The room was full of l_____r.', 'sent_zh': '房間裡充滿了笑聲。', 'meaning_zh': '笑聲'},
    {'answer_en': 'meaning', 'cloze_en': 'What is the m_____g of this word?', 'sent_zh': '這個字的意思是什麼？', 'meaning_zh': '意思；意義'},
    {'answer_en': 'mechanic', 'cloze_en': 'The m_____c fixed my car.', 'sent_zh': '那位技工修好了我的車。', 'meaning_zh': '技工'},
    {'answer_en': 'medical', 'cloze_en': 'She needs m_____l care.', 'sent_zh': '她需要醫療照護。', 'meaning_zh': '醫療的'},
    {'answer_en': 'medicine', 'cloze_en': 'Take your m_____e twice a day.', 'sent_zh': '每天吃兩次藥。', 'meaning_zh': '藥；醫學'},
    {'answer_en': 'patient', 'cloze_en': 'The p_____t is waiting for the doctor.', 'sent_zh': '病人在等醫生。', 'meaning_zh': '病人；有耐心的'},
    {'answer_en': 'promise', 'cloze_en': 'Grace wins her friends’ trust by keeping every p_____e she makes.', 'sent_zh': '她透過信守每個承諾來贏得朋友的信任。', 'meaning_zh': '承諾'},
    {'answer_en': 'prompt', 'cloze_en': 'He gave a p_____t reply.', 'sent_zh': '他給了及時的回覆。', 'meaning_zh': '迅速的；提示'},
    {'answer_en': 'rely', 'cloze_en': 'You can r_____y on me.', 'sent_zh': '你可以依賴我。', 'meaning_zh': '依賴'},
    {'answer_en': 'route', 'cloze_en': 'This is the best r_____e to the museum.', 'sent_zh': '這是去博物館的最佳路線。', 'meaning_zh': '路線'},
    {'answer_en': 'slight', 'cloze_en': 'There is a s_____t chance of rain today.', 'sent_zh': '今天下雨的機會很小。', 'meaning_zh': '輕微的'},
    {'answer_en': 'slightly', 'cloze_en': 'The driver was only s_____y injured.', 'sent_zh': '駕駛只有輕傷。', 'meaning_zh': '稍微地'},
    {'answer_en': 'stability', 'cloze_en': 'Many years of hot sun affected the s_____y of the house.', 'sent_zh': '多年炎熱與暴風雨影響了房子的穩定性。', 'meaning_zh': '穩定性'},
    {'answer_en': 'terminal', 'cloze_en': 'The patient has t_____l lung cancer.', 'sent_zh': '病人罹患末期肺癌。', 'meaning_zh': '末期的；終端的'},
    {'answer_en': 'torture', 'cloze_en': 'Some prisoners were t_____d to death.', 'sent_zh': '有些囚犯被折磨致死。', 'meaning_zh': '拷打；折磨'},
    {'answer_en': 'tortured', 'cloze_en': 'Some of the prisoners were either beaten or t_____d to death.', 'sent_zh': '有些囚犯被毒打，或被折磨致死。', 'meaning_zh': '受折磨的'},
    {'answer_en': 'upright', 'cloze_en': 'Return your seats to the u_____t position.', 'sent_zh': '把座椅調回直立位置。', 'meaning_zh': '直立的'},
    {'answer_en': 'victim', 'cloze_en': 'The number of v_____s in plane crashes has increased.', 'sent_zh': '飛機失事的受害者人數增加。', 'meaning_zh': '受害者'},
    {'answer_en': 'warmth', 'cloze_en': 'Kind words create w_____h in people’s hearts.', 'sent_zh': '善意的話語帶來溫暖。', 'meaning_zh': '溫暖'},
]

# ===================== 樣式 =====================
def base_css():
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

def hard_css():
    st.markdown("""
    <style>
    body { background:#0e0f13 !important; }
    .block-container { color:#e7e9ee !important; }
    h2 { color:#e7e9ee !important; }
    .progress-card { background:#151824 !important; }
    .feedback-correct { color:#7ae582 !important; }
    .feedback-wrong { color:#ff6b6b !important; }
    .zh-blue { color:#8ab4ff !important; }
    </style>
    """, unsafe_allow_html=True)

base_css()

# ===================== 常數 =====================
QUESTIONS_PER_ROUND = 10
MODE_1 = "模式一\n-   【手寫輸入】"
MODE_2 = "模式二\n-   【中文選擇】"
MODE_3 = "模式三\n-   【英文選擇】"

# ===================== 判分工具：詞形彈性 =====================
def _norm(s: str) -> str:
    return (s or "").strip().lower()

def _variants(correct: str):
    c = _norm(correct)
    vs = {c, c+"s", c+"es"}
    if c.endswith("y"):
        vs.add(c[:-1]+"ies")
    # 過去式
    vs.add(c+"ed")
    if c.endswith("y"):
        vs.add(c[:-1]+"ied")
    # 動名詞
    if c.endswith("e") and not c.endswith("ee"):
        vs.add(c[:-1]+"ing")
    else:
        vs.add(c+"ing")
    if c.endswith("y"):
        vs.add(c[:-1]+"ying")
    return vs

def is_free_text_correct(user_ans: str, correct_en: str) -> bool:
    u = _norm(user_ans)
    if not u:
        return False
    c = _norm(correct_en)
    if u == c or u in _variants(c):
        return True
    if u.endswith("s") and u[:-1] == c:
        return True
    if u.endswith("es") and (u[:-2] == c or c+"e" == u[:-1]):
        return True
    if u.endswith("ies") and c.endswith("y") and u[:-3]+"y" == c:
        return True
    return False

# ===================== 狀態 =====================
def init_state():
    st.session_state.mode = MODE_1
    st.session_state.round_active = True
    st.session_state.used_answers = set()         # 已答對後加入，避重
    st.session_state.cur_round_qidx = []          # 本回合 10 題的索引
    st.session_state.cur_ptr = 0                  # 目前題目的指標（0~9）
    st.session_state.browse_idx = None            # 瀏覽上一題用（不影響 cur_ptr）
    st.session_state.records = []                 # (idx_label, prompt, chosen, correct_en, is_correct, mode)
    st.session_state.submitted = False
    st.session_state.last_feedback = ""
    st.session_state.options_cache = {}
    st.session_state.text_input_cache = ""
    # 總結 & 突擊模式
    st.session_state.summary_records = None
    st.session_state.hard_mode = False
    st.session_state.hard_qidx = []
    st.session_state.hard_ptr = 0
    st.session_state.hard_failed = False

def start_round10():
    # 從所有題中抽 10 題（避免重複答案）
    all_idx = list(range(len(QUESTION_BANK)))
    chosen = random.sample(all_idx, k=min(QUESTIONS_PER_ROUND, len(all_idx)))
    st.session_state.cur_round_qidx = chosen
    st.session_state.cur_ptr = 0
    st.session_state.browse_idx = None
    st.session_state.submitted = False
    st.session_state.last_feedback = ""
    st.session_state.options_cache = {}
    st.session_state.text_input_cache = ""
    st.session_state.records = []

if "round_active" not in st.session_state:
    init_state()
    start_round10()

# ===================== 側邊欄 =====================
with st.sidebar:
    st.markdown("### 設定")
    can_change_mode = (
        st.session_state.cur_ptr == 0 and
        not st.session_state.submitted and
        st.session_state.round_active and
        len(st.session_state.records) == 0 and
        not st.session_state.hard_mode
    )
    st.session_state.mode = st.radio("選擇練習模式", [MODE_1, MODE_2, MODE_3], index=0, disabled=not can_change_mode)
    if st.button("🔄 重新開始"):
        init_state()
        start_round10()
        st.rerun()

# ===================== 選項生成 =====================
def get_options_for_q(qidx, mode):
    key = (qidx, mode)
    if key in st.session_state.options_cache:
        return st.session_state.options_cache[key]
    item = QUESTION_BANK[qidx]
    correct_en = item["answer_en"].strip()
    correct_zh = (item.get("meaning_zh") or "").strip()

    if mode == MODE_2:  # 中文選項（直接用中文比對）
        pool = list({(it.get("meaning_zh") or "").strip()
                     for it in QUESTION_BANK
                     if (it.get("meaning_zh") or "").strip() and (it.get("meaning_zh") or "").strip() != correct_zh})
        distractors = random.sample(pool, k=min(3, len(pool)))
        display = list(dict.fromkeys([correct_zh] + distractors))
        random.shuffle(display)
        payload = {"display": display, "value": display[:]}

    elif mode == MODE_3:  # 英文選項
        pool = list({it["answer_en"].strip()
                     for it in QUESTION_BANK
                     if it["answer_en"].strip() and it["answer_en"].strip() != correct_en})
        distractors = random.sample(pool, k=min(3, len(pool)))
        display = list(dict.fromkeys([correct_en] + distractors))
        random.shuffle(display)
        payload = {"display": display, "value": display[:]}

    else:
        payload = {"display": [], "value": []}

    st.session_state.options_cache[key] = payload
    return payload

# ===================== UI 元件 =====================
def render_top_card(title_round, i, n):
    percent = int(i / n * 100) if n else 0
    st.markdown(
        f"""
        <div class="progress-card" style='background-color:#f5f5f5; padding:9px 14px; border-radius:12px;'>
            <div style='display:flex; align-items:center; justify-content:space-between; margin-bottom:4px;'>
                <div style='font-size:18px;'>🎯 {title_round}｜進度：{i} / {n}</div>
                <div style='font-size:16px; color:#555;'>{percent}%</div>
            </div>
            <progress value='{i}' max='{n if n else 1}' style='width:100%; height:14px;'></progress>
        </div>
        """,
        unsafe_allow_html=True
    )

def render_question_by_index(global_idx, label_no):
    """根據 global_idx 渲染題目；label_no 用於顯示 Q 編號（例如 1~10 或 11~30）"""
    q = QUESTION_BANK[global_idx]
    mode = st.session_state.mode

    if mode == MODE_3:
        prompt = q.get("sent_zh", "").strip()
        st.markdown(f"<h2>Q{label_no}. {prompt if prompt else '（此題缺少中文題幹）'}</h2>", unsafe_allow_html=True)
    else:
        st.markdown(f"<h2>Q{label_no}. {q['cloze_en']}</h2>", unsafe_allow_html=True)
        if mode == MODE_1 and q.get("sent_zh"):
            st.markdown(f"<div class='zh-blue'>📘 {q['sent_zh']}</div>", unsafe_allow_html=True)

    # 瀏覽模式下禁用作答
    browsing = st.session_state.browse_idx is not None
    disabled = browsing

    if mode == MODE_1:
        user_text = st.text_input("請輸入英文答案：",
                                  key=f"ti_{global_idx}_{label_no}",
                                  value=st.session_state.text_input_cache,
                                  disabled=disabled)
        return q, ("TEXT", user_text)
    else:
        payload = get_options_for_q(global_idx, mode)
        options_disp = payload["display"]
        if not options_disp:
            st.info("No options to select.")
            choice = None
        else:
            choice = st.radio("", options_disp, key=f"mc_{global_idx}_{label_no}",
                              label_visibility="collapsed", disabled=disabled)
        return q, ("MC", (choice, payload))

def record_and_feedback(idx_label, q, chosen_label, is_correct):
    st.session_state.records.append((
        idx_label,                                 # 題次顯示（Q1/Q11）
        q["cloze_en"] if st.session_state.mode != MODE_3 else q.get("sent_zh", ""),
        chosen_label,
        q["answer_en"].strip(),
        is_correct,
        st.session_state.mode
    ))
    if is_correct:
        st.session_state.last_feedback = "<div class='feedback-small feedback-correct'>✅ 回答正確</div>"
    else:
        st.session_state.last_feedback = f"<div class='feedback-small feedback-wrong'>❌ Incorrect. 正確答案：{q['answer_en'].strip()}</div>"

# ===================== 主流程：一般 10 題 =====================
def normal_mode_page():
    cur_ptr = st.session_state.cur_ptr
    browse_idx = st.session_state.browse_idx
    show_idx = st.session_state.cur_round_qidx[browse_idx if browse_idx is not None else cur_ptr]
    label_no = (browse_idx if browse_idx is not None else cur_ptr) + 1

    render_top_card("第 1 回合", cur_ptr + 1, len(st.session_state.cur_round_qidx))
    q, uinput = render_question_by_index(show_idx, label_no)

    # 回饋
    if st.session_state.submitted and st.session_state.last_feedback and (browse_idx is None):
        st.markdown(st.session_state.last_feedback, unsafe_allow_html=True)

    # 兩顆按鈕：回上一頁 / 送出or下一題
    left, right = st.columns([1, 2])
    with left:
        if st.button("⬅️ 回上一題", use_container_width=True):
            # 僅切到瀏覽模式，不影響目前 pointer；若已在第一題則不動
            if cur_ptr > 0:
                st.session_state.browse_idx = cur_ptr - 1
            st.rerun()

    with right:
        action_label = "下一題" if st.session_state.submitted or (st.session_state.browse_idx is not None) else "送出答案"
        if st.button(action_label, use_container_width=True, key="action_btn_normal"):
            # 若在瀏覽狀態，回到目前題目即可
            if st.session_state.browse_idx is not None:
                st.session_state.browse_idx = None
                st.rerun()

            mode = st.session_state.mode
            correct_en = q["answer_en"].strip()
            correct_zh = (q.get("meaning_zh") or "").strip()

            if not st.session_state.submitted:
                # 第一次按 -> 判分
                if uinput[0] == "TEXT":
                    ans = (uinput[1] or "").strip()
                    is_correct = is_free_text_correct(ans, correct_en)
                    record_and_feedback(label_no, q, ans, is_correct)
                else:
                    chosen_disp, payload = uinput[1]
                    if chosen_disp is None:
                        st.warning("請先選擇一個選項。")
                        st.stop()
                    if mode == MODE_2:
                        is_correct = (_norm(chosen_disp) == _norm(correct_zh))
                        record_and_feedback(label_no, q, chosen_disp, is_correct)
                    else:  # MODE_3
                        is_correct = (_norm(chosen_disp) == _norm(correct_en))
                        record_and_feedback(label_no, q, chosen_disp, is_correct)

                st.session_state.submitted = True
                if st.session_state.records[-1][4]:  # 最新這題若正確
                    st.session_state.used_answers.add(correct_en)
                st.rerun()

            else:
                # 第二次按 -> 進入下一題/或結束
                st.session_state.submitted = False
                st.session_state.last_feedback = ""
                st.session_state.text_input_cache = ""
                st.session_state.cur_ptr += 1

                if st.session_state.cur_ptr >= len(st.session_state.cur_round_qidx):
                    # 回合結束，進 Summary
                    st.session_state.round_active = False
                    st.session_state.summary_records = st.session_state.records[:]
                st.rerun()

    # 題後對照（只在非瀏覽 & 已提交）
    if (st.session_state.browse_idx is None) and st.session_state.submitted and len(st.session_state.records) > 0:
        en2zh = {it["answer_en"].strip(): (it.get("meaning_zh") or "").strip() for it in QUESTION_BANK}
        correct_en = q["answer_en"].strip()
        correct_zh = en2zh.get(correct_en, "")
        st.markdown("---")
        st.markdown(f"**正確答案：{correct_en}**　({correct_zh})")

# ===================== Summary（10 題後） =====================
def summary_page():
    recs = st.session_state.summary_records or []
    total = len(recs)
    correct = sum(1 for r in recs if r[4])
    acc = (correct / total * 100) if total else 0.0

    st.subheader("📊 總結")
    st.markdown(f"**Total Answered:** {total}")
    st.markdown(f"**Total Correct:** {correct}")
    st.markdown(f"**Accuracy:** {acc:.1f}%")

    # 錯題總覽
    wrongs = [r for r in recs if not r[4]]
    st.markdown("---")
    st.markdown("### ❌ 錯題總覽")
    if not wrongs:
        st.info("本回合無錯題！")
    else:
        for idx_label, prompt, chosen, correct_en, is_correct, _ in wrongs:
            en2zh = {it["answer_en"].strip(): (it.get("meaning_zh") or "").strip() for it in QUESTION_BANK}
            st.markdown(f"- **Q{idx_label}**：{prompt}")
            st.markdown(f"　你的答案：`{chosen}`")
            st.markdown(f"　正確答案：`{correct_en}`（{en2zh.get(correct_en, '')}）")

    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🔁 再玩一次", use_container_width=True):
            init_state()
            start_round10()
            st.rerun()
    with c2:
        # 全對才出現
        if correct == total and total == QUESTIONS_PER_ROUND:
            if st.button("⚡ 你渴望力量嗎", use_container_width=True):
                # 進入突擊模式：抽 20 題，不含前 10 題的答案
                used = set([QUESTION_BANK[i]["answer_en"] for i in st.session_state.cur_round_qidx])
                remain = [i for i, it in enumerate(QUESTION_BANK) if it["answer_en"] not in used]
                pick_n = min(20, len(remain))
                st.session_state.hard_qidx = random.sample(remain, k=pick_n)
                st.session_state.hard_ptr = 0
                st.session_state.hard_failed = False
                st.session_state.hard_mode = True
                st.session_state.browse_idx = None
                st.session_state.submitted = False
                st.session_state.last_feedback = ""
                hard_css()
                st.rerun()

# ===================== 突擊模式（Q11~Q30，答錯即結束） =====================
def hard_mode_page():
    hard_css()
    total = len(st.session_state.hard_qidx)
    # 若已失敗或已全部答完
    if st.session_state.hard_failed or st.session_state.hard_ptr >= total:
        st.subheader("⚡ 突擊模式結算")
        got = st.session_state.hard_ptr if not st.session_state.hard_failed else st.session_state.hard_ptr
        st.markdown(f"**你通過了：{got} / {total} 題**")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🔁 回到一般模式再來", use_container_width=True):
                init_state()
                start_round10()
                st.rerun()
        with c2:
            if st.button("🏁 結束", use_container_width=True):
                st.stop()
        st.stop()

    cur = st.session_state.hard_ptr
    show_idx = st.session_state.hard_qidx[st.session_state.browse_idx if st.session_state.browse_idx is not None else cur]
    # 顯示編號：Q11 起
    label_no = 11 + (st.session_state.browse_idx if st.session_state.browse_idx is not None else cur)

    render_top_card("⚡ 突擊模式", cur + 1, total)
    q, uinput = render_question_by_index(show_idx, label_no)

    # 回饋（只在非瀏覽 & 已提交）
    if st.session_state.submitted and st.session_state.last_feedback and (st.session_state.browse_idx is None):
        st.markdown(st.session_state.last_feedback, unsafe_allow_html=True)

    left, right = st.columns([1, 2])
    with left:
        if st.button("⬅️ 回上一題", use_container_width=True, key="hard_back"):
            if cur > 0:
                st.session_state.browse_idx = cur - 1
            st.rerun()

    with right:
        action_label = "下一題" if st.session_state.submitted or (st.session_state.browse_idx is not None) else "送出答案"
        if st.button(action_label, use_container_width=True, key="action_btn_hard"):
            if st.session_state.browse_idx is not None:
                st.session_state.browse_idx = None
                st.rerun()

            correct_en = q["answer_en"].strip()
            correct_zh = (q.get("meaning_zh") or "").strip()
            mode = st.session_state.mode

            if not st.session_state.submitted:
                if uinput[0] == "TEXT":
                    ans = (uinput[1] or "").strip()
                    is_correct = is_free_text_correct(ans, correct_en)
                    record_and_feedback(label_no, q, ans, is_correct)
                else:
                    chosen_disp, payload = uinput[1]
                    if chosen_disp is None:
                        st.warning("請先選擇一個選項。")
                        st.stop()
                    if mode == MODE_2:
                        is_correct = (_norm(chosen_disp) == _norm(correct_zh))
                        record_and_feedback(label_no, q, chosen_disp, is_correct)
                    else:
                        is_correct = (_norm(chosen_disp) == _norm(correct_en))
                        record_and_feedback(label_no, q, chosen_disp, is_correct)

                st.session_state.submitted = True
                if st.session_state.records[-1][4]:
                    st.session_state.used_answers.add(correct_en)
                else:
                    # 突擊模式錯一次就結束
                    st.session_state.hard_failed = True
                st.rerun()
            else:
                # 下一題（僅在未失敗時）
                st.session_state.submitted = False
                st.session_state.last_feedback = ""
                st.session_state.text_input_cache = ""
                if not st.session_state.hard_failed:
                    st.session_state.hard_ptr += 1
                st.rerun()

    # 題後對照（只在非瀏覽 & 已提交）
    if (st.session_state.browse_idx is None) and st.session_state.submitted:
        en2zh = {it["answer_en"].strip(): (it.get("meaning_zh") or "").strip() for it in QUESTION_BANK}
        correct_en = q["answer_en"].strip()
        correct_zh = en2zh.get(correct_en, "")
        st.markdown("---")
        st.markdown(f"**正確答案：{correct_en}**　({correct_zh})")

# ===================== 路由 =====================
if st.session_state.round_active:
    normal_mode_page()
else:
    # 顯示 Summary（含「你渴望力量嗎」）
    if not st.session_state.hard_mode:
        summary_page()
    else:
        hard_mode_page()
