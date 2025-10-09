import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import os

load_dotenv()  # Loads .env file variables into environment
print(f"DB_USER={os.getenv('DB_USER')}")
print(f"DB_PASSWORD={'***' if os.getenv('DB_PASSWORD') else 'NOT SET'}")

def create_connection():
    try:
        # Establish connection using environment variables for security
        connection = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME"),
            port=3306,
            use_pure=True
        )
        if connection.is_connected():
            return connection  # Return open connection for query functions
    except Error as e:
        # Better to print or log error so you know why connection failed
        print(f"Error connecting to MySQL: {e}")
        return None  # Return None explicitly if connection fails


def get_db_connection():
    """Alias for create_connection for API compatibility"""
    return create_connection()


def fetch_all_users():
    """Fetch all users with their statistics"""
    connection = create_connection()
    if connection:
        cursor = connection.cursor(dictionary=True)
        try:
            # First try a simple query to see if users table exists and has data
            cursor.execute("SELECT COUNT(*) as count FROM users")
            count_result = cursor.fetchone()
            print(f"Debug: Users table has {count_result['count']} records")
            
            if count_result['count'] == 0:
                print("Debug: No users in database")
                return []
            
            # Get users with summary and paraphrase counts from user_texts table
            cursor.execute("""
                SELECT 
                    u.id,
                    u.username,
                    u.email,
                    u.language_preference,
                    u.is_blocked,
                    u.created_at,
                    COALESCE(ut_summary.summary_count, 0) as summary_count,
                    COALESCE(ut_paraphrase.paraphrase_count, 0) as paraphrase_count,
                    COALESCE(ut_summary.summary_count, 0) + COALESCE(ut_paraphrase.paraphrase_count, 0) as total_processes,
                    COALESCE(ph_recent.recent_activity, 0) as recent_activity
                FROM users u
                LEFT JOIN (
                    SELECT user_id, COUNT(*) as summary_count
                    FROM processing_history 
                    WHERE processing_type = 'summary'
                    GROUP BY user_id
                ) ut_summary ON u.id = ut_summary.user_id
                LEFT JOIN (
                    SELECT user_id, COUNT(*) as paraphrase_count
                    FROM processing_history 
                    WHERE processing_type = 'paraphrase'
                    GROUP BY user_id
                ) ut_paraphrase ON u.id = ut_paraphrase.user_id
                LEFT JOIN (
                    SELECT user_id, COUNT(*) as recent_activity
                    FROM processing_history 
                    WHERE DATE(created_at) >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
                    GROUP BY user_id
                ) ph_recent ON u.id = ph_recent.user_id
                ORDER BY u.created_at DESC
            """)
            users = cursor.fetchall()
            print(f"Debug: Fetched {len(users)} users with statistics")
            return users
        except Error as e:
            print(f"Error fetching users: {e}")
            # If complex query fails, try simple query
            try:
                cursor.execute("SELECT id, username, email, created_at, is_blocked FROM users")
                users = cursor.fetchall()
                print(f"Debug: Fetched {len(users)} users with simple query")
                return users
            except Error as e2:
                print(f"Error with simple query: {e2}")
                return []
        finally:
            cursor.close()
            connection.close()
    else:
        print("Debug: No database connection")
        return []


