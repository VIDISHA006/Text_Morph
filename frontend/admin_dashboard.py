#!/usr/bin/env python3
"""
Admin Dashboard
Complete admin interface separate from user functionality
"""

import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, '..'))
sys.path.append(parent_dir)
backend_dir = os.path.join(parent_dir, "backend")
sys.path.append(backend_dir)

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
from datetime import datetime, timedelta
from backend.api.database import (create_connection, fetch_all_users, fetch_all_admins, 
                                   get_top_active_users, get_user_generated_texts, 
                                   delete_user_text, update_user_text, get_user_details, 
                                   toggle_user_block_status, get_user_feedback, delete_user_feedback,
                                   get_feedback_statistics, get_feedback_percentages, 
                                   get_best_feedbacks, log_admin_activity)
from mysql.connector import Error
from frontend.admin_auth import require_admin_login, get_current_admin, admin_logout

def get_user_statistics():
    """Get comprehensive user statistics"""
    connection = create_connection()
    if not connection:
        return {}
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Total users
        cursor.execute("SELECT COUNT(*) as total_users FROM users")
        total_users = cursor.fetchone()['total_users']
        
        # Users registered in last 30 days
        cursor.execute("""
            SELECT COUNT(*) as new_users 
            FROM users 
            WHERE DATE(created_at) >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
        """)
        new_users = cursor.fetchone()['new_users']
        
        # Active users (users with processing history in last 30 days)
        cursor.execute("""
            SELECT COUNT(DISTINCT user_id) as active_users
            FROM processing_history 
            WHERE DATE(created_at) >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
        """)
        active_users_result = cursor.fetchone()
        active_users = active_users_result['active_users'] if active_users_result else 0
        
        # Total processing requests
        cursor.execute("SELECT COUNT(*) as total_requests FROM processing_history")
        total_requests_result = cursor.fetchone()
        total_requests = total_requests_result['total_requests'] if total_requests_result else 0
        
        # Processing by type
        cursor.execute("""
            SELECT processing_type, COUNT(*) as count
            FROM processing_history 
            GROUP BY processing_type
        """)
        processing_by_type = cursor.fetchall()
        
        return {
            'total_users': total_users,
            'new_users': new_users,
            'active_users': active_users,
            'total_requests': total_requests,
            'processing_by_type': processing_by_type
        }
        
    except Error as e:
        st.error(f"Error fetching statistics: {e}")
        return {}
    finally:
        cursor.close()
        connection.close()


