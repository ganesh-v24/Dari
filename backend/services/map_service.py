import math
import osmnx as ox
import networkx as nx
from geopy.geocoders import Nominatim
from loguru import logger
from pydantic import BaseModel

geolocator = Nominatim(user_agent="dari_navigation")

class ShortcutRequest(BaseModel):
    start_location: str
    end_location: str

# ── helpers ──────────────────────────────────────────────────────────────────

def get_coords(place: str):
    logger.info(f"Geocoding {place}...")
    loc = geolocator.geocode(place)
    if loc:
        return loc.latitude, loc.longitude
    return None


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return great-circle distance between two lat/lon points in km."""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# ── main routing entry ───────────────────────────────────────────────────────

def find_shortcut(start_name: str, end_name: str):
    start = get_coords(start_name)
    end = get_coords(end_name)

    if not start or not end:
        return {"error": "Could not find coordinates for one or both locations."}

    logger.info(f"Start: {start}, End: {end}")

    # Distance sanity check
    distance_km = _haversine_km(start[0], start[1], end[0], end[1])
    logger.info(f"Great-circle distance: {distance_km:.1f} km")

    MAX_WALK_KM = 50.0  # osmnx walk network is only practical below this
    if distance_km > MAX_WALK_KM:
        return {
            "error": (
                f"These locations are {distance_km:.0f} km apart — too far for a "
                f"walkable street-level route. Try two closer places within ~{MAX_WALK_KM:.0f} km."
            ),
            "start_coords": start,
            "end_coords": end,
            "distance_km": round(distance_km, 1),
        }

    # Dynamic bbox padding: larger for longer distances, capped at ~2 km
    padding_deg = min(0.02, max(0.005, distance_km * 0.0002))
    north = max(start[0], end[0]) + padding_deg
    south = min(start[0], end[0]) - padding_deg
    east = max(start[1], end[1]) + padding_deg
    west = min(start[1], end[1]) - padding_deg

    try:
        logger.info(f"Downloading walk network for bbox (padding {padding_deg:.4f}°)...")
        # osmnx 2.x expects bbox as (west, south, east, north)
        G = ox.graph_from_bbox(bbox=(west, south, east, north), network_type='walk')
    except Exception as e:
        logger.error(f"Error downloading graph: {e}")
        return {"error": f"Failed to get map data: {str(e)}"}

    logger.info("Finding nearest network nodes...")
    orig_node = ox.distance.nearest_nodes(G, X=start[1], Y=start[0])
    dest_node = ox.distance.nearest_nodes(G, X=end[1], Y=end[0])

    try:
        logger.info("Calculating shortest shortcut path...")
        route = nx.shortest_path(G, orig_node, dest_node, weight='length')
        route_coords = [[G.nodes[n]['y'], G.nodes[n]['x']] for n in route]

        return {
            "success": True,
            "start_coords": start,
            "end_coords": end,
            "route": route_coords,
            "distance_km": round(distance_km, 1),
        }
    except nx.NetworkXNoPath:
        logger.warning("No path found.")
        return {"error": "No walkable shortcut found between these locations."}
    except Exception as e:
        logger.error(f"Routing error: {e}")
        return {"error": str(e)}