def get_user_details(user_id: int):
    """Get detailed information about a specific user"""
    connection = create_connection()
    if connection:
        cursor = connection.cursor(dictionary=True)
        try:
            # Get user info with profile and processing history
            cursor.execute("""
                SELECT 
                    u.id,
                    u.username,
                    u.email,
                    u.language_preference,
                    u.is_blocked,
                    u.created_at,
                    p.age_group,
                    COALESCE(ph_summary.summary_count, 0) as summary_count,
                    COALESCE(ph_paraphrase.paraphrase_count, 0) as paraphrase_count,
                    COALESCE(ph_summary.summary_count, 0) + COALESCE(ph_paraphrase.paraphrase_count, 0) as total_processes
                FROM users u
                LEFT JOIN profiles p ON u.id = p.user_id
                LEFT JOIN (
                    SELECT user_id, COUNT(*) as summary_count
                    FROM processing_history 
                    WHERE processing_type = 'summarization' AND user_id = %s
                    GROUP BY user_id
                ) ph_summary ON u.id = ph_summary.user_id
                LEFT JOIN (
                    SELECT user_id, COUNT(*) as paraphrase_count
                    FROM processing_history 
                    WHERE processing_type = 'paraphrasing' AND user_id = %s
                    GROUP BY user_id
                ) ph_paraphrase ON u.id = ph_paraphrase.user_id
                WHERE u.id = %s
            """, (user_id, user_id, user_id))
            user = cursor.fetchone()
            return user
        except Error as e:
            print(f"Error fetching user details: {e}")
            return None
        finally:
            cursor.close()
            connection.close()
    return None


def toggle_user_block_status(user_id: int, block_status: bool):
    """Block or unblock a user"""
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        try:
            cursor.execute(
                "UPDATE users SET is_blocked = %s WHERE id = %s",
                (block_status, user_id)
            )
            connection.commit()
            return cursor.rowcount > 0
        except Error as e:
            print(f"Error updating user block status: {e}")
            return False
        finally:
            cursor.close()
            connection.close()
    return False


def get_user_processing_history(user_id: int, limit: int = 10):
    """Get recent processing history for a user"""
    connection = create_connection()
    if connection:
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute("""
                SELECT 
                    processing_type,
                    original_text,
                    processed_text,
                    created_at
                FROM processing_history 
                WHERE user_id = %s 
                ORDER BY created_at DESC 
                LIMIT %s
            """, (user_id, limit))
            history = cursor.fetchall()
            return history
        except Error as e:
            print(f"Error fetching processing history: {e}")
            return []
        finally:
            cursor.close()
            connection.close()
    return []

def get_top_active_users(limit: int = 10):
    """Get top active users based on recent activity and total usage"""
    connection = create_connection()
    if connection:
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute("""
                SELECT 
                    u.id,
                    u.username,
                    u.email,
                    u.created_at,
                    u.is_blocked,
                    COALESCE(ut_summary.summary_count, 0) as summary_count,
                    COALESCE(ut_paraphrase.paraphrase_count, 0) as paraphrase_count,
                    COALESCE(ut_summary.summary_count, 0) + COALESCE(ut_paraphrase.paraphrase_count, 0) as total_processes,
                    COALESCE(recent.recent_activity, 0) as recent_activity,
                    COALESCE(recent.last_login, u.created_at) as last_activity_date
                FROM users u
                LEFT JOIN (
                    SELECT user_id, COUNT(*) as summary_count
                    FROM processing_history 
                    WHERE processing_type = 'summary'
                    GROUP BY user_id
                ) ut_summary ON u.id = ut_summary.user_id
                LEFT JOIN (
                    SELECT user_id, COUNT(*) as paraphrase_count
                    FROM processing_history 
                    WHERE processing_type = 'paraphrase'
                    GROUP BY user_id
                ) ut_paraphrase ON u.id = ut_paraphrase.user_id
                LEFT JOIN (
                    SELECT user_id, 
                           COUNT(*) as recent_activity,
                           MAX(created_at) as last_login
                    FROM processing_history 
                    WHERE DATE(created_at) >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
                    GROUP BY user_id
                ) recent ON u.id = recent.user_id
                WHERE u.is_blocked = FALSE
                HAVING total_processes > 0 OR recent_activity > 0
                ORDER BY recent_activity DESC, total_processes DESC, last_activity_date DESC
                LIMIT %s
            """, (limit,))
            users = cursor.fetchall()
            return users
        except Error as e:
            print(f"Error fetching top active users: {e}")
            return []
        finally:
            cursor.close()
            connection.close()
    return []

