import datetime
from mcp.server.fastmcp import FastMCP
import os
import csv
import logging
import pandas as pd
import numpy as np
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from langchain_community.chat_models import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
import json
from mcp.types import Resource, Tool, TextContent

import langchain
langchain.verbose = True
langchain.debug = True


os.environ["GOOGLE_API_KEY"] = ""

# -------------------------------
# 🧩 Setup
# -------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

server = FastMCP(name="feedback_agent")
server.settings.port = 9001
server.settings.host = "localhost"

# Initialize sentiment analyzer
sid = SentimentIntensityAnalyzer()

# -------------------------------
# 🧠 MCP Tool
# -------------------------------
@server.tool()
def analyze_feedback(course_name: str, file_path: str, output_path: str) -> dict[str, str]:
    """
    Analyze student feedback quantitatively and qualitatively using both
    statistical metrics and an LLM (OpenAI GPT via LangChain).
    """
    try:
        logger.info(f"📂 Loading feedback data from: {file_path}")
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        # Load CSV
        df = pd.read_csv(file_path)
        expected_cols = {
            "student_id",
            "course",
            "course_content",
            "lecture_delivery",
            "teaching_materials",
            "practicals",
            "assessment",
            "text_feedback",
        }

        if set(df.columns) != expected_cols:
            raise ValueError(f"Invalid CSV format. Expected columns: {expected_cols}")

        # Filter for the specific course
        # df = df[df["course"].str.lower() == course_name.lower()]
        logger.info(f"✅ Loaded {len(df)} rows for course '{course_name}'.")

        # -------------------------------
        # 1️⃣ Quantitative Analysis
        # -------------------------------
        rating_cols = [
            "course_content",
            "lecture_delivery",
            "teaching_materials",
            "practicals",
            "assessment",
        ]

        ratings = {col: df[col].astype(float).tolist() for col in rating_cols}

        avg_rating = {k: np.mean(v) if v else 0 for k, v in ratings.items()}
        std_dev = {k: np.std(v) if v else 0 for k, v in ratings.items()}
        weak_areas = [k for k, v in avg_rating.items() if v < 3]
        strong_areas = [k for k, v in avg_rating.items() if v >= 4]

        logger.info(f"Average Ratings: {avg_rating}")
        logger.info(f"Rating StdDev: {std_dev}")
        logger.info(f"Weak Areas: {weak_areas}")
        logger.info(f"Strong Areas: {strong_areas}")

        logger.info(f"📊 Quantitative summary computed. Weak: {weak_areas}, Strong: {strong_areas}")

        # -------------------------------
        # 2️⃣ Sentiment Analysis
        # -------------------------------
        df["sentiment_score"] = df["text_feedback"].apply(lambda t: sid.polarity_scores(str(t))["compound"])
        logger.info(f"Sentiment Scores: {df['sentiment_score'].head()}")

        avg_sentiment = df["sentiment_score"].mean()

        # Categorize feedback based on sentiment
        df["sentiment_label"] = df["sentiment_score"].apply(
            lambda x: "positive" if x > 0.2 else ("negative" if x < -0.2 else "neutral")
        )

        positive_feedback = df[df["sentiment_label"] == "positive"]["text_feedback"].tolist()
        negative_feedback = df[df["sentiment_label"] == "negative"]["text_feedback"].tolist()

        logger.info(
            f"🧠 Sentiment analysis complete. Avg Sentiment: {avg_sentiment:.2f} "
            f"(Pos: {len(positive_feedback)}, Neg: {len(negative_feedback)})"
        )

        # -------------------------------
        # 3️⃣ LLM Contextual Summary (LangChain + GPT)
        # -------------------------------
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0.4,
            google_api_key=os.getenv("GOOGLE_API_KEY"),
        )
        prompt = ChatPromptTemplate.from_template("""
        You are an educational data analyst AI.
        You have analyzed student feedback for the course "{course_name}".
        
        Quantitative Summary:
        Average Ratings: {avg_rating}
        Rating StdDev: {std_dev}
        Strong Areas: {strong_areas}
        Weak Areas: {weak_areas}
        Average Sentiment: {avg_sentiment:.2f}
        
        Positive Feedback Examples:
        {positive_examples}
        
        Negative Feedback Examples:
        {negative_examples}

        Tasks:
        1️⃣ Summarize major positive themes students mentioned.
        2️⃣ Identify key areas needing improvement.
        3️⃣ Suggest 3 actionable curriculum or teaching updates.
        4️⃣ Give a 4-line executive summary for faculty.
        """)

        formatted_prompt = prompt.format(
            course_name=course_name,
            avg_rating=avg_rating,
            std_dev=std_dev,
            strong_areas=strong_areas,
            weak_areas=weak_areas,
            avg_sentiment=avg_sentiment,
            positive_examples="\n".join(positive_feedback[:30]),
            negative_examples="\n".join(negative_feedback[:30]),
        )

        logger.info("🤖 Sending summary request to LLM...")
        llm_response = llm.invoke(formatted_prompt)
        logger.info(f"LLM Response: {llm_response}")
        ai_summary = llm_response.content

        # -------------------------------
        # 4️⃣ Final Summary + Save Output
        # -------------------------------
        # Prepare the formatted strings for average ratings and standard deviation outside the f-string
        avg_rating_str = '\n'.join([f'  - {key.replace("_", " ").title()}: {value:.2f}' for key, value in avg_rating.items()])
        std_dev_str = '\n'.join([f'  - {key.replace("_", " ").title()}: {value:.3f}' for key, value in std_dev.items()])
        strong_areas_str = ', '.join(strong_areas) if strong_areas else 'None'
        weak_areas_str = ', '.join(weak_areas) if weak_areas else 'None'

        full_summary = f"""# Feedback Report for {course_name}\n## 📊 Quantitative Insights\n### **Average Ratings**\n- **Course Content:** {avg_rating['course_content']:.2f}\n- **Lecture Delivery:** {avg_rating['lecture_delivery']:.2f}\n- **Teaching Materials:** {avg_rating['teaching_materials']:.2f}\n- **Practicals:** {avg_rating['practicals']:.2f}\n- **Assessment:** {avg_rating['assessment']:.2f}\n### **Standard Deviation**\n- **Course Content:** {std_dev['course_content']:.3f}\n- **Lecture Delivery:** {std_dev['lecture_delivery']:.3f}\n- **Teaching Materials:** {std_dev['teaching_materials']:.3f}\n- **Practicals:** {std_dev['practicals']:.3f}\n- **Assessment:** {std_dev['assessment']:.3f}\n**Strong Areas:** {strong_areas_str}\n**Weak Areas:** {weak_areas_str}\n---\n## 🧠 Sentiment Analysis\n- **Average Sentiment:** {avg_sentiment:.2f}\n- **Positive Feedback Count:** {len(positive_feedback)}\n- **Negative Feedback Count:** {len(negative_feedback)}\n---\n- {ai_summary}"""




        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(full_summary)

        logger.info("✅ Feedback analysis + LLM summary saved successfully.")

        
        return {
            "summary": full_summary,
        }

    except Exception as e:
        logger.error(f"💥 Error in analyze_feedback: {str(e)}")
        return {"error": str(e)}


if __name__ == "__main__":
    logger.info("🚀 Starting enhanced Feedback MCP server...")
    server.run(transport="streamable-http")