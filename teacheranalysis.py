import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from animations import display_cards
from ai import ask_ai
from customquery import query_chatgpt


# ---------------- LOAD DATA ----------------
@st.cache_data
def load_data(file):

    if file.name.endswith(".csv"):
        df = pd.read_csv(file)

    elif file.name.endswith(".xlsx"):
        df = pd.read_excel(file)

    else:
        return None

    return df


# ---------------- COLUMN DETECTION ----------------
def detect_columns(df):

    id_candidates = ["roll","id","reg","studentid","學號","編號","座號"]
    name_candidates = ["name","student","fullname","姓名"]
    attendance_candidates = ["attendance","attend","出缺","出席","缺席"]

    ignore_words = ["total","sum","average","avg","percentage","percent","grade","平均","總分","等第"]

    id_col=None
    name_col=None
    attendance_col=None

    for col in df.columns:

        c=col.lower()

        if any(x in c for x in id_candidates):
            id_col=col

        elif any(x in c for x in name_candidates):
            name_col=col

        elif any(x in c for x in attendance_candidates):
            attendance_col=col

    subjects=[]

    for col in df.columns:

        c=col.lower()

        if col in [id_col,name_col,attendance_col]:
            continue

        if any(w in c for w in ignore_words):
            continue

        if pd.api.types.is_numeric_dtype(df[col]):
            subjects.append(col)

    return id_col,name_col,attendance_col,subjects


# ---------------- AI CLASS ANALYSIS ----------------
@st.cache_data(show_spinner=False)
def ai_class_analysis(summary):

    prompt=f"""
Class dataset summary:

{summary}

Explain briefly:

• weak subjects
• struggling students
• role of attendance
• teacher recommendations

Return 4 short bullet points.
"""

    return ask_ai("You are an educational data analyst.",prompt)


# ---------------- AI ATTENDANCE ----------------
@st.cache_data(show_spinner=False)
def ai_attendance_analysis(summary):

    prompt=f"""
Attendance summary:

{summary}

Explain briefly:

• attendance risk
• relation between attendance and performance
• one recommendation for teachers

Return 3 short bullet points.
"""

    return ask_ai("You are an academic analytics expert.",prompt)


# ---------------- STUDENT AI ADVICE ----------------
@st.cache_data(show_spinner=False)
def get_student_advice(student,marks,attendance):

    prompt=f"""
Student: {student}
Marks: {marks}
Attendance: {attendance}

Give 3 short improvement tips.
"""

    return ask_ai("You are a professional teacher mentor.",prompt)


# ---------------- STUDENT GRAPH ----------------
def plot_student_marks(subjects,marks,title):

    fig,ax=plt.subplots(figsize=(10,6))

    sns.barplot(
        x=subjects,
        y=marks,
        hue=subjects,
        palette="coolwarm",
        legend=False,
        ax=ax
    )

    ax.set_xlabel("科目")
    ax.set_ylabel("分數")
    ax.set_title(title)

    return fig


# ---------------- ATTENDANCE GRAPH ----------------
def plot_attendance(df,name_col,attendance_col):

    fig,ax=plt.subplots(figsize=(10,5))

    sns.barplot(
        x=df[name_col],
        y=df[attendance_col],
        hue=df[name_col],
        palette="viridis",
        legend=False,
        ax=ax
    )

    ax.set_xlabel("學生")
    ax.set_ylabel("出席率（%）")
    ax.set_title("每位學生出席率")

    plt.xticks(rotation=45)

    return fig


# ---------------- HEATMAP ----------------
def plot_heatmap(df,name_col,subjects):

    data=df[[name_col]+subjects].set_index(name_col)

    fig,ax=plt.subplots(figsize=(10,6))

    sns.heatmap(
        data,
        cmap="YlOrRd",
        annot=True,
        fmt=".0f",
        linewidths=0.5,
        ax=ax
    )

    ax.set_title("學生成績熱力圖")

    return fig


# ---------------- MAIN APP ----------------
def analysis():

    uploaded_file=st.file_uploader("上傳成績檔",type=["csv","xlsx"])

    ANALYSIS_ZH = {
        "Class Wide Performance Analysis": "班級整體分析",
        "Student Wise Performance Analysis": "個別學生分析",
        "Attendance Analysis": "出缺勤分析",
        "Ask Questions To The Data": "用問的查資料",
    }
    analysis_type=st.sidebar.radio(
        "分析項目：",
        list(ANALYSIS_ZH.keys()),
        format_func=lambda k: ANALYSIS_ZH.get(k, k),
    )

    if uploaded_file is None:
        st.info("上傳 CSV 或 Excel 成績檔開始（班務系統匯出的也可以）。")
        return

    df=load_data(uploaded_file)

    st.subheader("資料預覽")
    st.dataframe(df.head())

    id_col,name_col,attendance_col,subjects=detect_columns(df)

    if name_col is None:
        name_col=id_col

    if len(subjects)==0:
        st.error("偵測不到科目欄位。")
        return

    df["AverageScore"]=df[subjects].mean(axis=1)


