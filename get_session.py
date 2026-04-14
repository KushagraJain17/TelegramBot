import instaloader
import os
from dotenv import load_dotenv

load_dotenv()

def generate_session():
    L = instaloader.Instaloader()
    USER = os.getenv("INSTA_USER")
    PASS = os.getenv("INSTA_PASS")

    if not USER or not PASS:
        print("❌ Error: INSTA_USER or INSTA_PASS not found in .env")
        return

    print(f"🔐 Attempting interactive login for: {USER}")
    
    # This handler allows you to enter a 2FA code if prompted
    def fa_handler():
        return input("🔑 Enter 2FA code from your Authenticator/Email/SMS: ")

    try:
        # We use the internal _login method to handle 2FA more easily
        L.two_factor_handler = fa_handler
        L.login(USER, PASS)
        
        L.save_session_to_file(filename="insta_session")
        print("\n✅ SUCCESS! 'insta_session' has been created.")
        print("You can now start your bot.")
        
    except Exception as e:
        print(f"\n❌ Login Failed: {e}")
        print("\nIf you changed your password recently:")
        print("1. Log in to Instagram.com in your browser FIRST.")
        print("2. Ensure you can see your feed.")
        print("3. Then run this script again.")

if __name__ == "__main__":
    generate_session()
