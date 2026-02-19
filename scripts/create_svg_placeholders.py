"""
Create SVG placeholder sprites for missing buildings
These are temporary until real PNG sprites are generated
"""
import os
from pathlib import Path

SPRITES_DIR = Path('/app/frontend/public/sprites/buildings')

# Color schemes for different building types
COLORS = {
    "arena": {"primary": "#FF4444", "secondary": "#AA2222", "accent": "#FF8888"},
    "incubator": {"primary": "#FF8800", "secondary": "#AA5500", "accent": "#FFAA44"},
    "bridge": {"primary": "#4488FF", "secondary": "#2255AA", "accent": "#88BBFF"},
    "construction_small": {"primary": "#FFAA00", "secondary": "#AA7700", "accent": "#FFCC44"},
    "construction_medium": {"primary": "#FF8800", "secondary": "#AA5500", "accent": "#FFAA44"},
    "construction_large": {"primary": "#FF6600", "secondary": "#AA4400", "accent": "#FF8844"},
}

ICONS = {
    "arena": "⚔️",
    "incubator": "🚀",
    "bridge": "🌉",
    "construction_small": "🔨",
    "construction_medium": "🏗️",
    "construction_large": "🏗️",
}

def create_svg_sprite(building_type: str, level: int = 0) -> str:
    """Create an isometric SVG sprite"""
    colors = COLORS.get(building_type, COLORS["arena"])
    icon = ICONS.get(building_type, "🏢")
    
    # Adjust brightness based on level
    level_factor = 1 + (level * 0.05) if level > 0 else 1
    
    # Building height increases with level
    height_offset = min(level * 2, 20) if level > 0 else 0
    
    svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="64" height="64" viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="topGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:{colors["accent"]};stop-opacity:1"/>
      <stop offset="100%" style="stop-color:{colors["primary"]};stop-opacity:1"/>
    </linearGradient>
    <linearGradient id="leftGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" style="stop-color:{colors["secondary"]};stop-opacity:1"/>
      <stop offset="100%" style="stop-color:{colors["primary"]};stop-opacity:0.8"/>
    </linearGradient>
    <linearGradient id="rightGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" style="stop-color:{colors["primary"]};stop-opacity:0.8"/>
      <stop offset="100%" style="stop-color:{colors["secondary"]};stop-opacity:1"/>
    </linearGradient>
    <filter id="glow">
      <feGaussianBlur stdDeviation="1" result="coloredBlur"/>
      <feMerge>
        <feMergeNode in="coloredBlur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>
  </defs>
  
  <!-- Isometric cube base -->
  <!-- Top face -->
  <polygon points="32,{8 - height_offset} 54,{20 - height_offset} 32,{32 - height_offset} 10,{20 - height_offset}" 
           fill="url(#topGrad)" stroke="#00ffff" stroke-width="0.5" filter="url(#glow)"/>
  
  <!-- Left face -->
  <polygon points="10,{20 - height_offset} 32,{32 - height_offset} 32,52 10,40" 
           fill="url(#leftGrad)" stroke="#00ffff" stroke-width="0.5"/>
  
  <!-- Right face -->
  <polygon points="32,{32 - height_offset} 54,{20 - height_offset} 54,40 32,52" 
           fill="url(#rightGrad)" stroke="#00ffff" stroke-width="0.5"/>
  
  <!-- Level indicator -->
  <text x="32" y="{26 - height_offset}" font-family="Arial, sans-serif" font-size="10" 
        font-weight="bold" fill="#000" text-anchor="middle" dominant-baseline="middle">
    {f'L{level}' if level > 0 else icon}
  </text>
  
  <!-- Neon glow effect at bottom -->
  <ellipse cx="32" cy="56" rx="20" ry="4" fill="{colors['accent']}" opacity="0.3"/>
</svg>'''
    
    return svg


def main():
    print("Creating SVG placeholder sprites...")
    
    # Missing arena levels (3-10)
    for level in range(3, 11):
        filename = f"arena_lvl{level}.png"  # Keep .png extension for compatibility
        filepath = SPRITES_DIR / filename
        if not filepath.exists():
            svg_content = create_svg_sprite("arena", level)
            # Save as SVG but with .png extension for now (will be replaced later)
            svg_filepath = filepath.with_suffix('.svg')
            with open(svg_filepath, 'w') as f:
                f.write(svg_content)
            print(f"  ✅ Created {svg_filepath.name}")
    
    # Missing incubator levels (1-10)
    for level in range(1, 11):
        filename = f"incubator_lvl{level}.png"
        filepath = SPRITES_DIR / filename
        if not filepath.exists():
            svg_content = create_svg_sprite("incubator", level)
            svg_filepath = filepath.with_suffix('.svg')
            with open(svg_filepath, 'w') as f:
                f.write(svg_content)
            print(f"  ✅ Created {svg_filepath.name}")
    
    # Missing bridge levels (1-10)
    for level in range(1, 11):
        filename = f"bridge_lvl{level}.png"
        filepath = SPRITES_DIR / filename
        if not filepath.exists():
            svg_content = create_svg_sprite("bridge", level)
            svg_filepath = filepath.with_suffix('.svg')
            with open(svg_filepath, 'w') as f:
                f.write(svg_content)
            print(f"  ✅ Created {svg_filepath.name}")
    
    # Construction sprites
    for size in ["small", "medium", "large"]:
        filename = f"construction_{size}.svg"
        filepath = SPRITES_DIR / filename
        if not filepath.exists():
            svg_content = create_svg_sprite(f"construction_{size}", 0)
            with open(filepath, 'w') as f:
                f.write(svg_content)
            print(f"  ✅ Created {filename}")
    
    print("\n✅ Done! SVG placeholders created.")
    
    # Count total
    png_count = len(list(SPRITES_DIR.glob("*.png")))
    svg_count = len(list(SPRITES_DIR.glob("*.svg")))
    print(f"📊 Total: {png_count} PNG + {svg_count} SVG = {png_count + svg_count} sprites")


if __name__ == "__main__":
    main()
