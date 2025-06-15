import requests
import streamlit as st
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")

st.set_page_config(page_title="AI SEO Blog Generator", layout="wide")
st.title("📝 AI-Powered SEO Blog Generator")

# Sidebar controls
st.sidebar.header("🔧 Controls")
mode = st.sidebar.radio("Choose mode", ["Single Keyword", "Bulk Upload"])
tone = st.sidebar.selectbox("Tone", ["Informative", "Professional", "Conversational", "Friendly"])
temperature = st.sidebar.slider("Creativity (temperature)", 0.0, 1.0, 0.7, 0.1)
max_tokens = st.sidebar.slider("Max Tokens", 500, 3000, 1500, 100)
include_faq = st.sidebar.checkbox("Include FAQ section")
add_cta = st.sidebar.checkbox("Add Call-to-Action")

# Keyword Suggestion
st.subheader("🔍 Keyword Suggestions")
seed_keyword = st.text_input("Enter a broad keyword to get suggestions")
if st.button("Suggest Keywords"):
    if not TOGETHER_API_KEY:
        st.error("API key is missing. Please set TOGETHER_API_KEY.")
    else:
        with st.spinner("Thinking of smart ideas..."):
            try:
                prompt = f"Generate 10 long-tail SEO keywords based on the keyword '{seed_keyword}' with high search intent."
                response = requests.post(
                    "https://api.together.xyz/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {TOGETHER_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "mistralai/Mixtral-8x7B-Instruct-v0.1",
                        "messages": [
                            {"role": "system", "content": "You are an SEO expert."},
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.5,
                        "max_tokens": 300,
                    }
                )
                if response.status_code == 200:
                    suggestions = response.json()["choices"][0]["message"]["content"]
                    st.code(suggestions)
                else:
                    error_msg = response.json().get("error", {}).get("message", "Unknown error")
                    st.error(f"Failed to fetch suggestions: {error_msg}")
            except Exception as e:
                st.error(f"Error while calling API: {str(e)}")

# Prompt builder
def build_prompt(keyword):
    sections = [
        f"Write an SEO-optimized blog article for the keyword '{keyword}'.",
        f"Use a {tone.lower()} tone.",
        "Include Title, Meta Description, H1, H2, H3 headings, introduction and conclusion."
    ]
    if include_faq:
        sections.append("Add a Frequently Asked Questions section at the end.")
    if add_cta:
        sections.append("Add a compelling call-to-action at the end.")
    return "\n".join(sections)

# Content Generator Function
def generate_blog(keyword):
    prompt = build_prompt(keyword)
    try:
        response = requests.post(
            "https://api.together.xyz/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {TOGETHER_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "mistralai/Mixtral-8x7B-Instruct-v0.1",
                "messages": [
                    {"role": "system", "content": "You are a professional SEO blog writer."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": temperature,
                "max_tokens": max_tokens
            }
        )
        data = response.json()
        if response.status_code == 200:
            return data["choices"][0]["message"]["content"]
        else:
            return f"API Error: {data.get('error', {}).get('message', 'Unknown error')}"
    except Exception as e:
        return f"Exception occurred: {str(e)}"

# Blog Generation Mode
st.subheader("🛠 Blog Generator")

if mode == "Single Keyword":
    keyword = st.text_input("Enter a keyword")
    if st.button("Generate Blog") and keyword:
        with st.spinner("Crafting your blog..."):
            blog = generate_blog(keyword)
            if blog.startswith("API Error") or blog.startswith("Exception"):
                st.error(blog)
            else:
                st.markdown(blog)
                st.download_button("📥 Download Blog", blog, file_name=f"{keyword.replace(' ', '_')}.txt")

elif mode == "Bulk Upload":
    uploaded_file = st.file_uploader("Upload CSV with 'keyword' column", type=["csv"])
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        blogs = []
        if st.button("Generate Blogs in Bulk"):
            for idx, row in df.iterrows():
                with st.spinner(f"Generating blog for: {row['keyword']}"):
                    blog = generate_blog(row['keyword'])
                    blogs.append({"keyword": row['keyword'], "blog": blog})
            result_df = pd.DataFrame(blogs)
            st.success("All blogs generated!")
            csv = result_df.to_csv(index=False)
            st.download_button("📥 Download All Blogs (CSV)", csv, file_name="generated_blogs.csv")
