"""
Recategorize Existing HDFC Transactions
Run this to fix categories for already imported transactions

Usage:
    python recategorize_hdfc.py
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import app, db
from models.transaction import Transaction
from utils.smart_categorizer import SmartCategorizer, CategoryMapper

def recategorize_transactions():
    """Recategorize all HDFC email transactions"""
    
    print("\n" + "="*70)
    print("🔄 RECATEGORIZING HDFC TRANSACTIONS")
    print("="*70 + "\n")
    
    with app.app_context():
        try:
            # Get all HDFC email transactions
            transactions = Transaction.query.filter_by(source='hdfc_email').all()
            
            if not transactions:
                print("⚠️  No HDFC transactions found to recategorize")
                return
            
            print(f"Found {len(transactions)} HDFC transactions to recategorize\n")
            
            updated_count = 0
            error_count = 0
            
            for trans in transactions:
                try:
                    # Store original values
                    original_vendor = trans.vendor_name
                    original_category = trans.category.name if trans.category else 'Unknown'
                    
                    # Enhance transaction data
                    trans_data = {
                        'vendor_name': trans.vendor_name,
                        'description': trans.description or ''
                    }
                    
                    enhanced = SmartCategorizer.enhance_transaction(trans_data)
                    
                    # Get new category
                    new_category_name = enhanced['predicted_category']
                    new_category_id = CategoryMapper.get_category_id(new_category_name, db.session)
                    
                    # Get cleaned vendor name
                    cleaned_vendor = enhanced['vendor_name']
                    confidence = enhanced['category_confidence']
                    
                    # Update transaction
                    trans.vendor_name = cleaned_vendor
                    trans.category_id = new_category_id
                    
                    # Show what changed
                    if original_vendor != cleaned_vendor or original_category != new_category_name:
                        print(f"✅ Transaction {trans.id}:")
                        if original_vendor != cleaned_vendor:
                            print(f"   Vendor: {original_vendor}")
                            print(f"        → {cleaned_vendor}")
                        if original_category != new_category_name:
                            print(f"   Category: {original_category}")
                            print(f"          → {new_category_name} ({confidence:.0f}%)")
                        print()
                        updated_count += 1
                    
                except Exception as e:
                    print(f"❌ Error processing transaction {trans.id}: {e}")
                    error_count += 1
                    continue
            
            # Commit all changes
            if updated_count > 0:
                db.session.commit()
                print(f"\n{'='*70}")
                print(f"✅ RECATEGORIZATION COMPLETE!")
                print(f"{'='*70}")
                print(f"\n📊 Summary:")
                print(f"   • Total transactions: {len(transactions)}")
                print(f"   • Updated: {updated_count}")
                print(f"   • Unchanged: {len(transactions) - updated_count - error_count}")
                print(f"   • Errors: {error_count}")
                print(f"\n{'='*70}\n")
            else:
                print("\n✅ All transactions already have correct categories!")
                print(f"   Errors: {error_count}\n")
            
        except Exception as e:
            print(f"\n❌ RECATEGORIZATION FAILED!")
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    recategorize_transactions()
