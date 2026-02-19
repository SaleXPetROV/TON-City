"""
Create high-quality SVG sprites for missing buildings
These SVGs will be rendered to PNG-like quality
"""
import os
from pathlib import Path

SPRITES_DIR = Path('/app/frontend/public/sprites/buildings')

# Color schemes for each building type
BUILDING_COLORS = {
    "arena": {
        "primary": "#ef4444",  # Red
        "secondary": "#dc2626",
        "accent": "#f87171",
        "glow": "#ff6b6b"
    },
    "incubator": {
        "primary": "#f97316",  # Orange
        "secondary": "#ea580c",
        "accent": "#fb923c",
        "glow": "#ff9f43"
    },
    "bridge": {
        "primary": "#3b82f6",  # Blue
        "secondary": "#2563eb",
        "accent": "#60a5fa",
        "glow": "#00d4ff"
    },
    "construction": {
        "primary": "#eab308",  # Yellow
        "secondary": "#ca8a04",
        "accent": "#facc15",
        "glow": "#ffd700"
    }
}

def create_isometric_building_svg(building_type: str, level: int) -> str:
    """Create a detailed isometric building SVG"""
    colors = BUILDING_COLORS.get(building_type, BUILDING_COLORS["arena"])
    
    # Building dimensions scale with level
    base_height = 30 + level * 8
    width = 50
    depth = 25
    
    # Create gradient IDs
    grad_id = f"{building_type}_{level}"
    
    svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="64" height="80" viewBox="0 0 64 80" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <!-- Building gradients -->
    <linearGradient id="top_{grad_id}" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:{colors['accent']};stop-opacity:1"/>
      <stop offset="100%" style="stop-color:{colors['primary']};stop-opacity:1"/>
    </linearGradient>
    <linearGradient id="left_{grad_id}" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" style="stop-color:{colors['secondary']};stop-opacity:1"/>
      <stop offset="100%" style="stop-color:{colors['primary']};stop-opacity:0.8"/>
    </linearGradient>
    <linearGradient id="right_{grad_id}" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" style="stop-color:{colors['primary']};stop-opacity:0.9"/>
      <stop offset="100%" style="stop-color:{colors['secondary']};stop-opacity:1"/>
    </linearGradient>
    
    <!-- Glow effect -->
    <filter id="glow_{grad_id}" x="-50%" y="-50%" width="200%" height="200%">
      <feGaussianBlur stdDeviation="2" result="coloredBlur"/>
      <feMerge>
        <feMergeNode in="coloredBlur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>
    
    <!-- Shadow -->
    <filter id="shadow_{grad_id}" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="2" stdDeviation="2" flood-color="#000" flood-opacity="0.3"/>
    </filter>
  </defs>
  
  <!-- Ground shadow -->
  <ellipse cx="32" cy="72" rx="{width/2}" ry="8" fill="rgba(0,0,0,0.3)"/>
  
  <!-- Building base -->
  <g filter="url(#shadow_{grad_id})">
    <!-- Left face -->
    <polygon 
      points="8,{70 - base_height/3} 32,{70} 32,{70 - base_height} 8,{70 - base_height - base_height/3}" 
      fill="url(#left_{grad_id})"
    />
    
    <!-- Right face -->
    <polygon 
      points="56,{70 - base_height/3} 32,{70} 32,{70 - base_height} 56,{70 - base_height - base_height/3}" 
      fill="url(#right_{grad_id})"
    />
    
    <!-- Top face -->
    <polygon 
      points="32,{70 - base_height - depth/2} 8,{70 - base_height - base_height/3} 32,{70 - base_height} 56,{70 - base_height - base_height/3}" 
      fill="url(#top_{grad_id})"
    />
  </g>
  
  <!-- Windows/details on left face -->
  <g opacity="0.6">'''
    
    # Add windows based on level
    window_rows = min(level, 5)
    for row in range(window_rows):
        y_offset = 70 - base_height + 10 + row * 12
        svg += f'''
    <rect x="12" y="{y_offset}" width="6" height="4" fill="{colors['glow']}" rx="1"/>
    <rect x="22" y="{y_offset}" width="6" height="4" fill="{colors['glow']}" rx="1"/>'''
    
    svg += '''
  </g>
  
  <!-- Windows/details on right face -->
  <g opacity="0.6">'''
    
    for row in range(window_rows):
        y_offset = 70 - base_height + 10 + row * 12
        svg += f'''
    <rect x="36" y="{y_offset}" width="6" height="4" fill="{colors['glow']}" rx="1"/>
    <rect x="46" y="{y_offset}" width="6" height="4" fill="{colors['glow']}" rx="1"/>'''
    
    svg += f'''
  </g>
  
  <!-- Antenna/tower on top for higher levels -->'''
    
    if level >= 5:
        antenna_height = 5 + (level - 5) * 2
        svg += f'''
  <line x1="32" y1="{70 - base_height - depth/2}" x2="32" y2="{70 - base_height - depth/2 - antenna_height}" 
        stroke="{colors['glow']}" stroke-width="2"/>
  <circle cx="32" cy="{70 - base_height - depth/2 - antenna_height}" r="3" fill="{colors['glow']}" filter="url(#glow_{grad_id})"/>'''
    
    # Level badge
    svg += f'''
  
  <!-- Level badge -->
  <circle cx="52" cy="12" r="10" fill="{colors['primary']}" stroke="white" stroke-width="1"/>
  <text x="52" y="16" font-family="Arial, sans-serif" font-size="10" 
        font-weight="bold" fill="white" text-anchor="middle">{level}</text>
  
  <!-- Building type indicator glow -->
  <ellipse cx="32" cy="{70 - base_height - depth/2 - 5}" rx="8" ry="3" 
           fill="{colors['glow']}" opacity="0.5" filter="url(#glow_{grad_id})"/>
