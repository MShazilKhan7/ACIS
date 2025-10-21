from mcp import Client

def run_pipeline(course_name):
    feedback_client = Client("http://localhost:9001")
    perf_client = Client("http://localhost:9002")
    trend_client = Client("http://localhost:9003")
    rec_client = Client("http://localhost:9004")
    report_client = Client("http://localhost:9005")

    # Paths
    feedback_file = f"data/feedback/{course_name}_feedback.csv"
    performance_file = f"data/performance/{course_name}_scores.csv"
    job_file = "data/job_trends/job_market_trends.csv"
    curriculum_pdf = f"data/curriculum/{course_name}.pdf"
    output_pdf = f"results/{course_name}_final_report.pdf"

    feedback_res = feedback_client.call("analyze_feedback", {
        "course_name": course_name,
        "file_path": feedback_file,
        "output_path": f"results/{course_name}_feedback.csv"
    })
    performance_res = perf_client.call("evaluate_performance", {
        "course_name": course_name,
        "file_path": performance_file,
        "output_path": f"results/{course_name}_performance.csv"
    })
    trend_res = trend_client.call("analyze_job_trends", {
        "course_name": course_name,
        "file_path": job_file,
        "output_path": f"results/{course_name}_trends.csv"
    })
    rec_res = rec_client.call("recommend_curriculum_updates", {
        "course_name": course_name,
        "curriculum_path": curriculum_pdf,
        "feedback_summary": feedback_res["summary"],
        "performance_summary": performance_res["summary"],
        "trend_summary": trend_res["summary"]
    })
    report_res = report_client.call("generate_report", {
        "course_name": course_name,
        "feedback_summary": feedback_res["summary"],
        "performance_summary": performance_res["summary"],
        "trend_summary": trend_res["summary"],
        "recommendations": rec_res["curriculum_recommendations"],
        "output_pdf": output_pdf
    })

    print(report_res)

if __name__ == "__main__":
    run_pipeline("machine_learning")
