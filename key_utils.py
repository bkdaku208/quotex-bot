
import random
import string
import json
from datetime import datetime, timedelta

# File path for key storage
KEYS_FILE = "attached_assets/keys.json"

def load_keys():
    try:
        with open(KEYS_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_keys(keys):
    with open(KEYS_FILE, 'w') as f:
        json.dump(keys, f, indent=2)

def generate_key(duration_days):
    keys = load_keys()
    key = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
    
    keys[key] = {
        "duration_days": duration_days,
        "expiry_date": (datetime.now() + timedelta(days=duration_days)).isoformat(),
        "used_by": None
    }
    
    save_keys(keys)
    return key

def check_key_valid(key, user_id):
    keys = load_keys()
    if key not in keys:
        return False, "Invalid key. Please check your key and try again."
        
    key_data = keys[key]
    # Allow same user to reuse their key
    if key_data["used_by"] is not None and key_data["used_by"] != user_id:
        return False, "This key has already been used by another user."
        
    expiry = datetime.fromisoformat(key_data["expiry_date"])
    if datetime.now() > expiry:
        del keys[key]
        save_keys(keys)
        return False, "This key has expired. Please request a new one."
    
    # Only update used_by if it's not already set
    if key_data["used_by"] is None:
        key_data["used_by"] = user_id
        save_keys(keys)
    return True, f"Key activated! Valid until {expiry.strftime('%Y-%m-%d %H:%M:%S')}."
