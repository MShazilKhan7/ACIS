from mcp.server.fastmcp import FastMCP
import asyncio
from fpdf import FPDF, HTMLMixin
import traceback
import base64
import platform
import markdown
from fpdf.html import HTML2FPDF
import html

# Use SelectorEventLoop on Windows to avoid ConnectionResetError
if platform.system() == "Windows":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

server = FastMCP(name="report_agent")
server.settings.port = 9005
server.settings.host = "localhost"


class PDF(FPDF, HTMLMixin):
    pass


class PDF(FPDF, HTMLMixin):
    pass
HTML2FPDF.unescape = staticmethod(html.unescape)

def sanitize_text(text):
    """Replace non-latin-1 characters with a placeholder or remove them."""
    return text.encode('latin-1', errors='replace').decode('latin-1')


def markdown_to_html(md_text: str) -> str:
    """Convert Markdown text to basic HTML."""
    html = markdown.markdown(md_text, extensions=['fenced_code', 'tables'])
    return html


def create_pdf_in_memory(course_name, feedback_summary, performance_summary, trend_summary, recommendations):
    """Generate PDF in memory from Markdown-formatted sections and return as bytes."""
    print("[create_pdf_in_memory] Starting PDF generation...")
    try:
        pdf = PDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)

        # Convert and sanitize all sections
        course_name = sanitize_text(course_name)
        feedback_html = markdown_to_html(sanitize_text(feedback_summary))
        performance_html = markdown_to_html(sanitize_text(performance_summary))
        trend_html = markdown_to_html(sanitize_text(sanitize_text(trend_summary)))
        rec_html = markdown_to_html(sanitize_text(recommendations))

        # Add title
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, f"Curriculum Intelligence Report - {course_name}", ln=True, align="C")
        pdf.ln(10)

        # Write markdown-rendered sections
        pdf.write_html(f"<h2>Feedback Summary</h2>{feedback_html}")
        pdf.ln(5)
        pdf.write_html(f"<h2>Performance Summary</h2>{performance_html}")
        pdf.ln(5)
        pdf.write_html(f"<h2>Job Market Trends</h2>{trend_html}")
        pdf.ln(5)
        pdf.write_html(f"<h2>Recommended Curriculum Updates</h2>{rec_html}")

        pdf_bytes = pdf.output(dest="S").encode("latin-1")
        print("[create_pdf_in_memory] PDF generation completed successfully.")
        return pdf_bytes
    except Exception as e:
        print(f"[create_pdf_in_memory] Error while generating PDF: {e}")
        traceback.print_exc()
        raise


@server.tool()
async def generate_report(course_name: str, feedback_summary: str, performance_summary: str,
                         trend_summary: str, recommendations: str) -> dict[str, str]:
    """Asynchronous FastMCP tool to generate Markdown-rendered PDF report in memory."""
    print("[generate_report] Tool invoked.")
    print(f"[generate_report] course_name: {course_name}")

    try:
        print("[generate_report] Starting background PDF generation...")
        pdf_bytes = await asyncio.to_thread(
            create_pdf_in_memory, course_name, feedback_summary,
            performance_summary, trend_summary, recommendations
        )

        pdf_base64 = base64.b64encode(pdf_bytes).decode("utf-8")
        print("[generate_report] Report generated successfully.")
        return {
            "summary": "✅ Markdown-rendered report generated successfully",
            "pdf_data": pdf_base64
        }
    except Exception as e:
        print(f"[generate_report] ❌ Error: {e}")
        traceback.print_exc()
        return {"error": str(e)}


if __name__ == "__main__":
    server.run(transport="streamable-http")
