import os
import requests
import googlemaps

from src.core.logging import logger


class GoogleMapClient:
    def __init__(self):
        self.map_key = os.getenv("MAP_KEY")
        self.map_dir_url = os.getenv("MAP_DIR_URL")
        self.map_addr_url = os.getenv("MAP_ADDR_URL")
        self.map_wifi_url = os.getenv("MAP_WIFI_URL")

        if not self.map_key:
            raise ValueError("MAP_KEY is not configured")

        if not self.map_dir_url:
            raise ValueError("MAP_DIR_URL is not configured")

    def get_direction(
        self,
        origin: tuple[float, float],
        destination: tuple[float, float],
        mode: str,
        waypoints: list[tuple[float, float]] | None = None,
    ) -> dict:
        params = {
            "origin": f"{origin[0]},{origin[1]}",
            "destination": f"{destination[0]},{destination[1]}",
            "mode": mode,
            "key": self.map_key,
        }

        if waypoints:
            dedup_waypoints = []

            for waypoint in waypoints:
                if not dedup_waypoints or waypoint != dedup_waypoints[-1]:
                    dedup_waypoints.append(waypoint)

            if dedup_waypoints:
                params["waypoints"] = "|".join(
                    [f"{lat},{lng}" for lat, lng in dedup_waypoints]
                )

        try:
            response = requests.get(
                self.map_dir_url,
                params=params,
                timeout=5,
            )
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            logger.error(f"Google Direction API request failed: {e}")
            raise RuntimeError("Direction API error")

        routes = data.get("routes") or []

        if not routes:
            logger.error(f"No route found from Google Direction API: {data}")
            raise ValueError("No route found")

        route = routes[0]
        legs = route.get("legs") or []

        distance = 0
        duration = 0

        for leg in legs:
            distance += leg.get("distance", {}).get("value", 0)
            duration += leg.get("duration", {}).get("value", 0)

        overview_polyline = route.get("overview_polyline", {}).get("points")

        if not overview_polyline:
            logger.error(f"No overview polyline found: {data}")
            raise ValueError("No overview polyline found")

        direction = googlemaps.convert.decode_polyline(overview_polyline)

        return {
            "distance": distance,
            "duration": duration,
            "direction": direction,
        }

    def get_address(self, latlng: str) -> str:
        if not self.map_addr_url:
            raise ValueError("MAP_ADDR_URL is not configured")

        params = {
            "latlng": latlng,
            "key": self.map_key,
        }

        response = requests.get(
            self.map_addr_url,
            params=params,
            timeout=5,
        )
        response.raise_for_status()

        data = response.json()

        if not data.get("results"):
            raise ValueError("No address found")

        logger.debug("Get address succeed")

        return data["results"][0]["formatted_address"]

    def get_wifi_location(self, macs: str) -> dict:
        if not self.map_wifi_url:
            raise ValueError("MAP_WIFI_URL is not configured")

        ap_list = macs.split("|")
        wifi_access_points = []

        for ap in ap_list:
            parts = ap.split(",")

            if len(parts) >= 2:
                try:
                    signal_strength = int(parts[1].strip())
                except ValueError:
                    continue

                wifi_access_points.append(
                    {
                        "macAddress": parts[0].strip(),
                        "signalStrength": signal_strength,
                    }
                )

        payload = {
            "considerIp": False,
            "wifiAccessPoints": wifi_access_points,
        }

        url = f"{self.map_wifi_url}{self.map_key}"

        response = requests.post(
            url,
            json=payload,
            timeout=5,
        )
        response.raise_for_status()

        data = response.json()

        return {
            "latitude": data.get("location", {}).get("lat", 0),
            "longitude": data.get("location", {}).get("lng", 0),
            "accuracy": data.get("accuracy", 0),
        }