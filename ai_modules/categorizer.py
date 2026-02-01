from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
import pickle
import os
import json
from typing import Dict, List, Tuple, Optional
import re

class ImprovedTransactionCategorizer:
    """Categorize transactions using improved ML with context awareness"""
    
    def __init__(self, model_type='nb'):
        """
        Args:
            model_type: 'nb' (Naive Bayes), 'rf' (Random Forest), or 'lr' (Logistic Regression)
        """
        self.vectorizer = TfidfVectorizer(
            max_features=200, 
            ngram_range=(1, 3),  # Include trigrams for better context
            min_df=1,
            stop_words=None  # Keep all words for better domain specificity
        )
        
        # Select classifier
        if model_type == 'rf':
            self.classifier = RandomForestClassifier(n_estimators=100, random_state=42)
        elif model_type == 'lr':
            self.classifier = LogisticRegression(max_iter=1000, random_state=42)
        else:
            self.classifier = MultinomialNB(alpha=0.1)  # Lower alpha for better fit
        
        self.trained = False
        self.categories = {}
        self.model_type = model_type
    
    def get_enhanced_training_data(self) -> Dict[str, List[str]]:
        """Enhanced training data with more examples and context"""
        return {
            'Food & Dining': [
                # Fast food chains
                'mcdonalds', 'kfc', 'dominos', 'pizza hut', 'subway', 'starbucks',
                'burger king', 'wendys', 'taco bell', 'dunkin donuts',
                # Restaurants
                'restaurant', 'cafe', 'food', 'dining', 'eatery', 'bistro', 'diner',
                'barbeque nation', 'mainland china', 'punjabi by nature',
                # Delivery services
                'swiggy', 'zomato', 'uber eats', 'food delivery', 'food order',
                # Indian restaurants
                'haldirams', 'bikanervala', 'sagar ratna', 'saravana bhavan',
                # Cuisines
                'burger', 'pizza', 'coffee', 'breakfast', 'lunch', 'dinner',
                'biryani', 'chinese food', 'north indian', 'south indian',
                # Grocery
                'grocery', 'supermarket', 'food mart', 'bakery', 'cafe coffee day',
                'more megastore', 'reliance fresh', 'big basket', 'grofers',
                # Beverages
                'juice corner', 'tea stall', 'smoothie', 'ice cream parlor'
            ],
            
            'Transportation': [
                # Ride sharing
                'uber', 'ola', 'ola cabs', 'uber cab', 'taxi', 'cab', 'ride share',
                'meru cabs', 'auto rickshaw', 'rickshaw',
                # Fuel
                'fuel', 'petrol', 'diesel', 'gas', 'gas station', 'petrol pump',
                'bpcl', 'hpcl', 'iocl', 'shell', 'hp petrol', 'indian oil', 'essar',
                # Public transport
                'metro', 'bus', 'railway', 'train', 'local train', 'irctc',
                'delhi metro', 'mumbai metro', 'bangalore metro',
                # Other
                'parking', 'toll', 'toll plaza', 'valet parking',
                # Airlines
                'flight', 'airline', 'indigo', 'spicejet', 'air india', 'vistara',
                # Car services
                'car wash', 'car service', 'vehicle maintenance'
            ],
            
            'Shopping': [
                # E-commerce
                'amazon', 'flipkart', 'myntra', 'ajio', 'nykaa', 'snapdeal',
                'online shopping', 'e-commerce', 'online purchase',
                # Retail chains
                'reliance trends', 'westside', 'pantaloons', 'shoppers stop',
                'lifestyle', 'central', 'max fashion',
                # Grocery/Supermarkets
                'dmart', 'big bazaar', 'more', 'reliance fresh', 'walmart',
                'spencer', 'hyper city',
                # Fashion
                'clothing', 'fashion', 'apparel', 'shoes', 'footwear',
                'handbag', 'accessories', 'jewelry', 'watches',
                # Electronics
                'electronics', 'croma', 'vijay sales', 'reliance digital',
                'laptop', 'mobile', 'gadget', 'appliances',
                # Department stores
                'mall', 'shop', 'store', 'retail', 'boutique', 'showroom',
                # Specific items
                'book store', 'stationery', 'gifts', 'toys', 'furniture',
                'home decor', 'kitchenware'
            ],
            
            'Entertainment': [
                # Streaming
                'netflix', 'amazon prime', 'hotstar', 'disney', 'zee5',
                'sony liv', 'voot', 'alt balaji', 'prime video',
                # Music
                'spotify', 'apple music', 'youtube premium', 'gaana', 'wynk',
                'jio saavn', 'music subscription',
                # Movies
                'movie', 'cinema', 'theatre', 'pvr', 'inox', 'cinepolis',
                'carnival', 'bookmyshow', 'paytm movies', 'film',
                # Gaming
                'gaming', 'game', 'playstation', 'xbox', 'steam', 'epic games',
                'pubg', 'free fire', 'gaming subscription',
                # Events
                'concert', 'event', 'show', 'entertainment', 'festival',
                'comedy show', 'live show', 'sports event', 'match ticket',
                # Hobbies
                'gym membership', 'fitness center', 'yoga class', 'dance class',
                'art supplies', 'hobby'
            ],
            
            'Utilities': [
                # Electricity
                'electricity', 'electric bill', 'power bill', 'electricity board',
                'bescom', 'msedcl', 'tata power', 'adani electricity',
                # Water
                'water', 'water bill', 'water supply', 'municipal water',
                # Gas
                'gas', 'lpg', 'cooking gas', 'gas cylinder', 'bharat gas',
                'hp gas', 'indane gas',
                # Internet/Broadband
                'internet', 'broadband', 'wifi', 'internet bill', 'fiber',
                'act fibernet', 'hathway', 'tikona', 'netplus', 'local cable',
                # Mobile/Phone
                'mobile', 'phone', 'recharge', 'mobile recharge', 'prepaid',
                'postpaid', 'phone bill', 'telecom',
                # Telecom providers
                'jio', 'airtel', 'vodafone', 'vi', 'idea', 'bsnl', 'reliance jio',
                # DTH
                'dth', 'tata sky', 'dish tv', 'sun direct', 'airtel digital tv',
                # Other
                'bill payment', 'utility', 'utility bill', 'municipal tax'
            ],
            
            'Healthcare': [
                # Medical facilities
                'hospital', 'clinic', 'nursing home', 'medical center',
                'apollo', 'max', 'fortis', 'manipal', 'columbia asia',
                'medanta', 'aiims', 'lilavati',
                # Doctors
                'doctor', 'physician', 'consultant', 'specialist',
                'dental', 'dentist', 'orthodontist',
                # Services
                'medical', 'health', 'healthcare', 'checkup', 'consultation',
                'treatment', 'surgery', 'operation', 'therapy',
                # Pharmacy
                'pharmacy', 'medicine', 'drug', 'chemist', 'medical store',
                'apollo pharmacy', 'medplus', 'netmeds', '1mg',
                # Labs
                'lab', 'laboratory', 'diagnostic', 'test', 'pathology',
                'dr lal pathlabs', 'thyrocare', 'metropolis',
                # Alternative medicine
                'ayurveda', 'homeopathy', 'physiotherapy', 'optician',
                # Wellness
                'health insurance claim', 'medical insurance'
            ],
            
            'Education': [
                # Institutions
                'school', 'college', 'university', 'institute', 'academy',
                'coaching', 'tuition', 'tutorial', 'training center',
                # Online learning
                'udemy', 'coursera', 'edx', 'skillshare', 'linkedin learning',
                'byjus', 'unacademy', 'vedantu', 'toppr', 'online course',
                # Materials
                'book', 'textbook', 'notebook', 'stationery', 'study material',
                'library', 'library fine',
                # Services
                'education', 'learning', 'study', 'training', 'certification',
                'exam', 'exam fee', 'admission', 'tuition fee', 'school fee',
                # Specific
                'ielts', 'toefl', 'gre', 'gmat', 'cat', 'jee', 'neet',
                'language class', 'programming course', 'workshop', 'seminar'
            ],
            
            'Travel': [
                # Accommodation
                'hotel', 'resort', 'guest house', 'lodge', 'inn', 'hostel',
                'oyo', 'treebo', 'fab hotels', 'airbnb', 'homestay',
                'taj', 'oberoi', 'itc', 'hyatt', 'marriott',
                # Flight
                'flight', 'airline', 'airways', 'air ticket', 'flight booking',
                'indigo', 'spicejet', 'air india', 'vistara', 'go air',
                # Train
                'train', 'railway', 'irctc', 'train ticket', 'tatkal',
                # Travel booking
                'makemytrip', 'goibibo', 'cleartrip', 'yatra', 'ixigo',
                'travel booking', 'trip', 'tour', 'vacation', 'holiday',
                # Other
                'travel', 'tourism', 'tour package', 'travel agent',
                'visa', 'passport', 'luggage', 'travel insurance',
                'car rental', 'bike rental'
            ],
            
            'Insurance': [
                'insurance', 'policy', 'premium', 'insurance premium',
                # Life insurance
                'life insurance', 'lic', 'hdfc life', 'icici prudential',
                'max life', 'sbi life', 'bajaj allianz life',
                # Health insurance
                'health insurance', 'medical insurance', 'mediclaim',
                'star health', 'care health', 'niva bupa',
                # General insurance
                'car insurance', 'vehicle insurance', 'motor insurance',
                'home insurance', 'property insurance', 'travel insurance',
                'bajaj allianz', 'new india assurance', 'oriental insurance',
                # Other
                'coverage', 'claim', 'policy renewal', 'insurance renewal'
            ],
            
            'Investments & Savings': [
                # Mutual funds
                'mutual fund', 'sip', 'systematic investment', 'fund house',
                'hdfc mutual fund', 'icici prudential mf', 'sbi mutual fund',
                # Stocks
                'stock', 'share', 'equity', 'zerodha', 'upstox', 'groww',
                'angel broking', 'stock market', 'trading',
                # Fixed deposits
                'fixed deposit', 'fd', 'recurring deposit', 'rd',
                # Other
                'investment', 'savings', 'portfolio', 'demat', 'ppf',
                'nps', 'national pension', 'gold bond', 'sukanya samriddhi'
            ],
            
            'Personal Care': [
                'salon', 'spa', 'beauty parlor', 'hair cut', 'grooming',
                'lakme salon', 'naturals', 'jawed habib', 'green trends',
                'massage', 'facial', 'manicure', 'pedicure',
                'cosmetics', 'makeup', 'skincare', 'perfume',
                'laundry', 'dry cleaning', 'ironing service'
            ],
            
            'Home & Garden': [
                'furniture', 'home decor', 'furnishing', 'ikea', 'urban ladder',
                'pepperfry', 'hometown', 'decor', 'interior',
                'hardware', 'tools', 'plumbing', 'electrical',
                'gardening', 'plants', 'nursery', 'landscaping',
                'home repair', 'maintenance', 'cleaning service',
                'pest control', 'painting', 'carpenter', 'electrician', 'plumber'
            ],
            
            'Pets': [
                'pet', 'pet food', 'pet store', 'veterinary', 'vet',
                'pet clinic', 'dog food', 'cat food', 'pet supplies',
                'pet grooming', 'pet care', 'animal hospital'
            ],
            
            'Donations & Charity': [
                'donation', 'charity', 'ngo', 'trust', 'foundation',
                'contribute', 'giving', 'welfare', 'relief fund',
                'temple', 'church', 'mosque', 'gurudwara', 'religious'
            ],
            
            'Government & Legal': [
                'government', 'municipal', 'tax', 'income tax', 'property tax',
                'fine', 'penalty', 'challan', 'traffic fine',
                'legal', 'lawyer', 'attorney', 'court', 'legal fee',
                'notary', 'registration', 'license', 'permit',
                'passport fee', 'visa fee', 'aadhar', 'pan card'
            ],
            
            'Other': [
                'miscellaneous', 'other', 'general', 'unknown', 'various',
                'payment', 'transfer', 'service', 'charge', 'fee',
                'atm withdrawal', 'cash withdrawal', 'bank charge'
            ]
        }
    
    def augment_training_data(self, categories_dict: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """Augment training data with variations"""
        augmented = {}
        
        for category, keywords in categories_dict.items():
            expanded = set(keywords)
            
            for keyword in keywords:
                # Add singular/plural variations
                if keyword.endswith('s') and len(keyword) > 3:
                    expanded.add(keyword[:-1])
                else:
                    expanded.add(keyword + 's')
                
                # Add variations with/without spaces
                if ' ' in keyword:
                    expanded.add(keyword.replace(' ', ''))
                
                # Add common prefixes
                expanded.add(f"purchase {keyword}")
                expanded.add(f"payment {keyword}")
                expanded.add(f"bill {keyword}")
            
            augmented[category] = list(expanded)
        
        return augmented
    
    def train(self, categories_dict: Optional[Dict[str, List[str]]] = None):
        """Train the classifier with optional custom categories"""
        if categories_dict is None:
            categories_dict = self.get_enhanced_training_data()
        
        # Augment training data
        categories_dict = self.augment_training_data(categories_dict)
        
        # Store category mapping
        self.categories = {i: name for i, name in enumerate(categories_dict.keys())}
        
        # Prepare training data
        texts = []
        labels = []
        
        for label_id, (category, keywords) in enumerate(categories_dict.items()):
            for keyword in keywords:
                texts.append(keyword.lower())
                labels.append(label_id)
        
        # Train
        X = self.vectorizer.fit_transform(texts)
        self.classifier.fit(X, labels)
        self.trained = True
        
        print(f"✅ Categorizer trained with {len(texts)} examples across {len(categories_dict)} categories")
        print(f"   Model type: {self.model_type}")
    
    def extract_features(self, vendor_name: str, description: str = '', amount: float = None) -> str:
        """Extract and combine features for better classification"""
        features = []
        
        # Vendor name
        if vendor_name:
            features.append(vendor_name.lower())
        
        # Description
        if description:
            features.append(description.lower())
        
        # Amount-based hints (e.g., small amounts often food, large amounts often shopping)
        if amount:
            if amount < 500:
                features.append('small_transaction')
            elif amount > 10000:
                features.append('large_transaction')
        
        return ' '.join(features)
    
    def predict_category(self, vendor_name: str, description: str = '', amount: float = None) -> Tuple[str, float]:
        """Predict category for a transaction with confidence"""
        if not self.trained:
            # Train with default data if not trained
            self.train()
        
        # Combine all features
        text = self.extract_features(vendor_name, description, amount)
        
        if not text.strip():
            return 'Other', 0.0
        
        # Transform and predict
        try:
            X = self.vectorizer.transform([text])
            prediction = self.classifier.predict(X)[0]
            
            # Get category name
            category_name = self.categories.get(prediction, 'Other')
            
            # Get confidence score
            if hasattr(self.classifier, 'predict_proba'):
                probabilities = self.classifier.predict_proba(X)[0]
                confidence = max(probabilities) * 100
            else:
                confidence = 50.0  # Default confidence for classifiers without probability
            
            return category_name, confidence
            
        except Exception as e:
            print(f"Error predicting category: {e}")
            return 'Other', 0.0
    
    def predict_with_alternatives(self, vendor_name: str, description: str = '', 
                                  amount: float = None, top_n: int = 3) -> List[Tuple[str, float]]:
        """Predict category with top N alternatives"""
        if not self.trained:
            self.train()
        
        text = self.extract_features(vendor_name, description, amount)
        
        if not text.strip():
            return [('Other', 0.0)]
        
        try:
            X = self.vectorizer.transform([text])
            
            if hasattr(self.classifier, 'predict_proba'):
                probabilities = self.classifier.predict_proba(X)[0]
                
                # Get top N categories
                top_indices = probabilities.argsort()[-top_n:][::-1]
                results = []
                
                for idx in top_indices:
                    category_name = self.categories.get(idx, 'Other')
                    confidence = probabilities[idx] * 100
                    results.append((category_name, confidence))
                
                return results
            else:
                prediction = self.classifier.predict(X)[0]
                category_name = self.categories.get(prediction, 'Other')
                return [(category_name, 50.0)]
                
        except Exception as e:
            print(f"Error predicting alternatives: {e}")
            return [('Other', 0.0)]
    
    def save_model(self, filepath: str):
        """Save trained model to disk"""
        model_data = {
            'vectorizer': self.vectorizer,
            'classifier': self.classifier,
            'categories': self.categories,
            'trained': self.trained,
            'model_type': self.model_type
        }
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)
        
        print(f"✅ Model saved to {filepath}")
    
    def load_model(self, filepath: str) -> bool:
        """Load trained model from disk"""
        if os.path.exists(filepath):
            try:
                with open(filepath, 'rb') as f:
                    model_data = pickle.load(f)
                
                self.vectorizer = model_data['vectorizer']
                self.classifier = model_data['classifier']
                self.categories = model_data['categories']
                self.trained = model_data['trained']
                self.model_type = model_data.get('model_type', 'nb')
                
                print(f"✅ Model loaded from {filepath}")
                return True
            except Exception as e:
                print(f"Error loading model: {e}")
                return False
        return False
    
    def retrain_with_feedback(self, vendor_name: str, description: str, 
                             correct_category: str, amount: float = None):
        """Retrain model with user feedback"""
        # Add new example to training data
        text = self.extract_features(vendor_name, description, amount)
        
        # Find category ID
        category_id = None
        for cid, cname in self.categories.items():
            if cname == correct_category:
                category_id = cid
                break
        
        if category_id is None:
            print(f"Warning: Category '{correct_category}' not found")
            return
        
        # This is a simplified version - in production, you'd want to:
        # 1. Store feedback examples
        # 2. Periodically retrain with accumulated feedback
        # 3. Validate model performance
        
        print(f"Feedback recorded: '{vendor_name}' -> '{correct_category}'")

TransactionCategorizer = ImprovedTransactionCategorizer
