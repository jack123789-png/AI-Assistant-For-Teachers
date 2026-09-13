import streamlit as st
import re
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from io import BytesIO
from ai import ask_ai
import figures
from docx.shared import Inches
from concurrent.futures import ThreadPoolExecutor, as_completed


# ---------------- GENERATE ONE MCQ ----------------
def generate_single_mcq(topic, difficulty, q_number):

    system_prompt = """
You are an expert educational assessment designer.
Generate high-quality multiple-choice questions.
"""

    user_prompt = f"""
Generate ONE multiple-choice question in Traditional Chinese (Taiwan).

Topic: {topic}
Difficulty: {difficulty}

Rules:
- 4 options only (a,b,c,d)
- Options must be short; question and options in Traditional Chinese
- Include correct answer
- No coding questions

Format EXACTLY:

Q{q_number}: Question text
a. Option
b. Option
c. Option
d. Option
Answer: a
"""

    return ask_ai(system_prompt, user_prompt)


# ---------------- FORMAT QUIZ ----------------
def format_quiz(quiz_text):

    lines = quiz_text.split("\n")

    formatted_quiz = []
    current_question = []

    for line in lines:

        if re.match(r"^Q\d+:", line):
            if current_question:
                formatted_quiz.append(current_question)
            current_question = [line]

        elif re.match(r"^[a-d]\.", line):
            current_question.append(line)

        elif line.startswith("Answer:"):
            current_question.append(line)

    if current_question:
        formatted_quiz.append(current_question)

    return formatted_quiz


# ---------------- BALANCED DIFFICULTY ----------------
def create_difficulty_mix(total):

    beginner = total // 3
    intermediate = total // 3
    expert = total - beginner - intermediate

    difficulties = (
        ["Beginner"] * beginner
        + ["Intermediate"] * intermediate
        + ["Expert"] * expert
    )

    return difficulties


DIFF_GUIDE = {
    "初階": "基本觀念、單一步驟，數字小（以一、二位數為主），直接套用定義或列舉",
    "中階": "兩步驟綜合，需先計算再判斷，數字中等，含完整計算過程",
    "進階": "生活情境應用，需自行判斷方法，數字稍大，可含干擾敘述",
}


def _level_text(level):
    return f"{level}（{DIFF_GUIDE.get(level, '')}）"


# ---------------- 填充題 ----------------
def generate_single_fill(topic, level, num):
    system_prompt = "You are an expert educational assessment designer."
    user_prompt = f"""
Generate ONE fill-in-the-blank question in Traditional Chinese (Taiwan).

Topic: {topic}
Level: {_level_text(level)}

Rules:
- 題目敘述後用 ___ 留空格作答
- 數字大小配合程度
- 最後一行只給答案

Format EXACTLY:

F{num}: 題目敘述 ___
答案：xxx
"""
    return ("fill", num, ask_ai(system_prompt, user_prompt))


def format_fill(quiz_text):
    lines = quiz_text.split("\n")
    out, cur = [], []
    for line in lines:
        if re.match(r"^F\d+:", line):
            if cur:
                out.append(cur)
            cur = [line]
        elif line.startswith("答案：") or line.startswith("答案:"):
            if cur:
                cur.append(line)
        elif line.strip() and cur:
            cur[-1] = cur[-1] + line.strip()
    if cur:
        out.append(cur)
    return out


# ---------------- 應用題 ----------------
def generate_single_app(topic, level, num):
    system_prompt = "You are an expert educational assessment designer."
    user_prompt = f"""
Generate ONE word problem in Traditional Chinese (Taiwan) with daily-life context.

Topic: {topic}
Level: {_level_text(level)}

Rules:
- 生活化情境，敘述清楚
- 數字大小配合程度
- 最後一段給計算過程與答案

Format EXACTLY:

P{num}: 題目敘述
解答：計算過程與答案
"""
    return ("app", num, ask_ai(system_prompt, user_prompt))


def format_app(quiz_text):
    lines = quiz_text.split("\n")
    out, cur = [], []
    for line in lines:
        if re.match(r"^P\d+:", line):
            if cur:
                out.append(cur)
            cur = [line]
        elif line.startswith("解答：") or line.startswith("解答:"):
            if cur:
                cur.append(line)
        elif line.strip() and cur:
            cur[-1] = cur[-1] + line.strip()
    if cur:
        out.append(cur)
    return out


