import os
import sys
from dotenv import load_dotenv
from sqlalchemy import text
load_dotenv()

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app.db import engine

def add_role_column():
    """Add role column to users table"""
    with engine.connect() as conn:
        try:
            # Check if column exists
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='users' AND column_name='role'
            """))
            
            if result.fetchone():
                print("✅ Role column already exists in users table")
                return
            
            # Add role column with default value 'user'
            conn.execute(text("""
                ALTER TABLE users 
                ADD COLUMN role VARCHAR DEFAULT 'user'
            """))
            
            # Update existing users to have 'user' role
            conn.execute(text("""
                UPDATE users 
                SET role = 'user' 
                WHERE role IS NULL
            """))
            
            conn.commit()
            print("✅ Role column added to users table successfully!")
            
        except Exception as e:
            print(f"❌ Error adding role column: {e}")
            conn.rollback()

def add_is_global_column():
    """Add is_global column to documents table"""
    with engine.connect() as conn:
        try:
            # Check if column exists
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='documents' AND column_name='is_global'
            """))
            
            if result.fetchone():
                print("✅ is_global column already exists in documents table")
                return
            
            # Add is_global column with default value false
            conn.execute(text("""
                ALTER TABLE documents 
                ADD COLUMN is_global BOOLEAN DEFAULT false
            """))
            
            # Set existing documents as not global (user-specific)
            conn.execute(text("""
                UPDATE documents 
                SET is_global = false 
                WHERE is_global IS NULL
            """))
            
            conn.commit()
            print("✅ is_global column added to documents table successfully!")
            
        except Exception as e:
            print(f"❌ Error adding is_global column: {e}")
            conn.rollback()

def show_current_users():
    """Display current users and their roles"""
    with engine.connect() as conn:
        try:
            result = conn.execute(text("""
                SELECT email, role, created_at 
                FROM users 
                ORDER BY created_at DESC
            """))
            
            users = result.fetchall()
            if users:
                print("\n📋 Current users in database:")
                print("-" * 50)
                for user in users:
                    role_display = user[1] if user[1] else 'user'
                    print(f"  Email: {user[0]}")
                    print(f"  Role: {role_display}")
                    print(f"  Created: {user[2]}")
                    print("-" * 50)
            else:
                print("\n📋 No users found in database")
                
        except Exception as e:
            print(f"❌ Error fetching users: {e}")

def upgrade_user_to_admin(email):
    """Upgrade an existing user to admin role"""
    with engine.connect() as conn:
        try:
            result = conn.execute(
                text("UPDATE users SET role = 'admin' WHERE email = :email"),
                {"email": email}
            )
            conn.commit()
            
            if result.rowcount > 0:
                print(f"✅ User {email} upgraded to admin!")
                return True
            else:
                print(f"❌ User {email} not found")
                return False
                
        except Exception as e:
            print(f"❌ Error upgrading user: {e}")
            conn.rollback()
            return False

if __name__ == "__main__":
    print("🔄 Starting database migration...")
    print("=" * 50)
    
    # Add missing columns
    add_role_column()
    add_is_global_column()
    
    # Show current users
    show_current_users()
    
    # Ask if user wants to upgrade someone to admin
    print("\n" + "=" * 50)
    upgrade = input("\n❓ Do you want to upgrade an existing user to admin? (y/n): ").lower()
    
    if upgrade == 'y':
        email = input("Enter the email of the user to upgrade: ")
        upgrade_user_to_admin(email)
        show_current_users()
    
    print("\n✅ Migration complete!")
    print("🚀 You can now restart the server and use the admin features")