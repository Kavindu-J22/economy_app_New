import mysql.connector
from mysql.connector import Error
import json
from datetime import datetime
from config import Config

class Database:
    def __init__(self):
        self.connection = None
        self.config = {
            'host': Config.DB_HOST,
            'user': Config.DB_USER,
            'password': Config.DB_PASSWORD,
            'database': Config.DB_NAME,
            'autocommit': True
        }
        self.connect()

    def connect(self):
        try:
            self.connection = mysql.connector.connect(
                host=Config.DB_HOST,
                user=Config.DB_USER,
                password=Config.DB_PASSWORD,
                database=Config.DB_NAME,
                autocommit=True
            )
            print("Successfully connected to MySQL database")
        except Error as e:
            print(f"Error connecting to MySQL: {e}")
            self.connection = None

    def execute_query(self, query, params=None):
        max_retries = 3
        retry_count = 0

        while retry_count < max_retries:
            try:
                # Always create a fresh connection for each query to avoid sync issues
                connection = mysql.connector.connect(**self.config)
                cursor = connection.cursor(dictionary=True, buffered=True)

                cursor.execute(query, params)

                if query.strip().upper().startswith('SELECT'):
                    result = cursor.fetchall()
                else:
                    result = cursor.rowcount
                    connection.commit()

                cursor.close()
                connection.close()
                return result

            except Error as e:
                retry_count += 1
                print(f"Database error (attempt {retry_count}/{max_retries}): {e}")

                if retry_count >= max_retries:
                    print(f"Database error after {max_retries} attempts: {e}")
                    return None

                # Wait before retry
                import time
                time.sleep(0.5 * retry_count)

        return None

    def get_user_by_username(self, username):
        query = "SELECT * FROM users WHERE username = %s AND is_active = TRUE"
        result = self.execute_query(query, (username,))
        return result[0] if result else None

    def get_user_by_id(self, user_id):
        query = "SELECT * FROM users WHERE id = %s AND is_active = TRUE"
        result = self.execute_query(query, (user_id,))
        return result[0] if result else None

    def create_user(self, username, email, password_hash, first_name, last_name, phone=None, address=None):
        query = """
        INSERT INTO users (username, email, password_hash, first_name, last_name, phone, address)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        return self.execute_query(query, (username, email, password_hash, first_name, last_name, phone, address))

    def save_currency_transaction(self, user_id, from_currency, to_currency, amount_from,
                                amount_to, exchange_rate, fee_percentage, fee_amount, total_cost):
        query = """
        INSERT INTO transactions
        (user_id, from_currency, to_currency, amount_from, amount_to, exchange_rate,
         fee_percentage, fee_amount, total_cost, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'completed')
        """
        return self.execute_query(query, (user_id, from_currency, to_currency, amount_from,
                                        amount_to, exchange_rate, fee_percentage, fee_amount, total_cost))

    def save_investment_quote(self, user_id, investment_type, initial_lump_sum, monthly_investment,
                            year_1_min, year_1_max, year_5_min, year_5_max, year_10_min, year_10_max,
                            total_fees_1y, total_fees_5y, total_fees_10y, total_tax_1y, total_tax_5y, total_tax_10y):
        query = """
        INSERT INTO investment_quotes
        (user_id, investment_type, initial_lump_sum, monthly_investment,
         year_1_min, year_1_max, year_5_min, year_5_max, year_10_min, year_10_max,
         total_fees_1y, total_fees_5y, total_fees_10y, total_tax_1y, total_tax_5y, total_tax_10y)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        return self.execute_query(query, (user_id, investment_type, initial_lump_sum, monthly_investment,
                                        year_1_min, year_1_max, year_5_min, year_5_max, year_10_min, year_10_max,
                                        total_fees_1y, total_fees_5y, total_fees_10y, total_tax_1y, total_tax_5y, total_tax_10y))

    def get_exchange_rate(self, from_currency, to_currency):
        query = "SELECT rate FROM exchange_rates WHERE base_currency = %s AND target_currency = %s"
        result = self.execute_query(query, (from_currency, to_currency))
        return result[0]['rate'] if result else None

    def update_exchange_rate(self, from_currency, to_currency, rate):
        query = """
        INSERT INTO exchange_rates (base_currency, target_currency, rate)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE rate = %s, last_updated = CURRENT_TIMESTAMP
        """
        return self.execute_query(query, (from_currency, to_currency, rate, rate))

    def get_user_transactions(self, user_id, limit=50):
        query = """
        SELECT * FROM transactions
        WHERE user_id = %s
        ORDER BY transaction_date DESC
        LIMIT %s
        """
        return self.execute_query(query, (user_id, limit)) or []

    def get_user_quotes(self, user_id, limit=20):
        query = """
        SELECT * FROM investment_quotes
        WHERE user_id = %s
        ORDER BY created_at DESC
        LIMIT %s
        """
        return self.execute_query(query, (user_id, limit)) or []

    def log_error(self, error_type, error_message, user_id=None, stack_trace=None, request_data=None):
        query = """
        INSERT INTO error_logs (user_id, error_type, error_message, stack_trace, request_data)
        VALUES (%s, %s, %s, %s, %s)
        """
        request_json = json.dumps(request_data) if request_data else None
        return self.execute_query(query, (user_id, error_type, error_message, stack_trace, request_json))

    def create_session(self, user_id, session_token, expires_at):
        query = """
        INSERT INTO user_sessions (user_id, session_token, expires_at)
        VALUES (%s, %s, %s)
        """
        return self.execute_query(query, (user_id, session_token, expires_at))

    def get_session(self, session_token):
        query = """
        SELECT s.*, u.username, u.user_type
        FROM user_sessions s
        JOIN users u ON s.user_id = u.id
        WHERE s.session_token = %s AND s.expires_at > NOW()
        """
        result = self.execute_query(query, (session_token,))
        return result[0] if result else None

    def delete_session(self, session_token):
        query = "DELETE FROM user_sessions WHERE session_token = %s"
        return self.execute_query(query, (session_token,))

    def close(self):
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("MySQL connection closed")
