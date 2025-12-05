import streamlit as st
import json
import glob

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="ARC Raiders Companion", layout="wide", page_icon="🦾")

# --- 2. ROBUST DATA LOADER ---
@st.cache_data
def load_database():
    """
    Loads all JSON files into a relational dictionary.
    Aggregates individual files from arcraiders-data-main directory.
    Uses try/except to safely handle missing files.
    """
    db = {
        "items": [],
        "modules": [],
        "quests": [],
        "bots": [],
        "trades": [],
        "maps": []
    }
    
    # Load items from individual files
    item_files = glob.glob("arcraiders-data-main/items/*.json")
    for item_file in item_files:
        try:
            with open(item_file, "r", encoding="utf-8") as f:
                item_data = json.load(f)
                if isinstance(item_data, dict):
                    db["items"].append(item_data)
        except (FileNotFoundError, json.JSONDecodeError):
            pass
    
    # Load hideout modules from individual files
    module_files = glob.glob("arcraiders-data-main/hideout/*.json")
    for module_file in module_files:
        try:
            with open(module_file, "r", encoding="utf-8") as f:
                module_data = json.load(f)
                if isinstance(module_data, dict):
                    db["modules"].append(module_data)
        except (FileNotFoundError, json.JSONDecodeError):
            pass
    
    # Load quests from individual files
    quest_files = glob.glob("arcraiders-data-main/quests/*.json")
    for quest_file in quest_files:
        try:
            with open(quest_file, "r", encoding="utf-8") as f:
                quest_data = json.load(f)
                if isinstance(quest_data, dict):
                    db["quests"].append(quest_data)
        except (FileNotFoundError, json.JSONDecodeError):
            pass
    
    # Load consolidated files
    try:
        with open("arcraiders-data-main/bots.json", "r", encoding="utf-8") as f:
            db["bots"] = json.load(f)
    except FileNotFoundError:
        pass
    
    try:
        with open("arcraiders-data-main/trades.json", "r", encoding="utf-8") as f:
            db["trades"] = json.load(f)
    except FileNotFoundError:
        pass
    
    try:
        with open("arcraiders-data-main/maps.json", "r", encoding="utf-8") as f:
            db["maps"] = json.load(f)
    except FileNotFoundError:
        pass
            
    # Pre-build lookup dictionaries for O(1) lookups
    db["item_by_id"] = {item["id"]: item for item in db["items"] if "id" in item}
    db["quests_by_item"] = {}
    db["upgrades_by_item"] = {}
    
    # Build quest lookup
    for quest in db["quests"]:
        if "requiredItemIds" in quest:
            for req in quest["requiredItemIds"]:
                item_id = req["itemId"]
                if item_id not in db["quests_by_item"]:
                    db["quests_by_item"][item_id] = []
                db["quests_by_item"][item_id].append(quest)
    
    # Build upgrade lookup
    for mod in db["modules"]:
        if "levels" in mod:
            for lvl in mod["levels"]:
                if "requirementItemIds" in lvl:
                    for req in lvl["requirementItemIds"]:
                        item_id = req["itemId"]
                        if item_id not in db["upgrades_by_item"]:
                            db["upgrades_by_item"][item_id] = []
                        db["upgrades_by_item"][item_id].append({
                            "module": mod,
                            "level": lvl
                        })
    
    return db

# Load database with spinner
with st.spinner("Loading game data..."):
    DB = load_database()

# Check if database loaded successfully
if not DB["items"]:
    st.error("⚠️ No items loaded! Please check that arcraiders-data-main/items/*.json files exist.")
    st.stop()

# --- 3. LOGIC FUNCTIONS ---

def get_item_name(item_id):
    """Returns English name if available, else ID - uses lookup dictionary"""
    item = DB["item_by_id"].get(item_id)
    if item and "name" in item and "en" in item["name"]:
        return item["name"]["en"]
    return item_id.replace("_", " ").title()

def get_item_by_id(item_id):
    """Get item by ID using lookup dictionary"""
    return DB["item_by_id"].get(item_id)

def get_item_name_with_scrap(item_id):
    """Returns item name with scrap breakdown for dropdowns"""
    item = DB["item_by_id"].get(item_id)
    name = get_item_name(item_id)
    
    if item and "recyclesInto" in item and item["recyclesInto"]:
        scrap_items = []
        for mat_id, qty in item["recyclesInto"].items():
            mat_name = get_item_name(mat_id)
            scrap_items.append(f"{mat_name} x{qty}")
        scrap_text = " → " + ", ".join(scrap_items)
        return f"{name}{scrap_text}"
    
    return name

