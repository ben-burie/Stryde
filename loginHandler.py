from supabase import create_client, Client
from dotenv import load_dotenv
import os

load_dotenv()

SUPABASE_URL = os.getenv('DB_URL')
SUPABASE_KEY = os.getenv('DB_KEY')

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def login_user(email: str, password: str):
    try:
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        print(f"✓ User {email} logged in successfully")
        return response
    except Exception as e:
        print(f"✗ Login failed for {email}: {str(e)}")
        return None


def verify_token(token: str):
    try:
        response = supabase.auth.get_user(token)
        user = response.user
        print(f"Token verified for user {user.email}")
        return user
    except Exception as e:
        print(f"Token verification failed: {str(e)}")
        return None


def signup_user(email: str, password: str):
    try:
        response = supabase.auth.sign_up({
            "email": email,
            "password": password
        })
        print(f"User {email} signed up successfully")
        return response
    except Exception as e:
        print(f"Signup failed for {email}: {str(e)}")
        return None