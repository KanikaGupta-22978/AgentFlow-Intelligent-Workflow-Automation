
from app.services.execution_service import execute_workflow


def main():
    print("===== WF004 PERFORMANCE REPORT TEST =====")

    # Test report for all available zones
    result = execute_workflow("WF004")

    print("WORKFLOW:", result["workflow_name"])
    print("WORKFLOW ID:", result["workflow_id"])
    print("ZONE:", result["zone"])
    print("TOTAL RECORDS:", result["total_records"])
    print(
        "AVERAGE PERFORMANCE SCORE:",
        result["average_performance_score"]
    )

    print("\n===== ZONE-SPECIFIC TEST =====")

    zone_result = execute_workflow(
        "WF004",
        {"zone": "Shivamogga Zone"},
    )

    print("ZONE:", zone_result["zone"])
    print("TOTAL RECORDS:", zone_result["total_records"])
    print(
        "AVERAGE PERFORMANCE SCORE:",
        zone_result["average_performance_score"]
    )


if __name__ == "__main__":
    main()