def display_ingredient_details(mat_id, qty):
    """Display full ingredient information in an expander"""
    mat_item = get_item_by_id(mat_id)
    mat_name = get_item_name(mat_id)
    
    if not mat_item:
        st.write(f"**{mat_name}**: x{qty} (Item data not found)")
        return
    
    # Check if ingredient can be obtained from scrap
    can_scrap = any(i for i in DB["items"] if "recyclesInto" in i and mat_id in i["recyclesInto"])
    scrap_indicator = "♻️" if can_scrap else ""
    
    with st.expander(f"{scrap_indicator} **{mat_name}** - x{qty} (Click for details)", expanded=False):
        col1, col2 = st.columns([1, 2])
        
        with col1:
            if "imageFilename" in mat_item:
                st.image(mat_item["imageFilename"], width=120)
            if "value" in mat_item:
                st.caption(f"💰 Sell Value: {mat_item['value']} coins")
            if "weightKg" in mat_item:
                st.caption(f"⚖️ Weight: {mat_item['weightKg']}kg")
        
        with col2:
            st.write(f"**Type:** {mat_item.get('type', 'Misc')} | **Rarity:** {mat_item.get('rarity', 'Common')}")
            if "description" in mat_item:
                st.write(f"_{mat_item['description'].get('en', '')}_")
            
            st.divider()
            
            # Reverse Scrap Sources
            scrap_sources = []
            for i in DB["items"]:
                if "recyclesInto" in i and mat_id in i["recyclesInto"]:
                    yield_qty = i["recyclesInto"][mat_id]
                    uses = find_usage(i["id"])
                    is_quest = any(u["type"] == "quest" for u in uses)
                    has_upgrade = any(u["type"] == "upgrade" for u in uses)
                    has_crafting = any(u["type"] == "crafting" for u in uses)
                    
                    # Calculate usefulness score (same as main Reverse Scrap Calculator)
                    if is_quest:
                        usefulness_score = 3
                    elif has_upgrade:
                        usefulness_score = 2
                    elif has_crafting:
                        usefulness_score = 1
                    else:
                        usefulness_score = 0  # No usage - best to recycle
                    
                    scrap_sources.append({
                        "name": i.get("name", {}).get("en", "Unknown"),
                        "qty": yield_qty,
                        "id": i["id"],
                        "found_in": i.get("foundIn", "Unknown"),
                        "usefulness_score": usefulness_score,
                        "is_quest": is_quest,
                        "has_upgrade": has_upgrade,
                        "has_crafting": has_crafting,
                        "uses": uses
                    })
            
            if scrap_sources:
                # Sort by usefulness (least useful first), then by yield quantity
                scrap_sources.sort(key=lambda x: (x["usefulness_score"], -x["qty"]))
                st.subheader("♻️ Reverse Scrap Sources")
                st.caption(f"These items can be recycled to obtain {mat_name} (sorted by usefulness - best to recycle first):")
                for source in scrap_sources[:10]:  # Limit to top 10
                    # Apply color coding based on usefulness
                    if source["usefulness_score"] == 0:
                        st.success(f"- **{source['name']}** → {source['qty']}x {mat_name} | ✅ **BEST TO RECYCLE** (No usage)")
                    elif source["usefulness_score"] == 1:
                        st.warning(f"- **{source['name']}** → {source['qty']}x {mat_name} | ⚠️ Used in crafting")
                    elif source["usefulness_score"] == 2:
                        st.warning(f"- **{source['name']}** → {source['qty']}x {mat_name} | ⚠️ Used in upgrades")
                    else:
                        st.error(f"- **{source['name']}** → {source['qty']}x {mat_name} | 🚨 **QUEST ITEM - DO NOT RECYCLE**")
                    
                    if source["found_in"] != "Unknown":
                        st.caption(f"  📍 Found in: {source['found_in']}")
            else:
                st.info(f"⚠️ {mat_name} cannot be obtained from recycling/scrapping items")
            
            # Usage Information
            uses = find_usage(mat_id)
            if uses:
                st.divider()
                st.subheader("⚠️ Usage Information")
                
                quest_uses = [u for u in uses if u["type"] == "quest"]
                upgrade_uses = [u for u in uses if u["type"] == "upgrade"]
                crafting_uses = [u for u in uses if u["type"] == "crafting"]
                trade_uses = [u for u in uses if u["type"] == "trade"]
                
                if quest_uses:
                    st.error("**🚨 QUEST ITEM - DO NOT SELL!**")
                    for use in quest_uses:
                        st.write(f"- 📜 **Quest:** {use['name']} (Need: {use['quantity']}x) - Trader: {use.get('trader', 'Unknown')}")
                
                if upgrade_uses:
                    st.warning("**🔨 Used in Hideout Upgrades:**")
                    for use in upgrade_uses:
                        st.write(f"- {use['name']} Level {use['level']} (Need: {use['quantity']}x)")
                
                if crafting_uses:
                    st.warning("**🛠️ Used in Other Crafting Recipes:**")
                    for use in crafting_uses:
                        st.write(f"- Recipe: {use['name']} (Need: {use['quantity']}x)")
                
                if trade_uses:
                    st.info("**💱 Can be Traded:**")
                    for use in trade_uses:
                        st.write(f"- Trader: {use['trader']} (Cost: {use['quantity']}x)")
            else:
                st.success("✅ Safe to sell - No current quest, upgrade, or crafting use found")
            
            # Where to Find
            sources = find_sources(mat_id)
            if sources:
                st.divider()
                st.subheader("📍 Where to Find")
                for source in sources:
                    st.write(f"- {source}")

