import httpx
import streamlit as st

API_URL = "http://localhost:8000"  # Replace with your backend URL

def login(email: str, password: str):
    """
    Calls your backend /login endpoint with email and password.
    On success, stores the JWT access token in Streamlit session_state.
    """
    login_data = {"email": email, "password": password}
    try:
        response = httpx.post(f"{API_URL}/auth/login", json=login_data, timeout=10)
        response.raise_for_status()
        data = response.json()
        token = data.get("access_token")
        user = data.get("user")
        if token and user:
            st.session_state["access_token"] = token
            st.session_state["logged_in"] = True
            st.session_state["email"] = user.get("email")
            st.session_state["user_id"]= user.get("id")
            print("login returning:", True, user)
            return True, user
        else:
            return False, None
    except httpx.HTTPError as e:
        # Check if it's a 4xx/5xx HTTP error (like 404, 401, etc.)
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_detail = e.response.json().get('detail', f"HTTP {e.response.status_code}")
                st.error(f"Login failed: {error_detail}")
            except:
                st.error(f"Login failed with status code: {e.response.status_code}")
        else:
            # This is likely a connection error
            st.error("Failed to connect to the backend server. Please ensure the backend is running.")
        return False, None
    except Exception:
        st.error("An unexpected error occurred during login.")
        return False, None

def logout():
    """
    Clears Streamlit session state.
    """
    st.session_state.clear()