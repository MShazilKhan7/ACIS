# import base64
# import streamlit as st
# import asyncio
# from utils.mcp_client import call_mcp_agent
# import os
# import shutil
# import logging
# from pathlib import Path

# # Set up logging
# logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
# logger = logging.getLogger(__name__)

# st.set_page_config(page_title="AI Curriculum Intelligence", page_icon="🤖", layout="wide")

# st.title("🎓 AI Curriculum Intelligence System")
# st.markdown("An interactive AI-driven platform to analyze student feedback, performance, and industry alignment using multi-agent MCP servers.")

# # --- File Upload UI ---
# st.sidebar.header("📂 Upload Course Data")
# course_name = st.sidebar.text_input("Course Name", "machine learning")

# feedback_file = st.sidebar.file_uploader("Upload Feedback CSV", type=["csv"])
# performance_file = st.sidebar.file_uploader("Upload Performance CSV", type=["csv"])
# curriculum_files = st.sidebar.file_uploader(
#     "Upload Curriculum Files (PDF/PPTX)", 
#     type=["pdf", "pptx", "ppt"], 
#     accept_multiple_files=True,
#     help="Upload one or more PDF or PPTX files for the curriculum."
# )
# job_trend_csv = st.sidebar.file_uploader("Upload Job Trends CSV", type=["csv"], help="Required: Upload custom job trends.")

# if st.sidebar.button("🚀 Run Analysis"):
#     if not all([feedback_file, performance_file, curriculum_files, job_trend_csv]):
#         st.error("Please upload all required files: Feedback CSV, Performance CSV, at least one Curriculum file (PDF/PPTX), and Job Trends CSV.")
#         st.stop()

#     # Clean up and create temp directory with absolute path
#     temp_dir = Path("temp_uploads").resolve()
#     shutil.rmtree(temp_dir, ignore_errors=True)
#     temp_dir.mkdir(exist_ok=True)

#     # Save uploads temporarily with absolute paths
#     feedback_path = temp_dir / f"{course_name}_feedback.csv"
#     performance_path = temp_dir / f"{course_name}_performance.csv"
#     job_trend_path = temp_dir / f"{course_name}_job_trends.csv"
#     curriculum_paths = []

#     # Validate and save files
#     for file_path, uploaded_file in [
#         (feedback_path, feedback_file),
#         (performance_path, performance_file),
#         (job_trend_path, job_trend_csv)
#     ]:
#         if uploaded_file:
#             try:
#                 with open(file_path, "wb") as f:
#                     f.write(uploaded_file.read())
#                 logger.info(f"Saved {file_path}")
#                 if not file_path.is_file():
#                     raise RuntimeError(f"File not found after saving: {file_path}")
#             except Exception as e:
#                 st.error(f"Failed to save {file_path.name}: {str(e)}")
#                 st.stop()
#         else:
#             st.error(f"Upload failed for {file_path.name}")
#             st.stop()

#     # Save multiple curriculum files
#     for idx, curriculum_file in enumerate(curriculum_files, 1):
#         ext = os.path.splitext(curriculum_file.name)[1].lower()
#         if ext not in [".pdf", ".pptx", ".ppt"]:
#             st.error(f"Unsupported file type for {curriculum_file.name}. Please upload PDF or PPTX files.")
#             st.stop()
#         curriculum_path = temp_dir / f"{course_name}_curriculum_{idx}{ext}"
#         try:
#             with open(curriculum_path, "wb") as f:
#                 f.write(curriculum_file.read())
#             logger.info(f"Saved {curriculum_path}")
#             if not curriculum_path.is_file():
#                 raise RuntimeError(f"File not found after saving: {curriculum_path}")
#             curriculum_paths.append(str(curriculum_path))
#         except Exception as e:
#             st.error(f"Failed to save {curriculum_path.name}: {str(e)}")
#             st.stop()

#     if not curriculum_paths:
#         st.error("No valid curriculum files uploaded.")
#         st.stop()

#     # --- Stream the "agentic" process visually ---
#     st.subheader("🧠 Agentic Workflow Progress")

