from __future__ import annotations

from dataclasses import dataclass


@dataclass
class BoundingBox:
    min_lat: float
    min_lon: float
    max_lat: float
    max_lon: float

    def contains(self, lat: float, lon: float) -> bool:
        return (
            self.min_lat <= lat <= self.max_lat
            and self.min_lon <= lon <= self.max_lon
        )


@dataclass
class GeoZone:
    name: str
    tight: BoundingBox | None = None
    wide: BoundingBox | None = None
    boxes: list[BoundingBox] | None = None  # for zones with multiple sub-boxes


class GeoRouter:
    """Routes lat/lon coordinates to a chokepoint, port cluster, or region.

    Checks tight boxes first (higher specificity), then wide boxes.
    Returns the zone name or 'unlocalized' if no match.
    """

    def __init__(self) -> None:
        self._zones = _build_zones()

    def route(self, lat: float, lon: float) -> str:
        """Return the name of the zone containing (lat, lon), or 'unlocalized'."""
        # First pass: tight boxes (most specific)
        for zone in self._zones:
            if zone.tight and zone.tight.contains(lat, lon):
                return zone.name
            if zone.boxes:
                for box in zone.boxes:
                    if box.contains(lat, lon):
                        return zone.name

        # Second pass: wide boxes
        for zone in self._zones:
            if zone.wide and zone.wide.contains(lat, lon):
                return zone.name

        return "unlocalized"

    def route_all(self, lat: float, lon: float) -> list[str]:
        """Return all zone names containing (lat, lon). Useful when zones overlap."""
        matches: list[str] = []
        for zone in self._zones:
            matched = False
            if zone.tight and zone.tight.contains(lat, lon):
                matched = True
            if not matched and zone.boxes:
                for box in zone.boxes:
                    if box.contains(lat, lon):
                        matched = True
                        break
            if not matched and zone.wide and zone.wide.contains(lat, lon):
                matched = True
            if matched:
                matches.append(zone.name)
        return matches if matches else ["unlocalized"]


def _build_zones() -> list[GeoZone]:
    """Build all chokepoint, port cluster, and regional zones."""
    zones: list[GeoZone] = []

    # ── Chokepoints ──

    zones.append(GeoZone(
        name="hormuz",
        tight=BoundingBox(26.20, 55.80, 26.80, 56.60),
        wide=BoundingBox(25.00, 54.00, 27.50, 58.00),
    ))

    zones.append(GeoZone(
        name="bab_el_mandeb",
        tight=BoundingBox(12.30, 43.10, 12.80, 43.60),
        wide=BoundingBox(11.50, 42.50, 13.50, 44.50),
    ))

    zones.append(GeoZone(
        name="suez",
        tight=BoundingBox(29.85, 32.30, 31.30, 32.60),
        wide=BoundingBox(29.00, 32.00, 31.80, 33.50),
    ))

    zones.append(GeoZone(
        name="panama",
        tight=BoundingBox(8.85, -79.95, 9.40, -79.50),
        wide=BoundingBox(8.00, -80.50, 9.80, -79.00),
    ))

    zones.append(GeoZone(
        name="malacca",
        tight=BoundingBox(1.05, 103.40, 1.50, 104.20),
        wide=BoundingBox(0.80, 99.00, 4.50, 104.50),
    ))

    zones.append(GeoZone(
        name="taiwan_strait",
        tight=BoundingBox(23.50, 118.00, 25.50, 120.50),
        wide=BoundingBox(22.00, 116.50, 26.50, 121.50),
    ))

    zones.append(GeoZone(
        name="turkish_straits",
        boxes=[
            BoundingBox(40.98, 28.95, 41.25, 29.15),  # Bosphorus
            BoundingBox(40.00, 26.15, 40.40, 26.75),  # Dardanelles
        ],
        wide=BoundingBox(39.80, 25.80, 41.40, 29.40),
    ))

    zones.append(GeoZone(
        name="gibraltar",
        tight=BoundingBox(35.80, -5.80, 36.10, -5.25),
        wide=BoundingBox(35.50, -6.50, 36.50, -4.50),
    ))

    zones.append(GeoZone(
        name="cape_of_good_hope",
        tight=BoundingBox(-35.00, 17.50, -33.50, 19.00),
        wide=BoundingBox(-36.00, 15.00, -32.00, 21.00),
    ))

    zones.append(GeoZone(
        name="danish_straits",
        boxes=[
            BoundingBox(55.40, 12.50, 55.95, 12.85),  # Oresund
            BoundingBox(55.10, 10.80, 55.60, 11.20),  # Great Belt
        ],
        wide=BoundingBox(54.50, 9.50, 57.80, 13.50),
    ))

    # ── Port Clusters ──

    zones.append(GeoZone(
        name="india_west_ports",
        boxes=[
            BoundingBox(18.85, 72.75, 19.10, 73.00),  # Mumbai/JNPT
            BoundingBox(22.65, 69.60, 22.85, 69.80),  # Mundra
            BoundingBox(22.95, 70.05, 23.10, 70.25),  # Kandla
        ],
        wide=BoundingBox(18.50, 68.50, 23.50, 73.50),
    ))

    zones.append(GeoZone(
        name="india_east_ports",
        boxes=[
            BoundingBox(13.05, 80.25, 13.20, 80.40),  # Chennai
            BoundingBox(17.65, 83.25, 17.75, 83.35),  # Vizag
            BoundingBox(20.20, 86.60, 20.35, 86.75),  # Paradip
        ],
        wide=BoundingBox(12.80, 79.50, 20.80, 87.50),
    ))

    zones.append(GeoZone(
        name="singapore",
        tight=BoundingBox(1.15, 103.60, 1.35, 104.10),
        wide=BoundingBox(0.90, 103.30, 1.55, 104.30),
    ))

    zones.append(GeoZone(
        name="rotterdam_antwerp",
        boxes=[
            BoundingBox(51.85, 3.85, 52.00, 4.50),  # Rotterdam
            BoundingBox(51.20, 4.25, 51.40, 4.45),  # Antwerp
        ],
        wide=BoundingBox(51.00, 3.00, 52.20, 4.80),
    ))

    zones.append(GeoZone(
        name="shanghai_ningbo",
        boxes=[
            BoundingBox(30.50, 121.80, 30.70, 122.10),  # Yangshan
            BoundingBox(31.30, 121.50, 31.45, 121.70),  # Waigaoqiao
            BoundingBox(29.70, 121.60, 30.10, 122.40),  # Ningbo-Zhoushan
        ],
        wide=BoundingBox(29.50, 121.00, 31.60, 122.80),
    ))

    # ── Regional Route Monitoring Areas ──

    zones.append(GeoZone(
        name="red_sea",
        wide=BoundingBox(12.30, 32.00, 30.00, 44.00),
    ))

    zones.append(GeoZone(
        name="south_china_sea",
        wide=BoundingBox(3.00, 103.00, 23.00, 121.00),
    ))

    zones.append(GeoZone(
        name="persian_gulf",
        wide=BoundingBox(23.50, 48.00, 30.50, 56.50),
    ))

    zones.append(GeoZone(
        name="black_sea",
        wide=BoundingBox(40.50, 27.50, 46.70, 42.00),
    ))

    zones.append(GeoZone(
        name="eastern_mediterranean",
        wide=BoundingBox(30.00, 24.00, 37.50, 36.50),
    ))

    return zones
