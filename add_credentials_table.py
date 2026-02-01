"""
Add Bank Credentials Table
Run this once: python add_credentials_table.py
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import app, db
from sqlalchemy import text

def add_credentials_table():
    """Add bank_credentials table to database"""
    
    print("\n" + "="*60)
    print("🔄 ADDING BANK CREDENTIALS TABLE")
    print("="*60 + "\n")
    
    with app.app_context():
        try:
            # Check if table exists
            with db.engine.connect() as conn:
                result = conn.execute(text(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='bank_credentials'"
                ))
                
                if result.fetchone():
                    print("⏭️  Table 'bank_credentials' already exists!")
                    return True
            
            # Create table
            print("🔧 Creating bank_credentials table...")
            
            create_sql = """
            CREATE TABLE bank_credentials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bank_name VARCHAR(50) DEFAULT 'HDFC',
                email_address VARCHAR(255) UNIQUE NOT NULL,
                encrypted_password TEXT NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                last_sync DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
            
            with db.engine.connect() as conn:
                conn.execute(text(create_sql))
                conn.commit()
            
            print("✅ Table created successfully!")
            
            # Create index
            print("🔧 Creating index...")
            with db.engine.connect() as conn:
                conn.execute(text(
                    "CREATE INDEX idx_bank_creds_email ON bank_credentials(email_address)"
                ))
                conn.commit()
            
            print("✅ Index created!")
            
            print("\n" + "="*60)
            print("✅ CREDENTIALS TABLE ADDED SUCCESSFULLY!")
            print("="*60)
            print("\nYour credentials will now persist across restarts!")
            print("\n" + "="*60 + "\n")
            
            return True
            
        except Exception as e:
            print(f"\n❌ FAILED!")
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    success = add_credentials_table()
    sys.exit(0 if success else 1)