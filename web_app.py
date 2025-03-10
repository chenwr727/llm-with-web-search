import asyncio
import re

import aiohttp
import streamlit as st

from schemas.chat_message import ChatMessage


def initialize_session_state():
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "history" not in st.session_state:
        st.session_state.history = []


async def handle_query(question: str, needs_crawler: bool, needs_filter: bool):
    st.session_state.messages.append(ChatMessage(role="user", content=question))
    st.session_state.history.append({"role": "user", "content": question})

    is_search = False
    search_content = ""
    is_reasoning = False
    reasoning_content = ""
    content = ""

    data = {
        "messages": [msg.model_dump() for msg in st.session_state.messages],
        "needs_crawler": needs_crawler,
        "needs_filter": needs_filter,
    }
    async with aiohttp.ClientSession() as client:
        async with client.post("http://localhost:8000/api/v1/chat", json=data, timeout=None) as response:
            async for line in response.content:
                chunk = re.sub(r"\r\n?$", "", line.decode("utf-8"))
                if not chunk:
                    continue

                if chunk.startswith("[SEARCH]"):
                    is_search = True
                    continue
                elif chunk.startswith("[/SEARCH]"):
                    is_search = False
                    continue
                elif chunk.startswith("[THINK]"):
                    is_reasoning = True
                    continue
                elif chunk.startswith("[/THINK]"):
                    is_reasoning = False
                    continue
                elif chunk.startswith("[DONE]"):
                    break

                if is_search:
                    search_content += chunk
                    search_placeholder.markdown(search_content, unsafe_allow_html=True)
                elif is_reasoning:
                    reasoning_content += chunk
                    reasoning_placeholder.markdown(reasoning_content)
                else:
                    content += chunk
                    output_placeholder.markdown(content, unsafe_allow_html=True)

    st.session_state.messages.append(ChatMessage(role="assistant", content=content))
    st.session_state.history.append(
        {"role": "assistant", "content": content, "search": search_content, "reasoning": reasoning_content}
    )


def config_search_tool():
    needs_crawler = st.sidebar.checkbox("开启爬取源网页", value=False)
    needs_filter = st.sidebar.checkbox("开启过滤和总结", value=False)
    return needs_crawler, needs_filter


def clean_history():
    button_clean = st.sidebar.button("清理会话历史", type="primary")
    if button_clean:
        st.session_state["messages"] = []
        st.session_state["history"] = []


def display_chat_history():
    for message in st.session_state.history:
        if message["role"] == "user":
            with st.chat_message(name="user", avatar="user"):
                st.markdown(message["content"])
        elif message["role"] == "assistant":
            with st.expander("search", expanded=True):
                st.markdown(message["search"], unsafe_allow_html=True)
            with st.expander("think", expanded=True):
                st.markdown(message["reasoning"])
            with st.chat_message(name="assistant", avatar="assistant"):
                st.markdown(message["content"], unsafe_allow_html=True)


st.set_page_config(page_title="Chat with LLM", layout="wide")
st.title("Chat with LLM")

css = """
<style>
    a[id^="footnote"] {
        display: block;
        position: relative;
        visibility: visible;
        height: 0;
        top: -60px;
    }
    html {
        scroll-behavior: smooth;
    }
</style>
"""
st.markdown(css, unsafe_allow_html=True)

needs_crawler, needs_filter = config_search_tool()

initialize_session_state()

clean_history()

display_chat_history()

with st.chat_message(name="user", avatar="user"):
    input_placeholder = st.empty()
with st.expander("search", expanded=True):
    search_placeholder = st.empty()
with st.expander("think", expanded=True):
    reasoning_placeholder = st.empty()
with st.chat_message(name="assistant", avatar="assistant"):
    output_placeholder = st.empty()

user_input = st.chat_input("请输入您的问题")
if user_input:
    input_placeholder.markdown(user_input)
    with st.spinner("正在处理..."):
        asyncio.run(handle_query(user_input, needs_crawler, needs_filter))