def find_usage(item_id):
    """Checks Quests, Trades, Upgrades, and Crafting for this item - optimized with lookup dictionaries"""
    usage = []
    
    # Check Modules (Upgrades) - use lookup dictionary
    if item_id in DB["upgrades_by_item"]:
        for upgrade_info in DB["upgrades_by_item"][item_id]:
            mod = upgrade_info["module"]
            lvl = upgrade_info["level"]
            for req in lvl.get("requirementItemIds", []):
                if req["itemId"] == item_id:
                    usage.append({
                        "type": "upgrade",
                        "name": mod.get('name', {}).get('en', 'Unknown'),
                        "level": lvl.get('level', 0),
                        "quantity": req.get('quantity', 1)
                    })

    # Check Quests - use lookup dictionary
    if item_id in DB["quests_by_item"]:
        for quest in DB["quests_by_item"][item_id]:
            for req in quest.get("requiredItemIds", []):
                if req["itemId"] == item_id:
                    usage.append({
                        "type": "quest",
                        "name": quest.get('name', {}).get('en', 'Unknown'),
                        "trader": quest.get('trader', 'Unknown'),
                        "quantity": req.get('quantity', 1)
                    })
    
    # Check Trades (items used as currency)
    for trade in DB["trades"]:
        if "cost" in trade and trade["cost"].get("itemId") == item_id:
            usage.append({
                "type": "trade",
                "trader": trade.get("trader", "Unknown"),
                "quantity": trade["cost"].get("quantity", 1)
            })
    
    # Check Crafting Recipes (items used as ingredients)
    for item in DB["items"]:
        recipe = item.get("recipe") or item.get("crafting") or item.get("craftMaterials")
        if recipe and isinstance(recipe, dict):
            if item_id in recipe:
                usage.append({
                    "type": "crafting",
                    "name": item.get("name", {}).get("en", "Unknown Item"),
                    "quantity": recipe[item_id]
                })
                    
    return usage

def find_sources(item_id):
    """Finds where an item comes from (Bots, Trades, Crafting) - optimized"""
    sources = []
    
    # Check Bots
    for bot in DB["bots"]:
        if "drops" in bot and item_id in bot["drops"]:
            sources.append(f"🤖 Drops from: {bot.get('name', 'Unknown Bot')}")
            
    # Check Crafting - use lookup dictionary
    item = DB["item_by_id"].get(item_id)
    if item:
        recipe = item.get("recipe") or item.get("crafting") or item.get("craftMaterials")
        if recipe:
            sources.append("🛠️ Craftable (See Recipe Book)")
    
    # Check Trades (items that can be purchased)
    for trade in DB["trades"]:
        if trade.get("itemId") == item_id:
            trader = trade.get("trader", "Unknown")
            cost = trade.get("cost", {})
            cost_item = get_item_name(cost.get("itemId", ""))
            cost_qty = cost.get("quantity", 0)
            sources.append(f"💱 Can be traded from {trader} (Cost: {cost_qty}x {cost_item})")
        
    return sources

def find_map_items(map_id):
    """Find all items available on a specific map through bot drops and foundIn locations"""
    map_items = {}
    
    # Find items through bot drops
    for bot in DB["bots"]:
        if "maps" in bot and map_id in bot["maps"]:
            if "drops" in bot:
                for item_id in bot["drops"]:
                    if item_id not in map_items:
                        map_items[item_id] = {
                            "sources": [],
                            "item": DB["item_by_id"].get(item_id)
                        }
                    map_items[item_id]["sources"].append({
                        "type": "bot_drop",
                        "bot_name": bot.get("name", "Unknown Bot"),
                        "bot_id": bot.get("id", "")
                    })
    
    # Find items through foundIn field (check if foundIn contains map-related keywords)
    map_name = ""
    for map_obj in DB["maps"]:
        if map_obj.get("id") == map_id:
            map_name = map_obj.get("name", {}).get("en", "").lower()
            break
    
    # Check items with foundIn field (this is a simple keyword match - may need refinement)
    # For now, we'll include items that might be found on maps through their foundIn field
    # This is less precise but provides additional context
    
    return map_items

# --- 4. UI: SIDEBAR ---
st.sidebar.title("🦾 ARC Raiders")
st.sidebar.caption("Companion Tool")
mode = st.sidebar.radio("Navigation", ["📦 Wiki", "♻️ Reverse Scrap", "🛠️ Crafting & Upgrades", "🗺️ Map Items", "🤖 Bots", "📜 Quests"], help="Wiki: Search items and see usage. Reverse Scrap: Find what items to pick up for materials. Crafting & Upgrades: View recipes and station upgrades. Map Items: View items found on specific maps. Bots: View enemy bot information, drops, and locations. Quests: View quest information, requirements, and rewards.")

# --- 5. MAIN PAGES ---

