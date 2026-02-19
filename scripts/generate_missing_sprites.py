"""
Script to generate missing building sprites for TON City Builder
Generates isometric 2.5D cyberpunk style PNG sprites
"""
import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv

load_dotenv('/app/backend/.env')

# Add backend to path
sys.path.insert(0, '/app/backend')

SPRITES_DIR = Path('/app/frontend/public/sprites/buildings')
SPRITES_DIR.mkdir(parents=True, exist_ok=True)

# Building prompts for each type
BUILDING_PROMPTS = {
    # Missing levels for existing buildings
    "helios_lvl2": "isometric pixel art solar power station level 2, medium size with more solar panels, cyberpunk futuristic style, neon cyan glow, dark space background, game asset sprite, clean edges, 64x64",
    "validator_lvl1": "isometric pixel art blockchain validator node level 1, small server rack with blinking lights, cyberpunk style, electric blue neon glow, dark background, game asset sprite, 64x64",
    
    # gram_bank levels 2-10
    "gram_bank_lvl2": "isometric pixel art crypto bank level 2, small modern bank building, cyberpunk style, gold and cyan neon, dark background, game asset sprite, 64x64",
    "gram_bank_lvl3": "isometric pixel art crypto bank level 3, medium bank with vault, cyberpunk style, gold accents, dark background, game asset sprite, 64x64",
    "gram_bank_lvl4": "isometric pixel art crypto bank level 4, larger bank with security, cyberpunk style, gold neon glow, dark background, game asset sprite, 64x64",
    "gram_bank_lvl5": "isometric pixel art crypto bank level 5, modern bank tower, cyberpunk style, gold and blue neon, dark background, game asset sprite, 64x64",
    "gram_bank_lvl6": "isometric pixel art crypto bank level 6, tall bank skyscraper, cyberpunk style, golden lights, dark background, game asset sprite, 64x64",
    "gram_bank_lvl7": "isometric pixel art crypto bank level 7, luxury bank complex, cyberpunk style, gold chrome, dark background, game asset sprite, 64x64",
    "gram_bank_lvl8": "isometric pixel art crypto bank level 8, mega bank headquarters, cyberpunk style, golden glow, dark background, game asset sprite, 64x64",
    "gram_bank_lvl9": "isometric pixel art crypto bank level 9, futuristic bank citadel, cyberpunk style, glowing gold, dark background, game asset sprite, 64x64",
    "gram_bank_lvl10": "isometric pixel art crypto bank level 10, legendary diamond bank palace, cyberpunk style, radiant gold aura, dark background, game asset sprite, 64x64",
    
    # DEX Exchange - all 10 levels
    "dex_lvl1": "isometric pixel art decentralized exchange level 1, small trading terminal, cyberpunk style, green chart displays, dark background, game asset sprite, 64x64",
    "dex_lvl2": "isometric pixel art decentralized exchange level 2, trading booth with screens, cyberpunk style, green neon, dark background, game asset sprite, 64x64",
    "dex_lvl3": "isometric pixel art decentralized exchange level 3, small trading floor, cyberpunk style, multiple screens, dark background, game asset sprite, 64x64",
    "dex_lvl4": "isometric pixel art decentralized exchange level 4, medium trading center, cyberpunk style, holographic charts, dark background, game asset sprite, 64x64",
    "dex_lvl5": "isometric pixel art decentralized exchange level 5, large trading hub, cyberpunk style, green glow, dark background, game asset sprite, 64x64",
    "dex_lvl6": "isometric pixel art decentralized exchange level 6, exchange tower, cyberpunk style, matrix-like displays, dark background, game asset sprite, 64x64",
    "dex_lvl7": "isometric pixel art decentralized exchange level 7, mega exchange complex, cyberpunk style, neon green, dark background, game asset sprite, 64x64",
    "dex_lvl8": "isometric pixel art decentralized exchange level 8, exchange skyscraper, cyberpunk style, glowing screens, dark background, game asset sprite, 64x64",
    "dex_lvl9": "isometric pixel art decentralized exchange level 9, futuristic exchange citadel, cyberpunk style, holographic trading, dark background, game asset sprite, 64x64",
    "dex_lvl10": "isometric pixel art decentralized exchange level 10, legendary crystal exchange palace, cyberpunk style, radiant green aura, dark background, game asset sprite, 64x64",
    
    # Casino - all 10 levels
    "casino_lvl1": "isometric pixel art crypto casino level 1, small slot machine booth, cyberpunk style, purple neon lights, dark background, game asset sprite, 64x64",
    "casino_lvl2": "isometric pixel art crypto casino level 2, small gambling room, cyberpunk style, purple glow, dark background, game asset sprite, 64x64",
    "casino_lvl3": "isometric pixel art crypto casino level 3, medium casino floor, cyberpunk style, neon purple and pink, dark background, game asset sprite, 64x64",
    "casino_lvl4": "isometric pixel art crypto casino level 4, casino building with sign, cyberpunk style, flashy lights, dark background, game asset sprite, 64x64",
    "casino_lvl5": "isometric pixel art crypto casino level 5, large casino complex, cyberpunk style, purple neon, dark background, game asset sprite, 64x64",
    "casino_lvl6": "isometric pixel art crypto casino level 6, luxury casino tower, cyberpunk style, vibrant purple, dark background, game asset sprite, 64x64",
    "casino_lvl7": "isometric pixel art crypto casino level 7, mega casino resort, cyberpunk style, neon extravaganza, dark background, game asset sprite, 64x64",
    "casino_lvl8": "isometric pixel art crypto casino level 8, casino skyscraper, cyberpunk style, purple glow, dark background, game asset sprite, 64x64",
    "casino_lvl9": "isometric pixel art crypto casino level 9, futuristic casino palace, cyberpunk style, holographic displays, dark background, game asset sprite, 64x64",
    "casino_lvl10": "isometric pixel art crypto casino level 10, legendary diamond casino, cyberpunk style, radiant purple aura, dark background, game asset sprite, 64x64",
    
    # Arena - all 10 levels
    "arena_lvl1": "isometric pixel art battle arena level 1, small fighting pit, cyberpunk style, red neon glow, dark background, game asset sprite, 64x64",
    "arena_lvl2": "isometric pixel art battle arena level 2, combat ring with seats, cyberpunk style, red lights, dark background, game asset sprite, 64x64",
    "arena_lvl3": "isometric pixel art battle arena level 3, medium arena with stands, cyberpunk style, red and orange, dark background, game asset sprite, 64x64",
    "arena_lvl4": "isometric pixel art battle arena level 4, arena stadium, cyberpunk style, fiery glow, dark background, game asset sprite, 64x64",
    "arena_lvl5": "isometric pixel art battle arena level 5, large battle colosseum, cyberpunk style, red neon, dark background, game asset sprite, 64x64",
    "arena_lvl6": "isometric pixel art battle arena level 6, mega arena complex, cyberpunk style, flames and lights, dark background, game asset sprite, 64x64",
    "arena_lvl7": "isometric pixel art battle arena level 7, championship arena, cyberpunk style, red glow, dark background, game asset sprite, 64x64",
    "arena_lvl8": "isometric pixel art battle arena level 8, legendary colosseum, cyberpunk style, fire effects, dark background, game asset sprite, 64x64",
    "arena_lvl9": "isometric pixel art battle arena level 9, futuristic battle dome, cyberpunk style, energy shields, dark background, game asset sprite, 64x64",
    "arena_lvl10": "isometric pixel art battle arena level 10, ultimate arena citadel, cyberpunk style, radiant red aura, dark background, game asset sprite, 64x64",
    
    # Incubator - all 10 levels
    "incubator_lvl1": "isometric pixel art startup incubator level 1, small office pod, cyberpunk style, orange neon, dark background, game asset sprite, 64x64",
    "incubator_lvl2": "isometric pixel art startup incubator level 2, coworking space, cyberpunk style, warm orange glow, dark background, game asset sprite, 64x64",
    "incubator_lvl3": "isometric pixel art startup incubator level 3, innovation lab, cyberpunk style, orange lights, dark background, game asset sprite, 64x64",
    "incubator_lvl4": "isometric pixel art startup incubator level 4, tech hub building, cyberpunk style, orange neon signs, dark background, game asset sprite, 64x64",
    "incubator_lvl5": "isometric pixel art startup incubator level 5, accelerator center, cyberpunk style, rocket motif, dark background, game asset sprite, 64x64",
    "incubator_lvl6": "isometric pixel art startup incubator level 6, innovation tower, cyberpunk style, orange glow, dark background, game asset sprite, 64x64",
    "incubator_lvl7": "isometric pixel art startup incubator level 7, tech campus, cyberpunk style, futuristic design, dark background, game asset sprite, 64x64",
    "incubator_lvl8": "isometric pixel art startup incubator level 8, mega incubator complex, cyberpunk style, orange lights, dark background, game asset sprite, 64x64",
    "incubator_lvl9": "isometric pixel art startup incubator level 9, futuristic launch pad, cyberpunk style, rocket ready, dark background, game asset sprite, 64x64",
    "incubator_lvl10": "isometric pixel art startup incubator level 10, legendary innovation citadel, cyberpunk style, radiant orange aura, dark background, game asset sprite, 64x64",
    
    # Bridge - all 10 levels
    "bridge_lvl1": "isometric pixel art cross-chain bridge level 1, small portal gateway, cyberpunk style, blue portal effect, dark background, game asset sprite, 64x64",
    "bridge_lvl2": "isometric pixel art cross-chain bridge level 2, gateway terminal, cyberpunk style, swirling blue energy, dark background, game asset sprite, 64x64",
    "bridge_lvl3": "isometric pixel art cross-chain bridge level 3, medium bridge hub, cyberpunk style, blue wormhole, dark background, game asset sprite, 64x64",
    "bridge_lvl4": "isometric pixel art cross-chain bridge level 4, bridge station, cyberpunk style, portal rings, dark background, game asset sprite, 64x64",
    "bridge_lvl5": "isometric pixel art cross-chain bridge level 5, large bridge complex, cyberpunk style, blue energy field, dark background, game asset sprite, 64x64",
    "bridge_lvl6": "isometric pixel art cross-chain bridge level 6, mega bridge tower, cyberpunk style, dimensional rift, dark background, game asset sprite, 64x64",
    "bridge_lvl7": "isometric pixel art cross-chain bridge level 7, interdimensional hub, cyberpunk style, blue glow, dark background, game asset sprite, 64x64",
    "bridge_lvl8": "isometric pixel art cross-chain bridge level 8, quantum bridge complex, cyberpunk style, energy vortex, dark background, game asset sprite, 64x64",
    "bridge_lvl9": "isometric pixel art cross-chain bridge level 9, futuristic bridge citadel, cyberpunk style, blue portal storm, dark background, game asset sprite, 64x64",
    "bridge_lvl10": "isometric pixel art cross-chain bridge level 10, legendary dimensional gateway, cyberpunk style, radiant blue aura, dark background, game asset sprite, 64x64",
    
    # Construction sprites for 3 tiers
    "construction_small": "isometric pixel art small construction site, scaffolding, crane, workers, cyberpunk style, yellow safety lights, dark background, game asset sprite, under construction sign, 64x64",
    "construction_medium": "isometric pixel art medium construction site, larger scaffolding, multiple cranes, cyberpunk style, orange warning lights, dark background, game asset sprite, 64x64",
    "construction_large": "isometric pixel art large construction site, massive scaffolding, tower crane, heavy machinery, cyberpunk style, flashing lights, dark background, game asset sprite, 64x64",
}


