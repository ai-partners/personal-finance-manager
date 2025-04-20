import os
from dotenv import load_dotenv
import logging
import pyodbc
from typing import Any, Callable, Set, Dict, List, Optional

# Load environment variables from .env file
load_dotenv()

# Database connection
def get_db_connection():
    conn_str = os.getenv("AZURE_SQL_CONNECTION_STRING")
    return pyodbc.connect(conn_str)

# Database interaction implementations
def get_user_accounts(user_id: int) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT Id, Name, Type FROM Accounts WHERE UserId = ?", user_id)
    accounts = [{"id": row[0], "name": row[1], "type": row[2]} for row in cursor.fetchall()]
    conn.close()
    return accounts

def get_transaction_categories(user_id, type=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if type:
        cursor.execute("SELECT Id, Name, Description FROM Categories WHERE UserId = ? AND Type = ?", 
                      (user_id, type))
    else:
        cursor.execute("SELECT Id, Name, Description FROM Categories WHERE UserId = ?", user_id)
        
    categories = [{"id": row[0], "name": row[1], "description": row[2]} for row in cursor.fetchall()]
    conn.close()
    return categories

# Statically defined user functions for fast reference
user_functions: Set[Callable[..., Any]] = {
    get_user_accounts,
    get_transaction_categories
}