import streamlit as st

# ---------------- PAGE CONFIG (MUST BE FIRST) ----------------
st.set_page_config(
    page_title="AI 備課助手",
    page_icon="🎓",
    layout="wide"
)

# ---------------- IMPORT MODULES ----------------
from teacheranalysis import analysis
from MCQ import MCQ
from LessonPlan import lessonplan
from lessonsummarize import summarize
from wellness import counsellor


# ---------------- HEADER SECTION ----------------
st.markdown(
    """
    <div style='text-align:center; padding-top:10px;'>
        <h1 style='margin-bottom:5px;'>AI 備課助手</h1>
        <p style='font-size:18px; margin-top:0px;'>
            成績分析・出題・教案・課程摘要，一站備課
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

st.divider()


# ---------------- SIDEBAR NAVIGATION ----------------
st.sidebar.title("備課選單")
st.sidebar.text_input("OpenAI API 金鑰", type="password",
                      key="openai_api_key", help="不會儲存成檔案，只留在此次瀏覽器連線中")

NAV_ZH = {
    "Perform Analysis": "成績分析",
    "Generate Quiz": "AI 出題",
    "Generate Lesson Plan / Notes": "教案／講義",
    "Summarize Lesson": "課程摘要",
    "Get Counselling By AI": "教師心情樹洞",
}
options = st.sidebar.selectbox(
    "想做什麼？",
    list(NAV_ZH.keys()),
    format_func=lambda k: NAV_ZH.get(k, k),
)


# ---------------- ROUTING ----------------
if options == "Perform Analysis":
    analysis()

elif options == "Generate Quiz":
    MCQ()

elif options == "Generate Lesson Plan / Notes":
    lessonplan()

elif options == "Summarize Lesson":
    summarize()

elif options == "Get Counselling By AI":
    counsellor()