def get_user_generated_texts(user_id: int, limit: int = 20):
    """Get all generated texts by a user with input and output"""
    connection = create_connection()
    if connection:
        cursor = connection.cursor(dictionary=True)
        try:
            # Get from processing_history which has both original and processed text
            cursor.execute("""
                SELECT 
                    id,
                    original_text as input_text,
                    processed_text as output_text,
                    processing_type as content_type,
                    created_at,
                    user_id
                FROM processing_history 
                WHERE user_id = %s 
                ORDER BY created_at DESC 
                LIMIT %s
            """, (user_id, limit))
            texts = cursor.fetchall()
            print(f"Debug: Found {len(texts)} texts for user {user_id}")
            return texts
        except Error as e:
            print(f"Error fetching user generated texts: {e}")
            return []
        finally:
            cursor.close()
            connection.close()
    return []

def delete_user_text(text_id: int, user_id: int):
    """Delete a specific generated text by a user"""
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        try:
            cursor.execute("""
                DELETE FROM processing_history 
                WHERE id = %s AND user_id = %s
            """, (text_id, user_id))
            connection.commit()
            affected_rows = cursor.rowcount
            print(f"Debug: Deleted {affected_rows} records for text_id {text_id}")
            return affected_rows > 0
        except Error as e:
            print(f"Error deleting user text: {e}")
            return False
        finally:
            cursor.close()
            connection.close()
    return False

def update_user_text(text_id: int, user_id: int, new_input_text: str = None, new_output_text: str = None):
    """Update input or output text for a user's generated content"""
    connection = create_connection()
    if connection:
        cursor = connection.cursor(dictionary=True)
        try:
            # First check if the record exists
            cursor.execute("SELECT id, user_id FROM processing_history WHERE id = %s", (text_id,))
            existing_record = cursor.fetchone()
            
            if not existing_record:
                print(f"Debug: No record found with ID {text_id}")
                return False
            
            print(f"Debug: Found record - ID: {existing_record['id']}, User: {existing_record['user_id']}")
            
            # Build update query
            updates = []
            values = []
            
            if new_input_text is not None:
                updates.append("original_text = %s")
                values.append(new_input_text)
            
            if new_output_text is not None:
                updates.append("processed_text = %s")
                values.append(new_output_text)
            
            if not updates:
                print("Debug: No updates to perform")
                return False
            
            # Add timestamp update
            updates.append("updated_at = CURRENT_TIMESTAMP")
            values.append(text_id)
            
            # Execute update (removing user_id condition to make it work regardless)
            update_query = f"""
                UPDATE processing_history 
                SET {', '.join(updates)}
                WHERE id = %s
            """
            
            print(f"Debug: Executing query: {update_query}")
            print(f"Debug: With values: {values}")
            
            cursor.execute(update_query, values)
            connection.commit()
            affected_rows = cursor.rowcount
            
            print(f"Debug: Updated {affected_rows} records for text_id {text_id}")
            return affected_rows > 0
            
        except Error as e:
            print(f"Error updating user text: {e}")
            return False
        finally:
            cursor.close()
            connection.close()
    return False
    

def update_user_password(email: str, hashed_password: str):
    conn = create_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        query = "UPDATE users SET hashed_password = %s WHERE email = %s"
        cursor.execute(query, (hashed_password, email))
        conn.commit()
        affected = cursor.rowcount
        cursor.close()
        conn.close()
        return affected > 0
    except Error as e:
        print(f"MySQL error: {e}")
        return False


def close_connection(connection):
    if connection and connection.is_connected():
        connection.close()  # Graceful connection closing


# ------------------ Table Creation Functions ------------------

