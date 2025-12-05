# ARC Raiders Companion App - Data Structure Documentation

## Overview

This document describes the complete data structure used in the ARC Raiders Companion application. The application is a Streamlit-based web tool that provides information about items, crafting recipes, hideout upgrades, quests, bots, maps, trades, skill nodes, and projects from the ARC Raiders game.

## Data File Organization

The application uses JSON files organized in two main locations:

### Primary Data Files (in `/data` directory)
- `items.json` - Complete item database
- `hideoutModules.json` - Hideout station upgrade requirements
- `quests.json` - Quest information and objectives

### Extended Data Files (in `/arcraiders-data-main` directory)
- `bots.json` - Enemy bot information
- `maps.json` - Map/location data
- `trades.json` - Trader exchange information
- `skillNodes.json` - Skill tree node data
- `projects.json` - Project/expedition data

---

## 1. Items Data Structure (`items.json`)

### Schema
```json
{
  "id": "string",                    // Unique item identifier (e.g., "fabric", "arc_alloy")
  "name": {                          // Multi-language name object
    "en": "string",                  // English name
    "de": "string",                  // German
    "fr": "string",                  // French
    "es": "string",                  // Spanish
    "pt": "string",                  // Portuguese
    "pl": "string",                  // Polish
    "no": "string",                  // Norwegian
    "da": "string",                  // Danish
    "it": "string",                  // Italian
    "ru": "string",                  // Russian
    "ja": "string",                  // Japanese
    "zh-CN": "string",               // Simplified Chinese
    "zh-TW": "string",               // Traditional Chinese
    "uk": "string",                  // Ukrainian
    "tr": "string",                  // Turkish
    "kr": "string",                  // Korean
    "hr": "string",                  // Croatian
    "sr": "string"                   // Serbian
  },
  "description": {                   // Multi-language description (same language keys as name)
    "en": "string",
    // ... other languages
  },
  "type": "string",                  // Item category (e.g., "Basic Material", "Weapon", "Consumable")
  "rarity": "string",                // Rarity level (e.g., "Common", "Rare", "Epic", "Legendary")
  "value": number,                   // Sell value in coins
  "recyclesInto": {                  // Materials obtained when recycling/scrapping
    "material_id": quantity,         // Key: item ID, Value: quantity produced
    // Example: {"metal_parts": 2, "plastic_parts": 1}
  },
  "imageFilename": "string",         // URL to item image (e.g., "https://cdn.arctracker.io/items/fabric.png")
  "weightKg": number,                // Item weight in kilograms
  "stackSize": number,               // Maximum stack size in inventory
  "foundIn": "string",               // Location description (e.g., "Commercial, Medical, Residential")
  "effects": {                       // Item effects/statistics (optional)
    "EffectName": {
      "en": "string",                // Effect name in English
      // ... other languages
      "value": "string"              // Effect value (e.g., "0.4/s", "25s")
    }
  },
  "recipe": {                        // Crafting recipe (optional)
    "ingredient_id": quantity,       // Key: item ID, Value: quantity required
    // Example: {"fabric": 2, "metal_parts": 1}
  },
  "craftBench": "string"             // Required crafting station (optional)
}
```

### Example Item
```json
{
  "id": "fabric",
  "name": {
    "en": "Fabric",
    "de": "Stoff",
    "fr": "Tissu"
  },
  "description": {
    "en": "Used to craft medical supplies and shields. Can be used to slowly restore small amounts of health."
  },
  "type": "Basic Material",
  "rarity": "Common",
  "value": 50,
  "recyclesInto": {},
  "imageFilename": "https://cdn.arctracker.io/items/fabric.png",
  "weightKg": 0.1,
  "stackSize": 50,
  "foundIn": "Commercial, Medical, Residential",
  "effects": {
    "Healing": {
      "en": "Healing",
      "value": "0.4/s"
    },
    "Duration": {
      "en": "Duration",
      "value": "25s"
    }
  }
}
```

---

## 2. Hideout Modules Data Structure (`hideoutModules.json`)

### Schema
```json
{
  "id": "string",                    // Module identifier (e.g., "scrappy", "workbench", "stash")
  "name": {                          // Multi-language name (same structure as items)
    "en": "string",
    // ... other languages
  },
  "maxLevel": number,                // Maximum upgrade level
  "levels": [                         // Array of level definitions
    {
      "level": number,                // Level number (1, 2, 3, etc.)
      "requirementItemIds": [         // Items required for this upgrade
        {
          "itemId": "string",         // Item ID
          "quantity": number          // Quantity required
        }
      ],
      "otherRequirements": [          // Non-item requirements (optional)
        "string"                      // e.g., "5000 Coins"
      ],
      "description": "string"         // Level description (optional)
    }
  ]
}
```

