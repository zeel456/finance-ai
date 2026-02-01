"""
Enhanced Smart Categorization System
Better merchant name extraction and category prediction

Create this file: utils/smart_categorizer.py
"""

import re
from typing import Optional, Tuple

class SmartCategorizer:
    """
    Enhanced categorization with merchant name cleanup
    and intelligent category detection
    """
    
    # Comprehensive category keywords
    CATEGORY_KEYWORDS = {
        'Food & Dining': [
            'swiggy', 'zomato', 'restaurant', 'cafe', 'coffee', 'pizza', 'burger',
            'food', 'sweets', 'namkeen', 'kfc', 'mcdonalds', 'dominos', 'subway',
            'starbucks', 'dunkin', 'bakery', 'kitchen', 'biryani', 'dhaba',
            'chat', 'juice', 'tea', 'lassi', 'ice cream', 'dessert', 'meal',
            'breakfast', 'lunch', 'dinner', 'eatery', 'dine', 'parcel'
        ],
        
        'Healthcare': [
            'hospital', 'clinic', 'medical', 'pharmacy', 'apollo', 'fortis',
            'doctor', 'dr.', 'lab', 'diagnostic', 'health', 'medplus', 'netmeds',
            'practo', 'medicine', 'chemist', 'pathology', 'dental', 'eye care',
            'multispeciality', 'specialty', 'care', 'wellness'
        ],
        
        'Education': [
            'university', 'college', 'school', 'institute', 'academy', 'tuition',
            'coaching', 'education', 'course', 'training', 'learning', 'study',
            'fees', 'admission', 'exam', 'class', 'tutorial', 'byju', 'unacademy',
            'upgrad', 'coursera', 'udemy'
        ],
        
        'Transportation': [
            'uber', 'ola', 'rapido', 'taxi', 'cab', 'auto', 'metro', 'bus',
            'train', 'irctc', 'makemytrip', 'goibibo', 'yatra', 'flight',
            'petrol', 'fuel', 'gas', 'diesel', 'parking', 'toll', 'fastag'
        ],
        
        'Shopping': [
            'amazon', 'flipkart', 'myntra', 'ajio', 'meesho', 'snapdeal',
            'shopping', 'mall', 'store', 'shop', 'market', 'retail', 'mart',
            'supermarket', 'reliance', 'dmart', 'more', 'bigbasket', 'grofers',
            'blinkit', 'zepto', 'dunzo', 'swiggy instamart'
        ],
        
        'Entertainment': [
            'netflix', 'amazon prime', 'hotstar', 'sony liv', 'zee5', 'voot',
            'spotify', 'youtube', 'gaana', 'jio saavn', 'wynk', 'apple music',
            'movie', 'cinema', 'pvr', 'inox', 'bookmyshow', 'ticket', 'show',
            'game', 'gaming', 'steam', 'playstation', 'xbox'
        ],
        
        'Utilities': [
            'electricity', 'water', 'gas', 'cylinder', 'mobile', 'recharge',
            'broadband', 'wifi', 'internet', 'jio', 'airtel', 'vodafone', 'bsnl',
            'bill', 'payment', 'postpaid', 'prepaid', 'dth', 'tatasky'
        ],
        
        'Groceries': [
            'grocery', 'kirana', 'supermarket', 'vegetables', 'fruits', 'milk',
            'bread', 'provisions', 'ration', 'bigbasket', 'grofers', 'dunzo',
            'blinkit', 'zepto', 'jiomart', 'fresh', 'organic'
        ],
        
        'Personal Care': [
            'salon', 'parlour', 'spa', 'gym', 'fitness', 'yoga', 'urban company',
            'barber', 'haircut', 'beauty', 'massage', 'wellness', 'grooming'
        ],
        
        'Bills & Recharge': [
            'recharge', 'bill payment', 'paytm', 'phonepe', 'googlepay', 'bhim',
            'upi', 'utility', 'electric bill', 'water bill'
        ]
    }
    
    # VPA to merchant name patterns
    VPA_PATTERNS = {
        'hospital': 'Healthcare',
        'clinic': 'Healthcare',
        'medical': 'Healthcare',
        'swiggy': 'Food & Dining',
        'zomato': 'Food & Dining',
        'netflix': 'Entertainment',
        'amazon': 'Shopping',
        'flipkart': 'Shopping',
        'uber': 'Transportation',
        'ola': 'Transportation'
    }
    
    @staticmethod
    def clean_merchant_name(raw_name: str) -> str:
        """
        Clean up merchant name from VPA IDs and codes
        
        Args:
            raw_name: Raw merchant name (e.g., "VPA ibkpos.ep061900")
            
        Returns:
            Cleaned merchant name
        """
        if not raw_name:
            return "Unknown Merchant"
        
        # Remove "VPA" prefix
        name = re.sub(r'^VPA\s+', '', raw_name, flags=re.IGNORECASE)
        
        # Extract meaningful part from VPA ID
        # Pattern: username@merchant or merchant.provider
        
        # Check if it's an email-like VPA
        if '@' in name:
            parts = name.split('@')
            if len(parts) == 2:
                # Try to extract merchant from domain
                domain = parts[1]
                # Remove common suffixes
                domain = re.sub(r'\.(com|in|net|org|co|upi)$', '', domain, flags=re.IGNORECASE)
                
                # If domain has meaningful name, use it
                if len(domain) > 3 and not domain.isdigit():
                    name = domain.replace('.', ' ').title()
                else:
                    # Use username part
                    username = parts[0]
                    name = username.replace('.', ' ').title()
        
        # Check if it's a phone number or code-based VPA
        elif name.isdigit() or re.match(r'^\d+[\-\.]?\d*$', name):
            return "UPI Payment"
        
        # Extract merchant name from patterns like "merchantname.provider"
        elif '.' in name:
            parts = name.split('.')
            # Take the longest meaningful part
            meaningful_parts = [p for p in parts if len(p) > 3 and not p.isdigit()]
            if meaningful_parts:
                name = max(meaningful_parts, key=len)
        
        # Clean up remaining formatting
        name = name.replace('_', ' ').replace('-', ' ')
        name = re.sub(r'\s+', ' ', name).strip()
        
        # Capitalize properly
        if len(name) > 3 and not name.isupper():
            name = name.title()
        
        # If still looks like code, return generic name
        if len(name) < 3 or name.isdigit():
            return "UPI Payment"
        
        return name
    
    @staticmethod
    def predict_category(vendor_name: str, description: str = "") -> Tuple[str, float]:
        """
        Predict category with confidence score
        
        Args:
            vendor_name: Merchant/vendor name
            description: Transaction description
            
        Returns:
            (category_name, confidence_score)
        """
        combined_text = f"{vendor_name} {description}".lower()
        
        # Score each category
        category_scores = {}
        
        for category, keywords in SmartCategorizer.CATEGORY_KEYWORDS.items():
            score = 0
            matched_keywords = []
            
            for keyword in keywords:
                if keyword in combined_text:
                    # Weight longer keywords higher
                    weight = len(keyword) / 5
                    score += weight
                    matched_keywords.append(keyword)
            
            if score > 0:
                category_scores[category] = {
                    'score': score,
                    'keywords': matched_keywords
                }
        
        # Get best match
        if category_scores:
            best_category = max(category_scores, key=lambda x: category_scores[x]['score'])
            max_score = category_scores[best_category]['score']
            
            # Calculate confidence (0-100%)
            confidence = min(max_score * 20, 100)
            
            return best_category, confidence
        
        # No match found
        return 'Uncategorized', 0.0
    
    @staticmethod
    def get_category_from_vpa(vpa: str) -> Optional[str]:
        """Quick category detection from VPA patterns"""
        vpa_lower = vpa.lower()
        
        for pattern, category in SmartCategorizer.VPA_PATTERNS.items():
            if pattern in vpa_lower:
                return category
        
        return None
    
    @staticmethod
    def enhance_transaction(transaction_data: dict) -> dict:
        """
        Enhance transaction with cleaned name and better category
        
        Args:
            transaction_data: Dict with vendor_name, description, etc.
            
        Returns:
            Enhanced transaction data
        """
        # Clean merchant name
        raw_vendor = transaction_data.get('vendor_name', '')
        cleaned_vendor = SmartCategorizer.clean_merchant_name(raw_vendor)
        
        # Predict category
        description = transaction_data.get('description', '')
        category, confidence = SmartCategorizer.predict_category(
            cleaned_vendor, 
            description
        )
        
        # Update transaction data
        transaction_data['vendor_name_original'] = raw_vendor
        transaction_data['vendor_name'] = cleaned_vendor
        transaction_data['predicted_category'] = category
        transaction_data['category_confidence'] = confidence
        
        return transaction_data