if mode == "📦 Wiki":
    st.title("📦 Item Database")
    query = st.text_input("Search Item...", "", key="item_search")
    
    if query:
        # Filter items by English name
        results = [i for i in DB["items"] if "id" in i and query.lower() in i.get("name", {}).get("en", "").lower()]
        
        # Display result count
        if results:
            st.caption(f"Found {len(results)} item(s) - Showing top 20")
        else:
            st.warning(f"No items found matching '{query}'. Try a different search term.")
        
        # Limit to top 20 results for speed
        for item in results[:20]:
            if "id" not in item:
                continue
            uses = find_usage(item["id"])
            
            # Determine status color
            has_quest = any(u["type"] == "quest" for u in uses)
            has_upgrade_or_craft = any(u["type"] in ["upgrade", "crafting"] for u in uses)
            
            # Create status badge
            if has_quest:
                status_color = "🔴"
                status_text = "QUEST ITEM - DO NOT SELL"
            elif has_upgrade_or_craft:
                status_color = "🟡"
                status_text = "Used in Upgrades/Crafting"
            else:
                status_color = "🟢"
                status_text = "Safe to Sell"
            
            with st.expander(f"{status_color} {item.get('name', {}).get('en', 'Unknown')} ({item.get('rarity', 'Common')})", expanded=True):
                c1, c2 = st.columns([1, 3])
                
                with c1:
                    # Display Image from CDN
                    if "imageFilename" in item:
                        st.image(item["imageFilename"], width=120)
                
                with c2:
                    # Basic Stats
                    st.write(f"**Type:** {item.get('type', 'Misc')}")
                    st.write(f"**Weight:** {item.get('weightKg', 0)}kg | **Stack:** {item.get('stackSize', 1)}")
                    if "value" in item:
                        st.write(f"**Sell Value:** 💰 {item['value']} coins")
                    st.write(f"_{item.get('description', {}).get('en', '')}_")
                    
                    # THE ANALYSIS ENGINE
                    st.divider()
                    
                    # Section: Why This Item Matters
                    if uses:
                        st.subheader("⚠️ Why This Item Matters")
                        
                        # Group by type and prioritize quests
                        quest_uses = [u for u in uses if u["type"] == "quest"]
                        upgrade_uses = [u for u in uses if u["type"] == "upgrade"]
                        crafting_uses = [u for u in uses if u["type"] == "crafting"]
                        trade_uses = [u for u in uses if u["type"] == "trade"]
                        
                        if quest_uses:
                            st.error("**🚨 QUEST ITEM - DO NOT SELL!**")
                            for use in quest_uses:
                                st.write(f"- 📜 **Quest:** {use['name']} (Need: {use['quantity']}x) - Trader: {use.get('trader', 'Unknown')}")
                        
                        if upgrade_uses:
                            st.warning("**🔨 Used in Hideout Upgrades:**")
                            for use in upgrade_uses:
                                st.write(f"- {use['name']} Level {use['level']} (Need: {use['quantity']}x)")
                        
                        if crafting_uses:
                            st.warning("**🛠️ Used in Crafting:**")
                            for use in crafting_uses:
                                st.write(f"- Recipe: {use['name']} (Need: {use['quantity']}x)")
                        
                        if trade_uses:
                            st.info("**💱 Can be Traded:**")
                            for use in trade_uses:
                                st.write(f"- Trader: {use['trader']} (Cost: {use['quantity']}x)")
                    else:
                        st.success("✅ **Safe to Sell** - No current quest, upgrade, crafting, or trade use found")
                    
                    # Section: Sources (Where to get it)
                    sources = find_sources(item["id"])
                    if sources:
                        st.divider()
                        st.subheader("📍 Where to Find")
                        st.info("\n".join(sources))
                        
                    # Section: Scrap Output
                    if "recyclesInto" in item and item["recyclesInto"]:
                        st.divider()
                        st.subheader("♻️ Recycles Into")
                        for mat, qty in item["recyclesInto"].items():
                            st.write(f"- {get_item_name(mat)} x{qty}")
    else:
        st.info("👆 Type an item name above to search...")

