from mcp.server.fastmcp import FastMCP
import os
import pandas as pd
import numpy as np
import logging
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

# ============================================
# 🚀 Setup
# ============================================
load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("trend_agent")

# Initialize MCP Server
server = FastMCP(name="trend_agent")
server.settings.port = 9003
server.settings.host = "localhost"

# ============================================
# 🧠 Tool Definition
# ============================================
@server.tool()
def analyze_job_trends(course_name: str, file_path: str, output_path: str) -> dict[str, str]:
    """
    Analyze job market trends related to a course using Gemini,
    """
    print("analyze_job_trends called")
    try:
        # ===============================
        # 🧾 Load Data
        # ===============================
        print("loading the data")
        print("file path:", file_path)
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        df = pd.read_csv(file_path)
        required_cols = [
            "job_title",
            "required_skills",
            "salary_usd",
            "experience_level",
            "industry",
            "salary_bucket"
        ]
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            raise ValueError(f"Missing columns in dataset: {', '.join(missing)}")

        # ===============================
        # 🔍 Preprocess
        # ===============================
        df["job_title"] = df["job_title"].astype(str).str.lower()
        df["required_skills"] = df["required_skills"].astype(str).str.lower()
        df["industry"] = df["industry"].astype(str)
        df["salary_usd"] = pd.to_numeric(df["salary_usd"], errors="coerce")

        course_keywords = course_name.lower().split()
        df_relevant = df[
            df["job_title"].apply(lambda t: any(k in t for k in course_keywords)) |
            df["required_skills"].apply(lambda s: any(k in s for k in course_keywords))
        ]

        if df_relevant.empty:
            logger.warning(f"⚠️ No direct job matches for '{course_name}', using all data.")
            df_relevant = df.copy()

        # ===============================
        # 📊 Quantitative Analysis
        # ===============================
        avg_salary = df_relevant["salary_usd"].mean()
        salary_range = (df_relevant["salary_usd"].min(), df_relevant["salary_usd"].max())
        top_roles = df_relevant["job_title"].value_counts().head(5).index.tolist()
        top_industries = df_relevant["industry"].value_counts().head(5).index.tolist()

        # Skill frequency
        skills_series = df_relevant["required_skills"].str.split(",").explode().str.strip()
        top_skills = skills_series.value_counts().head(10).index.tolist()

        # Experience distribution
        exp_dist = df_relevant["experience_level"].value_counts(normalize=True).mul(100).round(1).to_dict()

        logger.info(f"📊 Extracted {len(top_roles)} top roles, {len(top_skills)} top skills.")


        # ===============================
        # 🧠 Gemini-Powered Industry Insights
        # ===============================
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0.3,
            google_api_key=os.getenv("GOOGLE_API_KEY"),
        )

        prompt = ChatPromptTemplate.from_template("""
        You are an AI Industry Analyst specializing in curriculum-to-job-market alignment.

        Course: "{course_name}"

        ---- Job Market Data ----
        Top Roles: {top_roles}
        Top Skills: {top_skills}
        Top Industries: {top_industries}
        Average Salary (USD): {avg_salary:.2f}
        Salary Range: {salary_range}
        Experience Level Distribution (%): {exp_dist}

        ---- Tasks ----
        1️⃣ Summarize how this course aligns with 2025 job market trends.
        2️⃣ Identify 5 new skills that should be added to this course to improve employability.
        3️⃣ Suggest 3 modern job roles graduates should target.
        4️⃣ Provide 2 actionable recommendations for educators to align course content with market demand.
        5️⃣ Conclude with a short executive summary for university administration (3–4 lines).
        """)

        formatted_prompt = prompt.format(
            course_name=course_name,
            top_roles=top_roles,
            top_skills=top_skills,
            top_industries=top_industries,
            avg_salary=avg_salary,
            salary_range=salary_range,
            exp_dist=exp_dist,
        )

        logger.info("🤖 Sending market analysis request to Gemini...")
        ai_response = llm.invoke(formatted_prompt)
        ai_summary = ai_response.content

        # ===============================
        # 🗂️ Save Report
        # ===============================
        
        # Prepare the formatted string for exp_dist outside the f-string
        exp_dist_str = '\n'.join([f'  - {key}: {value:.1f}%' for key, value in exp_dist.items()])

        report = f"""# Industry Trend Report for {course_name}\n## 📊 Quantitative Insights\n- **Top Industries:** {', '.join(top_industries)}\n- **Top Roles:** {', '.join(top_roles)}\n- **Top Skills:** {', '.join(top_skills)}\n- **Average Salary:** ${avg_salary:,.2f}\n- **Salary Range:** ${salary_range[0]:,.2f} - ${salary_range[1]:,.2f}\n- **Experience Distribution:**\n{exp_dist_str}\n---\n## 💬 Gemini AI Analysis\n{ai_summary}"""

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(report)

        logger.info("✅ Job trend analysis completed successfully.")
        return {"summary": report}

    except Exception as e:
        logger.error(f"💥 Error in trend analysis: {str(e)}")
        return {"error": str(e)}

# ============================================
# 🚀 Run MCP Server
# ============================================
if __name__ == "__main__":
    logger.info("🚀 Starting Trend MCP Server (Gemini-powered)...")
    server.run(transport="streamable-http")
