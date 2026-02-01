"""
Database Migration Script for HDFC Integration
Fixed for SQLite limitations

Usage:
    python migrate_hdfc.py
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, db
from sqlalchemy import text

def check_column_exists(table_name, column_name):
    """Check if column exists in table"""
    with db.engine.connect() as conn:
        result = conn.execute(text(f"PRAGMA table_info({table_name})"))
        columns = [row[1] for row in result]
        return column_name in columns

def migrate_database():
    """Migrate database to support HDFC integration"""
    
    print("\n" + "="*60)
    print("🔄 STARTING DATABASE MIGRATION FOR HDFC INTEGRATION")
    print("="*60 + "\n")
    
    with app.app_context():
        try:
            # Define new columns (WITHOUT UNIQUE constraint in ALTER TABLE)
            migrations = [
                {
                    'column': 'source',
                    'sql': "ALTER TABLE transactions ADD COLUMN source VARCHAR(50) DEFAULT 'manual'",
                    'description': 'Transaction source tracking'
                },
                {
                    'column': 'transaction_hash',
                    'sql': "ALTER TABLE transactions ADD COLUMN transaction_hash VARCHAR(32)",  # ← REMOVED UNIQUE
                    'description': 'Deduplication hash'
                },
                {
                    'column': 'reference_number',
                    'sql': "ALTER TABLE transactions ADD COLUMN reference_number VARCHAR(100)",
                    'description': 'Bank reference/UPI ID'
                },
                {
                    'column': 'account_number',
                    'sql': "ALTER TABLE transactions ADD COLUMN account_number VARCHAR(20)",
                    'description': 'Bank account number'
                },
                {
                    'column': 'transaction_type',
                    'sql': "ALTER TABLE transactions ADD COLUMN transaction_type VARCHAR(20) DEFAULT 'debit'",
                    'description': 'Debit/Credit indicator'
                },
                {
                    'column': 'is_deleted',
                    'sql': "ALTER TABLE transactions ADD COLUMN is_deleted BOOLEAN DEFAULT 0",
                    'description': 'Soft delete flag'
                }
            ]
            
            # Execute migrations
            added_count = 0
            skipped_count = 0
            
            with db.engine.connect() as conn:
                for migration in migrations:
                    column_name = migration['column']
                    
                    if check_column_exists('transactions', column_name):
                        print(f"⏭️  SKIPPED: {column_name} (already exists)")
                        skipped_count += 1
                    else:
                        print(f"🔧 ADDING: {column_name} - {migration['description']}")
                        conn.execute(text(migration['sql']))
                        conn.commit()
                        print(f"   ✅ Successfully added: {column_name}")
                        added_count += 1
            
            # Update existing transactions
            print("\n🔄 Updating existing transactions...")
            
            with db.engine.connect() as conn:
                # Set source='manual' for all existing transactions without source
                result = conn.execute(text(
                    "UPDATE transactions SET source = 'manual' WHERE source IS NULL"
                ))
                updated = result.rowcount
                conn.commit()
                print(f"   ✅ Updated {updated} transactions with source='manual'")
                
                # Set transaction_type='debit' for all existing transactions
                result = conn.execute(text(
                    "UPDATE transactions SET transaction_type = 'debit' WHERE transaction_type IS NULL"
                ))
                updated = result.rowcount
                conn.commit()
                print(f"   ✅ Updated {updated} transactions with transaction_type='debit'")
            
            # Create indexes for better performance
            print("\n🔧 Creating indexes...")
            
            try:
                with db.engine.connect() as conn:
                    # Index on source
                    conn.execute(text(
                        "CREATE INDEX IF NOT EXISTS idx_transactions_source ON transactions(source)"
                    ))
                    conn.commit()
                    print("   ✅ Created index: idx_transactions_source")
                    
                    # Index on transaction_hash (for deduplication)
                    # We'll create UNIQUE index separately
                    conn.execute(text(
                        "CREATE UNIQUE INDEX IF NOT EXISTS idx_transactions_hash ON transactions(transaction_hash) WHERE transaction_hash IS NOT NULL"
                    ))
                    conn.commit()
                    print("   ✅ Created unique index: idx_transactions_hash")
                    
                    # Index on transaction_date
                    conn.execute(text(
                        "CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(transaction_date)"
                    ))
                    conn.commit()
                    print("   ✅ Created index: idx_transactions_date")
                    
                    # Index on vendor_name for faster searches
                    conn.execute(text(
                        "CREATE INDEX IF NOT EXISTS idx_transactions_vendor ON transactions(vendor_name)"
                    ))
                    conn.commit()
                    print("   ✅ Created index: idx_transactions_vendor")
                    
            except Exception as e:
                print(f"   ⚠️  Index creation warning: {e}")
                print(f"   This is OK - indexes may already exist")
            
            # Verify the migration
            print("\n🔍 Verifying migration...")
            with db.engine.connect() as conn:
                result = conn.execute(text("PRAGMA table_info(transactions)"))
                columns = [row[1] for row in result]
                
                required = ['source', 'transaction_hash', 'reference_number', 
                           'account_number', 'transaction_type', 'is_deleted']
                
                all_ok = all(col in columns for col in required)
                
                if all_ok:
                    print("   ✅ All columns verified!")
                else:
                    missing = [col for col in required if col not in columns]
                    print(f"   ⚠️  Missing columns: {missing}")
            
            # Print summary
            print("\n" + "="*60)
            print("✅ MIGRATION COMPLETED SUCCESSFULLY!")
            print("="*60)
            print(f"\n📊 Summary:")
            print(f"   • Columns Added: {added_count}")
            print(f"   • Columns Skipped: {skipped_count}")
            print(f"   • Total Migrations: {len(migrations)}")
            print(f"\n🎉 Your database is now ready for HDFC integration!")
            print(f"\nNext steps:")
            print(f"   1. Restart your Flask app")
            print(f"   2. Visit http://localhost:5000/hdfc-sync")
            print(f"   3. Connect your Gmail account")
            print(f"   4. Start syncing transactions!")
            print("\n" + "="*60 + "\n")
            
            return True
            
        except Exception as e:
            print(f"\n❌ MIGRATION FAILED!")
            print(f"Error: {e}")
            print(f"\nPlease check the error and try again.")
            import traceback
            traceback.print_exc()
            return False

def verify_migration():
    """Verify migration was successful"""
    
    print("\n🔍 Verifying migration...")
    
    with app.app_context():
        try:
            with db.engine.connect() as conn:
                result = conn.execute(text("PRAGMA table_info(transactions)"))
                columns = [row[1] for row in result]
                
                required_columns = [
                    'source',
                    'transaction_hash',
                    'reference_number',
                    'account_number',
                    'transaction_type',
                    'is_deleted'
                ]
                
                all_present = all(col in columns for col in required_columns)
                
                if all_present:
                    print("✅ All required columns are present!")
                    print(f"\nCurrent columns in transactions table:")
                    for col in columns:
                        print(f"   • {col}")
                    
                    # Check indexes
                    print(f"\nIndexes:")
                    result = conn.execute(text("PRAGMA index_list(transactions)"))
                    indexes = [row[1] for row in result]
                    for idx in indexes:
                        print(f"   • {idx}")
                    
                    return True
                else:
                    print("❌ Some columns are missing!")
                    missing = [col for col in required_columns if col not in columns]
                    print(f"Missing columns: {missing}")
                    return False
                    
        except Exception as e:
            print(f"❌ Verification failed: {e}")
            return False

def rollback_migration():
    """Rollback migration (for SQLite, we need to recreate table)"""
    
    print("\n⚠️  ROLLING BACK MIGRATION...")
    print("This will remove all HDFC integration columns.")
    
    confirm = input("Are you sure? Type 'YES' to confirm: ")
    
    if confirm != 'YES':
        print("Rollback cancelled.")
        return
    
    with app.app_context():
        print("\n⚠️  SQLite limitation: Cannot drop columns directly")
        print("\nTo rollback manually:")
        print("1. Backup your database")
        print("2. Delete the database file")
        print("3. Restart the app (it will recreate tables)")
        print("\nOr keep the new columns - they won't affect existing functionality")

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Database migration for HDFC integration')
    parser.add_argument('--verify', action='store_true', help='Verify migration')
    parser.add_argument('--rollback', action='store_true', help='Rollback migration')
    
    args = parser.parse_args()
    
    if args.verify:
        verify_migration()
    elif args.rollback:
        rollback_migration()
    else:
        # Run migration
        success = migrate_database()
        
        if success:
            # Verify
            verify_migration()
        
        sys.exit(0 if success else 1)