elif mode == "♻️ Reverse Scrap":
    st.title("♻️ Reverse Scrap Calculator")
    st.info("Select a material you need, and we'll tell you what junk items contain it.")
    
    # Get all unique materials that appear in "recyclesInto" keys
    all_mats = set()
    for i in DB["items"]:
        if "recyclesInto" in i:
            for k in i["recyclesInto"].keys():
                all_mats.add(k)
    
    if not all_mats:
        st.warning("No materials found in item recycling data.")
        st.stop()
                
    target_mat = st.selectbox("I need this material...", sorted(list(all_mats)), format_func=get_item_name_with_scrap)
    
    if target_mat:
        st.subheader(f"📦 Sources for {get_item_name(target_mat)}")
        
        # Find junk that yields this
        sources = []
        for i in DB["items"]:
            if "id" not in i:
                continue
            if "recyclesInto" in i and target_mat in i["recyclesInto"]:
                uses = find_usage(i["id"])
                is_quest_item = any(u["type"] == "quest" for u in uses)
                has_upgrade = any(u["type"] == "upgrade" for u in uses)
                has_crafting = any(u["type"] == "crafting" for u in uses)
                has_trade = any(u["type"] == "trade" for u in uses)
                
                # Calculate usefulness score (lower = less useful = better to recycle)
                # 0 = no usage (best to recycle), 1 = crafting only, 2 = upgrade only, 3 = quest (never recycle)
                if is_quest_item:
                    usefulness_score = 3
                elif has_upgrade:
                    usefulness_score = 2
                elif has_crafting:
                    usefulness_score = 1
                else:
                    usefulness_score = 0  # No usage - best to recycle
                
                # Calculate efficiency (yield per weight)
                weight = i.get("weightKg", 0.1)
                yield_qty = i["recyclesInto"][target_mat]
                efficiency = yield_qty / weight if weight > 0 else yield_qty
                
                sources.append({
                    "name": i.get("name", {}).get("en", "Unknown"),
                    "qty": yield_qty,
                    "id": i["id"],
                    "is_quest": is_quest_item,
                    "has_upgrade": has_upgrade,
                    "has_crafting": has_crafting,
                    "has_trade": has_trade,
                    "uses": uses,  # Store full usage info
                    "found_in": i.get("foundIn", "Unknown"),
                    "weight": weight,
                    "efficiency": efficiency,
                    "image": i.get("imageFilename", ""),
                    "usefulness_score": usefulness_score,
                    "item_data": i  # Store full item data for display
                })
        
        # Sort by usefulness (least useful first), then by yield quantity
        sources.sort(key=lambda x: (x["usefulness_score"], -x["qty"]))
        
        if sources:
            st.success(f"Found {len(sources)} item(s) that yield **{get_item_name(target_mat)}**")
            st.caption("💡 Items are sorted by usefulness - least useful items (best to recycle) appear first")
            
            # Show best value indicator (from items with no usage)
            no_usage_sources = [s for s in sources if s["usefulness_score"] == 0]
            if no_usage_sources:
                best_source = max(no_usage_sources, key=lambda x: x["efficiency"])
                if best_source["efficiency"] > 0:
                    st.caption(f"💡 Best Value (No Usage): {best_source['name']} ({best_source['efficiency']:.2f} yield/kg)")
            
            for s in sources:
                with st.container(border=True):
                    col1, col2, col3 = st.columns([1, 3, 1])
                    
                    with col1:
                        if s["image"]:
                            st.image(s["image"], width=80)
                    
                    with col2:
                        # Determine recommendation level
                        if s["usefulness_score"] == 0:
                            st.success(f"**{s['name']}** - Yields {s['qty']}x | ✅ **BEST TO RECYCLE** (No usage found)")
                        elif s["usefulness_score"] == 1:
                            st.warning(f"**{s['name']}** - Yields {s['qty']}x | ⚠️ Used in crafting")
                        elif s["usefulness_score"] == 2:
                            st.warning(f"**{s['name']}** - Yields {s['qty']}x | ⚠️ Used in upgrades")
                        else:
                            st.error(f"**{s['name']}** - Yields {s['qty']}x | 🚨 **QUEST ITEM - DO NOT RECYCLE**")
                        
                        if s["found_in"] != "Unknown":
                            st.caption(f"📍 Found in: {s['found_in']}")
                        st.caption(f"⚖️ Weight: {s['weight']}kg | Efficiency: {s['efficiency']:.2f} yield/kg")
                        
                        # Display usage information inline
                        if s["uses"]:
                            st.divider()
                            st.caption("**Where this item is used:**")
                            
                            quest_uses = [u for u in s["uses"] if u["type"] == "quest"]
                            upgrade_uses = [u for u in s["uses"] if u["type"] == "upgrade"]
                            crafting_uses = [u for u in s["uses"] if u["type"] == "crafting"]
                            trade_uses = [u for u in s["uses"] if u["type"] == "trade"]
                            
                            if quest_uses:
                                for use in quest_uses:
                                    st.caption(f"🚨 **Quest:** {use['name']} (Need: {use['quantity']}x) - Trader: {use.get('trader', 'Unknown')}")
                            
                            if upgrade_uses:
                                for use in upgrade_uses:
                                    st.caption(f"🔨 **Upgrade:** {use['name']} Level {use['level']} (Need: {use['quantity']}x)")
                            
                            if crafting_uses:
                                for use in crafting_uses:
                                    st.caption(f"🛠️ **Crafting:** {use['name']} (Need: {use['quantity']}x)")
                            
                            if trade_uses:
                                for use in trade_uses:
                                    st.caption(f"💱 **Trade:** {use['trader']} (Cost: {use['quantity']}x)")
                        else:
                            st.caption("✅ No quest, upgrade, or crafting usage found - Safe to recycle")
                    
                    with col3:
                        st.metric("Yield", f"{s['qty']}x")
                        if s["usefulness_score"] == 0:
                            st.caption("🟢 Best")
                        elif s["usefulness_score"] == 1:
                            st.caption("🟡 OK")
                        elif s["usefulness_score"] == 2:
                            st.caption("🟠 Risky")
                        else:
                            st.caption("🔴 Avoid")
        else:
            st.warning(f"No items found that recycle into {get_item_name(target_mat)}")
    else:
        st.info("👆 Select a material above to find sources...")

