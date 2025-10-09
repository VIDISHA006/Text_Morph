#!/usr/bin/env python3
"""
Admin Authentication Module
Handles admin-specific authentication and session management
"""

import streamlit as st
import requests
import hashlib
import mysql.connector
from mysql.connector import Error
from backend.api.database import create_connection, update_admin_last_login
from backend.api.passhash import hash_password, verify_password
from datetime import datetime

API_URL = "http://localhost:8000"

def create_admin_account(name: str, email: str, password: str):
    """Create a new admin account"""
    connection = create_connection()
    if not connection:
        return False, "Database connection failed"
    
    try:
        cursor = connection.cursor()
        
        # Check if admin already exists
        cursor.execute("SELECT id FROM admins WHERE email = %s", (email,))
        if cursor.fetchone():
            return False, "Admin account with this email already exists"
        
        # Hash password
        hashed_password = hash_password(password)
        
        # Insert new admin
        cursor.execute("""
            INSERT INTO admins (name, email, password, is_active)
            VALUES (%s, %s, %s, %s)
        """, (name, email, hashed_password, True))
        
        connection.commit()
        return True, "Admin account created successfully"
        
    except Error as e:
        return False, f"Error creating admin account: {str(e)}"
    finally:
        cursor.close()
        connection.close()


def authenticate_admin(email: str, password: str):
    """Authenticate admin login credentials"""
    connection = create_connection()
    if not connection:
        return False, None, "Database connection failed"
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Get admin by email
        cursor.execute("""
            SELECT id, name, email, password, is_active 
            FROM admins 
            WHERE email = %s AND is_active = TRUE
        """, (email,))
        
        admin = cursor.fetchone()
        
        if not admin:
            return False, None, "Invalid email or admin account not found"
        
        # Verify password
        if verify_password(password, admin['password']):
            # Update last login
            update_admin_last_login(admin['id'])
            
            # Return admin info without password
            admin_info = {
                'id': admin['id'],
                'name': admin['name'],
                'email': admin['email'],
                'is_active': admin['is_active']
            }
            
            return True, admin_info, "Login successful"
        else:
            return False, None, "Invalid password"
            
    except Error as e:
        return False, None, f"Authentication error: {str(e)}"
    finally:
        cursor.close()
        connection.close()


def admin_login_form():
    """Display admin login form"""
    st.markdown("### Admin Login")
    
    with st.form("admin_login_form"):
        email = st.text_input("Admin Email", placeholder="admin@textmorph.com")
        password = st.text_input("Admin Password", type="password", placeholder="Enter admin password")
        
        col1, col2 = st.columns([1, 1])
        with col1:
            login_submitted = st.form_submit_button("Admin Login", width='stretch')
        with col2:
            if st.form_submit_button("Switch to User Login", width='stretch'):
                st.session_state.login_mode = "user"
                st.rerun()
    
    if login_submitted:
        if not email or not password:
            st.error("Please enter both email and password")
            return False
        
        # Authenticate admin
        success, admin_info, message = authenticate_admin(email, password)
        
        if success:
            # Set admin session
            st.session_state.admin_logged_in = True
            st.session_state.admin_info = admin_info
            st.session_state.admin_id = admin_info['id']
            st.session_state.admin_name = admin_info['name']
            st.session_state.admin_email = admin_info['email']
            
            st.success(f"Welcome, {admin_info['name']}!")
            st.rerun()
            return True
        else:
            st.error(message)
            return False
    
    return False


def admin_signup_form():
    """Display admin signup form (for initial setup)"""
    st.markdown("### 👤 Create Admin Account")
    st.info("⚠️ This is for creating admin accounts. Contact system administrator if you need access.")
    
    with st.form("admin_signup_form"):
        name = st.text_input("Full Name", placeholder="Enter admin full name")
        email = st.text_input("Email", placeholder="admin@textmorph.com")
        password = st.text_input("Password", type="password", placeholder="Enter strong password")
        confirm_password = st.text_input("Confirm Password", type="password", placeholder="Confirm password")
        
        signup_submitted = st.form_submit_button("Register", width='stretch')
    
    if signup_submitted:
        # Validation
        if not all([name, email, password, confirm_password]):
            st.error("Please fill in all fields")
            return False
        
        if password != confirm_password:
            st.error("Passwords do not match")
            return False
        
        if len(password) < 6:
            st.error("Password must be at least 6 characters long")
            return False
        
        # Create admin account
        success, message = create_admin_account(name, email, password)
        
        if success:
            st.success(message)
            st.info("Admin account created! Please login with your credentials.")
            return True
        else:
            st.error(message)
            return False
    
    return False


def admin_logout():
    """Logout admin user"""
    # Clear admin session variables
    admin_keys = [key for key in st.session_state.keys() if key.startswith('admin_')]
    for key in admin_keys:
        del st.session_state[key]
    
    # Reset login mode
    if 'login_mode' in st.session_state:
        del st.session_state['login_mode']
    
    st.success("Admin logged out successfully!")
    st.rerun()


def is_admin_logged_in():
    """Check if admin is logged in"""
    return st.session_state.get('admin_logged_in', False)


def get_current_admin():
    """Get current admin information"""
    if is_admin_logged_in():
        return st.session_state.get('admin_info', None)
    return None


def require_admin_login():
    """Decorator function to require admin login"""
    if not is_admin_logged_in():
        st.error("Admin access required. Please login as admin.")
        st.stop()
        return False
    return True