import streamlit as st
import requests
import json


API_URL = "http://127.0.0.1:8000"


st.set_page_config(
    page_title="Resume Skill Analyzer",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("📄 Resume Skill Analyzer")
st.write("Upload your resumes to analyze skills mentioned in the documents.")


st.sidebar.header("🔍 How It Works")
st.sidebar.write("1. Upload multiple resumes (PDF/DOCX)\n2. We analyze key skills\n3. View detected skills instantly")


uploaded_files = st.file_uploader("Upload Resumes (PDF/DOCX)", type=["pdf", "docx"], accept_multiple_files=True)

if uploaded_files:
    files_data = [("files", (file.name, file.getvalue())) for file in uploaded_files]

    with st.spinner("🔍 Analyzing resumes..."):
        response = requests.post(f"{API_URL}/upload", files=files_data)

    if response.status_code == 200:
        results = response.json()["uploaded_files"]
        for res in results:
            st.subheader(f"📌 Analysis Report for {res['filename']}")
            st.write(f"**Word Count:** {res['analysis']['word_count']}")
            st.write(f"**Extracted Skills:** {', '.join(res['analysis']['found_skills']) if res['analysis']['found_skills'] else 'No skills detected'}")
            st.write(f"**Suggestions:** {res['analysis']['suggestions']}")
            st.divider()
    else:
        st.error(f"⚠️ Error: {response.json().get('error', 'Unknown error occurred')}")


st.sidebar.subheader("📁 View Selected Resumes")

if st.sidebar.button("Get Selected Resumes"):
    response = requests.get(f"{API_URL}/getAllSelected")

    if response.status_code == 200:
        data = response.json()
        selected_files = data.get("selected_files", [])

        if selected_files:
            st.sidebar.write("📌 **Selected Resumes:**")
            for file in selected_files:
                resume_url = f"{API_URL}/download/{file}" 
                
                # Displaying clickable links
                st.sidebar.markdown(f"📄 [{file}]({resume_url})", unsafe_allow_html=True)

                # Optional: Adding a direct download button
                download_response = requests.get(resume_url)
                if download_response.status_code == 200:
                    st.sidebar.download_button(
                        label=f"⬇ Download {file}",
                        data=download_response.content,
                        file_name=file,
                        mime="application/pdf"  # Change if files are not PDFs
                    )
                else:
                    st.sidebar.error(f"❌ Unable to fetch {file}")

        else:
            st.sidebar.write("🚫 No selected resumes found.")
    else:
        st.sidebar.error("❌ Failed to fetch selected resumes!")



st.sidebar.subheader("🔧 Admin Panel")
new_skills = st.sidebar.text_area("Enter skills (comma-separated)", "Python, Machine Learning, AI, TensorFlow")
if st.sidebar.button("Update Skills"):
    skill_list = [skill.strip() for skill in new_skills.split(",")]
    response = requests.post(f"{API_URL}/admin", json={"skill": skill_list})
    if response.status_code == 200:
        st.sidebar.success("✅ Skills updated successfully!")
    else:
        st.sidebar.error("❌ Failed to update skills!")


st.sidebar.subheader("🚀 Server Status")
if st.sidebar.button("Check API Health"):
    response = requests.get(f"{API_URL}/healthcheck")
    if response.status_code == 200:
        st.sidebar.success(f"🟢 {response.json()['status']} - {response.json()['timestamp']}")
    else:
        st.sidebar.error("❌ Server is down!")