elif mode == "🛠️ Crafting & Upgrades":
    submode = st.radio("Category", ["Recipe Book", "Station Upgrades"], horizontal=True)
    
    if submode == "Recipe Book":
        st.title("📖 Recipe Book")
        st.info("Browse all craftable items and their recipes")
        
        # Find all craftable items
        craftables = []
        for item in DB["items"]:
            recipe = item.get("recipe") or item.get("crafting") or item.get("craftMaterials")
            if recipe and isinstance(recipe, dict):
                craftables.append(item)
        
        if craftables:
            # Create dropdown with scrap breakdown
            craftable_options = {}
            for item in craftables:
                item_id = item.get("id", "")
                item_name = item.get("name", {}).get("en", "Unknown")
                # Add scrap breakdown to display name
                display_name = get_item_name_with_scrap(item_id) if item_id else item_name
                craftable_options[display_name] = item
            
            target_name = st.selectbox("I want to craft...", sorted(craftable_options.keys()))
            target_item = craftable_options[target_name]
            
            # Display Recipe
            recipe = target_item.get("recipe") or target_item.get("crafting") or target_item.get("craftMaterials")
            
            st.divider()
            col1, col2 = st.columns([1, 2])
            
            with col1:
                if "imageFilename" in target_item:
                    st.image(target_item["imageFilename"], width=150)
                st.caption(f"**Crafting Station:** {target_item.get('craftBench', 'Unknown')}")
                if "type" in target_item:
                    st.caption(f"**Type:** {target_item['type']}")
                if "rarity" in target_item:
                    st.caption(f"**Rarity:** {target_item['rarity']}")
            
            with col2:
                st.subheader(f"🧪 {target_name}")
                if "description" in target_item:
                    st.write(target_item["description"].get("en", ""))
                
                st.divider()
                st.subheader("📋 Ingredients Required")
                st.caption("💡 Click on any ingredient to see detailed information including reverse scrap sources")
                
                for mat_id, qty in recipe.items():
                    display_ingredient_details(mat_id, qty)
        else:
            st.warning("No craftable items found in database")
    
    elif submode == "Station Upgrades":
        st.title("🏗️ Hideout Upgrade Tracker")
        st.info("View upgrade requirements for each hideout station")
        
        module_names = [m.get("name", {}).get("en", "Unknown") for m in DB["modules"]]
        target_mod = st.selectbox("Select Station", module_names)
        
        # Find the module data
        mod_data = next((m for m in DB["modules"] if m.get("name", {}).get("en") == target_mod), None)
        
        if mod_data:
            st.subheader(f"{target_mod}")
            st.caption(f"Max Level: {mod_data.get('maxLevel', 'Unknown')}")
            
            # Shopping list view
            all_requirements = {}
            for level in mod_data.get("levels", []):
                if "requirementItemIds" in level:
                    for req in level["requirementItemIds"]:
                        item_id = req["itemId"]
                        qty = req.get("quantity", 1)
                        if item_id in all_requirements:
                            all_requirements[item_id] += qty
                        else:
                            all_requirements[item_id] = qty
            
            if all_requirements:
                with st.expander("📝 Complete Shopping List (All Levels)", expanded=False):
                    st.caption("💡 Click on any item to see detailed information including reverse scrap sources")
                    for item_id, total_qty in sorted(all_requirements.items()):
                        display_ingredient_details(item_id, total_qty)
            
            st.divider()
            
            # Show each level
            for level in mod_data.get("levels", []):
                level_num = level.get("level", 0)
                with st.expander(f"Level {level_num}", expanded=(level_num <= 2)):
                    if "description" in level:
                        st.caption(level["description"])
                    
                    if "requirementItemIds" in level and level["requirementItemIds"]:
                        st.write("**Items Required:**")
                        st.caption("💡 Click on any item to see detailed information including reverse scrap sources")
                        for req in level["requirementItemIds"]:
                            display_ingredient_details(req["itemId"], req.get('quantity', 1))
                    else:
                        st.write("No material requirements (Starter level)")
                    
                    if "otherRequirements" in level and level["otherRequirements"]:
                        st.write("**Other Requirements:**")
                        for other in level["otherRequirements"]:
                            st.write(f"- {other}")
        else:
            st.error("Station not found")

elif mode == "🗺️ Map Items":
    st.title("🗺️ Map-Specific Item List")
    st.info("View items found on each map through bot drops and location-based loot")
    
    if not DB["maps"]:
        st.warning("No maps data loaded. Please check that arcraiders-data-main/maps.json exists.")
        st.stop()
    
    # Create map selector
    map_options = {m.get("name", {}).get("en", "Unknown"): m for m in DB["maps"]}
    selected_map_name = st.selectbox("Select a Map", sorted(map_options.keys()))
    selected_map = map_options[selected_map_name]
    map_id = selected_map.get("id", "")
    
    if map_id:
        # Display map image
        if "image" in selected_map:
            st.image(selected_map["image"], width=400)
        
        st.divider()
        
        # Find items for this map
        map_items = find_map_items(map_id)
        
        if map_items:
            st.subheader(f"📦 Items Found on {selected_map_name}")
            st.caption(f"Found {len(map_items)} unique item(s) through bot drops")
            st.caption("💡 Click on any item to see detailed information including reverse scrap sources")
            
            # Sort items by name
            sorted_items = sorted(map_items.items(), key=lambda x: x[1]["item"].get("name", {}).get("en", "Unknown") if x[1]["item"] else "Unknown")
            
            for item_id, item_info in sorted_items:
                item = item_info["item"]
                if not item:
                    continue
                
                # Show item with sources
                sources_list = item_info["sources"]
                bot_sources = [s for s in sources_list if s["type"] == "bot_drop"]
                
                if bot_sources:
                    bot_names = ", ".join([s["bot_name"] for s in bot_sources])
                    with st.expander(f"📦 {item.get('name', {}).get('en', 'Unknown')} - Drops from: {bot_names}", expanded=False):
                        # Use the same detailed display as other sections
                        display_ingredient_details(item_id, 1)
                        
                        # Show specific bot drop information
                        st.divider()
                        st.subheader("🤖 Bot Drop Sources")
                        for source in bot_sources:
                            bot_obj = next((b for b in DB["bots"] if b.get("id") == source["bot_id"]), None)
                            if bot_obj:
                                col_a, col_b = st.columns([1, 3])
                                with col_a:
                                    if "image" in bot_obj:
                                        st.image(bot_obj["image"], width=100)
                                with col_b:
                                    st.write(f"**{source['bot_name']}**")
                                    st.caption(f"Type: {bot_obj.get('type', 'Unknown')} | Threat: {bot_obj.get('threat', 'Unknown')}")
                                    if "description" in bot_obj:
                                        st.caption(bot_obj["description"])
                                    if "weakness" in bot_obj:
                                        st.caption(f"💡 Weakness: {bot_obj['weakness']}")
        else:
            st.warning(f"No items found for {selected_map_name}. Items may be found through other means (loot containers, etc.)")

