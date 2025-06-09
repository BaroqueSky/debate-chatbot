from openai import OpenAI
import streamlit as st
from streamlit_js_eval import streamlit_js_eval


st.set_page_config(page_title="Streamlit Chat", page_icon = "💬")
st.title("辯論機器人")                   



if "setup_complete" not in st.session_state:
    st.session_state.setup_complete = False
if "user_message_count" not in st.session_state:
    st.session_state.user_message_count = 0
if "feedback_shown" not in st.session_state:
    st.session_state.feedback_shown = False
if "messages" not in st.session_state:
    st.session_state.messages = []
if "chat_complete" not in st.session_state:
    st.session_state.chat_complete = False


def complete_setup():
    st.session_state.setup_complete = True
def show_feedback():
    st.session_state.feedback_shown = True

if not st.session_state.setup_complete:

    st.subheader('辯論主題', divider = 'rainbow')

    if "topic" not in st.session_state:
        st.session_state["topic"] = ""

    st.session_state["topic"] = st.text_input(label = "辯論主題", max_chars = 100, value = st.session_state["topic"], placeholder = "請輸入要進行辯論的主題")


    if "position" not in st.session_state:
        st.session_state["position"] = "贊成"
    if "round" not in st.session_state:
        st.session_state["round"] = "辯論回合數"
    if "rival" not in st.session_state:
        st.session_state["rival"] = "普通市民"


    st.subheader("辯論條件設定", divider = 'rainbow')

    col1, col2 = st.columns(2)
    with col1:
        st.session_state["position"] = st.radio(
            "請選擇立場",
            key = "position_radio",
            options = ["贊成", "反對"],
        )
    with col2:
        st.session_state["round"] = st.selectbox(
            "選擇回合數",
            ("3", "5", "7")
        )

    st.session_state["rival"] = st.selectbox(
        "選擇你的對手身分",
        ("普通市民", "網紅", "政治人物", "動保團體人員", "環保團體人員", "法學家", "經濟學家", "動物學家")
    )


    if st.button("開始辯論", on_click=complete_setup):
        st.write("設定完成，準備進行辯論...")


if st.session_state.setup_complete and not st.session_state.feedback_shown and not st.session_state.chat_complete:
    st.info(
        """
        請你開始一段簡單的自我介紹，並說明你的論點
        """,
        icon = "👋"
    )


    client = OpenAI(api_key = st.secrets["OPENAI_API_KEY"])

    if "openai_model" not in st.session_state:
        st.session_state["openai_model"] = "gpt-4o"

    if not st.session_state.messages:
        st.session_state.messages = [{
            "role": "system", 
            "content": (f"你是一名{st.session_state['rival']}。"
                        f"要與使用者進行主題為{st.session_state['topic']}的辯論。他的立場為{st.session_state['position']}。"
                        f"而你必須持與他相反的立場，並根據你的身分應有的知識量與看法，與使用者進行{st.session_state['round']}輪的對話辯論。用語上可以激進與激動一點。")
            }]

    for message in st.session_state.messages:
        if message["role"] != "system":
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    if st.session_state.user_message_count < int(st.session_state["round"]):
        if prompt := st.chat_input("請輸入對話", max_chars = 1000):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            
            if st.session_state.user_message_count < int(st.session_state["round"]) - 1:
                with st.chat_message("assistant"):
                    stream = client.chat.completions.create(
                        model = st.session_state["openai_model"],
                        messages = [
                            {"role": m["role"], "content": m["content"]}
                            for m in st.session_state.messages
                        ],
                        stream = True,
                    )
                    response = st.write_stream(stream)
                st.session_state.messages.append({"role": "assistant", "content": response})
            
            st.session_state.user_message_count += 1

    if st.session_state.user_message_count >= int(st.session_state["round"]):
        st.session_state.chat_complete = True

if st.session_state.chat_complete and not st.session_state.feedback_shown:
    if st.button("取得結果", on_click = show_feedback):
        st.write("結果生成中...")
    
if st.session_state.feedback_shown:
    st.subheader("辯論結果")

    conversation_history = "\n".join([f"{msg['role']}: {msg['content']}" for msg in st.session_state.messages])

    # Initialize new OpenAI client instance for feedback
    feedback_client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

    # Generate feedback using the stored messages and write a system prompt for the feedback
    feedback_completion = feedback_client.chat.completions.create(
        model="gpt-4o",
        messages = [
            { "role": "system",
            "content": """你是一個用來提供辯論表現回饋的輔助工具。
            你的評斷標準與語氣都相當犀利嚴格。
            在給予回饋之前，請先對表現打分，分數範圍為 1 到 10。
            請遵循以下格式：
            整體評分：//你給使用者的分數
            回饋內容：//在這裡撰寫你的回饋
            只需提供回饋，不要提出任何額外問題。
            並在最後說出你認為這場辯論中的勝利方為哪個立場。
            """},
            {"role": "user","content": f"以下是你需要評估的辯論內容。請記住，你只是一個工具，不應參與任何對話：{conversation_history}"}
        ]
    )

    st.write(feedback_completion.choices[0].message.content)

    if st.button("重新開始辯論", type = "primary"):
        streamlit_js_eval(js_expressions = "parent.window.location.reload()")