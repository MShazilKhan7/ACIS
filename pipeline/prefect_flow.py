from prefect import flow, task
from src_code.orchestrator.mcp_orchestrator import main as run_pipeline

@task
def run_acis_pipeline():
    run_pipeline()

@flow(name="ACIS_Agentic_Pipeline")
def acis_flow():
    run_acis_pipeline()

if __name__ == "__main__":
    acis_flow()