# ---------------- CLASS ANALYSIS ----------------
    if analysis_type=="Class Wide Performance Analysis":

        st.subheader("整體概況")

        c1,c2,c3=st.columns(3)

        c1.metric("學生人數",len(df))
        c2.metric("科目數",len(subjects))
        c3.metric("總平均",round(df["AverageScore"].mean(),2))

        display_cards(
            "Class Performance",
            df["AverageScore"].mean(),
            df[subjects].max().max(),
            df[subjects].min().min()
        )

        st.subheader("成績熱力圖")
        st.pyplot(plot_heatmap(df,name_col,subjects))

        summary={
            "subject_averages":df[subjects].mean().round(2).to_dict(),
            "lowest_students":df.nsmallest(3,"AverageScore")[[name_col,"AverageScore"]].to_dict(orient="records"),
            "attendance_mean":round(df[attendance_col].mean(),2) if attendance_col else None
        }

        if "class_ai" not in st.session_state:

            with st.spinner("分析班級表現中……"):
                st.session_state.class_ai=ai_class_analysis(summary)

        with st.expander("AI 班級分析"):
            st.markdown(st.session_state.class_ai)


# ---------------- STUDENT ANALYSIS ----------------
    elif analysis_type=="Student Wise Performance Analysis":

        student=st.selectbox("選擇學生",df[name_col].unique())

        data=df[df[name_col]==student].iloc[0]

        marks={s:data[s] for s in subjects}

        attendance=data[attendance_col] if attendance_col else "N/A"

        st.write("出缺勤：",attendance)

        st.pyplot(plot_student_marks(subjects,list(marks.values()),student))

        st.subheader("班級排名")

        ranking=df[[name_col,"AverageScore"]].sort_values(
            by="AverageScore",
            ascending=False
        )

        st.dataframe(ranking)

        strong_students=ranking.head(3)
        weak_students=ranking.tail(3)

        col1,col2=st.columns(2)

        with col1:
            st.markdown("### 🟢 表現好的學生")
            st.dataframe(strong_students)

        with col2:
            st.markdown("### 🔴 需要協助的學生")
            st.dataframe(weak_students)

        if f"student_ai_{student}" not in st.session_state:

            with st.spinner("產生學習建議中……"):
                st.session_state[f"student_ai_{student}"]=get_student_advice(student,marks,attendance)

        st.subheader("AI 學習建議")
        st.markdown(st.session_state[f"student_ai_{student}"])


# ---------------- ATTENDANCE ----------------
    elif analysis_type=="Attendance Analysis":

        if attendance_col is None:
            st.warning("缺少出缺勤欄位。")
            return

        st.subheader("出缺勤總覽")

        st.pyplot(plot_attendance(df,name_col,attendance_col))

        top=df.nlargest(3,attendance_col)[[name_col,attendance_col]]
        low=df.nsmallest(3,attendance_col)[[name_col,attendance_col]]

        col1,col2=st.columns(2)

        with col1:
            st.markdown("### 🟢 出席最高")
            st.dataframe(top)

        with col2:
            st.markdown("### 🔴 缺席警示")
            st.dataframe(low)

        summary={
            "average_attendance":round(df[attendance_col].mean(),2),
            "lowest_attendance":df[attendance_col].min(),
            "highest_attendance":df[attendance_col].max(),
            "average_score":round(df["AverageScore"].mean(),2)
        }

        if "attendance_ai" not in st.session_state:

            with st.spinner("分析出缺勤中……"):
                st.session_state.attendance_ai=ai_attendance_analysis(summary)

        st.subheader("AI 出缺勤觀察")
        st.markdown(st.session_state.attendance_ai)


# ---------------- AI QUESTIONS ----------------
    elif analysis_type=="Ask Questions To The Data":

        question=st.text_area("問一個關於這份資料的問題")

        if st.button("送出") and question:

            context=f"""
Columns: {list(df.columns)}

Sample data:
{df.head(10).to_string(index=False)}
"""

            with st.spinner("分析中……"):
                answer=query_chatgpt(question,context)

            st.success(answer)