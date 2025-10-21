from mcp.server.fastmcp import FastMCP
import os
import logging
import asyncio
import aiofiles
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import PyPDFLoader, UnstructuredPowerPointLoader
from langchain_core.prompts import ChatPromptTemplate
from pathlib import Path
import re
import socket

# ============================================================
# 🚀 Setup
# ============================================================

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("recommender_agent")

# Validate environment variables (only needed for Gemini LLM)
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise EnvironmentError("GOOGLE_API_KEY not found in environment variables.")

# Configuration
CONFIG = {
    "port": int(os.getenv("MCP_PORT", 9004)),
    "host": os.getenv("MCP_HOST", "localhost"),
    "llm_model": os.getenv("LLM_MODEL", "gemini-2.0-flash"),
    "llm_temperature": float(os.getenv("LLM_TEMPERATURE", 0.4)),
    "embedding_model": os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"),
    "context_limit": int(os.getenv("CONTEXT_LIMIT", 15000)),
    "vectorstore_cache_dir": os.getenv("VECTORSTORE_CACHE_DIR", "./vectorstore_cache"),
}

# Check if port is available
def check_port(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex((host, port)) != 0

if not check_port(CONFIG["host"], CONFIG["port"]):
    logger.error(f"Port {CONFIG['port']} is already in use. Please free the port or choose another.")
    raise SystemExit(1)

server = FastMCP(name="recommender_agent")
server.settings.port = CONFIG["port"]
server.settings.host = CONFIG["host"]

# ============================================================
# 🛠️ Utility Functions
# ============================================================

async def load_curriculum_file(path: str) -> list:
    """Load a single curriculum file (PDF or PPTX) asynchronously."""
    try:
        path = Path(path).resolve()  # Sanitize path
        if not path.is_file():
            raise FileNotFoundError(f"File not found: {path}")
        ext = path.suffix.lower()
        if ext == ".pdf":
            loader = PyPDFLoader(str(path))
        elif ext in [".pptx", ".ppt"]:
            loader = UnstructuredPowerPointLoader(str(path))
        else:
            raise ValueError(f"Unsupported file format: {path}")
        documents = await asyncio.to_thread(loader.load)
        logger.info(f"✅ Loaded {len(documents)} pages/slides from {path}")
        return documents
    except Exception as e:
        logger.error(f"💥 Failed to load {path}: {str(e)}")
        raise

async def load_curriculum_files(curriculum_paths: list[str]) -> list:
    """Load multiple curriculum files concurrently."""
    tasks = [load_curriculum_file(path) for path in curriculum_paths]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    documents = []
    for result in results:
        if isinstance(result, Exception):
            logger.error(f"💥 Error in file loading: {str(result)}")
            continue
        documents.extend(result)
    return documents

def validate_inputs(course_name: str, feedback_summary: str, performance_summary: str, trend_summary: str, output_path: str) -> None:
    """Validate input parameters."""
    if not all(isinstance(x, str) and x.strip() for x in [course_name, feedback_summary, performance_summary, trend_summary]):
        raise ValueError("All input summaries must be non-empty strings.")
    if not re.match(r'^[\w\s\-]+$', course_name):
        raise ValueError("Course name contains invalid characters.")
    if not output_path.endswith(".txt"):
        raise ValueError("Output path must be a .txt file.")
    output_path = Path(output_path).resolve()
    if not output_path.parent.exists():
        raise ValueError(f"Output directory does not exist: {output_path.parent}")

# ============================================================
# 🧠 Tool Definition
# ============================================================

@server.tool()
async def recommend_curriculum_updates(
    course_name: str,
    curriculum_paths: list[str],
    feedback_summary: str,
    performance_summary: str,
    trend_summary: str,
    output_path: str = "recommendations.txt"
) -> dict[str, str]:
    """
    Generate curriculum update recommendations using Gemini and RAG context from PDFs/PPTs.
    
    Args:
        course_name: Name of the course.
        curriculum_paths: List of paths to curriculum files (PDF/PPTX).
        feedback_summary: Summary of student feedback.
        performance_summary: Summary of student performance.
        trend_summary: Summary of industry trends.
        output_path: Path to save recommendations (default: recommendations.txt).
    
    Returns:
        Dict containing recommendations or error message.
    """
    try:
        # ---------------------------------------
        # 1️⃣ Validate Inputs
        # ---------------------------------------
        validate_inputs(course_name, feedback_summary, performance_summary, trend_summary, output_path)
        logger.info(f"Starting recommendation process for course: {course_name}")

        # ---------------------------------------
        # 2️⃣ Load Files Asynchronously
        # ---------------------------------------
        curriculum_documents = await load_curriculum_files(curriculum_paths)
        if not curriculum_documents:
            raise ValueError("No content loaded from curriculum files.")

        # ---------------------------------------
        # 3️⃣ Build or Load Vector Store (RAG)
        # ---------------------------------------
        cache_path = Path(CONFIG["vectorstore_cache_dir"]) / f"{course_name}_faiss_index"
        embeddings = HuggingFaceEmbeddings(model_name=CONFIG["embedding_model"])
        
        if cache_path.exists():
            logger.info(f"Loading cached vector store from {cache_path}")
            vectorstore = FAISS.load_local(str(cache_path), embeddings, allow_dangerous_deserialization=True)
        else:
            logger.info("Building new vector store...")
            vectorstore = FAISS.from_documents(curriculum_documents, embeddings)
            vectorstore.save_local(str(cache_path))
            logger.info(f"Saved vector store to {cache_path}")

        retriever = vectorstore.as_retriever(search_kwargs={"k": 5})

        # ---------------------------------------
        # 4️⃣ Create Query and Retrieve Context
        # ---------------------------------------
        query = f"""
        Course: {course_name}
        Feedback Insights: {feedback_summary}
        Performance Insights: {performance_summary}
        Job Market Insights: {trend_summary}

        Based on these insights, identify what content in the current curriculum should be
        improved, expanded, or newly added to align with student needs and industry demand.
        """

        try:
            retrieved_docs = retriever.invoke(query)
        except Exception as e:
            logger.error(f"💥 Retriever error: {str(e)}")
            return {"error": f"Retriever error: {str(e)}"}
        context = "\n".join([d.page_content for d in retrieved_docs])[:CONFIG["context_limit"]]
        logger.info(f"Retrieved {len(retrieved_docs)} documents for context (truncated to {len(context)} chars)")

        # ---------------------------------------
        # 5️⃣ Gemini LLM Reasoning
        # ---------------------------------------
        llm = ChatGoogleGenerativeAI(
            model=CONFIG["llm_model"],
            temperature=CONFIG["llm_temperature"],
            google_api_key=GOOGLE_API_KEY
        )

        prompt = ChatPromptTemplate.from_template("""
        You are an AI Curriculum Development Specialist.

        Course: "{course_name}"

        ---- Context from Curriculum ----
        {context}

        ---- Integrated Insights ----
        Student Feedback Summary:
        {feedback_summary}

        Student Performance Summary:
        {performance_summary}

        Industry Trend Summary:
        {trend_summary}

        ---- Tasks ----
        1️⃣ Suggest 3–5 detailed curriculum improvements (e.g., new topics, projects, or tools).
        2️⃣ Highlight missing modern skills or industry-relevant modules.
        3️⃣ Recommend case studies, hands-on labs, or emerging technologies to include.
        4️⃣ Provide a concise 4-line executive summary for educators.

        Ensure the output is structured with clear headings and actionable details.
        """)

        formatted_prompt = prompt.format(
            course_name=course_name,
            context=context,
            feedback_summary=feedback_summary,
            performance_summary=performance_summary,
            trend_summary=trend_summary
        )

        logger.info("🤖 Sending recommendation request to Gemini...")
        try:
            ai_response = llm.invoke(formatted_prompt)  # Removed 'await' since invoke is synchronous
            ai_summary = ai_response.content
        except Exception as e:
            logger.error(f"💥 Gemini API error: {str(e)}")
            return {"error": f"Gemini API error: {str(e)}"}

        # ---------------------------------------
        # 6️⃣ Save and Return
        # ---------------------------------------
        output_path = Path(output_path).resolve()
        os.makedirs(output_path.parent, exist_ok=True)
        async with aiofiles.open(output_path, "w", encoding="utf-8") as f:
            await f.write(ai_summary)

        logger.info(f"✅ Curriculum recommendations saved to {output_path}")
        return {"curriculum_recommendations": ai_summary}

    except FileNotFoundError as e:
        logger.error(f"💥 File error: {str(e)}")
        return {"error": f"File error: {str(e)}"}
    except ValueError as e:
        logger.error(f"💥 Input validation error: {str(e)}")
        return {"error": f"Input validation error: {str(e)}"}
    except ConnectionResetError as e:
        logger.warning(f"💥 Connection reset by client: {str(e)}")
        return {"error": f"Connection reset by client: {str(e)}"}
    except Exception as e:
        logger.error(f"💥 Unexpected error: {str(e)}")
        return {"error": f"Unexpected error: {str(e)}"}

# ============================================================
# 🚀 Run MCP Server
# ============================================================

if __name__ == "__main__":
    logger.info("🚀 Starting Recommender MCP Server (Gemini + RAG)...")
    server.run(transport="streamable-http")