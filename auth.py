import bcrypt
import jwt
import secrets
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, session
from database import Database
from config import Config

class AuthManager:
    def __init__(self):
        self.db = Database()
        self.secret_key = Config.SECRET_KEY

    def hash_password(self, password):
        """Hash a password using bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    def verify_password(self, password, hashed_password):
        """Verify a password against its hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

    def generate_session_token(self):
        """Generate a secure session token"""
        return secrets.token_urlsafe(32)

    def create_session(self, user_id):
        """Create a new user session"""
        session_token = self.generate_session_token()
        expires_at = datetime.now() + timedelta(hours=24)  # 24 hour session

        self.db.create_session(user_id, session_token, expires_at)
        return session_token

    def validate_session(self, session_token):
        """Validate a session token"""
        return self.db.get_session(session_token)

    def login(self, username, password):
        """Authenticate user and create session"""
        try:
            print(f"Login attempt for username: {username}")
            user = self.db.get_user_by_username(username)
            if not user:
                print(f"User not found: {username}")
                return None, "Invalid username or password"

            print(f"User found: {user['username']}, type: {user['user_type']}, active: {user['is_active']}")

            if not self.verify_password(password, user['password_hash']):
                print(f"Password verification failed for user: {username}")
                return None, "Invalid username or password"

            print(f"Password verified successfully for user: {username}")

            # Create session
            session_token = self.create_session(user['id'])

            return {
                'user_id': user['id'],
                'username': user['username'],
                'user_type': user['user_type'],
                'session_token': session_token,
                'first_name': user['first_name'],
                'last_name': user['last_name']
            }, "Login successful"

        except Exception as e:
            print(f"Login error: {e}")
            self.db.log_error("login_error", str(e))
            return None, "Login failed due to system error"

    def register(self, username, email, password, first_name, last_name, phone=None, address=None):
        """Register a new user"""
        try:
            # Check if username already exists
            existing_user = self.db.get_user_by_username(username)
            if existing_user:
                return None, "Username already exists"

            # Hash password
            password_hash = self.hash_password(password)

            # Create user
            result = self.db.create_user(username, email, password_hash, first_name, last_name, phone, address)

            if result:
                return {"message": "User registered successfully"}, "Registration successful"
            else:
                return None, "Registration failed"

        except Exception as e:
            self.db.log_error("registration_error", str(e))
            return None, "Registration failed due to system error"

    def logout(self, session_token):
        """Logout user by deleting session"""
        try:
            self.db.delete_session(session_token)
            return True, "Logout successful"
        except Exception as e:
            self.db.log_error("logout_error", str(e))
            return False, "Logout failed"

    def require_auth(self, f):
        """Decorator to require authentication"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            session_token = request.headers.get('Authorization')
            if not session_token:
                session_token = request.cookies.get('session_token')

            if not session_token:
                return jsonify({'error': 'Authentication required'}), 401

            # Remove 'Bearer ' prefix if present
            if session_token.startswith('Bearer '):
                session_token = session_token[7:]

            session_data = self.validate_session(session_token)
            if not session_data:
                return jsonify({'error': 'Invalid or expired session'}), 401

            # Add user info to request context
            request.user = {
                'id': session_data['user_id'],
                'username': session_data['username'],
                'user_type': session_data['user_type']
            }

            return f(*args, **kwargs)
        return decorated_function

    def require_admin(self, f):
        """Decorator to require admin privileges"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not hasattr(request, 'user') or request.user['user_type'] != 'admin':
                return jsonify({'error': 'Admin privileges required'}), 403
            return f(*args, **kwargs)
        return decorated_function

    def validate_password_strength(self, password):
        """Validate password strength"""
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"

        if not any(c.isupper() for c in password):
            return False, "Password must contain at least one uppercase letter"

        if not any(c.islower() for c in password):
            return False, "Password must contain at least one lowercase letter"

        if not any(c.isdigit() for c in password):
            return False, "Password must contain at least one number"

        return True, "Password is strong"

    def validate_email(self, email):
        """Basic email validation"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
