#!/usr/bin/env python3
"""
Setup script for TinyFish API Key
"""
import os

print("=" * 60)
print("TinyScout - TinyFish API Key Setup")
print("=" * 60)
print()
print("Please enter your TinyFish API key.")
print()

api_key = input("Enter your TINYFISH_API_KEY: ").strip()

if not api_key:
    print("❌ No API key provided. Exiting.")
    exit(1)

# Read existing .env
env_path = os.path.join(os.path.dirname(__file__), ".env")
env_lines = []

if os.path.exists(env_path):
    with open(env_path, "r") as f:
        env_lines = f.readlines()

# Remove any existing TINYFISH_API_KEY lines
env_lines = [line for line in env_lines if not line.startswith("TINYFISH_API_KEY")]

# Add new key
env_lines.append(f"\n# TinyFish API Key\n")
env_lines.append(f"TINYFISH_API_KEY={api_key}\n")

# Write back
with open(env_path, "w") as f:
    f.writelines(env_lines)

print()
print("✅ TinyFish API key saved to .env file")
print()
print("Next steps:")
print("1. Install TinyFish SDK (if not already installed)")
print("2. Switch to TinyFish backend:")
print("   - Edit .env and change: RETRIEVER_BACKEND=tinyfish")
print()
print("Or test with HTTP backend first:")
print("  export PYTHONPATH=$PYTHONPATH:. && streamlit run ui/dashboard.py")
print()