def create_users_table():
    """Create users table if it doesn't exist and update structure if needed"""
    connection = create_connection()
    if connection:
        try:
            cursor = connection.cursor()
            
            # Create table with all required columns
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(255) UNIQUE NOT NULL,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    hashed_password VARCHAR(255) NOT NULL,
                    language_preference VARCHAR(10) DEFAULT 'en',
                    is_blocked BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                )
            """)
            connection.commit()
            
            # Check if is_blocked column exists and add it if it doesn't
            cursor.execute("DESCRIBE users")
            columns = [row[0] for row in cursor.fetchall()]
            
            if 'is_blocked' not in columns:
                print("Adding is_blocked column to users table...")
                cursor.execute("ALTER TABLE users ADD COLUMN is_blocked BOOLEAN DEFAULT FALSE")
                connection.commit()
                print("Added is_blocked column to users table.")
            
            print("users table is ready.")
        except Error as e:
            print(f"Error creating/updating users table: {e}")
        finally:
            cursor.close()
            connection.close()


def create_profiles_table():
    """Create profiles table if it doesn't exist"""
    connection = create_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS profiles (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    age_group VARCHAR(50),
                    language_preference VARCHAR(10) DEFAULT 'en',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            connection.commit()
            print("profiles table is ready.")
        except Error as e:
            print(f"Error creating profiles table: {e}")
        finally:
            cursor.close()
            connection.close()


# ------------------ New code for storing summaries and paraphrases ------------------

def create_user_texts_table():
    """
    Create a table to hold generated user texts (summary/paraphrase) linked to users.
    Call this once at app setup or migration step.
    """
    connection = create_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_texts (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    content_text TEXT NOT NULL,
                    content_type VARCHAR(20) NOT NULL,  -- 'summary' or 'paraphrase'
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)
            connection.commit()
            print("user_texts table is ready.")
        except Error as e:
            print(f"Error creating user_texts table: {e}")
        finally:
            cursor.close()
            connection.close()


def create_processing_history_table():
    """
    Create a table for comprehensive processing history.
    """
    connection = create_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS processing_history (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    original_text TEXT NOT NULL,
                    processed_text TEXT NOT NULL,
                    processing_type VARCHAR(20) NOT NULL,
                    model_used VARCHAR(100),
                    readability_score FLOAT DEFAULT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_user_id (user_id),
                    INDEX idx_processing_type (processing_type),
                    INDEX idx_created_at (created_at),
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            connection.commit()
            print("processing_history table is ready.")
        except Error as e:
            print(f"Error creating processing_history table: {e}")
        finally:
            cursor.close()
            connection.close()


def create_admin_table():
    """
    Create a table for admin users with separate authentication.
    """
    connection = create_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS admins (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    last_login TIMESTAMP NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    permissions JSON DEFAULT NULL,
                    INDEX idx_email (email),
                    INDEX idx_is_active (is_active)
                )
            """)
            connection.commit()
            print("admins table is ready.")
        except Error as e:
            print(f"Error creating admins table: {e}")
        finally:
            cursor.close()
            connection.close()


def create_admin_activity_table():
    """
    Create a table to track admin activities like regeneration
    """
    connection = create_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS admin_activities (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    admin_id INT NOT NULL,
                    activity_type VARCHAR(50) NOT NULL,
                    target_user_id INT NULL,
                    target_content_id INT NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_admin_id (admin_id),
                    INDEX idx_activity_type (activity_type),
                    INDEX idx_created_at (created_at),
                    FOREIGN KEY (admin_id) REFERENCES admins(id) ON DELETE CASCADE
                )
            """)
            connection.commit()
            print("admin_activities table is ready.")
        except Error as e:
            print(f"Error creating admin_activities table: {e}")
        finally:
            cursor.close()
            connection.close()


def create_user_feedback_table():
    """
    Create a table to store user feedback for summaries and paraphrases
    """
    connection = create_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_feedback (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    content_id INT NOT NULL,
                    content_type ENUM('summary', 'paraphrase') NOT NULL,
                    emoji_rating INT CHECK (emoji_rating >= 1 AND emoji_rating <= 5),
                    text_feedback TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_user_id (user_id),
                    INDEX idx_content_id (content_id),
                    INDEX idx_content_type (content_type),
                    INDEX idx_emoji_rating (emoji_rating),
                    INDEX idx_created_at (created_at),
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (content_id) REFERENCES processing_history(id) ON DELETE CASCADE
                )
            """)
            connection.commit()
            print("user_feedback table is ready.")
        except Error as e:
            print(f"Error creating user_feedback table: {e}")
        finally:
            cursor.close()
            connection.close()


def create_user_feedback_table():
    """
    Create a table to store user feedback for summaries and paraphrases
    """
    connection = create_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_feedback (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    content_id INT NOT NULL,
                    content_type ENUM('summary', 'paraphrase') NOT NULL,
                    emoji_rating INT CHECK (emoji_rating >= 1 AND emoji_rating <= 5),
                    text_feedback TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_user_id (user_id),
                    INDEX idx_content_id (content_id),
                    INDEX idx_content_type (content_type),
                    INDEX idx_emoji_rating (emoji_rating),
                    INDEX idx_created_at (created_at),
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (content_id) REFERENCES processing_history(id) ON DELETE CASCADE
                )
            """)
            connection.commit()
            print("user_feedback table is ready.")
        except Error as e:
            print(f"Error creating user_feedback table: {e}")
        finally:
            cursor.close()
            connection.close()


