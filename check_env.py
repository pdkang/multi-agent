import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def check_env_vars():
    """Check if required environment variables are set"""
    required_vars = ['OPENAI_API_KEY', 'ARES_API_KEY']
    missing_vars = []
    
    for var in required_vars:
        value = os.getenv(var)
        if value is None:
            missing_vars.append(var)
        else:
            # Show first 4 characters of the key for verification
            print(f"{var} is set: {value[:4]}...")
    
    if missing_vars:
        print("\nMissing environment variables:")
        for var in missing_vars:
            print(f"- {var}")
        print("\nPlease set these variables in your .env file or system environment.")
    else:
        print("\nAll required environment variables are set!")

if __name__ == "__main__":
    check_env_vars() 