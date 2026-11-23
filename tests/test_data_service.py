
from app.services.data_service import (
    load_alerts,
    load_performance_stats,
    get_available_zones,
    get_performance_by_zone,
)


def main():
    alerts = load_alerts()
    performance = load_performance_stats()
    zones = get_available_zones()

    print("ALERT COUNT:", len(alerts))
    print("PERFORMANCE COUNT:", len(performance))
    print("AVAILABLE ZONES:", zones)

    print(
        "SHIVAMOGGA RECORDS:",
        len(get_performance_by_zone("Shivamogga Zone"))
    )

    print(
        "MUMBAI RECORDS:",
        len(get_performance_by_zone("Mumbai"))
    )


if __name__ == "__main__":
    main()