#     # Define async helper function
#     async def run_agent_calls():
#         # Calling Feedback Agent
#         with st.spinner("🗣️ Feedback Agent analyzing student sentiments..."):
#             feedback_res = await call_mcp_agent(
#                 "http://localhost:9001/mcp",
#                 "analyze_feedback",
#                 {"course_name": course_name, "file_path": str(feedback_path), "output_path": str(temp_dir / "feedback_out.csv")}
#             )
#             logger.info(f"Feedback Agent Response: {feedback_res}")
#             if feedback_res.get("error"):
#                 st.error(f"Feedback Agent error: {feedback_res.get('error')}")
#                 st.stop()
#             st.success("✅ Feedback analysis complete!")
#             st.markdown(feedback_res.get("summary", "No summary available"))

#         # Performance Agent
#         with st.spinner("📊 Performance Agent evaluating academic data..."):
#             perf_res = await call_mcp_agent(
#                 "http://localhost:9002/mcp",
#                 "evaluate_performance",
#                 {"course_name": course_name, "file_path": str(performance_path), "output_path": str(temp_dir / "perf_out.csv")}
#             )
#             logger.info(f"Performance Agent Response: {perf_res}")
#             if perf_res.get("error"):
#                 st.error(f"Performance Agent error: {perf_res.get('error')}")
#                 st.stop()
#             st.success("✅ Performance analysis complete!")
#             st.markdown(perf_res.get("summary", "No summary available"))

#         # Trend Agent
#         with st.spinner("💼 Trend Agent identifying industry-relevant skills..."):
#             trend_res = await call_mcp_agent(
#                 "http://localhost:9003/mcp",
#                 "analyze_job_trends",
#                 {"course_name": course_name, "file_path": str(job_trend_path), "output_path": str(temp_dir / "trends_out.csv")}
#             )
#             logger.info(f"Trend Agent Response: {trend_res}")
#             if trend_res.get("error"):
#                 st.error(f"Trend Agent error: {trend_res.get('error')}")
#                 st.stop()
#             st.success("✅ Job trend analysis complete!")
#             st.markdown(trend_res.get("summary", "No summary available"))

#         # Recommender Agent
#         with st.spinner("🧩 Recommender Agent generating curriculum updates..."):
#             rec_res = await call_mcp_agent(
#                 "http://localhost:9004/mcp",
#                 "recommend_curriculum_updates",
#                 {
#                     "course_name": course_name,
#                     "curriculum_paths": curriculum_paths,
#                     "feedback_summary": feedback_res.get("summary", ""),
#                     "performance_summary": perf_res.get("summary", ""),
#                     "trend_summary": trend_res.get("summary", ""),
#                     "output_path": str(temp_dir / "recommendations.txt")
#                 }
#             )
#             logger.info(f"Recommender Agent Response: {rec_res}")
#             if rec_res.get("error"):
#                 st.error(f"Recommender Agent error: {rec_res.get('error')}")
#                 st.stop()
#             st.success("✅ Curriculum recommendations ready!")
#             st.markdown("### ✨ Recommended Updates")
#             st.info(rec_res.get("curriculum_recommendations", "No recommendations available"))

#         # Report Agent
#         with st.spinner("📄 Generating final report..."):
#             report_res = await call_mcp_agent(
#                 "http://localhost:9005/mcp",
#                 "generate_report",
#                 {
#                     "course_name": course_name,
#                     "feedback_summary": feedback_res.get("summary", ""),
#                     "performance_summary": perf_res.get("summary", ""),
#                     "trend_summary": trend_res.get("summary", ""),
#                     "recommendations": rec_res.get("curriculum_recommendations", "")
#                 }
#             )
#             logger.info(f"Report Agent Response: {report_res}")
#             if report_res.get("error"):
#                 st.error(f"Report Agent error: {report_res.get('error')}")
#                 st.stop()
#             st.success("✅ Report generated successfully!")
#             pdf_data = report_res.get("pdf_data")
#             if pdf_data:
#                 # Decode base64-encoded PDF data
#                 pdf_bytes = base64.b64decode(pdf_data)
#                 st.download_button(
#                     "📥 Download Report",
#                     pdf_bytes,
#                     file_name="final_report.pdf",
#                     mime="application/pdf"
#                 )
#             else:
#                 st.error("No PDF data returned by the server.")

