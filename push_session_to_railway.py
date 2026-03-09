#!/usr/bin/env python3
"""
Push Telegram session files directly to Railway
This script uploads the session files to Railway so the bot can connect to Telegram
"""
import os
import subprocess
import sys

def check_railway_cli():
    """Check if Railway CLI is installed"""
    try:
        result = subprocess.run(['railway', '--version'], capture_output=True, text=True)
        print(f"✅ Railway CLI found: {result.stdout.strip()}")
        return True
    except FileNotFoundError:
        print("❌ Railway CLI not found!")
        print("\n📥 Install Railway CLI:")
        print("   npm install -g @railway/cli")
        print("   or visit: https://docs.railway.app/develop/cli")
        return False

def check_session_files():
    """Check if session files exist"""
    session_file = 'session_testpob1234.session'
    journal_file = 'session_testpob1234.session-journal'
    
    files_exist = []
    
    if os.path.exists(session_file):
        size = os.path.getsize(session_file)
        print(f"✅ Found {session_file} ({size} bytes)")
        files_exist.append(session_file)
    else:
        print(f"❌ {session_file} not found!")
    
    if os.path.exists(journal_file):
        size = os.path.getsize(journal_file)
        print(f"✅ Found {journal_file} ({size} bytes)")
        files_exist.append(journal_file)
    else:
        print(f"⚠️  {journal_file} not found (optional)")
    
    return files_exist

def read_file_as_base64(filepath):
    """Read file and encode as base64"""
    import base64
    with open(filepath, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode('utf-8')

def push_to_railway():
    """Push session files to Railway as environment variables"""
    print("\n" + "="*60)
    print("🚂 PUSHING SESSION FILES TO RAILWAY")
    print("="*60)
    
    # Check Railway CLI
    if not check_railway_cli():
        return False
    
    print("\n📁 Checking session files...")
    files = check_session_files()
    
    if not files:
        print("\n❌ No session files found!")
        print("\n💡 Make sure you have run the bot locally first to create session files")
        return False
    
    print("\n🔐 Encoding session files to base64...")
    
    # Encode session file
    if 'session_testpob1234.session' in files:
        session_b64 = read_file_as_base64('session_testpob1234.session')
        print(f"✅ Encoded session file ({len(session_b64)} chars)")
    else:
        print("❌ Cannot proceed without main session file")
        return False
    
    # Encode journal file if exists
    journal_b64 = None
    if 'session_testpob1234.session-journal' in files:
        journal_b64 = read_file_as_base64('session_testpob1234.session-journal')
        print(f"✅ Encoded journal file ({len(journal_b64)} chars)")
    
    print("\n🚂 Uploading to Railway...")
    print("⏳ This may take a moment...\n")
    
    # Set TELEGRAM_SESSION_FILE
    try:
        cmd = ['railway', 'variables', 'set', f'TELEGRAM_SESSION_FILE={session_b64}']
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ TELEGRAM_SESSION_FILE uploaded successfully")
        else:
            print(f"❌ Failed to upload TELEGRAM_SESSION_FILE")
            print(f"   Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error uploading TELEGRAM_SESSION_FILE: {e}")
        return False
    
    # Set TELEGRAM_SESSION_JOURNAL if exists
    if journal_b64:
        try:
            cmd = ['railway', 'variables', 'set', f'TELEGRAM_SESSION_JOURNAL={journal_b64}']
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ TELEGRAM_SESSION_JOURNAL uploaded successfully")
            else:
                print(f"⚠️  Failed to upload TELEGRAM_SESSION_JOURNAL (optional)")
                print(f"   Error: {result.stderr}")
        except Exception as e:
            print(f"⚠️  Error uploading TELEGRAM_SESSION_JOURNAL: {e}")
    
    print("\n" + "="*60)
    print("✅ SESSION FILES UPLOADED TO RAILWAY!")
    print("="*60)
    print("\n💡 Next steps:")
    print("   1. Deploy your code: railway up")
    print("   2. Check logs: railway logs")
    print("   3. The bot should now connect to Telegram automatically!")
    print("\n🎯 The bot will recreate session files from environment variables")
    
    return True

def main():
    """Main function"""
    print("\n" + "="*60)
    print("🚂 RAILWAY SESSION FILE UPLOADER")
    print("="*60)
    print("\nThis script will:")
    print("  1. Check for Telegram session files")
    print("  2. Encode them to base64")
    print("  3. Upload to Railway as environment variables")
    print("  4. Your bot will recreate them on Railway")
    print("\n" + "="*60)
    
    # Check if user is logged in to Railway
    print("\n🔐 Checking Railway authentication...")
    try:
        result = subprocess.run(['railway', 'whoami'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Logged in as: {result.stdout.strip()}")
        else:
            print("❌ Not logged in to Railway!")
            print("\n💡 Login first:")
            print("   railway login")
            return
    except Exception as e:
        print(f"❌ Error checking Railway auth: {e}")
        return
    
    # Check if in a Railway project
    print("\n📦 Checking Railway project...")
    try:
        result = subprocess.run(['railway', 'status'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Railway project detected")
        else:
            print("❌ Not in a Railway project!")
            print("\n💡 Link your project first:")
            print("   railway link")
            return
    except Exception as e:
        print(f"❌ Error checking Railway project: {e}")
        return
    
    # Push session files
    success = push_to_railway()
    
    if success:
        print("\n🎉 All done! Your bot should now work on Railway!")
    else:
        print("\n❌ Upload failed. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
