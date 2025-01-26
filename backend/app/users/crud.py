from ..database import get_db_connection
import bcrypt
from psycopg2 import DatabaseError, IntegrityError

def hash_password(password: str):
    '''Hash a password for storing.'''
    if not password:
        raise ValueError("Password cannot be empty.")
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(password: str, hashed_password: str):
    '''Check a stored password against one provided by user.'''
    if not password or not hashed_password:
        raise ValueError("Password and hashed password must be provided.")
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

def create_user(data: dict):
    query = """
    INSERT INTO Users (FirstName, LastName, Username, Password, Email, Role)
    VALUES (%s, %s, %s, %s, %s, %s)
    RETURNING UserID;
    """
    if not all(key in data for key in ("firstname", "lastname", "username", "password", "email", "role")):
        raise ValueError("Missing required user fields.")
    
    data["password"] = hash_password(data["password"])
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (data["firstname"], data["lastname"], data["username"], data["password"], data["email"], data["role"]))
                user_id = cursor.fetchone()[0]
                conn.commit()
        return user_id
    except IntegrityError:
        raise ValueError("Username or email already exists.")
    except DatabaseError as e:
        raise RuntimeError(f"Database error: {e}")

def get_user_by_id(user_id: int):
    if not user_id:
        raise ValueError("User ID must be provided.")
    query = """
    SELECT * FROM Users WHERE UserID = %s;
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (user_id,))
                user = cursor.fetchone()
                if not user:
                    raise ValueError(f"User with ID {user_id} not found.")
        return user
    except DatabaseError as e:
        raise RuntimeError(f"Database error: {e}")

def get_all_users():
    query = """
    SELECT * FROM Users;
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                users = cursor.fetchall()
        return users
    except DatabaseError as e:
        raise RuntimeError(f"Database error: {e}")

def update_user(user_id: int, data: dict):
    if not user_id or not data:
        raise ValueError("User ID and update data must be provided.")
    
    query = """
    UPDATE Users
    SET FirstName = %s, LastName = %s, Username = %s, Password = %s, Email = %s, Role = %s
    WHERE UserID = %s;
    """
    if "password" in data:
        data["password"] = hash_password(data["password"])
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (data["firstname"], data["lastname"], data["username"], data["password"], data["email"], data["role"], user_id))
                if cursor.rowcount == 0:
                    raise ValueError(f"User with ID {user_id} not found.")
                conn.commit()
    except DatabaseError as e:
        raise RuntimeError(f"Database error: {e}")

def delete_user(user_id: int):
    if not user_id:
        raise ValueError("User ID must be provided.")
    query = """
    DELETE FROM Users WHERE UserID = %s;
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (user_id,))
                if cursor.rowcount == 0:
                    raise ValueError(f"User with ID {user_id} not found.")
                conn.commit()
    except DatabaseError as e:
        raise RuntimeError(f"Database error: {e}")

def get_user_by_username_or_email(username: str, email: str):
    if not username and not email:
        raise ValueError("Username or email must be provided.")
    query = """
    SELECT * FROM Users WHERE Username = %s OR Email = %s;
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (username, email))
                user = cursor.fetchone()
                if not user:
                    raise ValueError("No user found with the provided username or email.")
        return user
    except DatabaseError as e:
        raise RuntimeError(f"Database error: {e}")

def login_user(username: str, password: str):
    if not username or not password:
        raise ValueError("Username and password must be provided.")
    query = """
    SELECT * FROM Users WHERE Username = %s;
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (username,))
                user = cursor.fetchone()
                if not user:
                    raise ValueError("Invalid username or password.")
                if not check_password(password, user["Password"]):
                    raise ValueError("Invalid username or password.")
        return user
    except DatabaseError as e:
        raise RuntimeError(f"Database error: {e}")
