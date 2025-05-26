#!/usr/bin/env python3
"""
Demo version of Enomy-Finances application
This version uses in-memory storage instead of MySQL for demonstration purposes
"""

from flask import Flask, render_template, request, jsonify, make_response
from flask_cors import CORS
import json
import traceback
from datetime import datetime, timedelta
import bcrypt
import secrets
import requests

app = Flask(__name__)
app.secret_key = 'demo-secret-key-change-in-production'
CORS(app)

# In-memory storage for demo
demo_data = {
    'users': [],
    'sessions': {},
    'transactions': [],
    'quotes': [],
    'errors': []
}

# Demo configuration
DEMO_CONFIG = {
    'SUPPORTED_CURRENCIES': ['GBP', 'USD', 'EUR', 'BRL', 'JPY', 'TRY'],
    'INVESTMENT_TYPES': {
        'basic': {
            'name': 'Basic Savings Plan',
            'return_min': 0.012,
            'return_max': 0.024,
            'max_yearly': 20000,
            'min_monthly': 50,
            'min_lump_sum': 0,
            'monthly_fee': 0.0025,
            'tax_rate': 0,
            'tax_threshold': 0
        },
        'plus': {
            'name': 'Savings Plan Plus',
            'return_min': 0.03,
            'return_max': 0.055,
            'max_yearly': 30000,
            'min_monthly': 50,
            'min_lump_sum': 300,
            'monthly_fee': 0.003,
            'tax_rate': 0.1,
            'tax_threshold': 12000
        },
        'managed': {
            'name': 'Managed Stock Investments',
            'return_min': 0.04,
            'return_max': 0.23,
            'max_yearly': float('inf'),
            'min_monthly': 150,
            'min_lump_sum': 1000,
            'monthly_fee': 0.013,
            'tax_rates': [0.1, 0.2],
            'tax_thresholds': [12000, 50000]
        }
    }
}

# Demo exchange rates (normally would come from external API)
DEMO_EXCHANGE_RATES = {
    'GBP': {'USD': 1.27, 'EUR': 1.17, 'BRL': 6.35, 'JPY': 188.5, 'TRY': 43.2},
    'USD': {'GBP': 0.79, 'EUR': 0.92, 'BRL': 5.01, 'JPY': 148.3, 'TRY': 34.1},
    'EUR': {'GBP': 0.85, 'USD': 1.09, 'BRL': 5.43, 'JPY': 161.2, 'TRY': 37.0},
    'BRL': {'GBP': 0.16, 'USD': 0.20, 'EUR': 0.18, 'JPY': 29.7, 'TRY': 6.8},
    'JPY': {'GBP': 0.0053, 'USD': 0.0067, 'EUR': 0.0062, 'BRL': 0.034, 'TRY': 0.23},
    'TRY': {'GBP': 0.023, 'USD': 0.029, 'EUR': 0.027, 'BRL': 0.15, 'JPY': 4.36}
}

# Helper functions
def hash_password(password):
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(password, hashed_password):
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

def generate_session_token():
    return secrets.token_urlsafe(32)

def validate_email(email):
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password_strength(password):
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"
    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one number"
    return True, "Password is strong"

def calculate_currency_fee(amount):
    """Calculate fee based on amount"""
    if amount <= 500:
        return 0.035  # 3.5%
    elif amount <= 1500:
        return 0.027  # 2.7%
    elif amount <= 2500:
        return 0.020  # 2.0%
    else:
        return 0.015  # 1.5%

