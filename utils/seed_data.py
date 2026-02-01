from models.database import db
from models.document import Document
from models.transaction import Transaction
from models.category import Category
from datetime import datetime, timedelta
import random

class SeedData:
    """Generate dummy data for testing"""
    
    # Sample vendors by category
    VENDORS = {
        'Food & Dining': ['McDonald\'s', 'Starbucks', 'Domino\'s Pizza', 'Subway', 'Local Restaurant', 'Food Mart', 'Cafe Coffee Day', 'Pizza Hut'],
        'Transportation': ['Shell Gas', 'Uber', 'Ola', 'Metro Card', 'Parking Lot', 'Car Service', 'BPCL Petrol'],
        'Shopping': ['Amazon', 'Flipkart', 'Walmart', 'Target', 'Best Buy', 'Local Store', 'Reliance Digital'],
        'Entertainment': ['Netflix', 'Amazon Prime', 'Spotify', 'Cinema Hall', 'Gaming Store', 'BookMyShow', 'Disney+ Hotstar'],
        'Utilities': ['Electric Company', 'Water Department', 'Jio Fiber', 'Airtel', 'BSNL', 'Gas Agency'],
        'Healthcare': ['City Hospital', 'Apollo Pharmacy', 'Dental Clinic', 'Vision Center', 'Fortis Hospital', 'Max Healthcare'],
        'Education': ['Udemy', 'Coursera', 'Book Store', 'Byju\'s', 'Unacademy', 'Stationery Shop'],
        'Travel': ['MakeMyTrip', 'Goibibo', 'OYO Rooms', 'Airbnb', 'Cleartrip', 'IRCTC'],
        'Insurance': ['LIC', 'HDFC Life', 'ICICI Prudential', 'Star Health', 'Bajaj Allianz'],
        'Other': ['Hardware Store', 'Miscellaneous', 'Unknown Vendor', 'General Store']
    }
    
    @staticmethod
    def generate_transactions(num_transactions=50):
        """Generate dummy transactions"""
        categories = Category.query.all()
        
        if not categories:
            print("❌ No categories found. Please run app first to seed categories.")
            return
        
        print(f"🌱 Generating {num_transactions} dummy transactions...")
        
        transactions_created = 0
        
        for i in range(num_transactions):
            try:
                # Random category
                category = random.choice(categories)
                
                # Random vendor from category
                vendors_list = SeedData.VENDORS.get(category.name, ['Unknown Vendor'])
                vendor = random.choice(vendors_list)
                
                # Random date in last 90 days
                days_ago = random.randint(0, 90)
                transaction_date = datetime.now() - timedelta(days=days_ago)
                
                # Random amount based on category
                if category.name in ['Travel', 'Insurance', 'Healthcare']:
                    amount = round(random.uniform(1000, 15000), 2)
                elif category.name in ['Shopping', 'Entertainment']:
                    amount = round(random.uniform(500, 5000), 2)
                elif category.name in ['Food & Dining']:
                    amount = round(random.uniform(100, 1500), 2)
                else:
                    amount = round(random.uniform(200, 3000), 2)
                
                # Random tax (5-18%)
                tax_percentage = random.choice([5, 12, 18])
                tax_amount = round(amount * (tax_percentage / 100), 2)
                
                # Payment method
                payment_method = random.choice(['Card', 'Cash', 'UPI', 'Net Banking', 'Wallet'])
                
                transaction = Transaction(
                    document_id=None,  # No document for dummy data
                    transaction_date=transaction_date.date(),
                    amount=amount,
                    currency='INR',
                    vendor_name=vendor,
                    description=f'Payment to {vendor}',
                    category_id=category.id,
                    payment_method=payment_method,
                    tax_amount=tax_amount,
                    tax_percentage=tax_percentage
                )
                
                db.session.add(transaction)
                transactions_created += 1
                
            except Exception as e:
                print(f"⚠️ Error creating transaction {i+1}: {str(e)}")
                continue
        
        try:
            db.session.commit()
            print(f"✅ Generated {transactions_created} transactions successfully!")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error committing transactions: {str(e)}")
    
    @staticmethod
    def generate_documents(num_docs=10):
        """Generate dummy documents"""
        print(f"🌱 Generating {num_docs} dummy documents...")
        
        doc_types = ['invoice', 'receipt', 'statement']
        documents_created = 0
        
        for i in range(num_docs):
            try:
                doc_type = random.choice(doc_types)
                filename = f"dummy_{doc_type}_{i+1}.pdf"
                
                document = Document(
                    filename=filename,
                    original_filename=filename,
                    file_type=doc_type,
                    file_path=f"/uploads/{filename}",
                    processed=random.choice([True, False]),
                    raw_text=f"Dummy text content for {filename}"
                )
                
                db.session.add(document)
                documents_created += 1
                
            except Exception as e:
                print(f"⚠️ Error creating document {i+1}: {str(e)}")
                continue
        
        try:
            db.session.commit()
            print(f"✅ Generated {documents_created} documents successfully!")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error committing documents: {str(e)}")
    
    @staticmethod
    def clear_all_data():
        """Clear all data (use with caution!)"""
        try:
            print("🗑️  Clearing all data...")
            Transaction.query.delete()
            Document.query.delete()
            db.session.commit()
            print("✅ All data cleared!")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error clearing data: {str(e)}")