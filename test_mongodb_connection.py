"""
Test MongoDB Connection Script
Run this to diagnose MongoDB connection issues
"""
import os
from dotenv import load_dotenv
from pymongo import MongoClient
from urllib.parse import quote_plus
import certifi

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")

if not MONGO_URI:
    print("❌ MONGO_URI not found in .env file")
    exit(1)

print("="*60)
print("MongoDB Connection Test")
print("="*60)
print(f"\nConnection String: {MONGO_URI[:50]}...")  # Show first 50 chars only

# Check if it's Atlas or local
if MONGO_URI.startswith("mongodb+srv://"):
    print("✓ Detected: MongoDB Atlas connection")
    
    # Parse connection string to check format
    try:
        # Extract parts
        uri_parts = MONGO_URI.replace("mongodb+srv://", "").split("@")
        if len(uri_parts) == 2:
            creds = uri_parts[0]
            rest = uri_parts[1]
            if ":" in creds:
                username = creds.split(":")[0]
                password = creds.split(":")[1]
                print(f"✓ Username: {username}")
                print(f"✓ Password: {'*' * len(password)} ({len(password)} chars)")
            else:
                print("⚠️  Warning: No password found in connection string")
        else:
            print("⚠️  Warning: Connection string format might be incorrect")
    except:
        pass
    
    # Check for required parameters
    if "retryWrites" not in MONGO_URI:
        print("⚠️  Warning: 'retryWrites=true' not in connection string")
    if "w=majority" not in MONGO_URI:
        print("⚠️  Warning: 'w=majority' not in connection string")
else:
    print("✓ Detected: Local MongoDB connection")

print("\n" + "="*60)
print("Attempting connection...")
print("="*60)

try:
    if MONGO_URI.startswith("mongodb+srv://"):
        # Ensure proper format
        if "retryWrites" not in MONGO_URI:
            separator = "&" if "?" in MONGO_URI else "?"
            MONGO_URI = f"{MONGO_URI}{separator}retryWrites=true&w=majority"
        
        # Try with certifi certificates (fixes Python 3.13 SSL issues)
        try:
            client = MongoClient(
                MONGO_URI,
                serverSelectionTimeoutMS=30000,
                connectTimeoutMS=30000,
                socketTimeoutMS=30000,
                tlsCAFile=certifi.where()  # Use certifi certificates
            )
        except Exception as cert_err:
            print(f"⚠️  Certifi approach failed, trying without: {cert_err}")
            client = MongoClient(
                MONGO_URI,
                serverSelectionTimeoutMS=30000,
                connectTimeoutMS=30000,
                socketTimeoutMS=30000
            )
    else:
        client = MongoClient(
            MONGO_URI,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
            socketTimeoutMS=5000
        )
    
    # Test connection
    client.admin.command('ping')
    print("\n✅ SUCCESS! Connected to MongoDB!")
    
    # Get database info
    db_name = os.getenv("DB_NAME", "expen")
    db = client.get_database(db_name)
    print(f"✓ Database: {db_name}")
    
    # List collections
    collections = db.list_collection_names()
    print(f"✓ Collections found: {len(collections)}")
    if collections:
        print(f"  - {', '.join(collections)}")
    
    client.close()
    print("\n✅ Connection test passed!")
    
except Exception as e:
    error_msg = str(e)
    print(f"\n❌ CONNECTION FAILED!")
    print(f"\nError: {error_msg}")
    
    print("\n" + "="*60)
    print("TROUBLESHOOTING:")
    print("="*60)
    
    if "SSL" in error_msg or "TLS" in error_msg:
        print("\n🔧 SSL/TLS Error Solutions:")
        print("1. Verify your connection string uses: mongodb+srv://")
        print("2. Check MongoDB Atlas Network Access - whitelist your IP")
        print("3. If password has special characters, URL-encode them:")
        print("   Example: @ becomes %40, # becomes %23")
        print("4. Try regenerating your connection string from Atlas dashboard")
    
    if "authentication" in error_msg.lower():
        print("\n🔧 Authentication Error Solutions:")
        print("1. Verify username and password in MongoDB Atlas")
        print("2. Check Database Access → Users in Atlas dashboard")
        print("3. Make sure user has read/write permissions")
        print("4. URL-encode special characters in password")
    
    if "timeout" in error_msg.lower():
        print("\n🔧 Timeout Error Solutions:")
        print("1. Check your internet connection")
        print("2. Verify MongoDB Atlas cluster is running (not paused)")
        print("3. Check firewall/antivirus settings")
        print("4. Try whitelisting 0.0.0.0/0 in Network Access (dev only)")
    
    print("\n" + "="*60)
    print("CONNECTION STRING FORMAT:")
    print("="*60)
    print("mongodb+srv://username:password@cluster.mongodb.net/database?retryWrites=true&w=majority")
    print("\nExample:")
    print("MONGO_URI=mongodb+srv://myuser:mypass123@cluster0.xxxxx.mongodb.net/expenzo?retryWrites=true&w=majority")
    print("="*60)

