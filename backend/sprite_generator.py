"""
Sprite Generation Service for TON City Builder
Generates isometric building sprites using AI
"""
import os
import base64
import asyncio
import logging
from typing import Optional, Dict
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Sprite cache in memory (in production use Redis or file storage)
sprite_cache: Dict[str, str] = {}

# Pre-defined prompts for each building type and level
BUILDING_PROMPTS = {
    "farm": {
        "base": "isometric pixel art farm building, golden wheat field, rustic wooden barn, cyberpunk style, neon accents, dark background, game asset, 64x64 sprite",
        "levels": {
            1: "small simple farm",
            2: "slightly larger farm with fence",
            3: "medium farm with silo",
            4: "large farm with multiple barns",
            5: "industrial farm complex with neon lights",
            6: "high-tech automated farm",
            7: "mega farm with drones",
            8: "corporate farm empire",
            9: "futuristic vertical farm",
            10: "legendary golden farm, glowing"
        }
    },
    "factory": {
        "base": "isometric pixel art factory building, industrial smokestacks, cyberpunk style, neon blue and purple accents, dark background, game asset, 64x64 sprite",
        "levels": {
            1: "small workshop",
            2: "basic factory",
            3: "medium factory with chimney",
            4: "large industrial plant",
            5: "automated factory with robots",
            6: "high-tech manufacturing",
            7: "mega factory complex",
            8: "corporate industrial hub",
            9: "futuristic nano-factory",
            10: "legendary chrome factory, glowing neon"
        }
    },
    "shop": {
        "base": "isometric pixel art retail shop, storefront with neon sign, cyberpunk style, glass windows, dark background, game asset, 64x64 sprite",
        "levels": {
            1: "tiny corner shop",
            2: "small convenience store",
            3: "medium retail store",
            4: "large supermarket",
            5: "modern mall section",
            6: "high-end boutique",
            7: "mega store complex",
            8: "luxury shopping center",
            9: "futuristic holographic store",
            10: "legendary crystal shopping palace, glowing"
        }
    },
    "restaurant": {
        "base": "isometric pixel art restaurant building, neon food sign, outdoor seating, cyberpunk style, warm lights, dark background, game asset, 64x64 sprite",
        "levels": {
            1: "small food stall",
            2: "basic diner",
            3: "cozy restaurant",
            4: "popular eatery",
            5: "upscale dining",
            6: "gourmet restaurant",
            7: "celebrity chef venue",
            8: "michelin star restaurant",
            9: "futuristic food palace",
            10: "legendary golden restaurant, glowing"
        }
    },
    "bank": {
        "base": "isometric pixel art bank building, marble columns, vault door, cyberpunk style, gold and cyan neon, dark background, game asset, 64x64 sprite",
        "levels": {
            1: "small credit union",
            2: "local bank branch",
            3: "regional bank",
            4: "city bank",
            5: "national bank",
            6: "investment bank",
            7: "international bank",
            8: "central bank",
            9: "crypto bank tower",
            10: "legendary diamond bank, glowing gold"
        }
    },
    "power_plant": {
        "base": "isometric pixel art power plant, cooling towers, electric sparks, cyberpunk style, blue energy glow, dark background, game asset, 64x64 sprite",
        "levels": {
            1: "small generator",
            2: "basic power station",
            3: "coal plant",
            4: "gas turbine plant",
            5: "solar farm",
            6: "wind farm",
            7: "nuclear plant",
            8: "fusion reactor",
            9: "antimatter plant",
            10: "legendary plasma core, pulsing energy"
        }
    },
    "quarry": {
        "base": "isometric pixel art quarry mine, excavation pit, mining equipment, cyberpunk style, orange and cyan lights, dark background, game asset, 64x64 sprite",
        "levels": {
            1: "small dig site",
            2: "basic quarry",
            3: "open pit mine",
            4: "large excavation",
            5: "mechanized quarry",
            6: "deep mine shaft",
            7: "mega mining complex",
            8: "automated extraction",
            9: "laser mining facility",
            10: "legendary crystal mine, glowing gems"
        }
    },
    "construction": {
        "base": "isometric pixel art construction site, scaffolding, crane, workers, cyberpunk style, yellow safety lights, dark background, game asset, 64x64 sprite, under construction sign",
        "levels": {}
    }
}

# Default placeholder sprites (base64 encoded simple colored diamonds)
DEFAULT_SPRITES = {}