async def generate_sprite(name: str, prompt: str) -> bool:
    """Generate a single sprite"""
    output_path = SPRITES_DIR / f"{name}.png"
    
    if output_path.exists():
        print(f"  ⏭️  {name} already exists, skipping")
        return True
    
    api_key = os.environ.get("EMERGENT_LLM_KEY")
    if not api_key:
        print(f"  ❌ No EMERGENT_LLM_KEY found")
        return False
    
    try:
        from emergentintegrations.llm.openai.image_generation import OpenAIImageGeneration
        
        print(f"  🎨 Generating {name}...")
        image_gen = OpenAIImageGeneration(api_key=api_key)
        images = await image_gen.generate_images(
            prompt=prompt,
            model="gpt-image-1",
            number_of_images=1
        )
        
        if images and len(images) > 0:
            with open(output_path, "wb") as f:
                f.write(images[0])
            print(f"  ✅ {name} saved!")
            return True
        else:
            print(f"  ❌ No image generated for {name}")
            return False
            
    except Exception as e:
        print(f"  ❌ Error generating {name}: {e}")
        return False


async def main():
    print("=" * 60)
    print("🏗️  TON City Builder - Missing Sprites Generator")
    print("=" * 60)
    
    total = len(BUILDING_PROMPTS)
    success = 0
    failed = 0
    
    print(f"\n📋 Total sprites to generate: {total}\n")
    
    for i, (name, prompt) in enumerate(BUILDING_PROMPTS.items(), 1):
        print(f"[{i}/{total}] Processing {name}")
        result = await generate_sprite(name, prompt)
        if result:
            success += 1
        else:
            failed += 1
        
        # Small delay between requests
        if i < total:
            await asyncio.sleep(1)
    
    print("\n" + "=" * 60)
    print(f"✅ Successfully generated: {success}")
    print(f"❌ Failed: {failed}")
    print("=" * 60)
    
    # List final sprite count
    sprites = list(SPRITES_DIR.glob("*.png"))
    print(f"\n📊 Total sprites in folder: {len(sprites)}")


if __name__ == "__main__":
    asyncio.run(main())