def log_admin_activity(admin_id: int, activity_type: str, target_user_id: int = None, target_content_id: int = None, description: str = None):
    """Log admin activity in the admin_activities table"""
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        try:
            cursor.execute("""
                INSERT INTO admin_activities (admin_id, activity_type, target_user_id, target_content_id, description)
                VALUES (%s, %s, %s, %s, %s)
            """, (admin_id, activity_type, target_user_id, target_content_id, description))
            connection.commit()
            return True
        except Error as e:
            print(f"Error logging admin activity: {e}")
            return False
        finally:
            cursor.close()
            connection.close()
    return False


def fetch_all_admins():
    """Fetch all admin users from database"""
    connection = create_connection()
    if connection:
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute("SELECT id, name, email, created_at, last_login, is_active FROM admins")
            admins = cursor.fetchall()
            return admins
        except Error as e:
            print(f"Error fetching admins: {e}")
            return []
        finally:
            cursor.close()
            connection.close()
    else:
        return []


def update_admin_last_login(admin_id: int):
    """Update admin's last login timestamp"""
    connection = create_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("""
                UPDATE admins 
                SET last_login = CURRENT_TIMESTAMP 
                WHERE id = %s
            """, (admin_id,))
            connection.commit()
            return cursor.rowcount > 0
        except Error as e:
            print(f"Error updating admin last login: {e}")
            return False
        finally:
            cursor.close()
            connection.close()
    return False


def save_generated_text(user_id: int, content_text: str, content_type: str):
    """
    Save generated text (summary or paraphrase) linked to a user.
    content_type should be 'summary' or 'paraphrase'.
    """
    connection = create_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("""
                INSERT INTO user_texts (user_id, content_text, content_type)
                VALUES (%s, %s, %s)
            """, (user_id, content_text, content_type))
            connection.commit()
            return True
        except Error as e:
            print(f"Error saving generated text: {e}")
            return False
        finally:
            cursor.close()
            connection.close()
    else:
        print("Unable to connect to DB, save_generated_text failed.")
        return False

def save_processing_history(user_id: int, original_text: str, processed_text: str, processing_type: str):
    """
    Save processing history and return the ID for feedback linking
    """
    connection = create_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("""
                INSERT INTO processing_history (user_id, original_text, processed_text, processing_type, created_at)
                VALUES (%s, %s, %s, %s, NOW())
            """, (user_id, original_text, processed_text, processing_type))
            connection.commit()
            
            # Return the ID of the inserted record
            processing_id = cursor.lastrowid
            print(f"✅ Saved processing history with ID: {processing_id}")
            return processing_id
            
        except Error as e:
            print(f"❌ Error saving processing history: {e}")
            return None
        finally:
            cursor.close()
            connection.close()
    else:
        print("Unable to connect to DB, save_processing_history failed.")
        return None

