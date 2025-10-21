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

load_dotenv()  # load GOOGLE_API_KEY from .env
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("performance_agent")

# Initialize MCP Server
server = FastMCP(name="performance_agent")
server.settings.port = 9002
server.settings.host = "localhost"

# ============================================
# 🧠 Tool Definition
# ============================================
@server.tool()
def evaluate_performance(course_name: str, file_path: str, output_path: str) -> dict[str, float | str]:
    """
    Analyze student performance in a given course using descriptive statistics and
    Google Gemini for qualitative interpretation.
    """
    try:
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        df = pd.read_csv(file_path)
        required_columns = [
            "student_id",
            "student_name",
            "course",
            "marks_obtained",
            "total_marks",
            "grade",
            "grade_points",
            "attendance_percentage",
            "semester"
        ]
        missing = [c for c in required_columns if c not in df.columns]
        if missing:
            raise ValueError(f"Missing columns in dataset: {', '.join(missing)}")

        # # Filter for the given course
        # df = df[df["course"].str.lower() == course_name.lower()]
        # logger.info(f"✅ Loaded {len(df)} records for course: {course_name}")

        # ============================================
        # 📊 Quantitative Analysis
        # ============================================
        df["percentage"] = (df["marks_obtained"] / df["total_marks"]) * 100

        avg_marks = df["marks_obtained"].mean()
        avg_gpa = df["grade_points"].mean()
        avg_attendance = df["attendance_percentage"].mean()
        avg_percentage = df["percentage"].mean()

        # Grade distribution
        grade_counts = df["grade"].value_counts().to_dict()

        # Correlations (attendance vs marks, etc.)
        corr_attendance_marks = df["attendance_percentage"].corr(df["percentage"])
        corr_gpa_marks = df["grade_points"].corr(df["percentage"])

        # Identify outliers or top performers
        top_students = df.nlargest(3, "percentage")[["student_name", "percentage"]].to_dict(orient="records")
        low_students = df.nsmallest(3, "percentage")[["student_name", "percentage"]].to_dict(orient="records")

        # ============================================
        # 🧠 Gemini AI-Based Qualitative Analysis
        # ============================================
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0.4,
            google_api_key=os.getenv("GOOGLE_API_KEY"),
        )

        prompt = ChatPromptTemplate.from_template("""
        You are an educational performance analyst AI using Google Gemini.
        Analyze the following quantitative data for the course "{course_name}".

        Average Marks: {avg_marks:.2f}
        Average GPA: {avg_gpa:.2f}
        Average Attendance: {avg_attendance:.2f}%
        Average Percentage: {avg_percentage:.2f}%
        Correlation (Attendance vs Marks): {corr_attendance_marks:.2f}
        Correlation (GPA vs Marks): {corr_gpa_marks:.2f}
        Grade Distribution: {grade_counts}

        Top Performing Students: {top_students}
        Low Performing Students: {low_students}

        Tasks:
        1️⃣ Identify learning and performance trends.
        2️⃣ Highlight possible causes of low performance (e.g., attendance, assessment difficulty).
        3️⃣ Suggest 3 actionable recommendations to improve outcomes in {course_name}.
        4️⃣ Provide a short executive summary for educators.
        """)

        formatted_prompt = prompt.format(
            course_name=course_name,
            avg_marks=avg_marks,
            avg_gpa=avg_gpa,
            avg_attendance=avg_attendance,
            avg_percentage=avg_percentage,
            corr_attendance_marks=corr_attendance_marks,
            corr_gpa_marks=corr_gpa_marks,
            grade_counts=grade_counts,
            top_students=top_students,
            low_students=low_students
        )

        logger.info("🤖 Sending analysis to Gemini...")
        ai_response = llm.invoke(formatted_prompt)
        ai_summary = ai_response.content

        # ============================================
        # 🗂️ Save Report
        # ============================================
        
        # Prepare the formatted strings for grade_counts, top_students, and low_students outside the f-string
        grade_dist_str = '\n'.join([f'  - {grade}: {count}' for grade, count in grade_counts.items()])
        top_performers_str = '\n'.join([f'- {student["student_name"]}: {student["percentage"]:.1f}%' for student in top_students])
        low_performers_str = '\n'.join([f'- {student["student_name"]}: {student["percentage"]:.1f}%' for student in low_students])

        report_text = f"""# Performance Report for {course_name}\n## 📊 Quantitative Summary\n- **Average Marks:** {avg_marks:.2f}\n- **GPA:** {avg_gpa:.2f}\n- **Attendance:** {avg_attendance:.2f}%\n- **Average Percentage:** {avg_percentage:.2f}%\n- **Grade Distribution:**\n{grade_dist_str}\n- **Correlation (Attendance vs Marks):** {corr_attendance_marks:.2f}\n- **Correlation (GPA vs Marks):** {corr_gpa_marks:.2f}\n---\n## 🏅 Top Performers\n{top_performers_str}\n---\n## ⚠️ Low Performers\n{low_performers_str}\n---\n## 💬 Gemini AI Summary\n{ai_summary}"""



        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(report_text)

        logger.info("✅ Performance report successfully generated and saved.")
        return {
            "summary": report_text
        }

    except Exception as e:
        logger.error(f"💥 Error in performance analysis: {str(e)}")
        return {"error": str(e)}

# ============================================
# 🚀 Run MCP Server
# ============================================
if __name__ == "__main__":
    logger.info("🚀 Starting Performance MCP Server (Gemini-powered)...")
    server.run(transport="streamable-http")