def generate_placeholder_sprite(building_type: str, level: int = 1) -> str:
    """Generate a simple SVG placeholder sprite"""
    colors = {
        "farm": "#FFD700",
        "factory": "#708090",
        "shop": "#FF69B4",
        "restaurant": "#FF6347",
        "bank": "#4169E1",
        "power_plant": "#00CED1",
        "quarry": "#CD853F",
        "construction": "#FFA500"
    }
    
    color = colors.get(building_type, "#888888")
    # Adjust brightness based on level
    brightness = 0.5 + (level * 0.05)
    
    svg = f'''<svg width="64" height="64" xmlns="http://www.w3.org/2000/svg">
        <defs>
            <linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" style="stop-color:{color};stop-opacity:1" />
                <stop offset="100%" style="stop-color:{color};stop-opacity:{brightness}" />
            </linearGradient>
        </defs>
        <polygon points="32,4 60,20 60,44 32,60 4,44 4,20" fill="url(#grad)" stroke="#00ffff" stroke-width="2"/>
        <text x="32" y="36" font-family="Arial" font-size="16" font-weight="bold" fill="#000" text-anchor="middle">L{level}</text>
    </svg>'''
    
    return f"data:image/svg+xml;base64,{base64.b64encode(svg.encode()).decode()}"


async def generate_building_sprite(building_type: str, level: int = 1) -> Optional[str]:
    """
    Generate an AI sprite for a building type and level.
    Returns base64 encoded PNG image or None if generation fails.
    """
    cache_key = f"{building_type}_L{level}"
    
    # Check cache first
    if cache_key in sprite_cache:
        logger.info(f"Sprite cache hit: {cache_key}")
        return sprite_cache[cache_key]
    
    api_key = os.environ.get("EMERGENT_LLM_KEY")
    if not api_key:
        logger.warning("EMERGENT_LLM_KEY not set, using placeholder sprite")
        return generate_placeholder_sprite(building_type, level)
    
    try:
        from emergentintegrations.llm.openai.image_generation import OpenAIImageGeneration
        
        # Build prompt
        building_config = BUILDING_PROMPTS.get(building_type, BUILDING_PROMPTS.get("shop"))
        base_prompt = building_config["base"]
        level_detail = building_config.get("levels", {}).get(level, f"level {level}")
        
        full_prompt = f"{base_prompt}, {level_detail}"
        
        logger.info(f"Generating sprite for {building_type} level {level}")
        
        image_gen = OpenAIImageGeneration(api_key=api_key)
        images = await image_gen.generate_images(
            prompt=full_prompt,
            model="gpt-image-1",
            number_of_images=1
        )
        
        if images and len(images) > 0:
            image_base64 = base64.b64encode(images[0]).decode('utf-8')
            sprite_data = f"data:image/png;base64,{image_base64}"
            
            # Cache the result
            sprite_cache[cache_key] = sprite_data
            logger.info(f"Sprite generated and cached: {cache_key}")
            
            return sprite_data
        else:
            logger.warning(f"No image generated for {cache_key}")
            return generate_placeholder_sprite(building_type, level)
            
    except Exception as e:
        logger.error(f"Sprite generation failed: {e}")
        return generate_placeholder_sprite(building_type, level)


async def get_construction_sprite() -> str:
    """Get the construction/building sprite"""
    return await generate_building_sprite("construction", 1)


async def pregenerate_sprites(building_types: list = None, levels: list = None):
    """
    Pre-generate sprites for common building types and levels.
    Call this on server startup to warm up the cache.
    """
    if building_types is None:
        building_types = ["farm", "factory", "shop", "restaurant", "bank"]
    if levels is None:
        levels = [1, 2, 3, 5, 10]  # Common levels
    
    logger.info(f"Pre-generating sprites for {len(building_types)} types, {len(levels)} levels")
    
    tasks = []
    for bt in building_types:
        for level in levels:
            tasks.append(generate_building_sprite(bt, level))
    
    await asyncio.gather(*tasks, return_exceptions=True)
    logger.info(f"Sprite pre-generation complete. Cache size: {len(sprite_cache)}")


def get_cached_sprite(building_type: str, level: int) -> Optional[str]:
    """Get sprite from cache without generating"""
    cache_key = f"{building_type}_L{level}"
    return sprite_cache.get(cache_key)


def clear_sprite_cache():
    """Clear all cached sprites"""
    sprite_cache.clear()
    logger.info("Sprite cache cleared")