</svg>'''
    
    return svg


def create_construction_svg(size: str) -> str:
    """Create construction site SVG"""
    colors = BUILDING_COLORS["construction"]
    
    heights = {"small": 30, "medium": 45, "large": 60}
    height = heights.get(size, 30)
    
    svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="64" height="80" viewBox="0 0 64 80" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="scaff_grad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" style="stop-color:#374151;stop-opacity:1"/>
      <stop offset="100%" style="stop-color:#4b5563;stop-opacity:1"/>
    </linearGradient>
    <filter id="glow_const">
      <feGaussianBlur stdDeviation="1.5" result="coloredBlur"/>
      <feMerge>
        <feMergeNode in="coloredBlur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>
  </defs>
  
  <!-- Ground shadow -->
  <ellipse cx="32" cy="72" rx="25" ry="8" fill="rgba(0,0,0,0.3)"/>
  
  <!-- Base platform -->
  <polygon points="8,65 32,75 56,65 32,55" fill="#6b7280"/>
  
  <!-- Scaffolding poles -->
  <line x1="15" y1="65" x2="15" y2="{65 - height}" stroke="#9ca3af" stroke-width="3"/>
  <line x1="49" y1="65" x2="49" y2="{65 - height}" stroke="#9ca3af" stroke-width="3"/>
  <line x1="32" y1="55" x2="32" y2="{55 - height}" stroke="#9ca3af" stroke-width="3"/>
  
  <!-- Cross beams -->'''
    
    beam_count = height // 15
    for i in range(beam_count):
        y = 65 - (i + 1) * 15
        svg += f'''
  <line x1="15" y1="{y}" x2="49" y2="{y}" stroke="#6b7280" stroke-width="2"/>'''
    
    svg += f'''
  
  <!-- Crane for large -->'''
    
    if size == "large":
        svg += '''
  <line x1="32" y1="5" x2="32" y2="-15" stroke="#f59e0b" stroke-width="3"/>
  <line x1="20" y1="-15" x2="50" y2="-15" stroke="#f59e0b" stroke-width="3"/>
  <line x1="45" y1="-15" x2="45" y2="10" stroke="#374151" stroke-width="1"/>'''
    
    svg += f'''
  
  <!-- Warning lights -->
  <circle cx="15" cy="{65 - height}" r="4" fill="{colors['accent']}" filter="url(#glow_const)">
    <animate attributeName="opacity" values="1;0.3;1" dur="1s" repeatCount="indefinite"/>
  </circle>
  <circle cx="49" cy="{65 - height}" r="4" fill="{colors['accent']}" filter="url(#glow_const)">
    <animate attributeName="opacity" values="0.3;1;0.3" dur="1s" repeatCount="indefinite"/>
  </circle>
  
  <!-- Construction sign -->
  <rect x="24" y="58" width="16" height="12" fill="{colors['primary']}" rx="2"/>
  <text x="32" y="67" font-family="Arial, sans-serif" font-size="8" 
        font-weight="bold" fill="black" text-anchor="middle">🔨</text>
</svg>'''
    
    return svg


def main():
    print("Creating high-quality SVG sprites for missing buildings...")
    created = 0
    
    # Generate arena levels 3-10
    for level in range(3, 11):
        filename = f"arena_lvl{level}.png"
        filepath = SPRITES_DIR / filename
        # Remove old SVG if exists
        svg_path = filepath.with_suffix('.svg')
        if svg_path.exists():
            svg_path.unlink()
        
        # Create new PNG-compatible SVG
        svg_content = create_isometric_building_svg("arena", level)
        with open(svg_path, 'w') as f:
            f.write(svg_content)
        print(f"  ✅ Created arena_lvl{level}.svg")
        created += 1
    
    # Generate incubator levels 1-10
    for level in range(1, 11):
        svg_path = SPRITES_DIR / f"incubator_lvl{level}.svg"
        svg_content = create_isometric_building_svg("incubator", level)
        with open(svg_path, 'w') as f:
            f.write(svg_content)
        print(f"  ✅ Created incubator_lvl{level}.svg")
        created += 1
    
    # Generate bridge levels 1-10
    for level in range(1, 11):
        svg_path = SPRITES_DIR / f"bridge_lvl{level}.svg"
        svg_content = create_isometric_building_svg("bridge", level)
        with open(svg_path, 'w') as f:
            f.write(svg_content)
        print(f"  ✅ Created bridge_lvl{level}.svg")
        created += 1
    
    # Generate construction sprites
    for size in ["small", "medium", "large"]:
        svg_path = SPRITES_DIR / f"construction_{size}.svg"
        svg_content = create_construction_svg(size)
        with open(svg_path, 'w') as f:
            f.write(svg_content)
        print(f"  ✅ Created construction_{size}.svg")
        created += 1
    
    print(f"\n✅ Created {created} SVG sprites!")
    
    # Count totals
    png_count = len(list(SPRITES_DIR.glob("*.png")))
    svg_count = len(list(SPRITES_DIR.glob("*.svg")))
    print(f"📊 Total: {png_count} PNG + {svg_count} SVG = {png_count + svg_count} sprites")


if __name__ == "__main__":
    main()
