"""
Add Variables to Railway - Helper Script

This script will:
1. Generate your string session
2. Read all variables from .env
3. Create a file with all Railway CLI commands
4. Show you exactly what to do
"""

import asyncio
import os
from dotenv import load_dotenv
from telethon.sync import TelegramClient
from telethon.sessions import StringSession

load_dotenv()

API_ID = os.getenv('TELEGRAM_API_ID')
API_HASH = os.getenv('TELEGRAM_API_HASH')
PHONE_NUMBER = os.getenv('TELEGRAM_PHONE')

async def generate_and_create_commands():
    """Generate string session and create Railway commands"""
    
    print("=" * 70)
    print("🚀 Railway Variables Setup - Automated")
    print("=" * 70)
    print()
    print("Step 1: Generating Telegram String Session")
    print("-" * 70)
    print(f"📱 Phone: {PHONE_NUMBER}")
    print(f"🔑 API ID: {API_ID}")
    print()
    
    # Generate string session
    client = TelegramClient(StringSession(), API_ID, API_HASH)
    
    try:
        await client.start(phone=PHONE_NUMBER)
        string_session = client.session.save()
        
        print()
        print("✅ String session generated successfully!")
        print()
        
        await client.disconnect()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return
    
    print("Step 2: Reading .env file")
    print("-" * 70)
    
    # Read .env file
    env_vars = {}
    if os.path.exists('.env'):
        with open('.env', 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip("'\"")
                    if value:  # Only add non-empty values
                        env_vars[key] = value
    
    # Add string session
    env_vars['TELEGRAM_STRING_SESSION'] = string_session
    
    print(f"✅ Found {len(env_vars)} variables")
    print()
    
    print("Step 3: Creating Railway commands")
    print("-" * 70)
    
    # Create Railway CLI commands file
    commands = []
    commands.append("# Railway CLI Commands")
    commands.append("# Copy and paste these commands one by one")
    commands.append("")
    commands.append("# First, login to Railway:")
    commands.append("railway login")
    commands.append("")
    commands.append("# Link to your project:")
    commands.append("railway link")
    commands.append("")
    commands.append("# Add all variables:")
    
    for key, value in env_vars.items():
        # Escape special characters for command line
        escaped_value = value.replace('"', '\\"').replace('$', '\\$')
        commands.append(f'railway variables --set {key}="{escaped_value}"')
    
    commands.append("")
    commands.append("# Done! Now deploy:")
    commands.append("railway up")
    
    # Save to file
    with open('railway_commands.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(commands))
    
    print("✅ Created railway_commands.txt")
    print()
    
    # Also create a .env.railway file for manual copy-paste
    railway_env_lines = []
    railway_env_lines.append("# Railway Environment Variables")
    railway_env_lines.append("# Copy these to Railway Dashboard > Variables")
    railway_env_lines.append("")
    
    for key, value in env_vars.items():
        railway_env_lines.append(f"{key}={value}")
    
    with open('.env.railway', 'w', encoding='utf-8') as f:
        f.write('\n'.join(railway_env_lines))
    
    print("✅ Created .env.railway")
    print()
    
    print("=" * 70)
    print("📋 OPTION 1: Use Railway CLI (Recommended)")
    print("=" * 70)
    print()
    print("1. Install Railway CLI:")
    print("   Visit: https://docs.railway.app/develop/cli#install")
    print()
    print("2. Run these commands:")
    print("   railway login")
    print("   railway link")
    print()
    print("3. Copy commands from railway_commands.txt and run them")
    print()
    
    print("=" * 70)
    print("📋 OPTION 2: Use Railway Dashboard (Easier)")
    print("=" * 70)
    print()
    print("1. Go to: https://railway.app/dashboard")
    print("2. Click your project")
    print("3. Click 'Variables' tab")
    print("4. Open .env.railway file (created in your project folder)")
    print("5. Copy each variable and add to Railway:")
    print("   - Click '+ New Variable'")
    print("   - Paste variable name and value")
    print("   - Click 'Add'")
    print("   - Repeat for all variables")
    print()
    
    print("=" * 70)
    print("🔑 Your String Session (IMPORTANT!):")
    print("=" * 70)
    print()
    print(f"TELEGRAM_STRING_SESSION={string_session}")
    print()
    print("⚠️  Save this somewhere safe!")
    print()
    
    print("=" * 70)
    print("✅ Setup Complete!")
    print("=" * 70)
    print()
    print("Files created:")
    print("  ✓ railway_commands.txt - CLI commands")
    print("  ✓ .env.railway - Variables for dashboard")
    print()
    print("Next: Add variables to Railway using Option 1 or 2 above")
    print()

if __name__ == '__main__':
    asyncio.run(generate_and_create_commands())