def _choice_task(topic, level, num):
    diff_map = {"初階": "Beginner", "中階": "Intermediate", "進階": "Expert"}
    return ("choice", num,
            generate_single_mcq(f"{topic}（程度：{_level_text(level)}）",
                                diff_map.get(level, "Intermediate"), num))


# ---------------- 混合平行出題 ----------------
def generate_mixed_parallel(topic, level, n_choice, n_fill, n_app):
    tasks = []
    tasks += [("choice", i) for i in range(1, n_choice + 1)]
    tasks += [("fill", i) for i in range(1, n_fill + 1)]
    tasks += [("app", i) for i in range(1, n_app + 1)]
    results = {"choice": [], "fill": [], "app": []}
    raws = []
    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = []
        for kind, num in tasks:
            if kind == "choice":
                futures.append(executor.submit(_choice_task, topic, level, num))
            elif kind == "fill":
                futures.append(executor.submit(
                    lambda n=num: ("fill", n, generate_single_fill(topic, level, n)[2])))
            else:
                futures.append(executor.submit(
                    lambda n=num: ("app", n, generate_single_app(topic, level, n)[2])))
        for future in as_completed(futures):
            kind, num, text = future.result()
            raws.append(text)
            if kind == "choice":
                parsed = format_quiz(text)
            elif kind == "fill":
                parsed = format_fill(text)
            else:
                parsed = format_app(text)
            for q in parsed:
                results[kind].append((num, q))
    for kind in results:
        results[kind].sort(key=lambda x: x[0])
        results[kind] = [q for _, q in results[kind]]
    return results, raws


def _answer_of(question):
    for line in question:
        if line.startswith("Answer:"):
            return line.split(": ", 1)[1] if ": " in line else line[7:]
        if line.startswith("答案：") or line.startswith("答案:"):
            return line[3:]
        if line.startswith("解答：") or line.startswith("解答:"):
            return line[3:]
    return ""


# ---------------- 混合卷 DOCX ----------------
def generate_mixed_docx(sections, heading1, heading2, figs=None):
    doc = Document()
    h1 = doc.add_heading(heading1, level=0)
    h1.alignment = WD_ALIGN_PARAGRAPH.CENTER
    h2 = doc.add_heading(heading2, level=2)
    h2.alignment = WD_ALIGN_PARAGRAPH.CENTER

    doc.add_paragraph("姓名：")
    doc.add_paragraph("座號：")
    doc.add_paragraph("班級：")
    doc.add_paragraph("組別：")
    doc.add_paragraph("")

    titles = {"choice": "一、選擇題", "fill": "二、填充題", "app": "三、應用題"}
    for kind in ["choice", "fill", "app"]:
        if not sections.get(kind):
            continue
        doc.add_heading(titles[kind], level=1)
        for question in sections[kind]:
            for line in question:
                if (line.startswith("Answer:") or line.startswith("答案：")
                        or line.startswith("答案:") or line.startswith("解答：")
                        or line.startswith("解答:")):
                    continue
                doc.add_paragraph(line)
            doc.add_paragraph("")

    if figs:
        doc.add_heading("四、圖形題", level=1)
        for i, item in enumerate(figs):
            doc.add_paragraph(f"圖{i + 1}：{item['question']}")
            item["image"].seek(0)
            doc.add_picture(item["image"], width=Inches(5))
            doc.add_paragraph("")

    doc.add_page_break()
    doc.add_heading("參考答案", level=1)
    for kind in ["choice", "fill", "app"]:
        if not sections.get(kind):
            continue
        doc.add_heading(titles[kind], level=2)
        for i, question in enumerate(sections[kind]):
            doc.add_paragraph(f"第{i + 1}題：{_answer_of(question)}")
    if figs:
        doc.add_heading("四、圖形題", level=2)
        for i, item in enumerate(figs):
            doc.add_paragraph(f"圖{i + 1}：{item['answer']}")

    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer


# ---------------- PARALLEL QUIZ GENERATION ----------------
def generate_quiz_parallel(topic, difficulty, num_questions, balanced):

    results = []

    if balanced:
        difficulty_list = create_difficulty_mix(num_questions)
    else:
        difficulty_list = [difficulty] * num_questions

    with ThreadPoolExecutor(max_workers=5) as executor:

        futures = []

        for i, diff in enumerate(difficulty_list, start=1):
            futures.append(
                executor.submit(generate_single_mcq, topic, diff, i)
            )

        for future in as_completed(futures):
            results.append(future.result())

    return results


# ---------------- CREATE DOCX ----------------
def generate_docx(quiz, heading1, heading2):

    doc = Document()

    h1 = doc.add_heading(heading1, level=0)
    h1.alignment = WD_ALIGN_PARAGRAPH.CENTER

    h2 = doc.add_heading(heading2, level=2)
    h2.alignment = WD_ALIGN_PARAGRAPH.CENTER

    doc.add_paragraph("姓名：")
    doc.add_paragraph("座號：")
    doc.add_paragraph("班級：")
    doc.add_paragraph("組別：")
    doc.add_paragraph("")

    # Questions
    for question in quiz:

        for line in question:
            if not line.startswith("Answer:"):
                doc.add_paragraph(line)

        doc.add_paragraph("")

    # Answer Key
    doc.add_page_break()
    doc.add_heading("參考答案", level=1)

    for i, question in enumerate(quiz):

        for line in question:
            if line.startswith("Answer:"):
                ans = line.split(": ")[1]
                doc.add_paragraph(f"Q{i+1}: {ans}")

    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)

    return buffer