#     # Run the async function in the event loop
#     try:
#         asyncio.run(run_agent_calls())
#     except Exception as e:
#         st.error(f"Analysis failed: {str(e)}")
#         logger.error(f"💥 Analysis failed: {str(e)}")
#         st.stop()

import base64
import streamlit as st
import asyncio
from utils.mcp_client import call_mcp_agent
import os
import shutil
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

st.set_page_config(page_title="AI Curriculum Intelligence", page_icon="🤖", layout="wide")

st.title("🎓 AI Curriculum Intelligence System")
st.markdown("An interactive AI-driven platform to analyze student feedback, performance, and industry alignment using multi-agent MCP servers.")

# --- File Upload UI ---
st.sidebar.header("📂 Upload Course Data")
course_name = st.sidebar.text_input("Course Name", "machine learning")

feedback_file = st.sidebar.file_uploader("Upload Feedback CSV", type=["csv"])
performance_file = st.sidebar.file_uploader("Upload Performance CSV", type=["csv"])
curriculum_files = st.sidebar.file_uploader(
    "Upload Curriculum Files (PDF/PPTX)", 
    type=["pdf", "pptx", "ppt"], 
    accept_multiple_files=True,
    help="Upload one or more PDF or PPTX files for the curriculum."
)
job_trend_csv = st.sidebar.file_uploader("Upload Job Trends CSV", type=["csv"], help="Required: Upload custom job trends.")