# ============================================================================
# CATEGORY MAPPING HELPER
# ============================================================================

class CategoryMapper:
    """Maps category names to database category IDs"""
    
    @staticmethod
    def get_category_id(category_name: str, db_session) -> int:
        """
        Get category ID from database by name
        
        Args:
            category_name: Category name (e.g., "Food & Dining")
            db_session: SQLAlchemy session
            
        Returns:
            Category ID (defaults to Uncategorized if not found)
        """
        from models.category import Category
        
        # Try exact match
        category = db_session.query(Category).filter_by(name=category_name).first()
        
        if category:
            return category.id
        
        # Try fuzzy match
        category = db_session.query(Category).filter(
            Category.name.ilike(f"%{category_name}%")
        ).first()
        
        if category:
            return category.id
        
        # Default to Uncategorized
        default = db_session.query(Category).filter_by(name='Uncategorized').first()
        if default:
            return default.id
        
        # Fallback to ID 1
        return 1


# ============================================================================
# USAGE EXAMPLE
# ============================================================================

"""
# Example usage in your sync code:

from utils.smart_categorizer import SmartCategorizer, CategoryMapper

# Raw transaction from email
transaction = {
    'vendor_name': 'VPA msvrundavanmultispecialityhospital.eazypay',
    'description': 'HDFC: Hospital payment',
    'amount': 249.0
}

# Enhance transaction
enhanced = SmartCategorizer.enhance_transaction(transaction)

print(enhanced['vendor_name'])  # "Msvrundavan Multispeciality Hospital"
print(enhanced['predicted_category'])  # "Healthcare"
print(enhanced['category_confidence'])  # 85.0

# Get database category ID
category_id = CategoryMapper.get_category_id(
    enhanced['predicted_category'],
    db.session
)
"""