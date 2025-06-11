import streamlit as st
from get_visible_text import visible_text

st.set_page_config(page_title="Clean Text Extractor", page_icon="📝")

st.title("📝 Clean Text Extractor")
url = st.text_input("Paste a web URL")

if st.button("Extract") and url:
    with st.spinner("Fetching…"):
        try:
            text = visible_text(url)
            st.text_area("Result", text, height=400)
            st.download_button("💾 Download .txt", text, file_name="page.txt")
        except Exception as e:
            st.error(f"Error: {e}")
