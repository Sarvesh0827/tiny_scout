#!/usr/bin/env python3
"""
Setup script for TinyScout Claude API Key
"""
import os

print("=" * 60)
print("TinyScout - Claude API Key Setup")
print("=" * 60)
print()
print("Please enter your Anthropic API key.")
print("You can get one from: https://console.anthropic.com/")
print()

api_key = input("Enter your ANTHROPIC_API_KEY: ").strip()

if not api_key:
    print("❌ No API key provided. Exiting.")
    exit(1)

# Create .env file
env_path = os.path.join(os.path.dirname(__file__), ".env")

with open(env_path, "w") as f:
    f.write(f"# Anthropic API Key for Claude\n")
    f.write(f"ANTHROPIC_API_KEY={api_key}\n")

print()
print("✅ API key saved to .env file")
print()
print("You can now run the application with:")
print("  export PYTHONPATH=$PYTHONPATH:. && streamlit run ui/dashboard.py")
print()
