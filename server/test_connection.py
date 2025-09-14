#!/usr/bin/env python3
"""
Test MongoDB connection when actually used
"""
import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

def test_connection():
    MONGO_URI = os.getenv("MONGO_URI")
    print(f"Testing connection to: {MONGO_URI[:50]}...")
    
    try:
        # Try different connection methods
        print("Method 1: Basic connection")
        client = MongoClient(MONGO_URI)
        client.admin.command('ping')
        print("✅ Basic connection successful!")
        return True
    except Exception as e:
        print(f"❌ Basic connection failed: {e}")
    
    try:
        print("Method 2: With TLS")
        client = MongoClient(MONGO_URI, tls=True)
        client.admin.command('ping')
        print("✅ TLS connection successful!")
        return True
    except Exception as e:
        print(f"❌ TLS connection failed: {e}")
    
    try:
        print("Method 3: With TLS and invalid certs allowed")
        client = MongoClient(MONGO_URI, tls=True, tlsAllowInvalidCertificates=True)
        client.admin.command('ping')
        print("✅ TLS with invalid certs connection successful!")
        return True
    except Exception as e:
        print(f"❌ TLS with invalid certs connection failed: {e}")
    
    return False

if __name__ == "__main__":
    test_connection()
