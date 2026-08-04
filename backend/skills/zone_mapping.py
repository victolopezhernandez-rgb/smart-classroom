def get_zone(x: float, y: float) -> str:
    """
    Maps a floor coordinate (x, y) to a classroom zone.

    Zone layout:
      Zone A: x ∈ [0,5)  y ∈ [0,4)   Front-Left
      Zone B: x ∈ [5,10] y ∈ [0,4)   Front-Right
      Zone C: x ∈ [0,5)  y ∈ [4,8]   Back-Left
      Zone D: x ∈ [5,10] y ∈ [4,8]   Back-Right
    """
    if x < 5:
        return "zone_A" if y < 4 else "zone_C"
    else:
        return "zone_B" if y < 4 else "zone_D"


def get_zone_bounds(zone: str) -> dict:
    """Returns the bounding box of a zone (used by 3D renderer)."""
    bounds = {
        "zone_A": {"x_min": 0, "x_max": 5, "y_min": 0, "y_max": 4},
        "zone_B": {"x_min": 5, "x_max": 10, "y_min": 0, "y_max": 4},
        "zone_C": {"x_min": 0, "x_max": 5, "y_min": 4, "y_max": 8},
        "zone_D": {"x_min": 5, "x_max": 10, "y_min": 4, "y_max": 8},
    }
    return bounds.get(zone, {})


def get_zone_center(zone: str) -> tuple:
    """Returns the center (x, y) of a zone."""
    centers = {
        "zone_A": (2.5, 2.0),
        "zone_B": (7.5, 2.0),
        "zone_C": (2.5, 6.0),
        "zone_D": (7.5, 6.0),
    }
    return centers.get(zone, (5.0, 4.0))


def get_light_positions(zone: str) -> list:
    """Returns the (x, y) positions of the 2 light fixtures in each zone."""
    lights = {
        "zone_A": [(1.5, 1.5), (3.5, 2.5)],
        "zone_B": [(6.5, 1.5), (8.5, 2.5)],
        "zone_C": [(1.5, 5.5), (3.5, 6.5)],
        "zone_D": [(6.5, 5.5), (8.5, 6.5)],
    }
    return lights.get(zone, [])
