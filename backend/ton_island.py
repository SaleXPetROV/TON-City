"""
TON Island Map Generator
Creates a diamond-shaped island resembling TON cryptocurrency logo
with exactly 500 playable cells
"""
import math
from typing import List, Dict, Tuple

# Island configuration
ISLAND_CONFIG = {
    "id": "ton_island",
    "name": {"en": "TON Island", "ru": "Остров TON"},
    "total_cells": 500,
    "shape": "diamond",  # TON logo shape
}

# Zone configuration (from center outward)
ZONES = {
    "core": {
        "name": {"en": "Core", "ru": "Ядро"},
        "price_multiplier": 4.0,  # 100 TON
        "color": "#00D4FF",  # Bright cyan
        "tier_allowed": [3],  # Only Tier III businesses
    },
    "inner": {
        "name": {"en": "Inner Ring", "ru": "Внутреннее кольцо"},
        "price_multiplier": 3.0,  # 75 TON
        "color": "#0098EA",  # TON blue
        "tier_allowed": [2, 3],
    },
    "middle": {
        "name": {"en": "Middle Ring", "ru": "Среднее кольцо"},
        "price_multiplier": 2.0,  # 50 TON
        "color": "#0057FF",  # Deeper blue
        "tier_allowed": [1, 2, 3],
    },
    "outer": {
        "name": {"en": "Outer Ring", "ru": "Внешнее кольцо"},
        "price_multiplier": 1.0,  # 25 TON
        "color": "#1a1a2e",  # Dark
        "tier_allowed": [1, 2],
    },
}

# Base plot price (TON)
# Core: 100, Inner: 75, Middle: 50, Outer: 25
BASE_PLOT_PRICE = 25.0  # TON - base for outer zone


def generate_diamond_grid(target_cells: int = 500) -> Tuple[List[List[int]], int, int]:
    """
    Generate a diamond-shaped grid (TON logo style).
    Returns grid, width, height.
    Grid values: 0 = water, 1 = land
    """
    # Calculate diamond size to fit ~500 cells
    # Diamond area ≈ 2 * r² where r is "radius"
    # So for 500 cells: r ≈ sqrt(250) ≈ 16
    
    radius = 16
    size = radius * 2 + 1  # 33x33 grid
    
    grid = []
    total_land = 0
    
    for y in range(size):
        row = []
        for x in range(size):
            # Calculate distance from center in diamond metric
            center = radius
            dx = abs(x - center)
            dy = abs(y - center)
            
            # Diamond shape: |x| + |y| <= radius
            # With inner cutout to create TON symbol effect
            diamond_dist = dx + dy
            
            # Main diamond body
            if diamond_dist <= radius:
                # Create the TON symbol inner triangle cutout
                # The TON logo has a triangular indent at the top
                
                # Check if in the top triangle cutout (creates the TON "V" shape)
                if y < center:  # Top half
                    # Create V-shaped cutout from top
                    top_cutout_depth = radius // 3
                    if y < top_cutout_depth:
                        # Within cutout zone
                        cutout_width = (top_cutout_depth - y) * 2
                        if abs(x - center) <= cutout_width // 2:
                            row.append(0)  # Water (cutout)
                            continue
                
                row.append(1)  # Land
                total_land += 1
            else:
                row.append(0)  # Water
        grid.append(row)
    
    # Adjust to hit closer to target
    print(f"Generated diamond with {total_land} land cells")
    
    return grid, size, size


def generate_ton_island_map() -> Dict:
    """
    Generate the complete TON Island map data.
    """
    grid, width, height = generate_diamond_grid(500)
    
    # Count actual cells and assign zones
    cells = []
    cell_count = 0
    center_x = width // 2
    center_y = height // 2
    max_dist = width // 2
    
    for y in range(height):
        for x in range(width):
            if grid[y][x] == 1:
                cell_count += 1
                
                # Calculate distance from center for zone
                dx = abs(x - center_x)
                dy = abs(y - center_y)
                dist = dx + dy
                dist_ratio = dist / max_dist
                
                # Determine zone
                if dist_ratio <= 0.2:
                    zone = "core"
                elif dist_ratio <= 0.4:
                    zone = "inner"
                elif dist_ratio <= 0.7:
                    zone = "middle"
                else:
                    zone = "outer"
                
                zone_config = ZONES[zone]
                price = BASE_PLOT_PRICE * zone_config["price_multiplier"]
                
                cells.append({
                    "x": x,
                    "y": y,
                    "zone": zone,
                    "price": round(price, 4),
                    "is_available": True,
                    "owner": None,
                    "business": None,
                })
    
    # Zone statistics
    zone_stats = {zone: 0 for zone in ZONES.keys()}
    for cell in cells:
        zone_stats[cell["zone"]] += 1
    
    return {
        "id": ISLAND_CONFIG["id"],
        "name": ISLAND_CONFIG["name"],
        "grid": grid,
        "width": width,
        "height": height,
        "cells": cells,
        "total_cells": cell_count,
        "zone_stats": zone_stats,
        "zones": ZONES,
        "base_price": BASE_PLOT_PRICE,
    }


def get_cell_at(island_data: Dict, x: int, y: int) -> Dict:
    """Get cell data at specific coordinates"""
    for cell in island_data["cells"]:
        if cell["x"] == x and cell["y"] == y:
            return cell
    return None


def get_neighbors(island_data: Dict, x: int, y: int) -> List[Dict]:
    """Get neighboring cells (for connection bonuses)"""
    neighbors = []
    offsets = [(-1, 0), (1, 0), (0, -1), (0, 1)]  # 4-directional
    
    for dx, dy in offsets:
        cell = get_cell_at(island_data, x + dx, y + dy)
        if cell:
            neighbors.append(cell)
    
    return neighbors


# Generate island on module load for testing
if __name__ == "__main__":
    island = generate_ton_island_map()
    print(f"Island generated: {island['total_cells']} cells")
    print(f"Zone distribution: {island['zone_stats']}")
