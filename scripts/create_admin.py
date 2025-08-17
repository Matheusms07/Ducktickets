#!/usr/bin/env python3
"""
Create admin users script
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.database import SessionLocal, engine, Base
from app.models import User
from app.auth import auth_manager

def create_admin_user(email: str, password: str, full_name: str):
    """Create admin user"""
    
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            print(f"❌ User {email} already exists")
            return False
        
        # Hash password
        password_hash = auth_manager.get_password_hash(password)
        
        # Create admin user
        admin_user = User(
            email=email,
            password_hash=password_hash,
            full_name=full_name,
            is_admin=True
        )
        
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        print(f"✅ Admin user created successfully:")
        print(f"   Email: {email}")
        print(f"   Name: {full_name}")
        print(f"   ID: {admin_user.id}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def main():
    """Main function"""
    print("🦆 DuckTickets - Admin User Creation")
    print("=" * 40)
    
    # Create super admin
    success = create_admin_user(
        email="super_admin@ducktickets.com",
        password="12qwaszx",
        full_name="Super Administrator"
    )
    
    if success:
        print("\n🎉 Super admin created successfully!")
        print("\n📋 Login credentials:")
        print("   Email: super_admin@ducktickets.com")
        print("   Password: 12qwaszx")
        print("\n⚠️  IMPORTANT: Change this password in production!")
    else:
        print("\n❌ Failed to create super admin")
        sys.exit(1)

if __name__ == "__main__":
    main()