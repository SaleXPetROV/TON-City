"""
Generate missing PNG sprites using AI image generation
Then create 100 test users with full gameplay simulation
"""
import os
import sys
import asyncio
import random
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv

load_dotenv('/app/backend/.env')

SPRITES_DIR = Path('/app/frontend/public/sprites/buildings')

# Missing sprites to generate
MISSING_SPRITES = {
    # Arena levels 3-10
    "arena_lvl3": "isometric pixel art battle arena level 3, medium arena with stands, cyberpunk style, red and orange glow, dark background, game asset sprite, 64x64, transparent background",
    "arena_lvl4": "isometric pixel art battle arena level 4, arena stadium, cyberpunk style, fiery red glow, dark background, game asset sprite, 64x64, transparent background",
    "arena_lvl5": "isometric pixel art battle arena level 5, large battle colosseum, cyberpunk style, red neon lights, dark background, game asset sprite, 64x64, transparent background",
    "arena_lvl6": "isometric pixel art battle arena level 6, mega arena complex, cyberpunk style, flames and lights, dark background, game asset sprite, 64x64, transparent background",
    "arena_lvl7": "isometric pixel art battle arena level 7, championship arena, cyberpunk style, red glowing, dark background, game asset sprite, 64x64, transparent background",
    "arena_lvl8": "isometric pixel art battle arena level 8, legendary colosseum, cyberpunk style, fire effects, dark background, game asset sprite, 64x64, transparent background",
    "arena_lvl9": "isometric pixel art battle arena level 9, futuristic battle dome, cyberpunk style, energy shields, dark background, game asset sprite, 64x64, transparent background",
    "arena_lvl10": "isometric pixel art battle arena level 10, ultimate arena citadel, cyberpunk style, radiant red aura, dark background, game asset sprite, 64x64, transparent background",
    
    # Incubator levels 1-10
    "incubator_lvl1": "isometric pixel art startup incubator level 1, small office pod, cyberpunk style, orange neon, dark background, game asset sprite, 64x64, transparent background",
    "incubator_lvl2": "isometric pixel art startup incubator level 2, coworking space, cyberpunk style, warm orange glow, dark background, game asset sprite, 64x64, transparent background",
    "incubator_lvl3": "isometric pixel art startup incubator level 3, innovation lab, cyberpunk style, orange lights, dark background, game asset sprite, 64x64, transparent background",
    "incubator_lvl4": "isometric pixel art startup incubator level 4, tech hub building, cyberpunk style, orange neon signs, dark background, game asset sprite, 64x64, transparent background",
    "incubator_lvl5": "isometric pixel art startup incubator level 5, accelerator center, cyberpunk style, rocket motif, dark background, game asset sprite, 64x64, transparent background",
    "incubator_lvl6": "isometric pixel art startup incubator level 6, innovation tower, cyberpunk style, orange glow, dark background, game asset sprite, 64x64, transparent background",
    "incubator_lvl7": "isometric pixel art startup incubator level 7, tech campus, cyberpunk style, futuristic design, dark background, game asset sprite, 64x64, transparent background",
    "incubator_lvl8": "isometric pixel art startup incubator level 8, mega incubator complex, cyberpunk style, orange lights, dark background, game asset sprite, 64x64, transparent background",
    "incubator_lvl9": "isometric pixel art startup incubator level 9, futuristic launch pad, cyberpunk style, rocket ready, dark background, game asset sprite, 64x64, transparent background",
    "incubator_lvl10": "isometric pixel art startup incubator level 10, legendary innovation citadel, cyberpunk style, radiant orange aura, dark background, game asset sprite, 64x64, transparent background",
    
    # Bridge levels 1-10
    "bridge_lvl1": "isometric pixel art cross-chain bridge level 1, small portal gateway, cyberpunk style, blue portal effect, dark background, game asset sprite, 64x64, transparent background",
    "bridge_lvl2": "isometric pixel art cross-chain bridge level 2, gateway terminal, cyberpunk style, swirling blue energy, dark background, game asset sprite, 64x64, transparent background",
    "bridge_lvl3": "isometric pixel art cross-chain bridge level 3, medium bridge hub, cyberpunk style, blue wormhole, dark background, game asset sprite, 64x64, transparent background",
    "bridge_lvl4": "isometric pixel art cross-chain bridge level 4, bridge station, cyberpunk style, portal rings, dark background, game asset sprite, 64x64, transparent background",
    "bridge_lvl5": "isometric pixel art cross-chain bridge level 5, large bridge complex, cyberpunk style, blue energy field, dark background, game asset sprite, 64x64, transparent background",
    "bridge_lvl6": "isometric pixel art cross-chain bridge level 6, mega bridge tower, cyberpunk style, dimensional rift, dark background, game asset sprite, 64x64, transparent background",
    "bridge_lvl7": "isometric pixel art cross-chain bridge level 7, interdimensional hub, cyberpunk style, blue glow, dark background, game asset sprite, 64x64, transparent background",
    "bridge_lvl8": "isometric pixel art cross-chain bridge level 8, quantum bridge complex, cyberpunk style, energy vortex, dark background, game asset sprite, 64x64, transparent background",
    "bridge_lvl9": "isometric pixel art cross-chain bridge level 9, futuristic bridge citadel, cyberpunk style, blue portal storm, dark background, game asset sprite, 64x64, transparent background",
    "bridge_lvl10": "isometric pixel art cross-chain bridge level 10, legendary dimensional gateway, cyberpunk style, radiant blue aura, dark background, game asset sprite, 64x64, transparent background",
    
    # Construction sprites
    "construction_small": "isometric pixel art small construction site, scaffolding with yellow lights, cyberpunk style, dark background, game asset sprite, 64x64, transparent background",
    "construction_medium": "isometric pixel art medium construction site, crane and scaffolding, cyberpunk style, orange warning lights, dark background, game asset sprite, 64x64, transparent background",
    "construction_large": "isometric pixel art large construction site, tower crane and heavy machinery, cyberpunk style, flashing lights, dark background, game asset sprite, 64x64, transparent background",
}