def require_auth(f):
    """Decorator to require authentication"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        session_token = request.headers.get('Authorization')
        if not session_token:
            session_token = request.cookies.get('session_token')

        if not session_token:
            return jsonify({'error': 'Authentication required'}), 401

        if session_token.startswith('Bearer '):
            session_token = session_token[7:]

        session_data = demo_data['sessions'].get(session_token)
        if not session_data or session_data['expires_at'] < datetime.now():
            return jsonify({'error': 'Invalid or expired session'}), 401

        # Add user info to request context
        request.user = session_data['user']
        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/currency-converter')
def currency_converter():
    return render_template('currency-converter.html')

@app.route('/investment-calculator')
def investment_calculator():
    return render_template('investment-calculator.html')

@app.route('/dashboard')
def dashboard():
    return render_template('user-dashboard.html')

@app.route('/admin')
def admin_dashboard():
    return render_template('admin-dashboard.html')

# API Routes
@app.route('/api/register', methods=['POST'])
def api_register():
    try:
        data = request.get_json()

        # Validate required fields
        required_fields = ['username', 'email', 'password', 'first_name', 'last_name']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400

        # Check if username already exists
        if any(user['username'] == data['username'] for user in demo_data['users']):
            return jsonify({'error': 'Username already exists'}), 400

        # Validate email
        if not validate_email(data['email']):
            return jsonify({'error': 'Invalid email format'}), 400

        # Validate password strength
        is_strong, message = validate_password_strength(data['password'])
        if not is_strong:
            return jsonify({'error': message}), 400

        # Create user
        user = {
            'id': len(demo_data['users']) + 1,
            'username': data['username'],
            'email': data['email'],
            'password_hash': hash_password(data['password']),
            'first_name': data['first_name'],
            'last_name': data['last_name'],
            'phone': data.get('phone'),
            'address': data.get('address'),
            'user_type': 'admin' if data['username'] == 'admin' else 'client',
            'created_at': datetime.now().isoformat()
        }

        demo_data['users'].append(user)
        return jsonify({'message': 'Registration successful'}), 201

    except Exception as e:
        return jsonify({'error': 'Registration failed'}), 500

@app.route('/api/login', methods=['POST'])
def api_login():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return jsonify({'error': 'Username and password are required'}), 400

        # Find user
        user = next((u for u in demo_data['users'] if u['username'] == username), None)

        # Auto-create admin user if username is 'admin' and user doesn't exist
        if not user and username == 'admin':
            user = {
                'id': len(demo_data['users']) + 1,
                'username': 'admin',
                'email': 'admin@enomy-finances.com',
                'password_hash': hash_password(password),  # Use the provided password
                'first_name': 'Admin',
                'last_name': 'User',
                'phone': None,
                'address': None,
                'user_type': 'admin',
                'created_at': datetime.now().isoformat()
            }
            demo_data['users'].append(user)
            print(f"Auto-created admin user with password: {password}")

        if not user or not verify_password(password, user['password_hash']):
            return jsonify({'error': 'Invalid username or password'}), 401

        # Create session
        session_token = generate_session_token()
        demo_data['sessions'][session_token] = {
            'user': {
                'id': user['id'],
                'username': user['username'],
                'user_type': user['user_type'],
                'first_name': user['first_name'],
                'last_name': user['last_name']
            },
            'expires_at': datetime.now() + timedelta(hours=24)
        }

        response = make_response(jsonify({
            'message': 'Login successful',
            'user': demo_data['sessions'][session_token]['user']
        }))

        response.set_cookie('session_token', session_token,
                          httponly=True, secure=False, max_age=86400)

        return response, 200

    except Exception as e:
        return jsonify({'error': 'Login failed'}), 500

@app.route('/api/logout', methods=['POST'])
def api_logout():
    try:
        session_token = request.cookies.get('session_token')
        if session_token and session_token in demo_data['sessions']:
            del demo_data['sessions'][session_token]

        response = make_response(jsonify({'message': 'Logout successful'}))
        response.set_cookie('session_token', '', expires=0)
        return response, 200

    except Exception as e:
        return jsonify({'error': 'Logout failed'}), 500

@app.route('/api/exchange-rates/<currency>')
def api_exchange_rates(currency):
    try:
        if currency not in DEMO_CONFIG['SUPPORTED_CURRENCIES']:
            return jsonify({'error': 'Unsupported currency'}), 400

        rates = DEMO_EXCHANGE_RATES.get(currency, {})
        return jsonify({'base_currency': currency, 'rates': rates}), 200

    except Exception as e:
        return jsonify({'error': 'Failed to fetch exchange rates'}), 500

@app.route('/api/convert-currency', methods=['POST'])
@require_auth
def api_convert_currency():
    try:
        data = request.get_json()

        from_currency = data['from_currency'].upper()
        to_currency = data['to_currency'].upper()
        amount = float(data['amount'])

        if from_currency not in DEMO_CONFIG['SUPPORTED_CURRENCIES']:
            return jsonify({'error': f'Unsupported currency: {from_currency}'}), 400
        if to_currency not in DEMO_CONFIG['SUPPORTED_CURRENCIES']:
            return jsonify({'error': f'Unsupported currency: {to_currency}'}), 400

        if amount < 300 or amount > 5000:
            return jsonify({'error': 'Amount must be between 300 and 5,000'}), 400

        # Get exchange rate
        exchange_rate = DEMO_EXCHANGE_RATES[from_currency].get(to_currency, 1.0)

        # Calculate fee
        fee_percentage = calculate_currency_fee(amount)
        fee_amount = amount * fee_percentage
        amount_after_fee = amount - fee_amount
        converted_amount = amount_after_fee * exchange_rate

        result = {
            'original_amount': amount,
            'converted_amount': converted_amount,
            'exchange_rate': exchange_rate,
            'fee_percentage': fee_percentage * 100,
            'fee_amount': fee_amount,
            'amount_after_fee': amount_after_fee,
            'total_cost': amount
        }

        # Save transaction
        transaction = {
            'id': len(demo_data['transactions']) + 1,
            'user_id': request.user['id'],
            'from_currency': from_currency,
            'to_currency': to_currency,
            'amount_from': amount,
            'amount_to': converted_amount,
            'exchange_rate': exchange_rate,
            'fee_percentage': fee_percentage * 100,
            'fee_amount': fee_amount,
            'transaction_date': datetime.now().isoformat()
        }
        demo_data['transactions'].append(transaction)

        return jsonify({
            'conversion': result,
            'from_currency': from_currency,
            'to_currency': to_currency
        }), 200

    except Exception as e:
        return jsonify({'error': 'Conversion failed'}), 500

@app.route('/api/investment-types')
def api_investment_types():
    return jsonify({'investment_types': DEMO_CONFIG['INVESTMENT_TYPES']}), 200

@app.route('/api/supported-currencies')
def api_supported_currencies():
    return jsonify({'currencies': DEMO_CONFIG['SUPPORTED_CURRENCIES']}), 200

@app.route('/api/user/profile')
@require_auth
def api_user_profile():
    try:
        user = next((u for u in demo_data['users'] if u['id'] == request.user['id']), None)
        if user:
            user_copy = user.copy()
            user_copy.pop('password_hash', None)
            return jsonify({'user': user_copy}), 200
        else:
            return jsonify({'error': 'User not found'}), 404
    except Exception as e:
        return jsonify({'error': 'Failed to fetch user profile'}), 500

@app.route('/api/user/transactions')
@require_auth
def api_user_transactions():
    try:
        user_transactions = [t for t in demo_data['transactions'] if t['user_id'] == request.user['id']]
        return jsonify({'transactions': user_transactions}), 200
    except Exception as e:
        return jsonify({'error': 'Failed to fetch transactions'}), 500

@app.route('/api/user/quotes')
@require_auth
def api_user_quotes():
    try:
        user_quotes = [q for q in demo_data['quotes'] if q['user_id'] == request.user['id']]
        return jsonify({'quotes': user_quotes}), 200
    except Exception as e:
        return jsonify({'error': 'Failed to fetch quotes'}), 500

@app.route('/api/calculate-investment', methods=['POST'])
@require_auth
def api_calculate_investment():
    try:
        data = request.get_json()

        investment_type = data['investment_type']
        initial_lump_sum = float(data['initial_lump_sum'])
        monthly_investment = float(data['monthly_investment'])

        plan = DEMO_CONFIG['INVESTMENT_TYPES'][investment_type]

        # Basic validation
        if initial_lump_sum < plan['min_lump_sum']:
            return jsonify({'error': f'Minimum initial investment is £{plan["min_lump_sum"]}'}), 400
        if monthly_investment > 0 and monthly_investment < plan['min_monthly']:
            return jsonify({'error': f'Minimum monthly investment is £{plan["min_monthly"]}'}), 400

        # Simple calculation for demo
        projections = {}
        for years in [1, 5, 10]:
            total_invested = initial_lump_sum + (monthly_investment * 12 * years)
            min_value = total_invested * (1 + plan['return_min']) ** years
            max_value = total_invested * (1 + plan['return_max']) ** years
            fees = total_invested * plan['monthly_fee'] * 12 * years

            projections[f'year_{years}'] = {
                'min_value': min_value,
                'max_value': max_value,
                'min_profit': max(0, min_value - total_invested),
                'max_profit': max(0, max_value - total_invested),
                'total_fees': fees,
                'min_tax': 0,
                'max_tax': 0,
                'total_invested': total_invested
            }

        # Save quote
        quote = {
            'id': len(demo_data['quotes']) + 1,
            'user_id': request.user['id'],
            'investment_type': investment_type,
            'initial_lump_sum': initial_lump_sum,
            'monthly_investment': monthly_investment,
            'year_1_min': projections['year_1']['min_value'],
            'year_1_max': projections['year_1']['max_value'],
            'year_5_min': projections['year_5']['min_value'],
            'year_5_max': projections['year_5']['max_value'],
            'year_10_min': projections['year_10']['min_value'],
            'year_10_max': projections['year_10']['max_value'],
            'total_fees_1y': projections['year_1']['total_fees'],
            'total_fees_5y': projections['year_5']['total_fees'],
            'total_fees_10y': projections['year_10']['total_fees'],
            'total_tax_1y': 0,
            'total_tax_5y': 0,
            'total_tax_10y': 0,
            'created_at': datetime.now().isoformat()
        }
        demo_data['quotes'].append(quote)

        return jsonify({
            'projections': projections,
            'investment_type': investment_type,
            'plan_details': plan
        }), 200

    except Exception as e:
        return jsonify({'error': 'Investment calculation failed'}), 500

if __name__ == '__main__':
    print("Starting Enomy-Finances Demo Application...")
    print("This is a demonstration version using in-memory storage.")
    print("Visit http://localhost:5000 to access the application.")
    print("\nDemo credentials:")
    print("- Register a new account or")
    print("- Use username 'admin' with any password (will be created as admin)")
    print("\nPress Ctrl+C to stop the server.")

    app.run(debug=True, host='0.0.0.0', port=5000)
