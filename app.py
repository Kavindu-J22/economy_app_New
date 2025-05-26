from flask import Flask, render_template, request, jsonify, make_response, redirect, url_for
from flask_cors import CORS
import json
import traceback
from datetime import datetime

# Import our modules
from database import Database
from auth import AuthManager
from currency_api import CurrencyAPI
from calculations import CurrencyCalculator, InvestmentCalculator
from config import Config

app = Flask(__name__)
app.secret_key = Config.SECRET_KEY
CORS(app)

# Initialize components
db = Database()
auth_manager = AuthManager()
currency_api = CurrencyAPI()
currency_calc = CurrencyCalculator()
investment_calc = InvestmentCalculator()

# Error handler
@app.errorhandler(Exception)
def handle_error(error):
    error_message = str(error)
    stack_trace = traceback.format_exc()

    # Log error to database
    user_id = getattr(request, 'user', {}).get('id')

    # Safely get JSON data
    request_data = None
    try:
        if request.is_json:
            request_data = request.get_json()
    except:
        pass

    db.log_error("application_error", error_message, user_id, stack_trace, request_data)

    return jsonify({
        'error': 'An internal error occurred',
        'message': 'Please try again later'
    }), 500

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

@app.route('/favicon.ico')
def favicon():
    return '', 204  # No Content

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

        # Validate email
        if not auth_manager.validate_email(data['email']):
            return jsonify({'error': 'Invalid email format'}), 400

        # Validate password strength
        is_strong, message = auth_manager.validate_password_strength(data['password'])
        if not is_strong:
            return jsonify({'error': message}), 400

        # Register user
        result, message = auth_manager.register(
            data['username'],
            data['email'],
            data['password'],
            data['first_name'],
            data['last_name'],
            data.get('phone'),
            data.get('address')
        )

        if result:
            return jsonify({'message': message}), 201
        else:
            return jsonify({'error': message}), 400

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

        result, message = auth_manager.login(username, password)

        if result:
            response = make_response(jsonify({
                'message': message,
                'user': {
                    'id': result['user_id'],
                    'username': result['username'],
                    'user_type': result['user_type'],
                    'first_name': result['first_name'],
                    'last_name': result['last_name']
                }
            }))

            # Set session cookie
            response.set_cookie('session_token', result['session_token'],
                              httponly=True, secure=False, max_age=86400)  # 24 hours

            return response, 200
        else:
            return jsonify({'error': message}), 401

    except Exception as e:
        return jsonify({'error': 'Login failed'}), 500

@app.route('/api/logout', methods=['POST'])
def api_logout():
    try:
        session_token = request.cookies.get('session_token')
        if session_token:
            auth_manager.logout(session_token)

        response = make_response(jsonify({'message': 'Logout successful'}))
        response.set_cookie('session_token', '', expires=0)
        return response, 200

    except Exception as e:
        return jsonify({'error': 'Logout failed'}), 500

@app.route('/api/exchange-rates/<currency>')
def api_exchange_rates(currency):
    try:
        if currency not in Config.SUPPORTED_CURRENCIES:
            return jsonify({'error': 'Unsupported currency'}), 400

        rates = currency_api.get_all_rates_for_currency(currency)
        return jsonify({'base_currency': currency, 'rates': rates}), 200

    except Exception as e:
        return jsonify({'error': 'Failed to fetch exchange rates'}), 500

@app.route('/api/convert-currency', methods=['POST'])
@auth_manager.require_auth
def api_convert_currency():
    try:
        data = request.get_json()

        # Validate input
        required_fields = ['from_currency', 'to_currency', 'amount']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400

        from_currency = data['from_currency'].upper()
        to_currency = data['to_currency'].upper()
        amount = float(data['amount'])

        # Validate currencies
        if from_currency not in Config.SUPPORTED_CURRENCIES:
            return jsonify({'error': f'Unsupported currency: {from_currency}'}), 400
        if to_currency not in Config.SUPPORTED_CURRENCIES:
            return jsonify({'error': f'Unsupported currency: {to_currency}'}), 400

        # Get exchange rate
        exchange_rate = currency_api.get_exchange_rate(from_currency, to_currency)
        if not exchange_rate:
            return jsonify({'error': 'Unable to get exchange rate'}), 500

        # Calculate conversion
        result, message = currency_calc.calculate_conversion(amount, exchange_rate)

        if result:
            # Save transaction to database
            db.save_currency_transaction(
                request.user['id'],
                from_currency,
                to_currency,
                result['original_amount'],
                result['converted_amount'],
                result['exchange_rate'],
                result['fee_percentage'],
                result['fee_amount'],
                result['total_cost']
            )

            return jsonify({
                'conversion': result,
                'from_currency': from_currency,
                'to_currency': to_currency
            }), 200
        else:
            return jsonify({'error': message}), 400

    except ValueError:
        return jsonify({'error': 'Invalid amount'}), 400
    except Exception as e:
        return jsonify({'error': 'Conversion failed'}), 500