### Example Hideout Module
```json
{
  "id": "scrappy",
  "name": {
    "en": "Scrappy",
    "de": "Scrappy",
    "fr": "Coquillard"
  },
  "maxLevel": 5,
  "levels": [
    {
      "level": 1,
      "requirementItemIds": []
    },
    {
      "level": 2,
      "requirementItemIds": [
        {
          "itemId": "dog_collar",
          "quantity": 1
        }
      ]
    },
    {
      "level": 3,
      "requirementItemIds": [
        {
          "itemId": "lemon",
          "quantity": 3
        },
        {
          "itemId": "apricot",
          "quantity": 3
        }
      ]
    }
  ]
}
```

---

## 3. Quests Data Structure (`quests.json`)

### Schema
```json
{
  "id": "string",                    // Quest identifier (e.g., "ss1", "ss2")
  "updatedAt": "string",              // Last update date (e.g., "11/06/2025")
  "name": {                          // Multi-language quest name
    "en": "string",
    // ... other languages
  },
  "trader": "string",                 // Trader who gives the quest (e.g., "Shani", "Celeste", "Apollo")
  "description": {                   // Multi-language quest description
    "en": "string",
    // ... other languages
  },
  "objectives": [                    // Quest objectives
    {
      "en": "string",                // Objective text in English
      // ... other languages
    }
  ],
  "rewardItemIds": [                 // Rewards for completing quest
    {
      "itemId": "string",            // Item ID
      "quantity": number             // Quantity awarded
    }
  ],
  "xp": number,                      // Experience points awarded
  "previousQuestIds": [              // Prerequisite quest IDs
    "string"
  ],
  "nextQuestIds": [                  // Follow-up quest IDs
    "string"
  ]
}
```

### Example Quest
```json
{
  "id": "ss1",
  "updatedAt": "11/06/2025",
  "name": {
    "en": "Picking Up The Pieces",
    "de": "Die Scherben aufsammeln"
  },
  "trader": "Shani",
  "description": {
    "en": "The storm has mostly settled, but much of our infrastructure has taken a proper beating."
  },
  "objectives": [
    {
      "en": "Visit any area on your map with a loot category icon"
    },
    {
      "en": "Loot 3 containers"
    }
  ],
  "rewardItemIds": [
    {
      "itemId": "ferro_iii",
      "quantity": 1
    },
    {
      "itemId": "medium_ammo",
      "quantity": 80
    }
  ],
  "xp": 0,
  "previousQuestIds": [],
  "nextQuestIds": ["ss2", "ss3"]
}
```

---

## 4. Bots Data Structure (`bots.json`)

### Schema
```json
{
  "id": "string",                    // Bot identifier (e.g., "arc_bastion", "arc_bombardier")
  "name": "string",                  // Bot name (e.g., "BASTION", "BOMBARDIER")
  "image": "string",                 // URL to bot image
  "type": "string",                  // Bot type (e.g., "Heavy Assault", "Heavy Artillery", "Area Denial")
  "threat": "string",                // Threat level (e.g., "Critical", "High", "Medium", "Low")
  "description": "string",           // Bot description
  "weakness": "string",              // How to defeat the bot
  "maps": [                          // Maps where this bot appears
    "string"                         // Map IDs
  ],
  "destroyXp": number,               // XP for destroying the bot
  "lootXp": number,                  // XP for looting the bot
  "drops": [                         // Items that drop from this bot
    "string"                         // Item IDs
  ]
}
```

### Example Bot
```json
{
  "id": "arc_bastion",
  "name": "BASTION",
  "image": "https://cdn.arctracker.io/bots/arc_bastion.png",
  "type": "Heavy Assault",
  "threat": "Critical",
  "description": "Massive, crab-like machines that are slow but devastating.",
  "weakness": "Destroy the canister on his rear, to expose it's weakpoint.",
  "maps": ["dam_battlegrounds", "the_spaceport", "the_blue_gate"],
  "destroyXp": 500,
  "lootXp": 250,
  "drops": ["arc_alloy", "arc_powercell", "arc_motion_core", "arc_circuitry", "bastion_cell"]
}
```

---

## 5. Maps Data Structure (`maps.json`)

### Schema
```json
{
  "id": "string",                    // Map identifier (e.g., "dam_battlegrounds", "the_spaceport")
  "name": {                          // Multi-language map name
    "en": "string",
    // ... other languages
  },
  "image": "string"                  // URL to map image
}
```

### Example Map
```json
{
  "id": "dam_battlegrounds",
  "name": {
    "en": "Dam Battlegrounds",
    "de": "Damm-Schlachtfelder",
    "fr": "barrages_champs_de_bataille"
  },
  "image": "https://cdn.arctracker.io/maps/dam_battlegrounds.png"
}
```

---

## 6. Trades Data Structure (`trades.json`)

### Schema
```json
{
  "trader": "string",                // Trader name (e.g., "Celeste", "Apollo", "Shani", "Lance", "Tianwen")
  "itemId": "string",                // Item being sold
  "quantity": number,                // Quantity sold
  "cost": {                          // Cost to purchase
    "itemId": "string",              // Item ID used as currency
    "quantity": number               // Quantity required
  },
  "dailyLimit": number | null        // Daily purchase limit (null = unlimited)
}
```