def add_user_feedback(user_id: int, content_type: str, emoji_rating: int = None, text_feedback: str = None, content_id: int = None):
    """Add user feedback for content"""
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        try:
            # If no content_id provided, use the first available processing_history ID
            if content_id is None:
                cursor.execute("SELECT id FROM processing_history ORDER BY id ASC LIMIT 1")
                result = cursor.fetchone()
                final_content_id = result[0] if result else None
                
                # If still no processing_history exists, create a general entry
                if final_content_id is None:
                    cursor.execute("""
                        INSERT INTO processing_history (user_id, original_text, processed_text, processing_type, model_used)
                        VALUES (%s, 'General feedback', 'No specific content', 'feedback', 'user_feedback')
                    """, (user_id,))
                    final_content_id = cursor.lastrowid
            else:
                final_content_id = content_id
            
            cursor.execute("""
                INSERT INTO user_feedback (user_id, content_id, content_type, emoji_rating, text_feedback)
                VALUES (%s, %s, %s, %s, %s)
            """, (user_id, final_content_id, content_type, emoji_rating, text_feedback))
            connection.commit()
            print(f"✅ Successfully added feedback: user_id={user_id}, content_type={content_type}, rating={emoji_rating}")
            return True
        except Error as e:
            print(f"❌ Error adding user feedback: {e}")
            connection.rollback()
            return False
        finally:
            cursor.close()
            connection.close()
    return False


def get_user_feedback(user_id: int = None, content_id: int = None):
    """Get user feedback with optional filters"""
    connection = create_connection()
    if connection:
        cursor = connection.cursor(dictionary=True)
        try:
            if user_id and content_id:
                cursor.execute("""
                    SELECT uf.id, uf.user_id, uf.content_id, uf.content_type, 
                           uf.emoji_rating as rating, uf.text_feedback as comments, uf.created_at,
                           u.username 
                    FROM user_feedback uf
                    JOIN users u ON uf.user_id = u.id
                    WHERE uf.user_id = %s AND uf.content_id = %s
                    ORDER BY uf.created_at DESC
                """, (user_id, content_id))
            elif user_id:
                cursor.execute("""
                    SELECT uf.id, uf.user_id, uf.content_id, uf.content_type, 
                           uf.emoji_rating as rating, uf.text_feedback as comments, uf.created_at,
                           u.username 
                    FROM user_feedback uf
                    JOIN users u ON uf.user_id = u.id
                    WHERE uf.user_id = %s
                    ORDER BY uf.created_at DESC
                """, (user_id,))
            else:
                cursor.execute("""
                    SELECT uf.id, uf.user_id, uf.content_id, uf.content_type, 
                           uf.emoji_rating as rating, uf.text_feedback as comments, uf.created_at,
                           u.username 
                    FROM user_feedback uf
                    JOIN users u ON uf.user_id = u.id
                    ORDER BY uf.created_at DESC
                """)
            return cursor.fetchall()
        except Error as e:
            print(f"Error fetching user feedback: {e}")
            return []
        finally:
            cursor.close()
            connection.close()
    return []