@app.route('/api/calculate-investment', methods=['POST'])
@auth_manager.require_auth
def api_calculate_investment():
    try:
        data = request.get_json()

        # Validate input
        required_fields = ['investment_type', 'initial_lump_sum', 'monthly_investment']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400

        investment_type = data['investment_type']
        initial_lump_sum = float(data['initial_lump_sum'])
        monthly_investment = float(data['monthly_investment'])

        # Calculate investment projections
        result, message = investment_calc.calculate_investment_projection(
            investment_type, initial_lump_sum, monthly_investment
        )

        if result:
            # Save quote to database
            try:
                db.save_investment_quote(
                    request.user['id'],
                    investment_type,
                    initial_lump_sum,
                    monthly_investment,
                    result['year_1']['min_value'],
                    result['year_1']['max_value'],
                    result['year_5']['min_value'],
                    result['year_5']['max_value'],
                    result['year_10']['min_value'],
                    result['year_10']['max_value'],
                    result['year_1']['total_fees'],
                    result['year_5']['total_fees'],
                    result['year_10']['total_fees'],
                    result['year_1']['min_tax'],
                    result['year_5']['min_tax'],
                    result['year_10']['min_tax']
                )
            except Exception as e:
                print(f"Failed to save investment quote: {e}")
                # Continue anyway - don't fail the calculation

            return jsonify({
                'projections': result,
                'investment_type': investment_type,
                'plan_details': Config.INVESTMENT_TYPES[investment_type]
            }), 200
        else:
            return jsonify({'error': message}), 400

    except ValueError:
        return jsonify({'error': 'Invalid investment amounts'}), 400
    except Exception as e:
        return jsonify({'error': 'Investment calculation failed'}), 500

@app.route('/api/user/transactions')
@auth_manager.require_auth
def api_user_transactions():
    try:
        transactions = db.get_user_transactions(request.user['id'])
        return jsonify({'transactions': transactions}), 200
    except Exception as e:
        return jsonify({'error': 'Failed to fetch transactions'}), 500

@app.route('/api/user/quotes')
@auth_manager.require_auth
def api_user_quotes():
    try:
        quotes = db.get_user_quotes(request.user['id'])
        return jsonify({'quotes': quotes}), 200
    except Exception as e:
        return jsonify({'error': 'Failed to fetch quotes'}), 500

@app.route('/api/investment-types')
def api_investment_types():
    try:
        return jsonify({'investment_types': Config.INVESTMENT_TYPES}), 200
    except Exception as e:
        return jsonify({'error': 'Failed to fetch investment types'}), 500

@app.route('/api/supported-currencies')
def api_supported_currencies():
    try:
        return jsonify({'currencies': Config.SUPPORTED_CURRENCIES}), 200
    except Exception as e:
        return jsonify({'error': 'Failed to fetch supported currencies'}), 500

