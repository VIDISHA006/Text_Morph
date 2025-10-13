import httpx
import streamlit as st

API_URL = "http://localhost:8000"  # Replace with your backend URL



def get_profile():
    """
    Fetches the current user profile from backend /profile (GET).
    Uses JWT access token stored in session_state.
    """
    token = st.session_state.get('access_token')
    headers = {"Authorization": f"Bearer {st.session_state.get('access_token')}"}
    try:
        response = httpx.get(f"{API_URL}/profile/read", headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            st.error("Profile not found. Please contact support.")
        else:
            try:
                error_detail = e.response.json().get('detail', 'Unknown error')
            except:
                error_detail = f"HTTP {e.response.status_code} error"
            st.error(f"Error fetching profile: {error_detail}")
        return None
    except Exception as e:
        error_msg = str(e)
        if "timeout" in error_msg.lower():
            st.error("Request timed out. Please try again.")
        else:
            st.error(f"Error fetching profile: {error_msg}")
        return None

def update_profile(age_group, language_preference):
    """
    Sends profile updates to backend /profile (PUT).
    """
    headers = {"Authorization": f"Bearer {st.session_state.get('access_token')}"}
    payload = {"age_group": str(age_group), "language_preference": language_preference}
    try:
        response = httpx.put(f"{API_URL}/profile/update", json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        return True
    except httpx.HTTPStatusError as e:
        try:
            error_detail = e.response.json().get('detail', 'Unknown error')
        except:
            error_detail = f"HTTP {e.response.status_code} error"
        st.error(f"Error updating profile: {error_detail}")
        return False
    except Exception as e:
        error_msg = str(e)
        if "timeout" in error_msg.lower():
            st.error("Request timed out. Please try again.")
        else:
            st.error(f"Error updating profile: {error_msg}")
        return False
def profile_page():
    # Add some spacing to avoid UI overlap
    st.write("")
    st.write("")
    st.write("")
    
    # Profile page title
    st.markdown("### User Profile Settings")
    st.write("")
    
    # Initialize session state values once
    if "profile_loaded" not in st.session_state or not st.session_state.profile_loaded:
        profile = get_profile()
        if not profile:
            st.error("Could not load profile.")
            return
        try:
            age_value = int(profile.get("age_group", 18))
        except (ValueError, TypeError):
            age_value = 18
        st.session_state.age_group = age_value
        st.session_state.language_preference = profile.get("language_preference", "English")
        st.session_state.profile_loaded = True

    age_min = 18
    age_max = 65

    st.markdown("**Age Group:**")
    age_group = st.slider("Select your age", min_value=age_min, max_value=age_max, value=st.session_state.age_group)
    
    st.write("")  # Add spacing
    st.markdown("**Language Preference:**")
    language_preference = st.radio("Choose your preferred language", options=["English", "Hindi"], index=0 if st.session_state.language_preference == "English" else 1)

    st.write("")  # Add spacing
    st.markdown("**Current Settings:**")
    st.info(f"**Age:** {age_group} years")
    st.info(f"**Language:** {language_preference}")

    # Update session state with current widget values on interaction, but do NOT update backend yet
    st.session_state.age_group = age_group
    st.session_state.language_preference = language_preference

    st.write("")  # Add spacing before button
    if st.button("Save Profile", type="primary"):
        success = update_profile(age_group, language_preference)
        if success:
            st.success("Profile updated successfully!")  