#!/usr/bin/env python3
"""
Fix admin credentials and create proper password hash
"""

import bcrypt
import mysql.connector
from config import Config

def generate_password_hash(password):
    """Generate bcrypt hash for password"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def fix_admin_credentials():
    """Fix admin credentials in database"""
    try:
        # Connect to database
        connection = mysql.connector.connect(
            host=Config.DB_HOST,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME
        )

        cursor = connection.cursor()

        # Generate correct password hash for "Admin@123"
        password_hash = generate_password_hash("Admin@123")
        print(f"Generated password hash: {password_hash}")

        # Check if admin user exists (check both old and new usernames)
        cursor.execute("SELECT id, username FROM users WHERE username IN ('admin', 'adminEco')")
        admin_user = cursor.fetchone()

        if admin_user:
            # Update existing admin user
            cursor.execute(
                "UPDATE users SET username = %s, password_hash = %s, email = %s WHERE username IN ('admin', 'adminEco')",
                ('adminEco', password_hash, 'admineco@enomy-finances.com')
            )
            print("Updated existing admin user credentials")
        else:
            # Create new admin user
            cursor.execute("""
                INSERT INTO users (username, email, password_hash, first_name, last_name, user_type, is_active)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                'adminEco',
                'admineco@enomy-finances.com',
                password_hash,
                'Admin',
                'User',
                'admin',
                True
            ))
            print("Created new admin user")

        connection.commit()

        # Verify the admin user
        cursor.execute("SELECT username, email, user_type FROM users WHERE username = 'adminEco'")
        admin_info = cursor.fetchone()
        print(f"Admin user verified: {admin_info}")

        cursor.close()
        connection.close()

        print("\n✅ Admin credentials fixed successfully!")
        print("Username: adminEco")
        print("Password: Admin@123")
        print("Email: admineco@enomy-finances.com")

        return True

    except Exception as e:
        print(f"Error fixing admin credentials: {e}")
        return False

if __name__ == "__main__":
    print("Fixing admin credentials...")
    success = fix_admin_credentials()
    if success:
        print("\nAdmin credentials are now working!")
    else:
        print("\nFailed to fix admin credentials.")