### Example Trade
```json
{
  "trader": "Celeste",
  "itemId": "chemicals",
  "quantity": 1,
  "cost": {
    "itemId": "assorted_seeds",
    "quantity": 1
  },
  "dailyLimit": null
}
```

---

## 7. Skill Nodes Data Structure (`skillNodes.json`)

### Schema
```json
{
  "id": "string",                    // Skill node identifier
  "name": {                          // Multi-language skill name
    "en": "string",
    // ... other languages
  },
  "description": {                   // Multi-language skill description
    "en": "string",
    // ... other languages
  },
  "impactedSkill": {                 // Skill affected by this node
    "en": "string",
    // ... other languages
  }
  // Additional properties may include prerequisites, costs, etc.
}
```

### Example Skill Node
```json
{
  "id": "cond_1",
  "name": {
    "en": "Used To The Weight",
    "de": "An das Gewicht gewöhnt"
  },
  "description": {
    "en": "Wearing a shield doesn't slow you down as much."
  },
  "impactedSkill": {
    "en": "Movement Speed",
    "de": "Bewegungsgeschwindigkeit"
  }
}
```

---

## 8. Projects Data Structure (`projects.json`)

### Schema
```json
{
  "id": "string",                    // Project identifier (e.g., "expedition_project")
  "name": {                          // Multi-language project name
    "en": "string",
    // ... other languages
  },
  "description": {                   // Multi-language project description
    "en": "string",
    // ... other languages
  },
  "phases": [                        // Project phases
    {
      "phase": number,               // Phase number
      "name": {                      // Phase name
        "en": "string",
        // ... other languages
      }
      // Additional phase properties (requirements, rewards, etc.)
    }
  ]
}
```

### Example Project
```json
{
  "id": "expedition_project",
  "name": {
    "en": "Expedition Project",
    "de": "Expedition"
  },
  "description": {
    "en": "Embark on a dangerous expedition beyond the Rust Belt."
  },
  "phases": [
    {
      "phase": 1,
      "name": {
        "en": "Foundation",
        "de": "Grundgestell"
      }
    }
  ]
}
```

---

## Data Relationships

### Key Relationships:

1. **Items ↔ Hideout Modules**: Items are referenced by `itemId` in hideout module requirements
2. **Items ↔ Quests**: Items are referenced in quest rewards (`rewardItemIds`)
3. **Items ↔ Trades**: Items are referenced in trade definitions (`itemId`, `cost.itemId`)
4. **Items ↔ Bots**: Items are referenced in bot drop lists (`drops`)
5. **Quests ↔ Quests**: Quests reference each other via `previousQuestIds` and `nextQuestIds`
6. **Bots ↔ Maps**: Bots reference maps via `maps` array
7. **Items ↔ Items**: Items can reference other items in:
   - `recyclesInto` (recycling outputs)
   - `recipe` (crafting ingredients)

---

## Application Data Loading

The application (`app.py`) currently loads data using the following structure:

```python
data = {
    "items": [],      # Loaded from data/items.json
    "modules": []     # Loaded from data/hideoutModules.json
}
```

The application primarily uses:
- **Items**: For item database, scrap calculator, and crafting recipes
- **Hideout Modules**: For station upgrade requirements

Additional data files (bots, maps, trades, quests, skillNodes, projects) are available in the `arcraiders-data-main` directory but are not currently loaded by the main application.

---

## Language Support

All text fields support multiple languages using a consistent language code system:
- `en` - English
- `de` - German
- `fr` - French
- `es` - Spanish
- `pt` - Portuguese
- `pl` - Polish
- `no` - Norwegian
- `da` - Danish
- `it` - Italian
- `ru` - Russian
- `ja` - Japanese
- `zh-CN` - Simplified Chinese
- `zh-TW` - Traditional Chinese
- `uk` - Ukrainian
- `tr` - Turkish
- `kr` - Korean
- `hr` - Croatian
- `sr` - Serbian

---

## Data Statistics

Based on the file structure:
- **Items**: 452+ individual item JSON files + 1 consolidated `items.json`
- **Quests**: 80+ quest files
- **Hideout Modules**: 9 module types (scrappy, workbench, stash, etc.)
- **Bots**: 15+ bot types
- **Maps**: 6 map locations
- **Trades**: 900+ trade entries
- **Skill Nodes**: Multiple skill tree nodes
- **Projects**: Multiple project types

---

## Notes for Integration

1. **Item IDs**: All item references use consistent string IDs (e.g., `"fabric"`, `"arc_alloy"`)
2. **Image URLs**: Images are hosted on CDN at `https://cdn.arctracker.io/`
3. **Optional Fields**: Many fields are optional - always check for existence before accessing
4. **Array Structures**: Most data is stored as JSON arrays at the root level
5. **Nested Objects**: Multi-language support uses nested objects with language codes as keys

---

## Future Considerations

- Consider normalizing item references to reduce data duplication
- Add validation schemas for data integrity
- Consider database migration for better query performance
- Implement caching strategies for large datasets
- Add versioning for data updates

---

*Document generated for academic/collaborative purposes*
*Last updated: Based on current codebase structure*

