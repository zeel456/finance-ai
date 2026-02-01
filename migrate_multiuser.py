"""
Database Migration Script
Adds user_id columns to existing tables for multi-user support
Run this ONCE after adding the User model
"""

from models.database import db
from sqlalchemy import text

def upgrade_database_for_multiuser():
    """
    Add user_id columns to transactions, budgets, and documents tables
    This should be run once when implementing multi-user support
    """
    print("\n" + "="*70)
    print("DATABASE MIGRATION: Adding Multi-User Support")
    print("="*70 + "\n")
    
    try:
        with db.engine.connect() as conn:
            # Check existing tables and columns
            tables_to_update = ['transactions', 'budgets', 'documents']
            
            for table_name in tables_to_update:
                print(f"🔄 Checking table: {table_name}")
                
                # Check if table exists
                result = conn.execute(text(
                    f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'"
                ))
                
                if not result.fetchone():
                    print(f"   ⏭️  Table '{table_name}' doesn't exist, skipping")
                    continue
                
                # Check if user_id column already exists
                result = conn.execute(text(f"PRAGMA table_info({table_name})"))
                columns = [row[1] for row in result]
                
                if 'user_id' in columns:
                    print(f"   ✅ Column 'user_id' already exists in {table_name}")
                else:
                    # Add user_id column
                    conn.execute(text(
                        f"ALTER TABLE {table_name} ADD COLUMN user_id INTEGER"
                    ))
                    conn.commit()
                    print(f"   ✅ Added 'user_id' column to {table_name}")
                    
                    # Add index for performance
                    try:
                        conn.execute(text(
                            f"CREATE INDEX idx_{table_name}_user_id ON {table_name}(user_id)"
                        ))
                        conn.commit()
                        print(f"   ✅ Created index on {table_name}.user_id")
                    except Exception as e:
                        print(f"   ⚠️  Index might already exist: {e}")
            
            print("\n" + "="*70)
            print("✅ MIGRATION COMPLETED SUCCESSFULLY")
            print("="*70 + "\n")
            print("Next steps:")
            print("1. Restart your Flask application")
            print("2. Create your first user account")
            print("3. Existing data will be shown to all users until assigned")
            print("\n")
            
            return True
            
    except Exception as e:
        print(f"\n❌ MIGRATION FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def assign_existing_data_to_user(user_id):
    """
    Assign all existing unassigned data to a specific user
    Useful after creating the first admin user
    
    Args:
        user_id: ID of the user to assign data to
    """
    print(f"\n🔄 Assigning existing data to user ID {user_id}...")
    
    try:
        from models.transaction import Transaction
        from models.budget import Budget
        from models.document import Document
        
        # Assign unassigned transactions
        trans_count = Transaction.query.filter_by(user_id=None).update({'user_id': user_id})
        
        # Assign unassigned budgets
        budget_count = Budget.query.filter_by(user_id=None).update({'user_id': user_id})
        
        # Assign unassigned documents
        doc_count = Document.query.filter_by(user_id=None).update({'user_id': user_id})
        
        db.session.commit()
        
        print(f"   ✅ Assigned {trans_count} transactions")
        print(f"   ✅ Assigned {budget_count} budgets")
        print(f"   ✅ Assigned {doc_count} documents")
        print(f"\n✅ Data assignment completed!\n")
        
        return True
        
    except Exception as e:
        db.session.rollback()
        print(f"\n❌ Assignment failed: {e}\n")
        return False


def create_admin_user(username, email, password, full_name=None):
    """
    Create the first admin user
    
    Args:
        username: Admin username
        email: Admin email
        password: Admin password
        full_name: Optional full name
    
    Returns:
        User object if successful, None otherwise
    """
    from models.user import User
    
    print(f"\n🔄 Creating admin user: {username}")
    
    # Check if user already exists
    existing = User.query.filter(
        (User.username == username) | (User.email == email)
    ).first()
    
    if existing:
        print(f"   ⚠️  User already exists!")
        return existing
    
    # Create admin user
    user, error = User.create_user(
        username=username,
        email=email,
        password=password,
        full_name=full_name or username
    )
    
    if error:
        print(f"   ❌ Failed to create user: {error}")
        return None
    
    # Make user admin
    user.is_admin = True
    db.session.commit()
    
    print(f"   ✅ Admin user created successfully!")
    print(f"   Username: {user.username}")
    print(f"   Email: {user.email}")
    print(f"   User ID: {user.id}\n")
    
    return user


# ============================================================================
# COMMAND LINE INTERFACE
# ============================================================================

if __name__ == '__main__':
    print("\n" + "="*70)
    print("FINANCE AI - DATABASE MIGRATION TOOL")
    print("="*70)
    
    from app import app
    
    with app.app_context():
        print("\nWhat would you like to do?")
        print("1. Upgrade database (add user_id columns)")
        print("2. Create admin user")
        print("3. Assign existing data to user")
        print("4. Complete setup (all of the above)")
        
        choice = input("\nEnter choice (1-4): ").strip()
        
        if choice == '1':
            upgrade_database_for_multiuser()
        
        elif choice == '2':
            print("\n--- Create Admin User ---")
            username = input("Username: ").strip()
            email = input("Email: ").strip()
            password = input("Password: ").strip()
            full_name = input("Full Name (optional): ").strip()
            
            user = create_admin_user(username, email, password, full_name or None)
            
        elif choice == '3':
            user_id = input("User ID to assign data to: ").strip()
            try:
                user_id = int(user_id)
                assign_existing_data_to_user(user_id)
            except ValueError:
                print("❌ Invalid user ID")
        
        elif choice == '4':
            # Complete setup
            print("\n--- COMPLETE SETUP ---\n")
            
            # Step 1: Upgrade database
            if not upgrade_database_for_multiuser():
                print("❌ Setup failed at database upgrade")
                exit(1)
            
            # Step 2: Create admin user
            print("\n--- Create Admin User ---")
            username = input("Username: ").strip()
            email = input("Email: ").strip()
            password = input("Password: ").strip()
            full_name = input("Full Name (optional): ").strip()
            
            user = create_admin_user(username, email, password, full_name or None)
            
            if not user:
                print("❌ Setup failed at user creation")
                exit(1)
            
            # Step 3: Assign existing data
            assign_data = input("\nAssign existing data to this user? (y/n): ").strip().lower()
            
            if assign_data == 'y':
                assign_existing_data_to_user(user.id)
            
            print("\n" + "="*70)
            print("🎉 SETUP COMPLETED SUCCESSFULLY!")
            print("="*70)
            print("\nYou can now:")
            print(f"1. Login with username: {user.username}")
            print("2. Start using the multi-user Finance AI system")
            print("3. Create additional user accounts as needed\n")
        
        else:
            print("❌ Invalid choice")