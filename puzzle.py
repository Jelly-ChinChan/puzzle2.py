# streamlit_app.py —— 內建題庫 + 模式2/3選項配對顯示（Bugfix 版）
import streamlit as st
import random

st.set_page_config(page_title="Cloze Test Practice (3 modes, rounds)", page_icon="📝", layout="centered")

# ===================== 內建題庫（由 Excel 轉為常數） =====================
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

# ===================== 樣式 & 常數 =====================
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

# ===================== 工具：字形比對（新增） =====================
def _norm(s: str) -> str:
    return (s or "").strip().lower()

def _variants(correct: str):
    c = _norm(correct)
    vs = {c}
    # 複數/三單
    vs.add(c + "s")
    vs.add(c + "es")
    if c.endswith("y"):
        vs.add(c[:-1] + "ies")
    # 過去式
    vs.add(c + "ed")
    if c.endswith("y"):
        vs.add(c[:-1] + "ied")
    # 動名詞
    if c.endswith("e") and not c.endswith("ee"):
        vs.add(c[:-1] + "ing")
    else:
        vs.add(c + "ing")
    if c.endswith("y"):
        vs.add(c[:-1] + "ying")
    return vs

def is_free_text_correct(user_ans: str, correct_en: str) -> bool:
    u = _norm(user_ans)
    if not u:
        return False
    if u == _norm(correct_en):
        return True
    if u in _variants(correct_en):
        return True
    # 也接受「去尾 s」與「去尾 es」的回推（例如 victims → victim）
    if u.endswith("s") and u[:-1] == _norm(correct_en):
        return True
    if u.endswith("es") and (u[:-2] == _norm(correct_en) or _norm(correct_en) + "e" == u[:-1]):
        return True
    if u.endswith("ies") and _norm(correct_en).endswith("y") and u[:-3] + "y" == _norm(correct_en):
        return True
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

# ===================== 選項生成 =====================
def get_options_for_q(qidx, mode):
    key = (qidx, mode)
    if key in st.session_state.options_cache:
        return st.session_state.options_cache[key]
    item = QUESTION_BANK[qidx]
    correct_en = item["answer_en"].strip()
    correct_zh = (item.get("meaning_zh") or "").strip()

    if mode == MODE_2:  # 中文選項（直接比中文）
        pool = list({(it.get("meaning_zh") or "").strip() for it in QUESTION_BANK if (it.get("meaning_zh") or "").strip() and (it.get("meaning_zh") or "").strip() != correct_zh})
        distractors = random.sample(pool, k=min(3, len(pool)))
        display = list(dict.fromkeys([correct_zh] + distractors))
        random.shuffle(display)
        payload = {"display": display, "value": display[:]}

    elif mode == MODE_3:  # 英文選項
        pool = list({it["answer_en"].strip() for it in QUESTION_BANK if it["answer_en"].strip() and it["answer_en"].strip() != correct_en})
        distractors = random.sample(pool, k=min(3, len(pool)))
        display = list(dict.fromkeys([correct_en] + distractors))
        random.shuffle(display)
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
        opts_disp, opts_val = [], []
    else:
        chosen_disp, payload = user_input
        if chosen_disp is None:
            st.warning("請先選擇一個選項。")
            return
        options_disp = payload["display"]
        options_val  = payload["value"]

        if mode == MODE_2:
            # 直接用中文義項比對（修正多義對不到英文的 bug）
            is_correct = (_norm(chosen_disp) == _norm(correct_zh))
            chosen_label = chosen_disp  # 中文
        else:  # MODE_3
            is_correct = (_norm(chosen_disp) == _norm(correct_en))
            chosen_label = chosen_disp  # 英文
        opts_disp, opts_val = options_disp, options_val

    if not st.session_state.submitted:
        st.session_state.submitted = True
        st.session_state.records.append((
            st.session_state.round,
            q["cloze_en"] if mode != MODE_3 else q.get("sent_zh", ""),
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

    # 上方回饋（送出後）
    if st.session_state.submitted and st.session_state.last_feedback:
        st.markdown(st.session_state.last_feedback, unsafe_allow_html=True)

    # 送出／下一題
    action_label = "下一題" if st.session_state.submitted else "送出答案"
    if st.button(action_label, key="action_btn"):
        handle_action(qidx, q, user_input)

    # ===== 提交後：固定顯示「正確答案（英 + 中）」 + 選項配對 =====
    if st.session_state.submitted and st.session_state.records:
        last = st.session_state.records[-1]
        # last: (round, prompt, chosen, correct_en, is_correct, opts_disp, opts_val)
        _, _, _, correct_en, _, opts_disp, _ = last

        # 英→中 對照
        en2zh = { it["answer_en"].strip(): (it.get("meaning_zh") or "").strip() for it in QUESTION_BANK }

        correct_zh = en2zh.get(correct_en, "")
        st.markdown("---")
        st.markdown(f"**正確答案：{correct_en}**　({correct_zh})")

        # 模式2：只列出中文選項清單（避免錯誤中→英對映）
        if st.session_state.mode == MODE_2 and opts_disp:
            st.markdown("**本題所有選項：**  ")
            st.markdown("、".join([str(zh).strip() for zh in opts_disp if str(zh).strip()]))

        # 模式3：列出「英文：中文」
        if st.session_state.mode == MODE_3 and opts_disp:
            pairs = []
            for en in opts_disp:
                en_s = str(en).strip()
                if not en_s:
                    continue
                zh_s = en2zh.get(en_s, "")
                pairs.append(f"{en_s}：{zh_s if zh_s else '(無中文)'}")
            if pairs:
                st.markdown("**本題所有選項：**  ")
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