@app.route('/api/admin/export-data')
@auth_manager.require_auth
def api_admin_export_data():
    try:
        # Check admin privileges
        if request.user['user_type'] != 'admin':
            return jsonify({'error': 'Admin privileges required'}), 403

        # Generate PDF report
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib import colors
        from io import BytesIO
        import base64
        from datetime import datetime

        # Create PDF buffer
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)

        # Container for the 'Flowable' objects
        elements = []

        # Define styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            textColor=colors.HexColor('#2c3e50'),
            alignment=1  # Center alignment
        )

        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            spaceAfter=12,
            textColor=colors.HexColor('#34495e')
        )

        # Title
        title = Paragraph("Enomy-Finances System Report", title_style)
        elements.append(title)
        elements.append(Spacer(1, 12))

        # Report metadata
        report_info = Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal'])
        elements.append(report_info)
        elements.append(Spacer(1, 20))

        # System Statistics
        elements.append(Paragraph("System Statistics", heading_style))

        # Get real statistics from database
        total_users = len(db.execute_query("SELECT id FROM users WHERE is_active = TRUE") or [])
        total_transactions = len(db.execute_query("SELECT id FROM transactions") or [])
        total_quotes = len(db.execute_query("SELECT id FROM investment_quotes") or [])
        total_errors = len(db.execute_query("SELECT id FROM error_logs WHERE created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)") or [])

        stats_data = [
            ['Metric', 'Value'],
            ['Total Active Users', str(total_users)],
            ['Total Transactions', str(total_transactions)],
            ['Investment Quotes', str(total_quotes)],
            ['Recent Errors (7 days)', str(total_errors)],
        ]

        stats_table = Table(stats_data, colWidths=[3*inch, 2*inch])
        stats_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))

        elements.append(stats_table)
        elements.append(Spacer(1, 20))

        # Recent Transactions
        elements.append(Paragraph("Recent Transactions", heading_style))

        transactions = db.execute_query("""
            SELECT t.*, u.username
            FROM transactions t
            JOIN users u ON t.user_id = u.id
            ORDER BY t.transaction_date DESC
            LIMIT 10
        """) or []

        if transactions:
            trans_data = [['User', 'From', 'To', 'Amount', 'Fee', 'Date']]
            for t in transactions:
                trans_data.append([
                    t['username'],
                    t['from_currency'],
                    t['to_currency'],
                    f"£{t['amount_from']:.2f}",
                    f"£{t['fee_amount']:.2f}",
                    t['transaction_date'].strftime('%Y-%m-%d')
                ])

            trans_table = Table(trans_data, colWidths=[1.2*inch, 0.8*inch, 0.8*inch, 1*inch, 0.8*inch, 1.4*inch])
            trans_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#27ae60')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(trans_table)
        else:
            elements.append(Paragraph("No transactions found", styles['Normal']))

        elements.append(Spacer(1, 20))

        # Investment Quotes Summary
        elements.append(Paragraph("Investment Quotes Summary", heading_style))

        quotes = db.execute_query("""
            SELECT iq.*, u.username
            FROM investment_quotes iq
            JOIN users u ON iq.user_id = u.id
            ORDER BY iq.created_at DESC
            LIMIT 10
        """) or []

        if quotes:
            quotes_data = [['User', 'Plan', 'Initial', 'Monthly', '10Y Max', 'Date']]
            for q in quotes:
                quotes_data.append([
                    q['username'],
                    q['investment_type'].title(),
                    f"£{q['initial_lump_sum']:.0f}",
                    f"£{q['monthly_investment']:.0f}",
                    f"£{q['year_10_max']:.0f}",
                    q['created_at'].strftime('%Y-%m-%d')
                ])

            quotes_table = Table(quotes_data, colWidths=[1.2*inch, 1*inch, 0.8*inch, 0.8*inch, 1*inch, 1.2*inch])
            quotes_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e74c3c')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightcyan),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(quotes_table)
        else:
            elements.append(Paragraph("No investment quotes found", styles['Normal']))

        # Build PDF
        doc.build(elements)

        # Get PDF data
        pdf_data = buffer.getvalue()
        buffer.close()

        # Return PDF as base64 for download
        pdf_base64 = base64.b64encode(pdf_data).decode('utf-8')

        return jsonify({
            'pdf_data': pdf_base64,
            'filename': f'enomy_finances_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
        }), 200

    except Exception as e:
        print(f"Export error: {e}")
        return jsonify({'error': 'Failed to generate report'}), 500

@app.route('/api/admin/stats')
@auth_manager.require_auth
def api_admin_stats():
    try:
        # Check admin privileges
        if request.user['user_type'] != 'admin':
            return jsonify({'error': 'Admin privileges required'}), 403

        # Get real statistics
        total_users = len(db.execute_query("SELECT id FROM users WHERE is_active = TRUE") or [])
        total_transactions = len(db.execute_query("SELECT id FROM transactions") or [])
        total_quotes = len(db.execute_query("SELECT id FROM investment_quotes") or [])
        total_errors = len(db.execute_query("SELECT id FROM error_logs WHERE created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)") or [])

        # Calculate revenue from fees
        fee_result = db.execute_query("SELECT SUM(fee_amount) as total_fees FROM transactions") or [{'total_fees': 0}]
        total_revenue = fee_result[0]['total_fees'] or 0

        return jsonify({
            'totalUsers': total_users,
            'totalTransactions': total_transactions,
            'totalQuotes': total_quotes,
            'totalErrors': total_errors,
            'totalRevenue': float(total_revenue)
        }), 200

    except Exception as e:
        print(f"Stats error: {e}")
        return jsonify({'error': 'Failed to fetch statistics'}), 500

@app.route('/api/admin/transactions')
@auth_manager.require_auth
def api_admin_transactions():
    try:
        # Check admin privileges
        if request.user['user_type'] != 'admin':
            return jsonify({'error': 'Admin privileges required'}), 403

        transactions = db.execute_query("""
            SELECT t.*, u.username
            FROM transactions t
            JOIN users u ON t.user_id = u.id
            ORDER BY t.transaction_date DESC
            LIMIT 50
        """) or []

        return jsonify({'transactions': transactions}), 200

    except Exception as e:
        print(f"Admin transactions error: {e}")
        return jsonify({'error': 'Failed to fetch transactions'}), 500

@app.route('/api/user/profile')
@auth_manager.require_auth
def api_user_profile():
    try:
        user = db.get_user_by_id(request.user['id'])
        if user:
            # Remove sensitive information
            user.pop('password_hash', None)
            return jsonify({'user': user}), 200
        else:
            return jsonify({'error': 'User not found'}), 404
    except Exception as e:
        return jsonify({'error': 'Failed to fetch user profile'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
