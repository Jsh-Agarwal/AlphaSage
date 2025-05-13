import streamlit as st
import requests

st.set_page_config(page_title="Investment Research Assistant", layout="wide")

st.title("📊 Investment Research Assistant")
st.markdown("Ask any investment-related question, and get a detailed research-backed answer.")

query = st.text_area("Enter your research topic or query", height=150)

if st.button("Submit Query"):
    if query.strip() == "":
        st.warning("Please enter a query before submitting.")
    else:
        with st.spinner("🔎 Generating your research-backed answer..."):
            try:
                response = requests.post(
                    "http://localhost:5000/query",  # Update if hosted remotely
                    json={"query": query},
                    timeout=300  # Set high timeout for long processing
                )
                data = response.json()
                if data.get("success"):
                    st.success("✅ Research complete!")
                    st.markdown(data["answer"], unsafe_allow_html=True)
                else:
                    st.error(f"❌ Error from server: {data.get('error')}")
            except Exception as e:
                st.error(f"⚠️ Failed to connect to the server: {str(e)}")

