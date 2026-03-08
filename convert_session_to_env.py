"""
Convert Telegram Session File to Environment Variable

This script:
1. Reads your session file
2. Converts it to base64
3. Creates environment variable that Railway can use
4. Railway will recreate the file from the variable
"""

import base64
import os

def convert_session_to_base64():
    """Convert session file to base64 string"""
    
    session_file = 'session_testpob1234.session'
    
    print("=" * 70)
    print("🔐 Session File to Environment Variable Converter")
    print("=" * 70)
    print()
    
    if not os.path.exists(session_file):
        print(f"❌ Error: {session_file} not found!")
        print()
        print("Please make sure you have:")
        print("1. Run the bot locally at least once")
        print("2. Completed OTP verification")
        print("3. The session file exists in the project folder")
        return None
    
    print(f"✅ Found {session_file}")
    print()
    
    # Read session file
    with open(session_file, 'rb') as f:
        session_data = f.read()
    
    # Convert to base64
    session_base64 = base64.b64encode(session_data).decode('utf-8')
    
    print(f"✅ Converted to base64 ({len(session_base64)} characters)")
    print()
    
    # Also check for journal file
    journal_file = 'session_testpob1234.session-journal'
    journal_base64 = None
    
    if os.path.exists(journal_file):
        with open(journal_file, 'rb') as f:
            journal_data = f.read()
        journal_base64 = base64.b64encode(journal_data).decode('utf-8')
        print(f"✅ Also found and converted {journal_file}")
        print()
    
    return session_base64, journal_base64

def create_env_file(session_base64, journal_base64):
    """Create .env.railway with session data"""
    
    # Read existing .env
    env_vars = {}
    if os.path.exists('.env'):
        with open('.env', 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip("'\"")
                    if value:
                        env_vars[key] = value
    
    # Add session data
    env_vars['TELEGRAM_SESSION_FILE'] = session_base64
    if journal_base64:
        env_vars['TELEGRAM_SESSION_JOURNAL'] = journal_base64
    
    # Create .env.railway
    with open('.env.railway', 'w', encoding='utf-8') as f:
        f.write("# Railway Environment Variables\n")
        f.write("# Copy these to Railway Dashboard > Variables\n\n")
        
        for key, value in env_vars.items():
            f.write(f"{key}={value}\n")
    
    print("✅ Created .env.railway with session data")
    print()

def create_railway_commands(session_base64, journal_base64):
    """Create Railway CLI commands"""
    
    # Read existing .env
    env_vars = {}
    if os.path.exists('.env'):
        with open('.env', 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip("'\"")
                    if value:
                        env_vars[key] = value
    
    # Add session data
    env_vars['TELEGRAM_SESSION_FILE'] = session_base64
    if journal_base64:
        env_vars['TELEGRAM_SESSION_JOURNAL'] = journal_base64
    
    commands = []
    commands.append("# Railway CLI Commands")
    commands.append("# Run these commands to add all variables")
    commands.append("")
    commands.append("railway login")
    commands.append("railway link")
    commands.append("")
    
    for key, value in env_vars.items():
        # Escape for command line
        escaped_value = value.replace('"', '\\"').replace('$', '\\$')
        commands.append(f'railway variables --set {key}="{escaped_value}"')
    
    commands.append("")
    commands.append("railway up")
    
    with open('railway_commands.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(commands))
    
    print("✅ Created railway_commands.txt")
    print()

if __name__ == '__main__':
    result = convert_session_to_base64()
    
    if result:
        session_base64, journal_base64 = result
        
        create_env_file(session_base64, journal_base64)
        create_railway_commands(session_base64, journal_base64)
        
        print("=" * 70)
        print("📋 Next Steps:")
        print("=" * 70)
        print()
        print("OPTION 1: Railway Dashboard (Recommended)")
        print("-" * 70)
        print("1. Go to: https://railway.app/dashboard")
        print("2. Click your project")
        print("3. Click 'Variables' tab")
        print("4. Open .env.railway file")
        print("5. Copy each variable to Railway:")
        print("   - Click '+ New Variable'")
        print("   - Paste name and value")
        print("   - Click 'Add'")
        print()
        print("OPTION 2: Railway CLI")
        print("-" * 70)
        print("1. Install Railway CLI: https://docs.railway.app/develop/cli")
        print("2. Run commands from railway_commands.txt")
        print()
        print("=" * 70)
        print("⚠️  IMPORTANT:")
        print("=" * 70)
        print()
        print("The session file has been converted to base64.")
        print("Railway will recreate the file from the environment variable.")
        print()
        print("Variables created:")
        print("  ✓ TELEGRAM_SESSION_FILE - Main session file")
        if journal_base64:
            print("  ✓ TELEGRAM_SESSION_JOURNAL - Journal file")
        print()
        print("=" * 70)
        print("✅ Conversion Complete!")
        print("=" * 70)
