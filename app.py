import streamlit as st
import json
import glob
import os

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="ARC Raiders Companion", layout="wide", page_icon="🦾")

# --- 1.5. AUTHENTICATION & USER DATA FUNCTIONS ---

def ensure_data_directories():
    """Ensure data directories exist"""
    os.makedirs("data", exist_ok=True)
    os.makedirs("data/user_data", exist_ok=True)

def load_users():
    """Load users from data/users.json"""
    ensure_data_directories()
    users_file = "data/users.json"
    if os.path.exists(users_file):
        try:
            with open(users_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    return {}

def save_users(users):
    """Save users to data/users.json"""
    ensure_data_directories()
    users_file = "data/users.json"
    with open(users_file, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2)

def register_user(username, password):
    """Register a new user"""
    users = load_users()
    if username in users:
        return False, "Username already exists"
    users[username] = password
    save_users(users)
    # Initialize user data file
    user_data = {
        "workshop_config": {},
        "shopping_list": [],
        "active_quests": []
    }
    save_user_data(username, user_data)
    return True, "Registration successful"

def authenticate_user(username, password):
    """Authenticate a user"""
    users = load_users()
    if username in users and users[username] == password:
        return True
    return False

def load_user_data(username):
    """Load user data from data/user_data/{username}.json"""
    ensure_data_directories()
    user_file = f"data/user_data/{username}.json"
    if os.path.exists(user_file):
        try:
            with open(user_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Ensure all required keys exist
                if "workshop_config" not in data:
                    data["workshop_config"] = {}
                if "shopping_list" not in data:
                    data["shopping_list"] = []
                if "active_quests" not in data:
                    data["active_quests"] = []
                return data
        except (FileNotFoundError, json.JSONDecodeError):
            pass
    # Return default structure
    return {
        "workshop_config": {},
        "shopping_list": [],
        "active_quests": []
    }

def save_user_data(username, data):
    """Save user data to data/user_data/{username}.json"""
    ensure_data_directories()
    user_file = f"data/user_data/{username}.json"
    with open(user_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def calculate_upgrade_requirements(workshop_config):
    """Calculate items needed for upgrades based on workshop config"""
    requirements = {}
    
    for module_id, config in workshop_config.items():
        current = config.get("current", 1)
        planned = config.get("planned", current)
        
        # Find the module
        module = next((m for m in DB["modules"] if m.get("id") == module_id), None)
        if not module:
            continue
        
        # Calculate requirements from current+1 to planned
        for level in module.get("levels", []):
            level_num = level.get("level", 0)
            if current < level_num <= planned:
                if "requirementItemIds" in level:
                    for req in level["requirementItemIds"]:
                        item_id = req["itemId"]
                        qty = req.get("quantity", 1)
                        if item_id in requirements:
                            requirements[item_id] += qty
                        else:
                            requirements[item_id] = qty
    
    return requirements

def get_active_quests_data(quest_ids):
    """Get full quest data for active quest IDs"""
    active_quests = []
    for quest_id in quest_ids:
        quest = next((q for q in DB["quests"] if q.get("id") == quest_id), None)
        if quest:
            active_quests.append(quest)
    return active_quests

def change_username(old_username, new_username):
    """Change username - returns (success, message)"""
    users = load_users()
    
    if new_username in users:
        return False, "Username already exists"
    
    if old_username not in users:
        return False, "Current username not found"
    
    # Update users file
    password = users[old_username]
    del users[old_username]
    users[new_username] = password
    save_users(users)
    
    # Rename user data file
    old_file = f"data/user_data/{old_username}.json"
    new_file = f"data/user_data/{new_username}.json"
    if os.path.exists(old_file):
        os.rename(old_file, new_file)
    
    return True, "Username changed successfully"

def change_password(username, old_password, new_password):
    """Change password - returns (success, message)"""
    users = load_users()
    
    if username not in users:
        return False, "Username not found"
    
    if users[username] != old_password:
        return False, "Current password is incorrect"
    
    users[username] = new_password
    save_users(users)
    return True, "Password changed successfully"

def delete_account(username):
    """Delete user account and all associated data"""
    users = load_users()
    
    if username not in users:
        return False, "Username not found"
    
    # Remove from users file
    del users[username]
    save_users(users)
    
    # Delete user data file
    user_file = f"data/user_data/{username}.json"
    if os.path.exists(user_file):
        os.remove(user_file)
    
    return True, "Account deleted successfully"

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

# Initialize session state
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "username" not in st.session_state:
    st.session_state.username = None

# Authentication check
if not st.session_state.authenticated:
    st.title("🦾 ARC Raiders Companion")
    st.subheader("Login or Register")
    
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        with st.form("login_form"):
            login_username = st.text_input("Username", key="login_username")
            login_password = st.text_input("Password", type="password", key="login_password")
            login_submit = st.form_submit_button("Login")
            
            if login_submit:
                if authenticate_user(login_username, login_password):
                    st.session_state.authenticated = True
                    st.session_state.username = login_username
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Invalid username or password")
    
    with tab2:
        with st.form("register_form"):
            reg_username = st.text_input("Username", key="reg_username")
            reg_password = st.text_input("Password", type="password", key="reg_password")
            reg_confirm = st.text_input("Confirm Password", type="password", key="reg_confirm")
            reg_submit = st.form_submit_button("Register")
            
            if reg_submit:
                if not reg_username or not reg_password:
                    st.error("Username and password are required")
                elif reg_password != reg_confirm:
                    st.error("Passwords do not match")
                else:
                    success, message = register_user(reg_username, reg_password)
                    if success:
                        st.success(message)
                        st.info("You can now login with your credentials")
                    else:
                        st.error(message)
    
    st.stop()

# Load database with spinner (only if authenticated)
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

# User info and logout
if st.session_state.authenticated:
    st.sidebar.write(f"**User:** {st.session_state.username}")
    if st.sidebar.button("Logout"):
        st.session_state.authenticated = False
        st.session_state.username = None
        st.rerun()
    st.sidebar.divider()

mode = st.sidebar.radio("Navigation", [
    "🏠 Welcome",
    "📊 Overview",
    "🏗️ Workshop Config",
    "🛒 Shopping List",
    "📦 Wiki",
    "♻️ Reverse Scrap",
    "📖 Recipe Book",
    "🗺️ Map Items",
    "🤖 Bots",
    "📜 Quests",
    "⚙️ Account Settings"
], help="Welcome: Get started guide and overview of all features. Overview: Your dashboard with active quests, shopping list, and workshop status. Workshop Config: Configure your hideout station levels. Shopping List: Track items you need to collect. Wiki: Search items and see usage. Reverse Scrap: Find what items to pick up for materials. Recipe Book: View crafting recipes and add ingredients to shopping list. Map Items: View items found on specific maps. Bots: View enemy bot information, drops, and locations. Quests: View quest information, requirements, and rewards. Account Settings: Manage your account settings.")

# --- 5. MAIN PAGES ---

# Load user data
user_data = load_user_data(st.session_state.username)

if mode == "🏠 Welcome":
    st.title("🦾 Welcome to ARC Raiders Companion")
    st.markdown("---")
    
    st.markdown("""
    ### Your Complete Guide to ARC Raiders
    
    This companion tool helps you manage your hideout upgrades, track quest requirements, 
    plan your crafting, and make informed decisions about which items to keep or recycle.
    """)
    
    st.divider()
    
    # Quick Start Section
    st.header("🚀 Quick Start Guide")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        **For New Users:**
        1. Configure your Workshop Config with current station levels
        2. Mark active quests you're working on
        3. Use Shopping List to track items you need
        4. Check Overview page for your progress summary
        """)
    
    with col2:
        st.markdown("""
        **Common Workflows:**
        - Planning upgrades → Workshop Config → Shopping List
        - Crafting items → Recipe Book → Shopping List
        - Quest tracking → Quests → Overview
        - Item decisions → Wiki or Reverse Scrap
        """)
    
    st.divider()
    
    # Feature Overview
    st.header("📚 Feature Guide")
    
    # Overview Section
    with st.expander("📊 Overview Dashboard", expanded=True):
        st.markdown("""
        **Purpose:** Your personal command center showing everything you need at a glance.
        
        **Use Cases:**
        - Quick view of active quests and their required items
        - Shopping list summary with top priority items
        - Workshop configuration status and progress
        
        **Workflow:**
        1. Start here each session to see what you're working on
        2. Review active quest requirements
        3. Check shopping list priorities
        4. Monitor workshop upgrade progress
        """)
    
    # Workshop Config Section
    with st.expander("🏗️ Workshop Configuration", expanded=False):
        st.markdown("""
        **Purpose:** Track your hideout station levels and plan upgrades.
        
        **Use Cases:**
        - Set current level for each station (Workbench, Scrappy, etc.)
        - Set target/planned level for each station
        - Visual progress tracking
        
        **Workflow:**
        1. Set your current level for each station
        2. Set your target level (where you want to upgrade to)
        3. Use "Add Items from Planned Upgrades" in Shopping List to auto-generate requirements
        4. Update current level as you complete upgrades
        """)
    
    # Shopping List Section
    with st.expander("🛒 Shopping List", expanded=False):
        st.markdown("""
        **Purpose:** Track all items you need to collect for upgrades, crafting, and quests.
        
        **Use Cases:**
        - Manual item tracking
        - Auto-populate from planned workshop upgrades
        - Add items from crafting recipes
        - View aggregated totals with source breakdown
        
        **Workflow:**
        1. **From Upgrades:** Click "Add Items from Planned Upgrades" to import all requirements
        2. **From Crafting:** Go to Recipe Book, select item, set quantity, click "Add All Ingredients"
        3. **Manual Entry:** Use the form to add individual items
        4. View breakdown to see where each item came from (upgrade/crafting/manual)
        5. Remove items as you collect them
        """)
    
    # Wiki Section
    with st.expander("📦 Wiki (Item Database)", expanded=False):
        st.markdown("""
        **Purpose:** Search and view detailed information about any item in the game.
        
        **Use Cases:**
        - Check if an item is used in quests (DO NOT SELL!)
        - See what items are used in upgrades or crafting
        - Find where items can be obtained
        - View item stats, rarity, and scrap output
        
        **Workflow:**
        1. Search for an item by name
        2. Review the status indicator (🔴 Quest item, 🟡 Used in upgrades/crafting, 🟢 Safe to sell)
        3. Check "Why This Item Matters" section
        4. View "Where to Find" for acquisition methods
        5. See "Recycles Into" to know what materials you'll get
        """)
    
    # Reverse Scrap Section
    with st.expander("♻️ Reverse Scrap Calculator", expanded=False):
        st.markdown("""
        **Purpose:** Find which items you should pick up to recycle for specific materials.
        
        **Use Cases:**
        - You need a specific material (e.g., "Metal Parts")
        - Find which junk items contain that material
        - Identify best items to recycle (common items with no usage)
        - Avoid recycling quest items or items needed for upgrades
        
        **Workflow:**
        1. Select the material you need from the dropdown
        2. Review the sorted list (best to recycle items appear first)
        3. Look for items marked "✅ BEST TO RECYCLE" (no usage, common rarity)
        4. Avoid items marked "🚨 QUEST ITEM - DO NOT RECYCLE"
        5. Check efficiency (yield per weight) for optimal choices
        """)
    
    # Recipe Book Section
    with st.expander("📖 Recipe Book", expanded=False):
        st.markdown("""
        **Purpose:** Browse all craftable items and their recipes, add ingredients to shopping list.
        
        **Use Cases:**
        - Plan what you want to craft
        - See ingredient requirements for any craftable item
        - Add recipe ingredients directly to shopping list
        - View detailed ingredient information
        
        **Workflow:**
        1. Select the item you want to craft
        2. Set the quantity you want to craft (multiplier)
        3. Click "Add All Ingredients" to add everything to shopping list
        4. Or click individual "Add" buttons for specific ingredients
        5. Review ingredient details (click expanders) for reverse scrap sources
        """)
    
    # Map Items Section
    with st.expander("🗺️ Map Items", expanded=False):
        st.markdown("""
        **Purpose:** See what items are available on each map through bot drops.
        
        **Use Cases:**
        - Plan which map to visit for specific items
        - See which bots drop which items
        - Find item locations for your shopping list
        
        **Workflow:**
        1. Select a map from the dropdown
        2. View all items that drop on that map
        3. See which bots drop each item
        4. Click items to see detailed information
        5. Add needed items to shopping list from Wiki or other pages
        """)
    
    # Bots Section
    with st.expander("🤖 Bots Database", expanded=False):
        st.markdown("""
        **Purpose:** View detailed information about enemy bots, their drops, and combat strategies.
        
        **Use Cases:**
        - Learn bot weaknesses and combat strategies
        - See what items each bot drops
        - Find which maps bots appear on
        - Plan farming routes for specific items
        
        **Workflow:**
        1. Search or filter bots by type/threat level
        2. Review bot information (sorted Low to High threat)
        3. Check drops to see what items you can get
        4. Note weaknesses for easier combat
        5. See map locations to know where to find them
        """)
    
    # Quests Section
    with st.expander("📜 Quest Database", expanded=False):
        st.markdown("""
        **Purpose:** View all quests, their requirements, rewards, and mark active quests.
        
        **Use Cases:**
        - Browse available quests
        - See quest requirements and rewards
        - Mark quests as active to track on Overview page
        - Understand quest chains and prerequisites
        
        **Workflow:**
        1. Search or filter quests by trader
        2. Review quest details (objectives, requirements, rewards)
        3. Click "Mark as Active" for quests you're working on
        4. View active quests and aggregated requirements on Overview page
        5. Remove from active when completed
        """)
    
    # Account Settings Section
    with st.expander("⚙️ Account Settings", expanded=False):
        st.markdown("""
        **Purpose:** Manage your account - change username, password, or delete account.
        
        **Use Cases:**
        - Change your username (must be unique)
        - Update your password
        - Delete your account and all associated data
        
        **Workflow:**
        1. **Change Username:** Enter new username (must not exist), click "Change Username"
        2. **Change Password:** Enter current password, new password, confirm, click "Change Password"
        3. **Delete Account:** Type your username to confirm, click "Delete Account" (permanent!)
        """)
    
    st.divider()
    
    # Common Workflows
    st.header("🔄 Common Workflows")
    
    workflow_col1, workflow_col2 = st.columns(2)
    
    with workflow_col1:
        st.subheader("Planning Hideout Upgrades")
        st.markdown("""
        1. Go to **Workshop Config**
        2. Set current level for each station
        3. Set planned/target level for each station
        4. Go to **Shopping List**
        5. Click "Add Items from Planned Upgrades"
        6. Review aggregated shopping list
        7. Use **Reverse Scrap** to find best items to recycle for materials
        8. Update Workshop Config as you complete upgrades
        """)
        
        st.subheader("Crafting Planning")
        st.markdown("""
        1. Go to **Recipe Book**
        2. Select item you want to craft
        3. Set quantity multiplier
        4. Click "Add All Ingredients" to shopping list
        5. Review shopping list for all needed materials
        6. Use **Wiki** to check if any ingredients are quest items
        7. Use **Reverse Scrap** to find sources for rare materials
        """)
    
    with workflow_col2:
        st.subheader("Quest Management")
        st.markdown("""
        1. Go to **Quests** page
        2. Search or filter by trader
        3. Review quest requirements and rewards
        4. Click "Mark as Active" for quests you're working on
        5. Go to **Overview** to see all active quest requirements
        6. Check **Shopping List** to see if you have items needed
        7. Remove from active when quest is completed
        """)
        
        st.subheader("Item Decision Making")
        st.markdown("""
        1. Find item in **Wiki** or see it in your inventory
        2. Check status indicator (🔴/🟡/🟢)
        3. Review "Why This Item Matters" section
        4. If safe to sell, check **Reverse Scrap** to see if it's valuable for materials
        5. Consider rarity - common items are better to recycle
        6. Make decision: keep for quest/upgrade or recycle for materials
        """)
    
    st.divider()
    
    # Tips Section
    st.header("💡 Pro Tips")
    
    tip_col1, tip_col2 = st.columns(2)
    
    with tip_col1:
        st.markdown("""
        - **Always check Overview first** - it shows your current priorities
        - **Use Reverse Scrap** before selling items - you might need the materials
        - **Common items are usually safe to recycle** - rare items should be checked first
        - **Mark quests as active** to see all requirements in one place
        """)
    
    with tip_col2:
        st.markdown("""
        - **Shopping List aggregates** items from multiple sources - check breakdown for details
        - **Workshop Config** auto-calculates requirements when you use "Add from Upgrades"
        - **Recipe Book** supports quantity multipliers - craft multiple items at once
        - **Bots are sorted** by threat level (Low to High) for easier browsing
        """)
    
    st.divider()
    
    # Getting Started
    st.header("🎯 Getting Started")
    st.markdown("""
    **New to the app? Follow these steps:**
    
    1. **Set up your Workshop** - Go to Workshop Config and set your current station levels
    2. **Mark Active Quests** - Go to Quests and mark the quests you're currently working on
    3. **Check Overview** - See your active quests and their requirements
    4. **Build Shopping List** - Add items from upgrades or crafting, or manually
    5. **Use Reverse Scrap** - When you need materials, find the best items to recycle
    6. **Explore Wiki** - Search for items to understand their value and usage
    
    **Ready to start?** Use the sidebar to navigate to any section!
    """)

elif mode == "📊 Overview":
    st.title("📊 Overview Dashboard")
    st.info("Your personal dashboard showing active quests, shopping list summary, and workshop configuration")
    
    # Active Quests Section
    st.header("📜 Active Quests")
    active_quest_ids = user_data.get("active_quests", [])
    active_quests = get_active_quests_data(active_quest_ids)
    
    if active_quests:
        st.success(f"You have {len(active_quests)} active quest(s)")
        
        # Aggregate all quest items
        quest_items = {}
        for quest in active_quests:
            if "requiredItemIds" in quest and quest["requiredItemIds"]:
                for req in quest["requiredItemIds"]:
                    item_id = req["itemId"]
                    qty = req.get("quantity", 1)
                    if item_id in quest_items:
                        quest_items[item_id] += qty
                    else:
                        quest_items[item_id] = qty
        
        # Display aggregated quest items
        if quest_items:
            st.subheader("📦 Total Quest Items Required")
            with st.expander("View All Quest Items", expanded=True):
                for item_id, total_qty in sorted(quest_items.items()):
                    st.write(f"- {get_item_name(item_id)} x{total_qty}")
        
        st.divider()
        
        # Individual quest details
        for quest in active_quests:
            quest_name = quest.get("name", {}).get("en", "Unknown Quest")
            trader = quest.get("trader", "Unknown")
            with st.expander(f"📜 {quest_name} - {trader}", expanded=False):
                col_a, col_b = st.columns([2, 1])
                with col_a:
                    if "description" in quest:
                        st.write(quest["description"].get("en", ""))
                    if "objectives" in quest and quest["objectives"]:
                        st.subheader("Objectives")
                        for i, obj in enumerate(quest["objectives"], 1):
                            st.write(f"{i}. {obj.get('en', 'Unknown')}")
                    if "requiredItemIds" in quest and quest["requiredItemIds"]:
                        st.subheader("Required Items")
                        for req in quest["requiredItemIds"]:
                            st.write(f"- {get_item_name(req['itemId'])} x{req.get('quantity', 1)}")
                with col_b:
                    if st.button(f"Remove from Active", key=f"remove_quest_{quest.get('id')}"):
                        if quest.get("id") in user_data["active_quests"]:
                            user_data["active_quests"].remove(quest.get("id"))
                            save_user_data(st.session_state.username, user_data)
                            st.rerun()
    else:
        st.info("No active quests. Mark quests as active from the Quests page.")
    
    st.divider()
    
    # Shopping List Summary
    st.header("🛒 Shopping List Summary")
    shopping_list = user_data.get("shopping_list", [])
    if shopping_list:
        total_items = len(shopping_list)
        total_quantities = sum(item.get("quantity", 0) for item in shopping_list)
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Items", total_items)
        with col2:
            st.metric("Total Quantities", total_quantities)
        
        st.subheader("Top Items Needed")
        # Sort by quantity and show top 5
        sorted_list = sorted(shopping_list, key=lambda x: x.get("quantity", 0), reverse=True)
        for item in sorted_list[:5]:
            item_name = get_item_name(item.get("item_id", ""))
            qty = item.get("quantity", 0)
            source = item.get("source", "manual")
            if source == "upgrade":
                source_label = "🔨 Upgrade"
            elif source == "crafting":
                source_label = "🛠️ Crafting"
            else:
                source_label = "✏️ Manual"
            st.write(f"- {item_name} x{qty} ({source_label})")
        
        if len(shopping_list) > 5:
            st.caption(f"... and {len(shopping_list) - 5} more items")
        
        st.info("💡 Use the sidebar to navigate to the Shopping List page")
    else:
        st.info("Your shopping list is empty. Add items manually or from planned upgrades.")
    
    st.divider()
    
    # Workshop Configuration Summary
    st.header("🏗️ Workshop Configuration")
    workshop_config = user_data.get("workshop_config", {})
    if workshop_config:
        # Get all modules for reference
        module_dict = {m.get("id"): m for m in DB["modules"]}
        
        cols = st.columns(3)
        col_idx = 0
        for module_id, config in workshop_config.items():
            module = module_dict.get(module_id)
            if module:
                module_name = module.get("name", {}).get("en", module_id)
                current = config.get("current", 1)
                planned = config.get("planned", current)
                max_level = module.get("maxLevel", 1)
                
                with cols[col_idx % 3]:
                    with st.container(border=True):
                        st.write(f"**{module_name}**")
                        st.write(f"Current: Level {current}")
                        st.write(f"Planned: Level {planned}")
                        if planned > current:
                            progress = ((current - 1) / (planned - 1)) * 100 if planned > 1 else 0
                            st.progress(progress / 100)
                            st.caption(f"{current}/{planned} levels")
                        else:
                            st.success("✅ Complete")
                col_idx += 1
        
        st.info("💡 Use the sidebar to navigate to the Workshop Config page")
    else:
        st.info("No workshop configuration set. Configure your stations in the Workshop Config page.")
        st.info("💡 Use the sidebar to navigate to the Workshop Config page")

elif mode == "🏗️ Workshop Config":
    st.title("🏗️ Workshop Configuration")
    st.info("Configure your current and planned levels for each hideout station")
    
    user_data = load_user_data(st.session_state.username)
    workshop_config = user_data.get("workshop_config", {})
    
    # Get all modules
    modules = DB["modules"]
    
    if not modules:
        st.warning("No hideout modules found in database.")
        st.stop()
    
    # Create configuration for each module
    updated = False
    for module in modules:
        module_id = module.get("id", "")
        module_name = module.get("name", {}).get("en", "Unknown")
        max_level = module.get("maxLevel", 1)
        
        # Ensure max_level is at least 1
        if max_level < 1:
            max_level = 1
        
        if not module_id:
            continue
        
        st.subheader(module_name)
        st.caption(f"Max Level: {max_level}")
        
        # Get current config or defaults
        current_config = workshop_config.get(module_id, {"current": 1, "planned": 1})
        current_level = current_config.get("current", 1)
        planned_level = current_config.get("planned", current_level)
        
        # Ensure values are within valid range
        current_level = max(1, min(current_level, max_level))
        planned_level = max(current_level, min(planned_level, max_level))
        
        col1, col2 = st.columns(2)
        with col1:
            new_current = st.number_input(
                f"Current Level",
                min_value=1,
                max_value=max_level,
                value=current_level,
                key=f"current_{module_id}"
            )
        with col2:
            # Ensure planned level is at least equal to current level
            safe_planned = max(new_current, planned_level)
            new_planned = st.number_input(
                f"Planned Level",
                min_value=new_current,
                max_value=max_level,
                value=safe_planned,
                key=f"planned_{module_id}"
            )
        
        # Update config if changed
        if new_current != current_level or new_planned != planned_level:
            workshop_config[module_id] = {
                "current": new_current,
                "planned": new_planned
            }
            updated = True
        
        # Show progress
        if new_planned > new_current:
            progress = ((new_current - 1) / (new_planned - 1)) * 100 if new_planned > 1 else 0
            st.progress(progress / 100)
            st.caption(f"Progress: {new_current}/{new_planned} levels")
        else:
            st.success("✅ Target reached!")
        
        st.divider()
    
    # Save if updated
    if updated:
        user_data["workshop_config"] = workshop_config
        save_user_data(st.session_state.username, user_data)
        st.success("Configuration saved!")

elif mode == "🛒 Shopping List":
    st.title("🛒 Shopping List")
    st.info("Track items you need to collect for upgrades and crafting")
    
    user_data = load_user_data(st.session_state.username)
    shopping_list = user_data.get("shopping_list", [])
    
    # Auto-populate from upgrades button
    st.subheader("Auto-Populate from Upgrades")
    if st.button("Add Items from Planned Upgrades"):
        workshop_config = user_data.get("workshop_config", {})
        requirements = calculate_upgrade_requirements(workshop_config)
        
        # Add items to shopping list (keep separate entries per source)
        for item_id, qty in requirements.items():
            # Always add as new entry to preserve source separation
            shopping_list.append({
                "item_id": item_id,
                "quantity": qty,
                "source": "upgrade"
            })
        
        user_data["shopping_list"] = shopping_list
        save_user_data(st.session_state.username, user_data)
        st.success(f"Added {len(requirements)} item(s) from planned upgrades!")
        st.rerun()
    
    st.divider()
    
    # Manual entry
    st.subheader("Add Item Manually")
    with st.form("add_item_form"):
        # Item search
        item_options = {get_item_name(item.get("id", "")): item.get("id", "") for item in DB["items"] if "id" in item}
        selected_item_name = st.selectbox("Select Item", sorted(item_options.keys()))
        quantity = st.number_input("Quantity", min_value=1, value=1)
        add_submit = st.form_submit_button("Add to Shopping List")
        
        if add_submit:
            selected_item_id = item_options[selected_item_name]
            # Always add as new entry to preserve source separation
            shopping_list.append({
                "item_id": selected_item_id,
                "quantity": quantity,
                "source": "manual"
            })
            user_data["shopping_list"] = shopping_list
            save_user_data(st.session_state.username, user_data)
            st.success(f"Added {get_item_name(selected_item_id)} x{quantity} to shopping list!")
            st.rerun()
    
    st.divider()
    
    # Display shopping list
    st.subheader("Your Shopping List")
    if shopping_list:
        # Aggregate items by item_id
        aggregated_items = {}
        for item in shopping_list:
            item_id = item.get("item_id", "")
            qty = item.get("quantity", 0)
            source = item.get("source", "manual")
            
            if item_id not in aggregated_items:
                aggregated_items[item_id] = {
                    "total_quantity": 0,
                    "breakdown": []
                }
            
            aggregated_items[item_id]["total_quantity"] += qty
            aggregated_items[item_id]["breakdown"].append({
                "quantity": qty,
                "source": source,
                "original_item": item
            })
        
        # Display aggregated items
        for item_id, item_data in sorted(aggregated_items.items(), key=lambda x: x[1]["total_quantity"], reverse=True):
            total_qty = item_data["total_quantity"]
            breakdown = item_data["breakdown"]
            
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                # Show total quantity
                display_ingredient_details(item_id, total_qty)
                
                # Show breakdown in expander (always show if there are entries)
                if breakdown:
                    with st.expander("View Breakdown", expanded=False):
                        for idx, entry in enumerate(breakdown):
                            source = entry["source"]
                            qty = entry["quantity"]
                            if source == "upgrade":
                                source_label = "🔨 Upgrade"
                            elif source == "crafting":
                                source_label = "🛠️ Crafting"
                            else:
                                source_label = "✏️ Manual"
                            
                            col_break1, col_break2 = st.columns([3, 1])
                            with col_break1:
                                st.write(f"- {source_label}: x{qty}")
                            with col_break2:
                                if st.button("Remove", key=f"remove_{item_id}_{source}_{idx}"):
                                    # Remove this specific entry
                                    shopping_list.remove(entry["original_item"])
                                    user_data["shopping_list"] = shopping_list
                                    save_user_data(st.session_state.username, user_data)
                                    st.rerun()
            
            with col2:
                # Remove all button
                if st.button("Remove All", key=f"remove_all_{item_id}"):
                    # Remove all entries for this item
                    shopping_list = [item for item in shopping_list if item.get("item_id") != item_id]
                    user_data["shopping_list"] = shopping_list
                    save_user_data(st.session_state.username, user_data)
                    st.rerun()
            
            with col3:
                # Show source indicators
                sources = set(entry["source"] for entry in breakdown)
                if len(sources) > 1:
                    st.write("📊 Mixed")
                elif "upgrade" in sources:
                    st.write("🔨 Upgrade")
                elif "crafting" in sources:
                    st.write("🛠️ Crafting")
                else:
                    st.write("✏️ Manual")
            
            st.divider()
        
        # Summary
        total_unique_items = len(aggregated_items)
        total_quantities = sum(item_data["total_quantity"] for item_data in aggregated_items.values())
        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Unique Items", total_unique_items)
        with col2:
            st.metric("Total Quantities", total_quantities)
    else:
        st.info("Your shopping list is empty. Add items manually or from planned upgrades.")

elif mode == "📦 Wiki":
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
                
                # Get rarity score (lower = more common = better to recycle)
                # Common = 0, Uncommon = 1, Rare = 2, Epic = 3, Legendary = 4
                rarity = i.get("rarity", "Common")
                rarity_order = {"Common": 0, "Uncommon": 1, "Rare": 2, "Epic": 3, "Legendary": 4}
                rarity_score = rarity_order.get(rarity, 0)
                
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
                    "rarity": rarity,
                    "rarity_score": rarity_score,
                    "item_data": i  # Store full item data for display
                })
        
        # Sort by usefulness (least useful first), then by rarity (common first), then by yield quantity
        sources.sort(key=lambda x: (x["usefulness_score"], x["rarity_score"], -x["qty"]))
        
        if sources:
            st.success(f"Found {len(sources)} item(s) that yield **{get_item_name(target_mat)}**")
            st.caption("💡 Items are sorted by usefulness, then rarity (common items preferred), then yield quantity")
            
            # Show best value indicator (from items with no usage, common rarity)
            no_usage_sources = [s for s in sources if s["usefulness_score"] == 0]
            if no_usage_sources:
                # Prefer common items
                common_no_usage = [s for s in no_usage_sources if s["rarity_score"] == 0]
                if common_no_usage:
                    best_source = max(common_no_usage, key=lambda x: x["efficiency"])
                else:
                    best_source = max(no_usage_sources, key=lambda x: (x["rarity_score"], x["efficiency"]))
                if best_source["efficiency"] > 0:
                    st.caption(f"💡 Best Value (No Usage, {best_source['rarity']}): {best_source['name']} ({best_source['efficiency']:.2f} yield/kg)")
            
            for s in sources:
                with st.container(border=True):
                    col1, col2, col3 = st.columns([1, 3, 1])
                    
                    with col1:
                        if s["image"]:
                            st.image(s["image"], width=80)
                    
                    with col2:
                        # Determine recommendation level
                        rarity_display = f" ({s['rarity']})" if s.get('rarity') else ""
                        if s["usefulness_score"] == 0:
                            st.success(f"**{s['name']}**{rarity_display} - Yields {s['qty']}x | ✅ **BEST TO RECYCLE** (No usage found)")
                        elif s["usefulness_score"] == 1:
                            st.warning(f"**{s['name']}**{rarity_display} - Yields {s['qty']}x | ⚠️ Used in crafting")
                        elif s["usefulness_score"] == 2:
                            st.warning(f"**{s['name']}**{rarity_display} - Yields {s['qty']}x | ⚠️ Used in upgrades")
                        else:
                            st.error(f"**{s['name']}**{rarity_display} - Yields {s['qty']}x | 🚨 **QUEST ITEM - DO NOT RECYCLE**")
                        
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

elif mode == "📖 Recipe Book":
    st.title("📖 Recipe Book")
    st.info("Browse all craftable items and their recipes. Add ingredients to your shopping list!")
    
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
                
            # Add to shopping list section
                st.divider()
            st.subheader("🛒 Add to Shopping List")
            col_a, col_b = st.columns([2, 1])
            with col_a:
                craft_quantity = st.number_input("Craft Quantity", min_value=1, value=1, key=f"craft_qty_{target_item.get('id', '')}")
            with col_b:
                st.write("")  # Spacer
                st.write("")  # Spacer
                if st.button("Add All Ingredients", key=f"add_recipe_{target_item.get('id', '')}"):
                    user_data = load_user_data(st.session_state.username)
                    shopping_list = user_data.get("shopping_list", [])
                    
                    # Add items to shopping list (keep separate entries per source)
                    for mat_id, base_qty in recipe.items():
                        total_qty = base_qty * craft_quantity
                        # Always add as new entry to preserve source separation
                        shopping_list.append({
                            "item_id": mat_id,
                            "quantity": total_qty,
                            "source": "crafting"
                        })
                    
                    user_data["shopping_list"] = shopping_list
                    save_user_data(st.session_state.username, user_data)
                    st.success(f"Added ingredients for {craft_quantity}x {target_name} to shopping list!")
                    st.rerun()
            
            st.divider()
            st.subheader("📋 Ingredients Required")
            st.caption("💡 Click on any ingredient to see detailed information including reverse scrap sources")
            
            for mat_id, qty in recipe.items():
                total_qty = qty * craft_quantity
                col_ing1, col_ing2 = st.columns([3, 1])
                with col_ing1:
                    display_ingredient_details(mat_id, total_qty)
                with col_ing2:
                    # Add individual ingredient button
                    if st.button("Add", key=f"add_ing_{mat_id}_{target_item.get('id', '')}"):
                        user_data = load_user_data(st.session_state.username)
                        shopping_list = user_data.get("shopping_list", [])
                        
                        # Always add as new entry to preserve source separation
                        shopping_list.append({
                            "item_id": mat_id,
                            "quantity": total_qty,
                            "source": "crafting"
                        })
                        user_data["shopping_list"] = shopping_list
                        save_user_data(st.session_state.username, user_data)
                        st.success(f"Added {get_item_name(mat_id)} x{total_qty} to shopping list!")
                        st.rerun()
    else:
        st.warning("No craftable items found in database")

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
    
    # Sort by threat level (Low to High), then by name
    threat_order = {"Low": 1, "Medium": 2, "High": 3, "Critical": 4}
    filtered_bots.sort(key=lambda x: (threat_order.get(x.get("threat", "Unknown"), 0), x.get("name", "").lower()))
    
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
            
            # Check if quest is active
            user_data = load_user_data(st.session_state.username)
            active_quests = user_data.get("active_quests", [])
            is_active = quest_id in active_quests
            
            with st.expander(f"📜 **{quest_name}** - {trader}" + (" ✅ ACTIVE" if is_active else ""), expanded=False):
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
                    # Active quest toggle
                    st.subheader("Quest Tracking")
                    if is_active:
                        if st.button("Remove from Active", key=f"deactivate_{quest_id}"):
                            if quest_id in user_data["active_quests"]:
                                user_data["active_quests"].remove(quest_id)
                                save_user_data(st.session_state.username, user_data)
                                st.success("Quest removed from active list")
                                st.rerun()
                    else:
                        if st.button("Mark as Active", key=f"activate_{quest_id}"):
                            if quest_id not in user_data["active_quests"]:
                                user_data["active_quests"].append(quest_id)
                                save_user_data(st.session_state.username, user_data)
                                st.success("Quest marked as active")
                                st.rerun()
                    
                    st.divider()
                    
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

elif mode == "⚙️ Account Settings":
    st.title("⚙️ Account Settings")
    st.info("Manage your account settings, change username/password, or delete your account")
    
    current_username = st.session_state.username
    
    # Change Username Section
    st.header("👤 Change Username")
    with st.form("change_username_form"):
        new_username = st.text_input("New Username", key="new_username")
        change_username_submit = st.form_submit_button("Change Username")
        
        if change_username_submit:
            if not new_username or new_username.strip() == "":
                st.error("Username cannot be empty")
            elif new_username == current_username:
                st.error("New username must be different from current username")
            else:
                success, message = change_username(current_username, new_username)
                if success:
                    st.success(message)
                    st.session_state.username = new_username
                    st.info("Please refresh the page or logout and login again with your new username")
                else:
                    st.error(message)
    
    st.divider()
    
    # Change Password Section
    st.header("🔒 Change Password")
    with st.form("change_password_form"):
        old_password = st.text_input("Current Password", type="password", key="old_password")
        new_password = st.text_input("New Password", type="password", key="new_password")
        confirm_password = st.text_input("Confirm New Password", type="password", key="confirm_password")
        change_password_submit = st.form_submit_button("Change Password")
        
        if change_password_submit:
            if not old_password or not new_password:
                st.error("All password fields are required")
            elif new_password != confirm_password:
                st.error("New passwords do not match")
            elif new_password == old_password:
                st.error("New password must be different from current password")
            else:
                success, message = change_password(current_username, old_password, new_password)
                if success:
                    st.success(message)
                else:
                    st.error(message)
    
    st.divider()
    
    # Delete Account Section
    st.header("🗑️ Delete Account")
    st.warning("⚠️ This action cannot be undone. All your data (workshop config, shopping list, active quests) will be permanently deleted.")
    
    with st.form("delete_account_form"):
        confirm_delete = st.text_input("Type your username to confirm deletion", key="confirm_delete_username")
        delete_submit = st.form_submit_button("Delete Account", type="primary")
        
        if delete_submit:
            if confirm_delete != current_username:
                st.error("Username confirmation does not match")
            else:
                success, message = delete_account(current_username)
                if success:
                    st.success(message)
                    st.info("You will be logged out. Please refresh the page.")
                    # Clear session state
                    st.session_state.authenticated = False
                    st.session_state.username = None
                    st.rerun()
                else:
                    st.error(message)