if st.sidebar.button("🚀 Run Analysis"):
    if not all([feedback_file, performance_file, curriculum_files, job_trend_csv]):
        st.error("Please upload all required files: Feedback CSV, Performance CSV, at least one Curriculum file (PDF/PPTX), and Job Trends CSV.")
        st.stop()

    # Clean up and create temp and results directories with absolute paths
    temp_dir = Path("temp_uploads").resolve()
    results_dir = Path("results").resolve()
    shutil.rmtree(temp_dir, ignore_errors=True)
    shutil.rmtree(results_dir, ignore_errors=True)
    temp_dir.mkdir(exist_ok=True)
    results_dir.mkdir(exist_ok=True)

    # Save uploads temporarily with absolute paths
    feedback_path = temp_dir / f"{course_name}_feedback.csv"
    performance_path = temp_dir / f"{course_name}_performance.csv"
    job_trend_path = temp_dir / f"{course_name}_job_trends.csv"
    curriculum_paths = []

    # Validate and save files
    for file_path, uploaded_file in [
        (feedback_path, feedback_file),
        (performance_path, performance_file),
        (job_trend_path, job_trend_csv)
    ]:
        if uploaded_file:
            try:
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.read())
                logger.info(f"Saved {file_path}")
                if not file_path.is_file():
                    raise RuntimeError(f"File not found after saving: {file_path}")
            except Exception as e:
                st.error(f"Failed to save {file_path.name}: {str(e)}")
                st.stop()
        else:
            st.error(f"Upload failed for {file_path.name}")
            st.stop()

    # Save multiple curriculum files
    for idx, curriculum_file in enumerate(curriculum_files, 1):
        ext = os.path.splitext(curriculum_file.name)[1].lower()
        if ext not in [".pdf", ".pptx", ".ppt"]:
            st.error(f"Unsupported file type for {curriculum_file.name}. Please upload PDF or PPTX files.")
            st.stop()
        curriculum_path = temp_dir / f"{course_name}_curriculum_{idx}{ext}"
        try:
            with open(curriculum_path, "wb") as f:
                f.write(curriculum_file.read())
            logger.info(f"Saved {curriculum_path}")
            if not curriculum_path.is_file():
                raise RuntimeError(f"File not found after saving: {curriculum_path}")
            curriculum_paths.append(str(curriculum_path))
        except Exception as e:
            st.error(f"Failed to save {curriculum_path.name}: {str(e)}")
            st.stop()

    if not curriculum_paths:
        st.error("No valid curriculum files uploaded.")
        st.stop()

    # --- Stream the "agentic" process visually ---
    st.subheader("🧠 Agentic Workflow Progress")

    # Define async helper function
    async def run_agent_calls():
        # Calling Feedback Agent
        with st.spinner("🗣️ Feedback Agent analyzing student sentiments..."):
            feedback_res = await call_mcp_agent(
                "http://localhost:9001/mcp",
                "analyze_feedback",
                {"course_name": course_name, "file_path": str(feedback_path), "output_path": str(results_dir / "feedback_out.csv")}
            )
            logger.info(f"Feedback Agent Response: {feedback_res}")
            if feedback_res.get("error"):
                st.error(f"Feedback Agent error: {feedback_res.get('error')}")
                st.stop()
            st.success("✅ Feedback analysis complete!")
            st.markdown(feedback_res.get("summary", "No summary available"))

        # Performance Agent
        with st.spinner("📊 Performance Agent evaluating academic data..."):
            perf_res = await call_mcp_agent(
                "http://localhost:9002/mcp",
                "evaluate_performance",
                {"course_name": course_name, "file_path": str(performance_path), "output_path": str(results_dir / "perf_out.csv")}
            )
            logger.info(f"Performance Agent Response: {perf_res}")
            if perf_res.get("error"):
                st.error(f"Performance Agent error: {perf_res.get('error')}")
                st.stop()
            st.success("✅ Performance analysis complete!")
            st.markdown(perf_res.get("summary", "No summary available"))

        # Trend Agent
        with st.spinner("💼 Trend Agent identifying industry-relevant skills..."):
            trend_res = await call_mcp_agent(
                "http://localhost:9003/mcp",
                "analyze_job_trends",
                {"course_name": course_name, "file_path": str(job_trend_path), "output_path": str(results_dir / "trends_out.csv")}
            )
            logger.info(f"Trend Agent Response: {trend_res}")
            if trend_res.get("error"):
                st.error(f"Trend Agent error: {trend_res.get('error')}")
                st.stop()
            st.success("✅ Job trend analysis complete!")
            st.markdown(trend_res.get("summary", "No summary available"))

        # Recommender Agent
        with st.spinner("🧩 Recommender Agent generating curriculum updates..."):
            rec_res = await call_mcp_agent(
                "http://localhost:9004/mcp",
                "recommend_curriculum_updates",
                {
                    "course_name": course_name,
                    "curriculum_paths": curriculum_paths,
                    "feedback_summary": feedback_res.get("summary", ""),
                    "performance_summary": perf_res.get("summary", ""),
                    "trend_summary": trend_res.get("summary", ""),
                    "output_path": str(results_dir / "recommendations.txt")
                }
            )
            logger.info(f"Recommender Agent Response: {rec_res}")
            if rec_res.get("error"):
                st.error(f"Recommender Agent error: {rec_res.get('error')}")
                st.stop()
            st.success("✅ Curriculum recommendations ready!")
            st.markdown("### ✨ Recommended Updates")
            st.info(rec_res.get("curriculum_recommendations", "No recommendations available"))

        # Report Agent
        with st.spinner("📄 Generating final report..."):
            report_res = await call_mcp_agent(
                "http://localhost:9005/mcp",
                "generate_report",
                {
                    "course_name": course_name,
                    "feedback_summary": feedback_res.get("summary", ""),
                    "performance_summary": perf_res.get("summary", ""),
                    "trend_summary": trend_res.get("summary", ""),
                    "recommendations": rec_res.get("curriculum_recommendations", "")
                }
            )
            logger.info(f"Report Agent Response: {report_res}")
            if report_res.get("error"):
                st.error(f"Report Agent error: {report_res.get('error')}")
                st.stop()
            st.success("✅ Report generated successfully!")
            pdf_data = report_res.get("pdf_data")
            if pdf_data:
                # Decode base64-encoded PDF data
                pdf_bytes = base64.b64decode(pdf_data)
                st.download_button(
                    "📥 Download Report",
                    pdf_bytes,
                    file_name="final_report.pdf",
                    mime="application/pdf"
                )
            else:
                st.error("No PDF data returned by the server.")

    # Run the async function in the event loop
    try:
        asyncio.run(run_agent_calls())
    except Exception as e:
        st.error(f"Analysis failed: {str(e)}")
        logger.error(f"💥 Analysis failed: {str(e)}")
        st.stop()