import os, json, requests
from dotenv import load_dotenv, set_key

def setup_new_scopes():
    load_dotenv()
    
    client_id = os.environ.get("ZOHO_CLIENT_ID")
    client_secret = os.environ.get("ZOHO_CLIENT_SECRET")
    
    print("\n--- ZOHO V2 API TOKEN UPGRADER ---")
    grant_token = input("Paste your newly generated Grant Token here: ").strip()
    
    print("\nExchanging token with Zoho...")
    url = f"https://accounts.zoho.in/oauth/v2/token"
    data = {
        "grant_type": "authorization_code",
        "client_id": client_id,
        "client_secret": client_secret,
        "code": grant_token
    }
    
    resp = requests.post(url, data=data)
    result = resp.json()
    
    if "error" in result:
        print(f"❌ ERROR: {result.get('error')} - {result.get('message', 'Invalid grant token')}")
    else:
        refresh_token = result.get("refresh_token")
        access_token = result.get("access_token")
        
        # 1. Update .env file
        set_key(".env", "ZOHO_REFRESH_TOKEN", refresh_token)
        print("✔ Updated .env with new ZOHO_REFRESH_TOKEN")
        
        # 2. Re-write zoho_token.json
        with open("zoho_token.json", "w") as f:
            json.dump({"access_token": access_token}, f, indent=4)
        print("✔ Generated new zoho_token.json with UPDATE scopes")
        
        print("\n🎉 Token upgrade successful! You can now use the Batch Upload & Excel Import features without HTTP 401 errors.")

if __name__ == "__main__":
    setup_new_scopes()
