from pymongo import MongoClient
import os
from dotenv import load_dotenv
import ssl

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")

# Create MongoDB client with robust SSL handling
def create_mongo_client():
    """Create MongoDB client with multiple fallback options"""
    if not MONGO_URI:
        raise ValueError("MONGO_URI environment variable not set")
    
    # Try different connection methods
    connection_methods = [
        # Method 1: Default connection
        lambda: MongoClient(MONGO_URI),
        
        # Method 2: TLS with invalid certs allowed
        lambda: MongoClient(MONGO_URI, tls=True, tlsAllowInvalidCertificates=True),
        
        # Method 3: Direct connection with timeout
        lambda: MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000, connectTimeoutMS=10000),
        
        # Method 4: Retry writes enabled
        lambda: MongoClient(MONGO_URI, retryWrites=True, retryReads=True),
    ]
    
    for i, method in enumerate(connection_methods, 1):
        try:
            print(f"🔄 Trying MongoDB connection method {i}...")
            client = method()
            # Test the connection
            client.admin.command('ping')
            print(f"✅ MongoDB connected successfully with method {i}")
            return client
        except Exception as e:
            print(f"❌ Method {i} failed: {str(e)[:100]}...")
            continue
    
    # If all methods fail, create a client anyway (it might work for some operations)
    print("⚠️ All connection methods failed, creating fallback client")
    return MongoClient(MONGO_URI, serverSelectionTimeoutMS=1000)

# Create the client
client = create_mongo_client()

db = client["sidequest_db"]  # one DB for everything

# Collections
user_profiles_col = db["user_profiles"]  # used app-wide
activities_col = db["activities"]        # optional Sidequest cache