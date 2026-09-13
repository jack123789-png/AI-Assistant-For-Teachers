import streamlit as st


def display_cards(title, average, highest, lowest):
    # Inject CSS once
    st.markdown(
        """
        <style>
        .card-container {
            display: flex;
            gap: 20px;
            justify-content: space-between;
            margin-top: 10px;
            margin-bottom: 20px;
        }

        .card {
            flex: 1;
            background: linear-gradient(135deg, #1f2937, #374151);
            border-radius: 16px;
            padding: 20px;
            text-align: center;
            color: white;
            box-shadow: 0 8px 20px rgba(0,0,0,0.25);
            transition: transform 0.25s ease, box-shadow 0.25s ease;
        }

        .card:hover {
            transform: translateY(-5px) scale(1.03);
            box-shadow: 0 12px 25px rgba(0,0,0,0.35);
        }

        .card h3 {
            font-size: 18px;
            margin-bottom: 8px;
            opacity: 0.85;
        }

        .card p {
            font-size: 26px;
            font-weight: bold;
            margin: 0;
        }

        .average {
            background: linear-gradient(135deg, #3b82f6, #2563eb);
        }

        .highest {
            background: linear-gradient(135deg, #10b981, #059669);
        }

        .lowest {
            background: linear-gradient(135deg, #ef4444, #dc2626);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.subheader(title)

    st.markdown(
        f"""
        <div class="card-container">
            <div class="card average">
                <h3>平均</h3>
                <p>{average:.2f}</p>
            </div>
            <div class="card highest">
                <h3>最高</h3>
                <p>{highest:.2f}</p>
            </div>
            <div class="card lowest">
                <h3>最低</h3>
                <p>{lowest:.2f}</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )