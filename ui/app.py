import streamlit as st
import requests
import json
import os

# Use environment variable for backend URL (useful for deployment)
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")






LOCAL_SCRIPT_PATH = r"C:\Users\RUPSA NANDA\OneDrive\Desktop\QA-AGENT\uploaded_docs\selenium_.py"

st.set_page_config(
    page_title="QA-Agent Dashboard",
    layout="wide"
)

st.title("🤖 QA-Agent – Automated Testcase & Script Generator")
st.markdown("This UI lets you upload documents, build a knowledge base, generate testcases and auto-create Selenium scripts.")

# Check backend connectivity
try:
    health_resp = requests.get(f"{BACKEND_URL}/health", timeout=5)
    if health_resp.ok:
        health_data = health_resp.json()
        if health_data.get("status") == "healthy":
            docs_count = health_data.get("chromadb_documents", 0)
            st.sidebar.success(f"✅ Backend connected ({docs_count} docs in KB)")
        else:
            st.sidebar.warning(f"⚠️ Backend degraded: {health_data.get('error', 'Unknown issue')}")
    else:
        st.sidebar.warning("⚠️ Backend may be having issues")
except requests.exceptions.Timeout:
    st.sidebar.error("❌ Backend timeout - service may be slow or sleeping")
    st.sidebar.info("💡 Render free tier services sleep after 15min inactivity. They wake up in ~30 seconds.")
except requests.exceptions.ConnectionError:
    st.sidebar.error(f"❌ Cannot reach backend at {BACKEND_URL}")
    st.sidebar.info("💡 Check if backend service is running in Render dashboard")
except Exception as e:
    error_msg = str(e)
    if "502" in error_msg or "Bad Gateway" in error_msg:
        st.sidebar.error("❌ Backend is down (502 error)")
        st.sidebar.info("💡 Backend may be sleeping or crashed. Check Render dashboard.")
    else:
        st.sidebar.warning(f"⚠️ Backend check failed: {error_msg}")

# Wake backend button (for sleeping services)
if st.sidebar.button("🔄 Wake Backend / Check Status"):
    status_placeholder = st.sidebar.empty()
    status_placeholder.info("⏳ Checking backend...")
    try:
        health_resp = requests.get(f"{BACKEND_URL}/health", timeout=10)
        if health_resp.ok:
            health_data = health_resp.json()
            status_placeholder.success(f"✅ Backend is awake! ({health_data.get('chromadb_documents', 0)} docs)")
        else:
            status_placeholder.warning("⚠️ Backend responded but may have issues")
    except Exception as e:
        status_placeholder.error("❌ Backend is not responding. It may be sleeping or crashed.")
        st.sidebar.info("💡 Go to Render dashboard and check backend service status")

st.sidebar.header("📁 Upload Documents")

if "uploaded_paths" not in st.session_state:
    st.session_state["uploaded_paths"] = []

uploaded_files = st.sidebar.file_uploader(
    "Upload support docs (HTML, MD, TXT, JSON, PDF)",
    accept_multiple_files=True
)

if uploaded_files:
    files_payload = []
    for f in uploaded_files:
        files_payload.append(("files", (f.name, f.getvalue(), f.type)))

    try:
        resp = requests.post(f"{BACKEND_URL}/upload_files/", files=files_payload, timeout=30)
        if resp.ok:
            result = resp.json()
            if result.get("status") == "ok":
                saved = result.get("saved", [])
                for s in saved:
                    if s["path"] not in st.session_state["uploaded_paths"]:
                        st.session_state["uploaded_paths"].append(s["path"])
                st.sidebar.success(f"✅ {len(saved)} file(s) uploaded successfully!")
            else:
                st.sidebar.error(f"❌ Upload failed: {result.get('message', 'Unknown error')}")
        else:
            error_msg = "Upload failed"
            try:
                error_data = resp.json()
                error_msg = error_data.get("message", error_msg)
            except:
                error_msg = resp.text[:200] if resp.text else error_msg
            st.sidebar.error(f"❌ {error_msg}")
    except requests.exceptions.Timeout:
        st.sidebar.error("❌ Upload timeout - file may be too large or server is slow")
    except requests.exceptions.ConnectionError:
        st.sidebar.error(f"❌ Cannot connect to backend at {BACKEND_URL}")
        st.sidebar.info("💡 Backend may be sleeping. Wait 30 seconds and try again.")
    except Exception as e:
        error_str = str(e)
        if "502" in error_str or "Bad Gateway" in error_str:
            st.sidebar.error("❌ Backend is down (502 error)")
            st.sidebar.info("💡 Backend service may be sleeping or crashed. Check Render dashboard.")
        else:
            st.sidebar.error(f"❌ Upload error: {error_str}")

st.sidebar.subheader("Uploaded Files")
for p in st.session_state["uploaded_paths"]:
    st.sidebar.write(f"- {p}")

if st.sidebar.button("Clear uploaded"):
    st.session_state["uploaded_paths"] = []

st.header("1️⃣ Build Knowledge Base")

if st.button("Build KB"):
    if not st.session_state["uploaded_paths"]:
        st.warning("⚠️ Upload files first.")
    else:
        with st.spinner("Building knowledge base... This may take a moment."):
            try:
                payload = {
                    "file_paths": st.session_state["uploaded_paths"],
                    "chunk_size": 1000,
                    "chunk_overlap": 200
                }
                resp = requests.post(f"{BACKEND_URL}/build_kb/", json=payload, timeout=120)

                if resp.ok:
                    result = resp.json()
                    if result.get("status") == "kb_built":
                        st.success(f"✅ Knowledge base built! Processed {result.get('num_chunks', 0)} chunks from {len(result.get('ingested_files', []))} file(s)")
                    elif result.get("status") == "no_docs_found":
                        st.warning(f"⚠️ {result.get('message', 'No documents found to process')}")
                    else:
                        st.info(f"ℹ️ {result}")
                else:
                    error_msg = "Build KB failed"
                    try:
                        error_data = resp.json()
                        error_msg = error_data.get("message", error_msg)
                    except:
                        error_msg = resp.text[:200] if resp.text else error_msg
                    st.error(f"❌ {error_msg}")
            except requests.exceptions.Timeout:
                st.error("❌ Build KB timeout - this may take longer for large files")
            except requests.exceptions.ConnectionError:
                st.error(f"❌ Cannot connect to backend at {BACKEND_URL}")
                st.info("💡 Backend may be sleeping. Wait 30 seconds and try again.")
            except Exception as e:
                error_str = str(e)
                if "502" in error_str or "Bad Gateway" in error_str:
                    st.error("❌ Backend is down (502 error)")
                    st.info("💡 Backend service may be sleeping or crashed. Check Render dashboard.")
                else:
                    st.error(f"❌ Error: {error_str}")


st.header("2️⃣ Generate Test Cases")

query = st.text_area("Enter your feature / requirement text:", height=80)
top_k = st.number_input("Top-K context retrieval:", 1, 10, 3)

if st.button("Generate Testcases"):
    if not query.strip():
        st.warning("Enter a requirement or feature.")
    else:
        with st.spinner("Generating test cases..."):
            resp = requests.post(
                f"{BACKEND_URL}/generate_testcases/",
                json={"query": query, "top_k": top_k}
            )
            if resp.ok:
                data = resp.json()
                st.session_state["generated"] = data.get("generated", [])
                st.success("Testcases generated!")
            else:
                st.error(resp.text)


if st.session_state.get("generated"):
    st.subheader("Generated Test Cases")
    for item in st.session_state["generated"]:
        st.code(json.dumps(item["payload"], indent=2))



st.header("3️⃣ Generate Selenium Script")

if st.button("Refresh Testcases from Backend"):
    resp = requests.get(f"{BACKEND_URL}/list_testcases/")
    if resp.ok:
        st.session_state["backend_cases"] = resp.json().get("items", [])
        st.success("Fetched testcases!")
    else:
        st.error("Failed to fetch")

cases = st.session_state.get("backend_cases", [])

if cases:
    selected_id = st.selectbox(
        "Choose a testcase ID:",
        [c["id"] for c in cases]
    )

    if st.button("Generate Selenium Script"):
        with st.spinner("Generating Selenium script..."):
            resp = requests.post(
                f"{BACKEND_URL}/generate_selenium_script/",
                json={"testcase_id": selected_id}
            )
            if resp.ok:
                data = resp.json()
     
                script_text = data.get("selenium_script") or data.get("script") or ""

                if script_text:
                    st.subheader("Generated Script")
                    st.code(script_text, language="python")

                
                    st.download_button(
                        label="Download script (.py)",
                        data=script_text,
                        file_name=f"selenium_{selected_id}.py",
                        mime="text/x-python"
                    )

     
                    if os.path.exists(LOCAL_SCRIPT_PATH):
                        st.markdown(f"Local script file detected: `{LOCAL_SCRIPT_PATH}`")
                        st.markdown(f"[Open local script](file:///{LOCAL_SCRIPT_PATH.replace(os.sep, '/')})")
                else:
                    st.error("Backend returned OK but no script text was found in the response.")
                    st.write(data)
            else:
                st.error(resp.text)
else:
    st.info("No testcases yet. Generate above.")

st.markdown("---")
st.caption(f"Backend running at: {BACKEND_URL}")
