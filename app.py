#app.py
from pathlib import Path
import os, openai, streamlit as st
from get_visible_text import visible_text

# ---------- load rules ----------
RULES_PATH = Path(__file__).with_name("translator_rules.txt")
TRANSLATOR_SYSTEM_PROMPT = RULES_PATH.read_text(encoding="utf-8")

openai.api_key = os.getenv("OPENAI_API_KEY")

# ---------- extractor tab ----------
tab_extract, tab_translate = st.tabs(["📝 Extract", "🌍 Translate"])

with tab_extract:
    url = st.text_input("Paste a URL")
    if st.button("Extract") and url:
        text = visible_text(url)
        st.session_state["last_text"] = text  # save for translation
        st.text_area("Clean text", text, height=400)

# ---------- translation chatbot ----------
with tab_translate:
    # Pick or paste source text
    default_text = st.session_state.get("last_text", "")
    src_text = st.text_area("Text to translate", default_text, height=200)

    tgt_lang = st.selectbox("Target language", ["en", "es", "de", "fr", "no"])
    if "chat" not in st.session_state:
        st.session_state.chat = []  # holds {"role":"user"/"assistant","content":...}

    # existing messages
    for m in st.session_state.chat:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    # new user prompt
    if prompt := st.chat_input("Ask about the translation, or type 'translate'"):
        st.session_state.chat.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # -------- build conversation w/ rules --------
        messages = [
            {"role": "system", "content": TRANSLATOR_SYSTEM_PROMPT},
            {"role": "user", "content": f"TARGET_LANG = {tgt_lang}\n\n{src_text}"},
        ]

        try:
            resp = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                max_tokens=2000,
                temperature=0.2,
            )
            answer = resp.choices[0].message.content.strip()
        except Exception as e:
            answer = f"❌ Error: {e}"

        st.session_state.chat.append({"role": "assistant", "content": answer})
        with st.chat_message("assistant"):
            st.markdown(answer)