async def generate_sprites():
    """Generate missing sprites using AI"""
    api_key = os.environ.get("EMERGENT_LLM_KEY")
    if not api_key:
        print("❌ No EMERGENT_LLM_KEY found")
        return 0
    
    try:
        from emergentintegrations.llm.openai.image_generation import OpenAIImageGeneration
        image_gen = OpenAIImageGeneration(api_key=api_key)
    except ImportError:
        print("❌ emergentintegrations not installed")
        return 0
    
    generated = 0
    
    for name, prompt in MISSING_SPRITES.items():
        output_path = SPRITES_DIR / f"{name}.png"
        
        # Skip if already exists as PNG
        if output_path.exists():
            print(f"  ⏭️  {name}.png already exists")
            continue
        
        try:
            print(f"  🎨 Generating {name}...")
            images = await image_gen.generate_images(
                prompt=prompt,
                model="gpt-image-1",
                number_of_images=1
            )
            
            if images and len(images) > 0:
                with open(output_path, "wb") as f:
                    f.write(images[0])
                print(f"  ✅ {name}.png saved!")
                generated += 1
            else:
                print(f"  ⚠️ No image generated for {name}")
                
        except Exception as e:
            print(f"  ❌ Error generating {name}: {e}")
            break  # Stop if we hit rate limits
        
        await asyncio.sleep(1)  # Rate limiting
    
    return generated


async def main():
    print("=" * 60)
    print("🎨 TON City Builder - Missing Sprites Generator")
    print("=" * 60)
    
    # Count current sprites
    png_count = len(list(SPRITES_DIR.glob("*.png")))
    svg_count = len(list(SPRITES_DIR.glob("*.svg")))
    print(f"\n📊 Current sprites: {png_count} PNG + {svg_count} SVG")
    print(f"📋 Missing sprites to generate: {len(MISSING_SPRITES)}")
    
    generated = await generate_sprites()
    
    # Final count
    png_count = len(list(SPRITES_DIR.glob("*.png")))
    svg_count = len(list(SPRITES_DIR.glob("*.svg")))
    print(f"\n📊 Final sprites: {png_count} PNG + {svg_count} SVG")
    print(f"✅ Generated: {generated} new sprites")


if __name__ == "__main__":
    asyncio.run(main())