elif mode == "🤖 Bots":
    st.title("🤖 Enemy Bot Database")
    st.info("View detailed information about enemy bots, their drops, locations, and combat strategies")
    
    if not DB["bots"]:
        st.warning("No bots data loaded. Please check that arcraiders-data-main/bots.json exists.")
        st.stop()
    
    # Search and filter options
    col1, col2, col3 = st.columns(3)
    
    with col1:
        search_query = st.text_input("🔍 Search Bot Name", "", key="bot_search")
    
    with col2:
        bot_types = sorted(list(set([b.get("type", "Unknown") for b in DB["bots"] if b.get("type")])))
        selected_type = st.selectbox("Filter by Type", ["All"] + bot_types)
    
    with col3:
        threat_levels = sorted(list(set([b.get("threat", "Unknown") for b in DB["bots"] if b.get("threat")])))
        selected_threat = st.selectbox("Filter by Threat", ["All"] + threat_levels)
    
    # Filter bots
    filtered_bots = DB["bots"]
    
    if search_query:
        filtered_bots = [b for b in filtered_bots if search_query.lower() in b.get("name", "").lower()]
    
    if selected_type != "All":
        filtered_bots = [b for b in filtered_bots if b.get("type") == selected_type]
    
    if selected_threat != "All":
        filtered_bots = [b for b in filtered_bots if b.get("threat") == selected_threat]
    
    # Sort by threat level (Critical > High > Medium > Low), then by name
    threat_order = {"Critical": 4, "High": 3, "Medium": 2, "Low": 1}
    filtered_bots.sort(key=lambda x: (threat_order.get(x.get("threat", "Unknown"), 0), x.get("name", "").lower()), reverse=True)
    
    if filtered_bots:
        st.success(f"Found {len(filtered_bots)} bot(s)")
        
        for bot in filtered_bots:
            # Determine threat color
            threat = bot.get("threat", "Unknown")
            if threat == "Critical":
                threat_color = "🔴"
            elif threat == "High":
                threat_color = "🟠"
            elif threat == "Medium":
                threat_color = "🟡"
            else:
                threat_color = "🟢"
            
            with st.expander(f"{threat_color} **{bot.get('name', 'Unknown')}** - {bot.get('type', 'Unknown')} ({threat} Threat)", expanded=False):
                col_a, col_b = st.columns([1, 2])
                
                with col_a:
                    if "image" in bot:
                        st.image(bot["image"], width=200)
                    
                    # Bot stats
                    if "destroyXp" in bot:
                        st.metric("Destroy XP", bot["destroyXp"])
                    if "lootXp" in bot:
                        st.metric("Loot XP", bot["lootXp"])
                
                with col_b:
                    st.subheader(f"{bot.get('name', 'Unknown')}")
                    st.write(f"**Type:** {bot.get('type', 'Unknown')} | **Threat Level:** {threat}")
                    
                    if "description" in bot:
                        st.write(f"_{bot['description']}_")
                    
                    if "weakness" in bot:
                        st.divider()
                        st.warning(f"💡 **Weakness:** {bot['weakness']}")
                    
                    # Maps where bot appears
                    if "maps" in bot and bot["maps"]:
                        st.divider()
                        st.subheader("🗺️ Maps")
                        st.caption("This bot appears on the following maps:")
                        map_list = []
                        for map_id in bot["maps"]:
                            map_obj = next((m for m in DB["maps"] if m.get("id") == map_id), None)
                            if map_obj:
                                map_name = map_obj.get("name", {}).get("en", map_id)
                                map_list.append(map_name)
                            else:
                                map_list.append(map_id.replace("_", " ").title())
                        st.write(", ".join(map_list))
                    
                    # Items dropped by bot
                    if "drops" in bot and bot["drops"]:
                        st.divider()
                        st.subheader("📦 Items Dropped")
                        st.caption("💡 Click on any item to see detailed information including reverse scrap sources")
                        
                        for item_id in bot["drops"]:
                            item = DB["item_by_id"].get(item_id)
                            if item:
                                # Show item with drill-down
                                display_ingredient_details(item_id, 1)
                            else:
                                st.write(f"- {get_item_name(item_id)} (Item data not found)")
                    else:
                        st.divider()
                        st.caption("No items dropped by this bot")
    else:
        st.warning("No bots found matching the search criteria.")

