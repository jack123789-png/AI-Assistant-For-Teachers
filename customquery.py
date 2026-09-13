import streamlit as st
import pandas as pd
from ai import ask_ai


# ---------------- AI DATA QUERY FUNCTION ----------------
def query_chatgpt(question, context):
    system_prompt = """
You are the world's best teacher and statistical data analyst.
You perform accurate calculations internally.
Return only the final clear answer.
Do NOT show calculation steps.
Be concise and precise.
"""

    user_prompt = f"""
Dataset:
{context}

Question:
{question}
"""

    return ask_ai(system_prompt, user_prompt)


# ---------------- STREAMLIT COMPONENT ----------------
def custom_query():
    st.subheader("問資料")

    uploaded_file = st.file_uploader("上傳學生成績 CSV", type="csv")

    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)

        st.write("### 已上傳資料")
        st.dataframe(df)

        question = st.text_area("想問什麼：")

        if st.button("送出"):
            if question.strip() == "":
                st.warning("請先輸入問題。")
            else:
                context = df.to_string(index=False)

                with st.spinner("分析中……"):
                    answer = query_chatgpt(question, context)

                st.success(answer)