# ---------------- STREAMLIT APP ----------------
def MCQ():

    st.subheader("AI 混合卷產生器")

    col1, col2 = st.columns(2)

    with col1:
        institute_name = st.text_input("學校／補習班名稱")
        topic = st.text_input("出題範圍（例：國小五年級 公因數與公倍數）")

    with col2:
        quiz_title = st.text_input("考卷標題")
        level = st.selectbox("難度", ["初階", "中階", "進階"])

    c1, c2, c3 = st.columns(3)

    with c1:
        n_choice = st.number_input("選擇題數", min_value=0, max_value=10, value=3)

    with c2:
        n_fill = st.number_input("填充題數", min_value=0, max_value=10, value=3)

    with c3:
        n_app = st.number_input("應用題數", min_value=0, max_value=10, value=2)

    show_answers = st.checkbox("顯示答案", value=True)

    st.markdown("**四、圖形題（程式繪圖，不花 token）**")

    use_nl = st.checkbox("數線", value=False)
    nl_lo, nl_hi, nl_mark = -5, 5, 3
    if use_nl:
        n1, n2, n3 = st.columns(3)
        nl_lo = n1.number_input("數線最小值", value=-5, step=1)
        nl_hi = n2.number_input("數線最大值", value=5, step=1)
        nl_mark = n3.number_input("A 點位置", value=3, step=1)

    use_ln = st.checkbox("一次函數圖形", value=False)
    ln_a, ln_b = 2, -1
    if use_ln:
        l1, l2 = st.columns(2)
        ln_a = l1.number_input("a（斜率）", value=2, step=1)
        ln_b = l2.number_input("b（y 截距）", value=-1, step=1)

    use_tr = st.checkbox("三角形角度", value=False)
    tr_a, tr_b = 50, 60
    if use_tr:
        t1, t2 = st.columns(2)
        tr_a = t1.number_input("角 A（度）", min_value=1, max_value=178, value=50, step=1)
        tr_b = t2.number_input("角 B（度）", min_value=1, max_value=178, value=60, step=1)

    use_bar = st.checkbox("統計長條圖", value=False)
    bar_title, bar_data = "資源回收量統計", "五甲:30,五乙:26,五丙:32"
    if use_bar:
        bar_title = st.text_input("長條圖標題", value="資源回收量統計")
        bar_data = st.text_input("資料（名稱:數值，逗號分隔）", value="五甲:30,五乙:26,五丙:32")

    # ---------- GENERATE ----------
    if st.button("開始出題"):

        if topic.strip() == "":
            st.error("請先輸入出題範圍。")
            return

        if n_choice + n_fill + n_app == 0:
            st.error("至少要出一題。")
            return

        with st.spinner("AI 出題中……"):
            sections, raws = generate_mixed_parallel(
                topic, level, n_choice, n_fill, n_app)

        total = sum(len(sections[k]) for k in sections)

        if total == 0:
            st.error("AI 沒有回傳可用題目，原始回應如下（拿去對金鑰或額度）：")
            for r in raws:
                st.code(r or "(空白回應)")
            return

        figs = []

        if use_nl:
            if nl_lo >= nl_hi or not (nl_lo <= nl_mark <= nl_hi):
                st.error("數線範圍或 A 點位置不合理。")
                return
            img, ans = figures.make_number_line(nl_lo, nl_hi, nl_mark)
            figs.append({"question": "如圖，數線上 A 點代表的數是多少？",
                         "answer": ans, "image": img})

        if use_ln:
            img, intercept, y2 = figures.make_linear(ln_a, ln_b)
            figs.append({"question": f"如圖為 y = ax + b 的圖形，求 a 與 b。",
                         "answer": f"a = {ln_a}；b = {ln_b}",
                         "image": img})

        if use_tr:
            if tr_a + tr_b >= 180:
                st.error("兩角之和必須小於 180 度。")
                return
            img, ans = figures.make_triangle(tr_a, tr_b)
            figs.append({"question": f"如圖，∠A = {tr_a}°，∠B = {tr_b}°，求∠C 是幾度？",
                         "answer": f"{ans} 度", "image": img})

        if use_bar:
            try:
                items = []
                for part in bar_data.split(","):
                    name, val = part.split(":")
                    items.append((name.strip(), int(val.strip())))
                assert items
            except Exception:
                st.error("長條圖資料格式錯誤，請用「名稱:數值，逗號分隔」。")
                return
            img, best, total = figures.make_bar(bar_title, items)
            figs.append({"question": f"如圖「{bar_title}」，數量最多的是哪一個？總數是多少？",
                         "answer": f"{best}；{total}", "image": img})

        st.session_state["mixed_quiz"] = sections
        st.session_state["fig_quiz"] = figs

        st.session_state["mixed_docx"] = generate_mixed_docx(
            sections,
            institute_name or "學校",
            f"{quiz_title or '考卷'}（{level}）",
            figs=figs,
        )

    # ---------- DISPLAY ----------
    if "mixed_quiz" in st.session_state:

        sections = st.session_state["mixed_quiz"]

        st.divider()

        if institute_name:
            st.write(f"### {institute_name}")

        if quiz_title:
            st.write(f"**{quiz_title}**")

        st.write("---")
        st.write("姓名：")
        st.write("座號：")
        st.write("班級：")
        st.write("組別：")
        st.write("")

        titles = {"choice": "一、選擇題", "fill": "二、填充題", "app": "三、應用題"}

        for kind in ["choice", "fill", "app"]:
            if not sections.get(kind):
                continue
            st.subheader(titles[kind])
            for question in sections[kind]:
                st.markdown(f"**{question[0]}**")
                for line in question[1:]:
                    if (line.startswith("Answer:") or line.startswith("答案：")
                            or line.startswith("答案:") or line.startswith("解答：")
                            or line.startswith("解答:")):
                        if show_answers:
                            st.success(line)
                    else:
                        st.write(line)
                st.write("")

        if st.session_state.get("fig_quiz"):
            st.subheader("四、圖形題")
            for i, item in enumerate(st.session_state["fig_quiz"]):
                st.markdown(f"**圖{i + 1}：{item['question']}**")
                item["image"].seek(0)
                st.image(item["image"], width=600)
                if show_answers:
                    st.success(item["answer"])
                st.write("")

        # ---------- ANSWER KEY ----------
        if show_answers:
            st.subheader("參考答案")
            for kind in ["choice", "fill", "app"]:
                if not sections.get(kind):
                    continue
                st.write(f"**{titles[kind]}**")
                for i, question in enumerate(sections[kind]):
                    st.write(f"第{i + 1}題：{_answer_of(question)}")

            if st.session_state.get("fig_quiz"):
                st.write("**四、圖形題**")
                for i, item in enumerate(st.session_state["fig_quiz"]):
                    st.write(f"圖{i + 1}：{item['answer']}")

        # ---------- DOWNLOAD ----------
        if "mixed_docx" in st.session_state:
            st.download_button(
                label="下載考卷（DOCX）",
                data=st.session_state["mixed_docx"],
                file_name="mixed_quiz.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