elif mode == "📜 Quests":
    st.title("📜 Quest Database")
    st.info("View quest information, requirements, rewards, and quest chains")
    
    if not DB["quests"]:
        st.warning("No quests data loaded. Please check that arcraiders-data-main/quests/*.json files exist.")
        st.stop()
    
    # Search and filter options
    col1, col2 = st.columns(2)
    
    with col1:
        search_query = st.text_input("🔍 Search Quest Name", "", key="quest_search")
    
    with col2:
        traders = sorted(list(set([q.get("trader", "Unknown") for q in DB["quests"] if q.get("trader")])))
        selected_trader = st.selectbox("Filter by Trader", ["All"] + traders)
    
    # Filter quests
    filtered_quests = DB["quests"]
    
    if search_query:
        filtered_quests = [q for q in filtered_quests if search_query.lower() in q.get("name", {}).get("en", "").lower()]
    
    if selected_trader != "All":
        filtered_quests = [q for q in filtered_quests if q.get("trader") == selected_trader]
    
    # Sort by trader, then by quest name
    filtered_quests.sort(key=lambda x: (x.get("trader", "Unknown"), x.get("name", {}).get("en", "").lower()))
    
    if filtered_quests:
        st.success(f"Found {len(filtered_quests)} quest(s)")
        
        for quest in filtered_quests:
            quest_name = quest.get("name", {}).get("en", "Unknown Quest")
            trader = quest.get("trader", "Unknown")
            quest_id = quest.get("id", "unknown")
            
            with st.expander(f"📜 **{quest_name}** - {trader}", expanded=False):
                col_a, col_b = st.columns([2, 1])
                
                with col_a:
                    st.subheader(quest_name)
                    st.caption(f"**Quest ID:** {quest_id} | **Trader:** {trader}")
                    
                    if "updatedAt" in quest:
                        st.caption(f"**Last Updated:** {quest['updatedAt']}")
                    
                    if "description" in quest:
                        st.write(f"_{quest['description'].get('en', '')}_")
                    
                    # Objectives
                    if "objectives" in quest and quest["objectives"]:
                        st.divider()
                        st.subheader("📋 Objectives")
                        for i, obj in enumerate(quest["objectives"], 1):
                            st.write(f"{i}. {obj.get('en', 'Unknown objective')}")
                    
                    # Required Items
                    if "requiredItemIds" in quest and quest["requiredItemIds"]:
                        st.divider()
                        st.subheader("📦 Required Items")
                        st.caption("💡 Click on any item to see detailed information including reverse scrap sources")
                        for req in quest["requiredItemIds"]:
                            display_ingredient_details(req["itemId"], req.get("quantity", 1))
                    
                    # Rewards
                    if "rewardItemIds" in quest and quest["rewardItemIds"]:
                        st.divider()
                        st.subheader("🎁 Rewards")
                        st.caption("💡 Click on any reward to see detailed information")
                        for reward in quest["rewardItemIds"]:
                            display_ingredient_details(reward["itemId"], reward.get("quantity", 1))
                    
                    # XP Reward
                    if "xp" in quest and quest["xp"] > 0:
                        st.divider()
                        st.metric("Experience Points", quest["xp"])
                
                with col_b:
                    # Quest Chain Information
                    has_prereq = "previousQuestIds" in quest and quest["previousQuestIds"]
                    has_next = "nextQuestIds" in quest and quest["nextQuestIds"]
                    
                    if has_prereq or has_next:
                        st.subheader("🔗 Quest Chain")
                        
                        if has_prereq:
                            st.write("**Prerequisites:**")
                            for prev_id in quest["previousQuestIds"]:
                                prev_quest = next((q for q in DB["quests"] if q.get("id") == prev_id), None)
                                if prev_quest:
                                    prev_name = prev_quest.get("name", {}).get("en", prev_id)
                                    st.caption(f"- {prev_name}")
                                else:
                                    st.caption(f"- {prev_id}")
                        
                        if has_next:
                            st.write("**Follow-up Quests:**")
                            for next_id in quest["nextQuestIds"]:
                                next_quest = next((q for q in DB["quests"] if q.get("id") == next_id), None)
                                if next_quest:
                                    next_name = next_quest.get("name", {}).get("en", next_id)
                                    st.caption(f"- {next_name}")
                                else:
                                    st.caption(f"- {next_id}")
                    
                    # Quick stats
                    if "requiredItemIds" in quest:
                        st.metric("Items Required", len(quest["requiredItemIds"]))
                    if "rewardItemIds" in quest:
                        st.metric("Rewards", len(quest["rewardItemIds"]))
    else:
        st.warning("No quests found matching the search criteria.")