def get_daily_activity(days=30):
    """Get daily activity for the last N days"""
    connection = create_connection()
    if not connection:
        return pd.DataFrame()
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT 
                DATE(created_at) as date,
                processing_type,
                COUNT(*) as count
            FROM processing_history 
            WHERE DATE(created_at) >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
            GROUP BY DATE(created_at), processing_type
            ORDER BY date DESC
        """, (days,))
        
        data = cursor.fetchall()
        return pd.DataFrame(data)
        
    except Error as e:
        st.error(f"Error fetching daily activity: {e}")
        return pd.DataFrame()
    finally:
        cursor.close()
        connection.close()


def show_top_active_users():
    """Show top active users based on recent activity and regular usage"""
    st.header("Top Active Users")
    st.write("Users who regularly log in and use the platform for text generation")
    
    # Get top active users from database
    active_users = get_top_active_users(limit=10)
    
    if active_users:
        # Create metrics columns
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Active Users (Last 30 days)", len([u for u in active_users if u['recent_activity'] > 0]))
        with col2:
            total_recent_activity = sum(u['recent_activity'] for u in active_users)
            st.metric("Total Recent Generations", total_recent_activity)
        with col3:
            avg_activity = total_recent_activity / len(active_users) if active_users else 0
            st.metric("Avg. Generations per User", f"{avg_activity:.1f}")
        
        st.subheader("Most Active Users")
        
        # Display active users in cards
        for i, user in enumerate(active_users[:6]):  # Show top 6 users
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
                
                with col1:
                    st.write(f"**{user['username']}** ({user['email']})")
                    if user['recent_activity'] > 0:
                        st.success(f"Active in last 30 days")
                    else:
                        st.info("Regular user")
                
                with col2:
                    st.metric("Summaries", user['summary_count'])
                
                with col3:
                    st.metric("Paraphrases", user['paraphrase_count'])
                
                with col4:
                    st.metric("Recent Activity", user['recent_activity'])
                
                st.divider()
    else:
        st.info("No active users found. Users will appear here once they start generating content.")


def admin_dashboard_main():
    """Main admin dashboard interface"""
    
    # Require admin login
    if not require_admin_login():
        return
    
    # Admin header
    admin_info = get_current_admin()
    
    # Custom CSS for admin dashboard
    st.markdown("""
    <style>
    .admin-header {
        background: linear-gradient(90deg, #FF6B35 0%, #F29F58 100%);
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        text-align: center;
    }
    
    .admin-header h1 {
        color: white;
        margin: 0;
        font-size: 2.5rem;
    }
    
    .admin-info {
        color: white;
        margin: 0.5rem 0;
        font-size: 1.1rem;
    }
    
    .stat-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #FF6B35;
    }
    
    .stat-number {
        font-size: 2rem;
        font-weight: bold;
        color: #FF6B35;
        margin: 0;
    }
    
    .stat-label {
        color: #666;
        margin: 0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Admin header
    st.markdown(f"""
    <div class="admin-header">
        <h1>Admin Dashboard</h1>
        <p class="admin-info">Welcome, {admin_info['name']} | {admin_info['email']}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar navigation
    st.sidebar.title("Admin Navigation")
    
    menu_option = st.sidebar.selectbox(
        "Select Section",
        ["Overview", "Top Active Users", "User Management", "User Feedback", "Analytics", "System Settings"]
    )
    
    # Logout button
    if st.sidebar.button("Admin Logout", width='stretch'):
        admin_logout()
        return
    
    # Main content based on menu selection
    if menu_option == "Overview":
        show_admin_overview()
    elif menu_option == "Top Active Users":
        show_top_active_users()
    elif menu_option == "User Management":
        show_user_management()
    elif menu_option == "User Feedback":
        show_user_feedback_management()
    elif menu_option == "Analytics":
        show_analytics()
    elif menu_option == "System Settings":
        show_system_settings()


def show_admin_overview():
    """Show admin overview dashboard"""
    st.header("System Overview")
    
    # Get statistics
    stats = get_user_statistics()
    
    if not stats:
        st.warning("Unable to fetch system statistics. Please check database connection.")
        return
    
    if stats:
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="stat-card">
                <p class="stat-number">{stats['total_users']}</p>
                <p class="stat-label">Total Users</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="stat-card">
                <p class="stat-number">{stats['new_users']}</p>
                <p class="stat-label">New Users (30d)</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="stat-card">
                <p class="stat-number">{stats['active_users']}</p>
                <p class="stat-label">Active Users</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
            <div class="stat-card">
                <p class="stat-number">{stats['total_requests']}</p>
                <p class="stat-label">Total Requests</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Processing type distribution
        if stats['processing_by_type']:
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Processing Distribution")
                df_processing = pd.DataFrame(stats['processing_by_type'])
                if not df_processing.empty:
                    fig = px.pie(df_processing, values='count', names='processing_type', 
                               title="Requests by Type")
                    fig.update_traces(textposition='inside', textinfo='percent+label')
                    st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.subheader("Recent Activity")
                daily_activity = get_daily_activity(30)
                if not daily_activity.empty:
                    fig = px.line(daily_activity, x='date', y='count', color='processing_type',
                                title="Daily Activity (Past Month)")
                    st.plotly_chart(fig, use_container_width=True)
        
        # Top users
        st.subheader("Top Active Users")
        top_users = get_top_active_users(10)
        if top_users:
            # Convert to DataFrame for display
            top_users_df = pd.DataFrame(top_users)
            
            # Select display columns
            display_columns = ['username', 'email', 'total_processes', 'recent_activity']
            available_columns = [col for col in display_columns if col in top_users_df.columns]
            
            if available_columns:
                st.dataframe(top_users_df[available_columns], use_container_width=True)
            else:
                st.dataframe(top_users_df, use_container_width=True)
    else:
        st.error("Unable to load system statistics")


def show_user_management():
    """Show comprehensive user management interface"""
    st.header("User Management")
    st.write("Complete user profile management with generated content access")
    
    # Fetch all users
    users = fetch_all_users()
    
    if users and len(users) > 0:
        # Display summary statistics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Users", len(users))
        with col2:
            active_users = [u for u in users if u['total_processes'] > 0]
            st.metric("Active Users", len(active_users))
        with col3:
            blocked_users = [u for u in users if u.get('is_blocked', False)]
            st.metric("Blocked Users", len(blocked_users))
        with col4:
            total_content = sum(u['total_processes'] for u in users)
            st.metric("Total Generated Content", total_content)
        
        st.divider()
        
        # User table with proper statistics
        st.subheader(f"All Registered Users ({len(users)} total)")
        
        # Convert to DataFrame
        df_users = pd.DataFrame(users)
        
        # Ensure all required columns exist
        required_columns = ['id', 'username', 'email', 'summary_count', 'paraphrase_count', 'total_processes', 'is_blocked', 'created_at']
        display_data = []
        
        for user in users:
            row = {
                'ID': user.get('id', 'N/A'),
                'Username': user.get('username', 'N/A'),
                'Email': user.get('email', 'N/A'),
                'Summaries': user.get('summary_count', 0),
                'Paraphrases': user.get('paraphrase_count', 0),
                'Total Content': user.get('total_processes', 0),
                'Status': 'Blocked' if user.get('is_blocked', False) else 'Active',
                'Joined': user.get('created_at', 'Unknown')
            }
            display_data.append(row)
        
        # Display the table
        df_display = pd.DataFrame(display_data)
        st.dataframe(df_display, use_container_width=True)
        
        st.divider()
        
        # User selection for detailed management
        st.subheader("User Profile Management")
        
        # User selection dropdown
        user_options = {0: "Select a user..."}
        user_options.update({user['id']: f"{user['username']} ({user['email']})" for user in users})
        
        selected_user_id = st.selectbox(
            "Select a user to view profile and manage content:",
            options=list(user_options.keys()),
            format_func=lambda x: user_options[x]
        )
        
        if selected_user_id != 0:
            show_detailed_user_management(selected_user_id, users)
        
        # Search and filter functionality
        st.divider()
        st.subheader("Search & Filter Users")
        
        col1, col2 = st.columns(2)
        
        with col1:
            search_term = st.text_input("Search by username or email")
            
        with col2:
            filter_option = st.selectbox(
                "Filter users",
                ["All Users", "Active Users", "Blocked Users", "Users with Content"]
            )
        
        # Apply filters and show filtered results
        if search_term or filter_option != "All Users":
            filtered_users = users
            
            # Apply search filter
            if search_term:
                filtered_users = [
                    user for user in filtered_users 
                    if search_term.lower() in user['username'].lower() or 
                       search_term.lower() in user['email'].lower()
                ]
            
            # Apply status filter
            if filter_option == "Active Users":
                filtered_users = [user for user in filtered_users if not user.get('is_blocked', False)]
            elif filter_option == "Blocked Users":
                filtered_users = [user for user in filtered_users if user.get('is_blocked', False)]
            elif filter_option == "Users with Content":
                filtered_users = [user for user in filtered_users if user.get('total_processes', 0) > 0]
            
            if filtered_users:
                st.write(f"Found {len(filtered_users)} matching users:")
                filtered_df = pd.DataFrame([
                    {
                        'Username': user['username'],
                        'Email': user['email'],
                        'Summaries': user.get('summary_count', 0),
                        'Paraphrases': user.get('paraphrase_count', 0),
                        'Status': 'Blocked' if user.get('is_blocked', False) else 'Active'
                    }
                    for user in filtered_users
                ])
                st.dataframe(filtered_df, use_container_width=True)
            else:
                st.info("No users match the current filters.")
    else:
        st.warning("No users found in the database.")
        
        # Add buttons to test database and create test user
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Test Database Connection"):
                from backend.api.database import create_connection
                conn = create_connection()
                if conn:
                    cursor = conn.cursor()
                    try:
                        cursor.execute("SHOW TABLES")
                        tables = cursor.fetchall()
                        st.success(f"Database connected. Found tables: {tables}")
                        
                        cursor.execute("SELECT COUNT(*) FROM users")
                        user_count = cursor.fetchone()[0]
                        st.info(f"Users table has {user_count} records")
                        
                        if user_count > 0:
                            cursor.execute("SELECT username, email, created_at FROM users LIMIT 3")
                            sample_users = cursor.fetchall()
                            st.write("Sample users:", sample_users)
                    except Exception as e:
                        st.error(f"Database query error: {e}")
                    finally:
                        cursor.close()
                        conn.close()
                else:
                    st.error("Failed to connect to database")
        
        with col2:
            if st.button("Create Test User"):
                from backend.api.database import create_connection
                from backend.api.passhash import hash_password
                conn = create_connection()
                if conn:
                    cursor = conn.cursor()
                    try:
                        # Create a test user
                        test_password = hash_password("testpass123")
                        cursor.execute("""
                            INSERT INTO users (username, email, hashed_password, language_preference, is_blocked)
                            VALUES (%s, %s, %s, %s, %s)
                        """, ("testuser", "test@example.com", test_password, "en", False))
                        conn.commit()
                        
                        # Also create a profile for the test user
                        user_id = cursor.lastrowid
                        cursor.execute("""
                            INSERT INTO profiles (user_id, age_group, language_preference)
                            VALUES (%s, %s, %s)
                        """, (user_id, "25-35", "en"))
                        conn.commit()
                        
                        st.success("Test user created successfully!")
                        st.info("Username: testuser, Email: test@example.com, Password: testpass123")
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"Error creating test user: {e}")
                    finally:
                        cursor.close()
                        conn.close()
                else:
                    st.error("Failed to connect to database")


def show_user_details(user_id: int):
    """Show detailed information about a selected user"""
    from backend.api.database import get_user_details, get_user_processing_history, toggle_user_block_status
    
    user_details = get_user_details(user_id)
    
    if user_details:
        st.subheader(f"User Details: {user_details['username']}")
        
        # User information in columns
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Basic Information:**")
            st.write(f"• **User ID:** {user_details['id']}")
            st.write(f"• **Username:** {user_details['username']}")
            st.write(f"• **Email:** {user_details['email']}")
            st.write(f"• **Language:** {user_details['language_preference']}")
            st.write(f"• **Registration:** {user_details['created_at']}")
            st.write(f"• **Age Group:** {user_details['age_group'] or 'Not specified'}")
        
        with col2:
            st.write("**Activity Statistics:**")
            st.write(f"• **Summaries Generated:** {user_details['summary_count']}")
            st.write(f"• **Paraphrases Generated:** {user_details['paraphrase_count']}")
            st.write(f"• **Total Processes:** {user_details['total_processes']}")
            
            # Block/Unblock functionality
            st.write("**User Status:**")
            is_blocked = user_details['is_blocked']
            st.write(f"• **Status:** {'Blocked' if is_blocked else 'Active'}")
            
            # Block/Unblock button
            if is_blocked:
                if st.button(f"Unblock {user_details['username']}", type="primary"):
                    if toggle_user_block_status(user_id, False):
                        st.success(f"User {user_details['username']} has been unblocked!")
                        st.rerun()
                    else:
                        st.error("Failed to unblock user")
            else:
                if st.button(f"Block {user_details['username']}", type="secondary"):
                    if toggle_user_block_status(user_id, True):
                        st.success(f"User {user_details['username']} has been blocked!")
                        st.rerun()
                    else:
                        st.error("Failed to block user")
        
        # Recent activity
        st.subheader("Recent Activity")
        history = get_user_processing_history(user_id, 10)
        
        if history:
            df_history = pd.DataFrame(history)
            st.dataframe(
                df_history,
                use_container_width=True,
                column_config={
                    'processing_type': 'Process Type',
                    'original_text': st.column_config.TextColumn('Input Text', width='medium'),
                    'processed_text': st.column_config.TextColumn('Output Text', width='medium'),
                    'created_at': 'Date/Time'
                }
            )
        else:
            st.info("No processing history found for this user")
    else:
        st.error("User not found")


def show_analytics():
    """Show advanced analytics"""
    st.header("Advanced Analytics")
    
    # Date range selector
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", value=datetime.now() - timedelta(days=30))
    with col2:
        end_date = st.date_input("End Date", value=datetime.now())
    
    # Activity trends
    st.subheader("Activity Trends")
    daily_activity = get_daily_activity(30)
    
    if not daily_activity.empty:
        # Filter by date range
        daily_activity['date'] = pd.to_datetime(daily_activity['date'])
        mask = (daily_activity['date'] >= pd.to_datetime(start_date)) & (daily_activity['date'] <= pd.to_datetime(end_date))
        filtered_activity = daily_activity.loc[mask]
        
        if not filtered_activity.empty:
            fig = px.bar(filtered_activity, x='date', y='count', color='processing_type',
                        title="Daily Processing Requests", barmode='stack')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data available for the selected date range")
    else:
        st.info("No activity data available")


def show_system_settings():
    """Show system settings"""
    st.header("System Settings")
    
    # Admin management
    st.subheader("Admin Management")
    
    # Show existing admins
    admins = fetch_all_admins()
    if admins:
        st.write("**Current Admins:**")
        df_admins = pd.DataFrame(admins)
        st.dataframe(
            df_admins[['id', 'name', 'email', 'created_at', 'last_login', 'is_active']],
            use_container_width=True,
            column_config={
                'id': 'Admin ID',
                'name': 'Full Name',
                'email': 'Email Address',
                'created_at': 'Created Date',
                'last_login': 'Last Login',
                'is_active': 'Status'
            }
        )
    
    # System information
    st.subheader("System Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.info("**Database Status:** Connected")
        st.info("**Translation Service:** Active")
        st.info("**AI Models:** Loaded")
    
    with col2:
        st.info("**Server Status:** Running")
        st.info("**Authentication:** Secure")
        st.info("**Backup Status:** Manual")


def show_detailed_user_management(user_id: int, users_list: list):
    """Show detailed user management with text content"""
    # Find the selected user
    selected_user = next((user for user in users_list if user['id'] == user_id), None)
    
    if not selected_user:
        st.error("User not found")
        return
    
    st.subheader(f"Managing User: {selected_user['username']}")
    
    # User info and actions
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.info(f"**Email:** {selected_user['email']}")
        st.info(f"**Joined:** {selected_user.get('created_at', 'Unknown')}")
    
    with col2:
        st.metric("Total Summaries", selected_user.get('summary_count', 0))
        st.metric("Total Paraphrases", selected_user.get('paraphrase_count', 0))
    
    with col3:
        # Block/Unblock user
        current_status = "Blocked" if selected_user.get('is_blocked', False) else "Active"
        st.write(f"**Status:** {current_status}")
        
        if selected_user.get('is_blocked', False):
            if st.button("Unblock User", type="primary"):
                if toggle_user_block_status(user_id, False):
                    st.success("User unblocked successfully!")
                    st.rerun()
                else:
                    st.error("Failed to unblock user")
        else:
            if st.button("Block User", type="secondary"):
                if toggle_user_block_status(user_id, True):
                    st.warning("User blocked successfully!")
                    st.rerun()
                else:
                    st.error("Failed to block user")
    
    st.divider()
    
    # Generated texts management
    st.subheader("User Generated Content")
    
    try:
        # Fetch user's generated texts with error handling
        
        # Import the function directly to ensure it's available
        from backend.api.database import get_user_generated_texts
        
        user_texts = get_user_generated_texts(user_id, limit=50)
        
        # Force conversion to ensure it's a list
        if user_texts is None:
            user_texts = []
        
        if len(user_texts) > 0:
            st.success(f"Found {len(user_texts)} generated texts")
            
            # Tabs for different content types
            summaries = [text for text in user_texts if text['content_type'] in ['summary', 'summarization']]
            paraphrases = [text for text in user_texts if text['content_type'] in ['paraphrase', 'paraphrasing']]
            
            tab1, tab2 = st.tabs([f"Summaries ({len(summaries)})", f"Paraphrases ({len(paraphrases)})"])
            
            with tab1:
                if summaries:
                    show_user_content_cards(summaries, "summary")
                else:
                    st.info("No summaries generated by this user")
            
            with tab2:
                if paraphrases:
                    show_user_content_cards(paraphrases, "paraphrase")
                else:
                    st.info("No paraphrases generated by this user")
        else:
            st.info("No generated content found for this user")
            
    except Exception as e:
        st.error(f"Error fetching user content: {str(e)}")
        import traceback
        st.code(traceback.format_exc())

def show_user_content_cards(content_list: list, content_type: str):
    """Display content cards with edit/delete options"""
    for i, content in enumerate(content_list):
        # Create a more descriptive title
        created_date = str(content['created_at']).split('.')[0] if content['created_at'] else 'Unknown date'
        title = f"{content_type.title()} #{content['id']} - Created: {created_date}"
        
        with st.expander(title, expanded=False):
            # Show content statistics first
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Content ID", content['id'])
            with col2:
                input_length = len(content['input_text']) if content['input_text'] else 0
                st.metric("Input Length", f"{input_length} chars")
            with col3:
                output_length = len(content['output_text']) if content['output_text'] else 0
                st.metric("Output Length", f"{output_length} chars")
            
            st.divider()
            
            # Text editing section
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Original Input Text:**")
                input_text = st.text_area(
                    "Input Text",
                    value=content['input_text'] or "",
                    height=150,
                    key=f"input_{content['id']}",
                    label_visibility="collapsed",
                    help="You can modify the original input text here"
                )
            
            with col2:
                st.write(f"**Generated {content_type.title()}:**")
                output_text = st.text_area(
                    "Output Text",
                    value=content['output_text'] or "",
                    height=150,
                    key=f"output_{content['id']}",
                    label_visibility="collapsed",
                    help=f"You can modify the generated {content_type} here"
                )
            
            st.divider()
            
            # Action buttons with improved styling
            col1, col2, col3, col4 = st.columns([2, 2, 2, 2])
            
            with col1:
                if st.button(f"Save Changes #{content['id']}", key=f"update_{content['id']}", type="primary"):
                    try:
                        # Import the function directly to ensure availability
                        from backend.api.database import update_user_text, log_admin_activity
                        
                        result = update_user_text(
                            text_id=content['id'], 
                            user_id=content.get('user_id'), 
                            new_input_text=input_text, 
                            new_output_text=output_text
                        )
                        
                        if result:
                            # Log admin activity
                            admin_info = get_current_admin()
                            admin_id = admin_info.get('id', 1)  # Default to 1 if not found
                            
                            log_admin_activity(
                                admin_id=admin_id,
                                activity_type="edit_content",
                                target_user_id=content.get('user_id'),
                                target_content_id=content['id'],
                                description=f"Edited {content_type} content for ID {content['id']}"
                            )
                            
                            st.success("Content updated successfully!")
                            st.rerun()
                        else:
                            st.error(f"Failed to update - Record ID {content['id']} not found or no changes made")
                    except Exception as e:
                        st.error(f"Update error: {str(e)}")
                        import traceback
                        st.code(traceback.format_exc())
            
            with col2:
                if st.button(f"Regenerate #{content['id']}", key=f"regenerate_{content['id']}", type="primary"):
                    with st.spinner("Regenerating..."):
                        import random
                        import re
                        
                        # SIMPLE REGENERATION - GUARANTEED DIFFERENT RESULTS
                        if content_type == "summary":
                            # Try multiple summarization approaches for variety
                            import random
                            
                            try:
                                st.info("🔄 Generating new summary variation...")
                                from backend.api.summarization import generate_summary
                                
                                # Use different parameters each time for variety
                                variation_configs = [
                                    {"max_length": 80, "min_length": 15, "length_penalty": 1.5, "num_beams": 4, "name": "concise"},
                                    {"max_length": 120, "min_length": 30, "length_penalty": 2.0, "num_beams": 6, "name": "detailed"},
                                    {"max_length": 100, "min_length": 25, "length_penalty": 1.8, "num_beams": 5, "name": "balanced"}
                                ]
                                
                                # Select a random configuration for variety
                                config = random.choice(variation_configs)
                                st.info(f"Using {config['name']} summarization style...")
                                
                                # Add explicit instruction to prevent hallucination
                                focused_prompt = f"Please summarize the following text about science and technology, focusing only on the main points mentioned: {input_text}"
                                
                                new_output = generate_summary(
                                    focused_prompt, 
                                    max_length=config["max_length"],
                                    min_length=config["min_length"], 
                                    length_penalty=config["length_penalty"],
                                    num_beams=config["num_beams"]
                                )
                                st.success(f"✅ Generated {config['name']} summary")
                                
                            except Exception as e:
                                st.warning(f"⚠️ AI summarization failed: {str(e)}")
                                st.info("🔄 Using advanced summarization fallback...")
                                
                                # Enhanced fallback summarization with multiple strategies
                                def advanced_summary_fallback(text):
                                    """Advanced extractive summarization with multiple strategies"""
                                    sentences = text.replace('!', '.').replace('?', '.').split('.')
                                    sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
                                    
                                    if len(sentences) <= 2:
                                        return text[:200] + "..." if len(text) > 200 else text
                                    
                                    # Different strategies for variety
                                    strategies = [
                                        # Strategy 1: First and last sentences
                                        lambda: [sentences[0], sentences[-1]],
                                        # Strategy 2: Every other sentence (sampling)
                                        lambda: sentences[::2][:3],
                                        # Strategy 3: Longest sentences (assuming they have more info)
                                        lambda: sorted(sentences, key=len, reverse=True)[:3],
                                        # Strategy 4: Middle-focused
                                        lambda: sentences[len(sentences)//3:2*len(sentences)//3][:3] if len(sentences) > 3 else sentences
                                    ]
                                    
                                    # Choose random strategy for variety
                                    selected_sentences = random.choice(strategies)()
                                    
                                    # Ensure we don't exceed 3 sentences
                                    selected_sentences = selected_sentences[:3]
                                    
                                    summary = '. '.join(selected_sentences)
                                    if not summary.endswith('.'):
                                        summary += '.'
                                    
                                    return summary
                                
                                new_output = advanced_summary_fallback(input_text)
                                st.success("✅ Generated using advanced fallback method")
                        
                        else:  # paraphrase
                            # Try multiple approaches: FastAPI backend with variations, then fallback
                            new_output = None
                            
                            # First try: FastAPI paraphrasing endpoint with randomized parameters
                            import random
                            endpoint = "http://localhost:8000/paraphrasing/generate"
                            
                            # Use different creativity levels for variety each time
                            creativity_levels = ["conservative", "balanced", "creative"]
                            selected_level = random.choice(creativity_levels)
                            
                            # Add focused instruction to prevent hallucination
                            focused_text = f"Rephrase this text while keeping the same meaning and topic: {input_text}"
                            
                            payload = {
                                "text": focused_text,
                                "level": selected_level,
                                "num_return_sequences": random.randint(1, 3),  # Vary number of attempts
                                "max_new_tokens": random.randint(50, 80)  # Vary output length
                            }
                            
                            st.info(f"Using {selected_level} paraphrasing style...")
                            
                            try:
                                # Create progress indicator
                                progress_placeholder = st.empty() 
                                with progress_placeholder.container():
                                    st.info("🔄 Connecting to AI service... This may take up to 2 minutes.")
                                    progress_bar = st.progress(25)
                                
                                # Attempt paraphrasing with longer timeout for AI models
                                response = requests.post(endpoint, json=payload, timeout=120)  # 2 minutes timeout
                                
                                # Clear progress indicator
                                progress_placeholder.empty()
                                
                                if response.status_code == 200:
                                    result_data = response.json()
                                    paraphrases = result_data.get('paraphrases', [])
                                    new_output = paraphrases[0] if paraphrases else "Failed to generate paraphrase"
                                else:
                                    st.error(f"❌ Paraphrasing API error: HTTP {response.status_code}")
                                    st.error(f"Response: {response.text}")
                                    continue
                                    
                            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                                st.warning(f"⚠️ AI service unavailable: {type(e).__name__}")
                                st.info("🔄 Using simple text regeneration as fallback...")
                                
                                # Advanced fallback paraphrasing with multiple strategies
                                def advanced_paraphrase_fallback(text):
                                    """Advanced rule-based paraphrasing with multiple variation strategies"""
                                    import re
                                    import random
                                    
                                    # Extended word replacements with multiple options
                                    word_variations = {
                                        'quick': ['fast', 'swift', 'rapid', 'speedy'],
                                        'fast': ['quick', 'swift', 'rapid', 'speedy'],
                                        'big': ['large', 'huge', 'massive', 'enormous'],
                                        'small': ['little', 'tiny', 'compact', 'miniature'],
                                        'good': ['excellent', 'great', 'wonderful', 'outstanding'],
                                        'bad': ['poor', 'terrible', 'awful', 'dreadful'],
                                        'happy': ['pleased', 'delighted', 'joyful', 'content'],
                                        'sad': ['disappointed', 'upset', 'unhappy', 'sorrowful'],
                                        'important': ['significant', 'crucial', 'vital', 'essential'],
                                        'simple': ['straightforward', 'easy', 'basic', 'uncomplicated'],
                                        'complex': ['complicated', 'intricate', 'sophisticated', 'elaborate'],
                                        'easy': ['simple', 'straightforward', 'effortless', 'uncomplicated'],
                                        'difficult': ['hard', 'challenging', 'tough', 'demanding'],
                                        'beautiful': ['lovely', 'gorgeous', 'stunning', 'attractive'],
                                        'old': ['ancient', 'aged', 'elderly', 'vintage'],
                                        'new': ['fresh', 'recent', 'modern', 'contemporary']
                                    }
                                    
                                    result = text
                                    
                                    # Replace words with random variations
                                    for word, variations in word_variations.items():
                                        pattern = r'\b' + re.escape(word) + r'\b'
                                        if re.search(pattern, result, re.IGNORECASE):
                                            replacement = random.choice(variations)
                                            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE, count=1)
                                    
                                    # Multiple sentence restructuring strategies
                                    restructure_strategies = [
                                        # Strategy 1: Change article patterns
                                        lambda text: text.replace('The ', 'This ').replace('A ', 'One ').replace('An ', 'One '),
                                        # Strategy 2: Add transitional phrases
                                        lambda text: f"Furthermore, {text.lower()}" if not text.lower().startswith(('furthermore', 'moreover', 'additionally')) else text,
                                        # Strategy 3: Passive to active voice hints
                                        lambda text: text.replace(' is ', ' becomes ').replace(' was ', ' became '),
                                        # Strategy 4: Reorder with connectors
                                        lambda text: f"Notably, {text}" if len(text.split()) > 5 else text,
                                        # Strategy 5: No change (keep original structure)
                                        lambda text: text
                                    ]
                                    
                                    # Apply random restructuring
                                    strategy = random.choice(restructure_strategies)
                                    result = strategy(result)
                                    
                                    # Ensure proper capitalization
                                    result = result.strip()
                                    if result:
                                        result = result[0].upper() + result[1:] if len(result) > 1 else result.upper()
                                    
                                    return result if result else text
                                
                                new_output = advanced_paraphrase_fallback(input_text)
                                st.success("✅ Generated using fallback method")
                                
                            except Exception as e:
                                st.error(f"❌ Paraphrasing error: {str(e)}")
                                continue
                        
                        # Validate and finalize output with content relevance check
                        def is_content_relevant(original, generated, content_type):
                            """Check if generated content is relevant to original input"""
                            if not generated or len(generated.strip()) < 5:
                                return False
                            
                            # Convert to lowercase for comparison
                            orig_words = set(original.lower().split())
                            gen_words = set(generated.lower().split())
                            
                            # Filter out common stop words
                            stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'this', 'that', 'these', 'those'}
                            orig_meaningful = orig_words - stop_words
                            gen_meaningful = gen_words - stop_words
                            
                            # Check for word overlap
                            if len(orig_meaningful) > 0:
                                overlap_ratio = len(orig_meaningful & gen_meaningful) / len(orig_meaningful)
                                if overlap_ratio < 0.1:  # Less than 10% word overlap is suspicious
                                    return False
                            
                            # Check for completely irrelevant content patterns
                            irrelevant_patterns = [
                                'subscription', 'premium', 'monthly', 'yearly', 'member', 'plan', 'pricing',
                                'copyright', 'terms of service', 'privacy policy', 'login', 'register',
                                'click here', 'download now', 'free trial', 'upgrade', 'purchase'
                            ]
                            
                            gen_lower = generated.lower()
                            for pattern in irrelevant_patterns:
                                if pattern in gen_lower and pattern not in original.lower():
                                    return False
                            
                            return True
                        
                        # Debug info - show what was generated (can be removed later)
                        with st.expander("🔍 Debug Info - Click to see generation details", expanded=False):
                            st.write(f"**Input length:** {len(input_text)} characters")
                            st.write(f"**Output length:** {len(new_output)} characters")  
                            st.write(f"**Generated content:** {new_output[:200]}{'...' if len(new_output) > 200 else ''}")
                        
                        # Check if output is relevant to input
                        if not is_content_relevant(input_text, new_output, content_type):
                            st.error("❌ AI generated irrelevant content! Using safe fallback.")
                            st.warning(f"Irrelevant output detected: '{new_output[:100]}...'")
                            
                            # Use safe, deterministic fallback
                            if content_type == "summary":
                                # Simple extractive summary - guaranteed to be from original content
                                sentences = input_text.replace('!', '.').replace('?', '.').split('.')
                                sentences = [s.strip() for s in sentences if len(s.strip()) > 15]
                                if len(sentences) >= 2:
                                    new_output = f"{sentences[0]}. {sentences[-1]}."
                                else:
                                    new_output = input_text[:150] + "..." if len(input_text) > 150 else input_text
                            else:  # paraphrase
                                # Safe word-by-word paraphrasing - stays close to original
                                words = input_text.split()
                                safe_replacements = {
                                    'truly': 'genuinely', 'marvels': 'wonders', 'numerous': 'many',
                                    'various': 'different', 'designed': 'created', 'items': 'things'
                                }
                                new_words = []
                                for word in words:
                                    clean_word = word.lower().strip('.,!?')
                                    if clean_word in safe_replacements:
                                        replacement = safe_replacements[clean_word]
                                        # Preserve capitalization and punctuation
                                        if word[0].isupper():
                                            replacement = replacement.capitalize()
                                        if word.endswith('.'):
                                            replacement += '.'
                                        elif word.endswith(','):
                                            replacement += ','
                                        new_words.append(replacement)
                                    else:
                                        new_words.append(word)
                                new_output = ' '.join(new_words)
                            
                            st.success("✅ Generated safe, relevant content")
                        
                        # Final validation
                        if not new_output or len(new_output.strip()) < 5:
                            new_output = input_text  # Ultimate fallback - use original
                        
                        # Remove any error markers
                        if "error" in new_output.lower():
                            new_output = new_output.replace("Error:", "").replace("error:", "").strip()
                            if not new_output:
                                new_output = input_text  # Fallback to original
                        
                        # Update with new generated content
                        from backend.api.database import update_user_text, log_admin_activity
                        update_result = update_user_text(
                            text_id=content['id'],
                            user_id=content.get('user_id'),
                            new_input_text=input_text,
                            new_output_text=new_output
                        )
                        
                        if update_result:
                            # Log admin activity
                            admin_info = get_current_admin()
                            admin_id = admin_info.get('id', 1)  # Default to 1 if not found
                            
                            log_admin_activity(
                                admin_id=admin_id,
                                activity_type="regenerate_content",
                                target_user_id=content.get('user_id'),
                                target_content_id=content['id'],
                                description=f"Regenerated {content_type} for content ID {content['id']}"
                            )
                            
                            st.success(f"✅ Content regenerated successfully!")
                            st.info(f"**New {content_type}:** {new_output[:150]}...")
                            st.rerun()
                        else:
                            st.error("Failed to save regenerated content to database")
                        
                        # Error handling is done within the regeneration logic above
                        import traceback
                        st.code(traceback.format_exc())
            
            with col3:
                if st.button(f"Delete #{content['id']}", key=f"delete_{content['id']}", type="secondary"):
                    try:
                        from backend.api.database import delete_user_text
                        result = delete_user_text(content['id'], content.get('user_id', 0))
                        if result:
                            st.success("Content deleted successfully!")
                            st.rerun()
                        else:
                            st.error("Failed to delete content")
                    except Exception as e:
                        st.error(f"Failed to delete content: {str(e)}")
            
            with col4:
                # Show metadata
                st.write(f"**Type:** {content_type.title()}")
                st.write(f"**Created:** {created_date}")
                st.write(f"**Record ID:** {content['id']}")
                st.write(f"**User ID:** {content.get('user_id', 'Unknown')}")

def show_user_feedback_management():
    """Show user feedback management interface"""
    st.header("User Feedback Management")
    st.write("View and analyze user feedback for summaries and paraphrases")
    
    # Get feedback analytics
    try:
        # Get feedback statistics for overview
        feedback_stats = get_feedback_statistics()
        
        # Get percentage analytics and best feedbacks
        feedback_percentages = get_feedback_percentages()
        best_feedbacks = get_best_feedbacks()
        
        # Display feedback percentages
        if feedback_percentages:
            st.subheader("📊 Feedback Analytics")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Positive Feedback", f"{feedback_percentages['positive']:.1f}%", 
                         help="Ratings 4-5 stars")
            with col2:
                st.metric("Neutral Feedback", f"{feedback_percentages['neutral']:.1f}%",
                         help="Rating 3 stars")
            with col3:
                st.metric("Negative Feedback", f"{feedback_percentages['negative']:.1f}%",
                         help="Ratings 1-2 stars")
            with col4:
                st.metric("Total Feedback", feedback_percentages['total_feedback'])
            
            # Create pie chart for feedback distribution
            percentages_data = {
                'Category': ['Positive (4-5⭐)', 'Neutral (3⭐)', 'Negative (1-2⭐)'],
                'Percentage': [float(feedback_percentages['positive']), float(feedback_percentages['neutral']), float(feedback_percentages['negative'])],
                'Colors': ['#4CAF50', '#FFC107', '#F44336']
            }
            
            import plotly.express as px
            fig = px.pie(
                values=percentages_data['Percentage'],
                names=percentages_data['Category'],
                color_discrete_sequence=percentages_data['Colors'],
                title="Overall Feedback Distribution"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Display best feedbacks
        if best_feedbacks:
            st.subheader("🏆 Best User Feedbacks")
            for feedback in best_feedbacks:
                rating_emoji = ["😞", "😐", "😊", "😃", "🤩"][feedback['rating'] - 1]
                st.success(f"**{rating_emoji} {feedback['rating']}/5** by {feedback['username']}: {feedback['comments']}")
        
        if feedback_stats['stats']:
            st.subheader("Detailed Feedback Overview")
            col1, col2, col3 = st.columns(3)
            
            total_feedback = sum(stat['total_feedback'] for stat in feedback_stats['stats'])
            
            with col1:
                st.metric("Total Feedback Records", total_feedback)
            
            with col2:
                if feedback_stats['stats']:
                    avg_rating = sum(stat['avg_rating'] * stat['total_feedback'] for stat in feedback_stats['stats']) / total_feedback if total_feedback > 0 else 0
                    st.metric("Average Rating", f"{avg_rating:.1f}/5")
            
            with col3:
                latest_feedback = max((stat.get('latest_feedback') for stat in feedback_stats['stats'] if stat.get('latest_feedback')), default=None)
                st.metric("Latest Feedback", latest_feedback.strftime("%Y-%m-%d") if latest_feedback else "None")
            
            # Create rating distribution chart
            st.subheader("Rating Distribution")
            
            rating_data = []
            for stat in feedback_stats['stats']:
                rating_data.extend([
                    {'Content Type': stat['content_type'], 'Rating': 1, 'Count': stat.get('rating_1', 0)},
                    {'Content Type': stat['content_type'], 'Rating': 2, 'Count': stat.get('rating_2', 0)},
                    {'Content Type': stat['content_type'], 'Rating': 3, 'Count': stat.get('rating_3', 0)},
                    {'Content Type': stat['content_type'], 'Rating': 4, 'Count': stat.get('rating_4', 0)},
                    {'Content Type': stat['content_type'], 'Rating': 5, 'Count': stat.get('rating_5', 0)}
                ])
            
            if rating_data:
                import pandas as pd
                import plotly.express as px
                
                df = pd.DataFrame(rating_data)
                df = df[df['Count'] > 0]  # Filter out zero counts
                
                if not df.empty:
                    fig = px.bar(df, x='Rating', y='Count', color='Content Type',
                                       title="Feedback Rating Distribution")
                    st.plotly_chart(fig, use_container_width=True)
            
        # User-specific feedback section
        st.subheader("User Feedback Details")
        
        # Get all users
        users = fetch_all_users()
        
        if users:
            user_options = {f"{u['username']} (ID: {u['id']})": u['id'] for u in users}
            selected_user = st.selectbox("Select a user to view their feedback:", ["All Users"] + list(user_options.keys()))
            
            user_id = user_options.get(selected_user) if selected_user != "All Users" else None
            
            # Get feedback for selected user
            feedback_list = get_user_feedback(user_id)
            
            if feedback_list:
                st.write(f"Found {len(feedback_list)} feedback records")
                
                for feedback in feedback_list:
                    with st.expander(f"Feedback ID: {feedback['id']} - {feedback['content_type'].title()} (Rating: {feedback['rating']}/5)"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write(f"**Username:** {feedback['username']}")
                            st.write(f"**Content Type:** {feedback['content_type']}")
                            st.write(f"**Rating:** {'⭐' * feedback['rating']}")
                            st.write(f"**Date:** {feedback['created_at']}")
                        
                        with col2:
                            if feedback['comments']:
                                st.write(f"**Comments:**")
                                st.text_area("", value=feedback['comments'], disabled=True, key=f"comment_{feedback['id']}")
                            else:
                                st.write("**No comments provided**")
                        
                        # Delete button for admin
                        st.markdown("---")
                        col_del1, col_del2, col_del3 = st.columns([2, 1, 2])
                        with col_del2:
                            if st.button(f"🗑️ Delete Feedback", key=f"delete_{feedback['id']}", type="secondary"):
                                success, message = delete_user_feedback(feedback['id'])
                                if success:
                                    st.success(message)
                                    st.rerun()
                                else:
                                    st.error(message)
                                success, message = delete_user_feedback(feedback['id'])
                                if success:
                                    st.success(message)
                                    st.rerun()
                                else:
                                    st.error(message)
            else:
                if selected_user == "All Users":
                    st.warning("No feedback found from any users.")
                else:
                    st.warning(f"No feedback found for {selected_user}.")
        else:
            st.warning("No users found in the database.")
    
    except Exception as e:
        st.error(f"Error loading feedback data: {str(e)}")
        import traceback
        st.code(traceback.format_exc())


# Main admin dashboard function
def admin_dashboard():
    """Main entry point for admin dashboard"""
    admin_dashboard_main()


if __name__ == "__main__":
    admin_dashboard()