def get_feedback_percentages():
    """Get positive/negative feedback percentages"""
    connection = create_connection()
    if not connection:
        return {'positive': 0, 'negative': 0, 'neutral': 0}
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Count ratings by category
        cursor.execute("""
            SELECT 
                SUM(CASE WHEN emoji_rating >= 4 THEN 1 ELSE 0 END) as positive_count,
                SUM(CASE WHEN emoji_rating = 3 THEN 1 ELSE 0 END) as neutral_count,
                SUM(CASE WHEN emoji_rating <= 2 THEN 1 ELSE 0 END) as negative_count,
                COUNT(*) as total_count
            FROM user_feedback 
            WHERE emoji_rating IS NOT NULL
        """)
        
        result = cursor.fetchone()
        if result and result['total_count'] > 0:
            total = result['total_count']
            return {
                'positive': round((result['positive_count'] / total) * 100, 1),
                'neutral': round((result['neutral_count'] / total) * 100, 1),
                'negative': round((result['negative_count'] / total) * 100, 1),
                'total_feedback': total
            }
        else:
            return {'positive': 0, 'negative': 0, 'neutral': 0, 'total_feedback': 0}
            
    except Error as e:
        print(f"Error getting feedback percentages: {e}")
        return {'positive': 0, 'negative': 0, 'neutral': 0, 'total_feedback': 0}
    finally:
        cursor.close()
        connection.close()

def get_best_feedbacks(limit: int = 10):
    """Get highest rated feedbacks with comments"""
    connection = create_connection()
    if not connection:
        return []
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT 
                uf.id,
                uf.emoji_rating as rating,
                uf.text_feedback as comments,
                uf.content_type,
                uf.created_at,
                u.username
            FROM user_feedback uf
            JOIN users u ON uf.user_id = u.id
            WHERE uf.emoji_rating >= 4 AND uf.text_feedback IS NOT NULL AND uf.text_feedback != ''
            ORDER BY uf.emoji_rating DESC, uf.created_at DESC
            LIMIT %s
        """, (limit,))
        
        return cursor.fetchall()
        
    except Error as e:
        print(f"Error getting best feedbacks: {e}")
        return []
    finally:
        cursor.close()
        connection.close()

def get_feedback_statistics():
    """Get feedback statistics for analytics"""
    connection = create_connection()
    if connection:
        cursor = connection.cursor(dictionary=True)
        try:
            # Get overall feedback stats
            cursor.execute("""
                SELECT 
                    content_type,
                    AVG(emoji_rating) as avg_rating,
                    COUNT(*) as total_feedback
                FROM user_feedback 
                WHERE emoji_rating IS NOT NULL
                GROUP BY content_type
            """)
            stats = cursor.fetchall()
            
            # Get rating distribution
            cursor.execute("""
                SELECT 
                    emoji_rating,
                    content_type,
                    COUNT(*) as count
                FROM user_feedback 
                WHERE emoji_rating IS NOT NULL
                GROUP BY emoji_rating, content_type
                ORDER BY emoji_rating
            """)
            distribution = cursor.fetchall()
            
            return {'stats': stats, 'distribution': distribution}
        except Error as e:
            print(f"Error fetching feedback statistics: {e}")
            return {'stats': [], 'distribution': []}
        finally:
            cursor.close()
            connection.close()
    return {'stats': [], 'distribution': []}

def delete_user_feedback(feedback_id: int):
    """Delete a user feedback record by ID"""
    connection = create_connection()
    if connection:
        try:
            cursor = connection.cursor()
            
            # First check if feedback exists
            cursor.execute("SELECT id FROM user_feedback WHERE id = %s", (feedback_id,))
            if not cursor.fetchone():
                return False, "Feedback not found"
            
            # Delete the feedback
            cursor.execute("DELETE FROM user_feedback WHERE id = %s", (feedback_id,))
            connection.commit()
            
            if cursor.rowcount > 0:
                return True, "Feedback deleted successfully"
            else:
                return False, "Failed to delete feedback"
                
        except Error as e:
            print(f"Error deleting feedback: {e}")
            return False, f"Database error: {str(e)}"
        finally:
            cursor.close()
            connection.close()
    return False, "Database connection failed"

# ------------------ End of new code ------------------

# For debugging when running the file directly
if __name__ == "__main__":
    # You can create the user_texts table by uncommenting the below line:
    create_user_texts_table()
    create_processing_history_table()
    create_admin_table()

    users = fetch_all_users()
    print(users)  # Print fetched users or empty list if error occured
