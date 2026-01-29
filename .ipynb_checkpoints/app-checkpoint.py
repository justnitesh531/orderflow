# ============================================
# ORDERFLOW - WEB APP v1.0
# ============================================

import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime

# Page config (MUST be first Streamlit command)
st.set_page_config(
    page_title="OrderFlow",
    page_icon="🛒",
    layout="wide"
)

# ============================================
# FIREBASE SETUP
# ============================================

@st.cache_resource
def init_firebase():
    """Initialize Firebase once."""
    try:
        firebase_admin.get_app()
    except ValueError:
        cred = credentials.Certificate('firebase-key.json')
        firebase_admin.initialize_app(cred)
    return firestore.client()

db = init_firebase()

# ============================================
# CATEGORIZATION ENGINE
# ============================================

KEYWORDS_DATABASE = {
    "Dairy & Milk Products": ["milk", "butter", "cheese", "paneer", "curd", "ghee", "cream"],
    "Meat, Poultry & Seafood": ["chicken", "mutton", "fish", "eggs", "prawns", "meat"],
    "Vegetables": ["onion", "tomato", "potato", "carrot", "beans", "cabbage", "spinach"],
    "Fruits": ["apple", "banana", "mango", "orange", "grapes"],
    "Rice, Grains & Pulses": ["rice", "wheat", "atta", "dal", "pasta", "noodles"],
    "Spices & Masala": ["salt", "pepper", "turmeric", "chilli", "masala", "jeera"],
    "Cooking Oil & Ghee": ["oil", "ghee", "butter", "refined"],
    "Bakery & Bread": ["bread", "bun", "cake", "biscuit", "pav"],
    "Beverages & Drinks": ["tea", "coffee", "juice", "water", "cold drink"],
    "Cleaning & Kitchen Supplies": ["tissue", "napkin", "detergent", "soap", "foil"]
}

def categorize_item(item_name):
    """Categorize item using keyword database."""
    if not item_name:
        return "Uncategorized"
    
    item_lower = item_name.lower().strip()
    
    # Exact match
    for category, keywords in KEYWORDS_DATABASE.items():
        if item_lower in keywords:
            return category
    
    # Partial match
    for category, keywords in KEYWORDS_DATABASE.items():
        for keyword in keywords:
            if keyword in item_lower:
                return category
    
    return "Uncategorized"

# ============================================
# DRAFT MANAGER
# ============================================

class DraftManager:
    """Manages drafts with Firebase."""
    
    def __init__(self):
        self.draft_ref = db.collection('drafts').document('current-draft')
    
    def add_item(self, item_name, quantity, added_by):
        """Add item to draft."""
        
        category = categorize_item(item_name)
        
        item = {
            "name": item_name.strip(),
            "quantity": quantity.strip(),
            "category": category,
            "added_by": added_by,
            "added_at": datetime.now().isoformat()
        }
        
        draft_doc = self.draft_ref.get()
        
        if draft_doc.exists:
            current_items = draft_doc.to_dict().get('items', [])
            current_items.append(item)
            self.draft_ref.update({'items': current_items})
        else:
            self.draft_ref.set({'items': [item], 'status': 'Draft'})
        
        return category
    
    def get_draft(self):
        """Get current draft."""
        draft_doc = self.draft_ref.get()
        if not draft_doc.exists:
            return {"items": [], "status": "Draft"}
        return draft_doc.to_dict()
    
    def remove_item(self, index):
        """Remove item at index."""
        draft = self.get_draft()
        items = draft.get('items', [])
        
        if 0 <= index < len(items):
            removed = items.pop(index)
            self.draft_ref.update({'items': items})
            return removed
        return None
    
    def clear_draft(self):
        """Clear all items."""
        self.draft_ref.set({'items': [], 'status': 'Draft'})

draft_manager = DraftManager()

# ============================================
# UI COMPONENTS
# ============================================

def show_header():
    """Display app header."""
    st.title("🛒 OrderFlow")
    st.markdown("---")

def show_current_draft():
    """Display current draft with delete buttons."""
    draft = draft_manager.get_draft()
    items = draft.get('items', [])
    
    if len(items) == 0:
        st.info("📋 Draft is empty. Add items below.")
        return
    
    st.subheader(f"📋 Current Draft ({len(items)} items)")
    
    # Group by category
    by_category = {}
    for item in items:
        cat = item['category']
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(item)
    
    # Display by category
    for category, cat_items in by_category.items():
        with st.expander(f"✅ {category} ({len(cat_items)} items)", expanded=True):
            for idx, item in enumerate(cat_items):
                # Find global index
                global_idx = items.index(item)
                
                col1, col2, col3 = st.columns([3, 2, 1])
                
                with col1:
                    st.write(f"**{item['name']}**")
                
                with col2:
                    st.write(f"{item['quantity']}")
                
                with col3:
                    if st.button("🗑️", key=f"del_{global_idx}"):
                        draft_manager.remove_item(global_idx)
                        st.rerun()
                
                st.caption(f"Added by {item['added_by']}")
                st.markdown("---")

def add_item_form():
    """Form to add new item."""
    st.subheader("➕ Add New Item")
    
    with st.form("add_item_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            item_name = st.text_input("Item Name", placeholder="e.g., Milk")
        
        with col2:
            quantity = st.text_input("Quantity", placeholder="e.g., 10L")
        
        added_by = st.text_input("Your Name", placeholder="e.g., Rajesh")
        
        submitted = st.form_submit_button("Add Item", use_container_width=True)
        
        if submitted:
            if not item_name or not item_name.strip():
                st.error("❌ Item name is required")
            elif not added_by or not added_by.strip():
                st.error("❌ Your name is required")
            else:
                category = draft_manager.add_item(item_name, quantity, added_by)
                if category == "Uncategorized":
                    st.warning(f"⚠️ Added {item_name} (needs categorization)")
                else:
                    st.success(f"✅ Added {item_name} to {category}")
                st.rerun()

# ============================================
# MAIN APP
# ============================================

def main():
    """Main app logic."""
    
    show_header()
    
    # Sidebar
    with st.sidebar:
        st.subheader("Actions")
        
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()
        
        if st.button("🗑️ Clear All Items", use_container_width=True):
            draft_manager.clear_draft()
            st.rerun()
        
        st.markdown("---")
        st.caption("OrderFlow v1.0")
    
    # Main content
    tab1, tab2 = st.tabs(["📋 Current Draft", "➕ Add Items"])
    
    with tab1:
        show_current_draft()
    
    with tab2:
        add_item_form()

if __name__ == "__main__":
    main()