#!/usr/bin/env python3
"""
Database setup script for Enomy-Finances application
This script creates the database and tables if they don't exist
"""

import mysql.connector
from mysql.connector import Error
from config import Config

def setup_database():
    """Create database and tables"""
    connection = None
    try:
        # Connect to MySQL server (without specifying database)
        connection = mysql.connector.connect(
            host=Config.DB_HOST,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD
        )
        
        cursor = connection.cursor()
        
        # Create database if it doesn't exist
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {Config.DB_NAME}")
        print(f"Database '{Config.DB_NAME}' created or already exists")
        
        # Use the database
        cursor.execute(f"USE {Config.DB_NAME}")
        
        # Read and execute the SQL setup file
        with open('database_setup.sql', 'r') as sql_file:
            sql_commands = sql_file.read()
            
        # Split commands by semicolon and execute each one
        commands = [cmd.strip() for cmd in sql_commands.split(';') if cmd.strip()]
        
        for command in commands:
            if command.upper().startswith(('CREATE', 'INSERT', 'USE')):
                try:
                    cursor.execute(command)
                    print(f"Executed: {command[:50]}...")
                except Error as e:
                    if "already exists" in str(e).lower():
                        print(f"Skipped (already exists): {command[:50]}...")
                    else:
                        print(f"Error executing command: {e}")
        
        connection.commit()
        print("Database setup completed successfully!")
        
    except Error as e:
        print(f"Error setting up database: {e}")
        return False
        
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()
            print("MySQL connection closed")
    
    return True

if __name__ == "__main__":
    print("Setting up Enomy-Finances database...")
    success = setup_database()
    if success:
        print("Database setup completed successfully!")
        print("You can now run the application with: python app.py")
    else:
        print("Database setup failed. Please check your MySQL configuration.")
