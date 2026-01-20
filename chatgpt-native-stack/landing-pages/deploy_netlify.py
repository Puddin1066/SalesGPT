"""
Deploy landing pages to Netlify (instant, free hosting).

Perfect for:
- Fast deployment without HubSpot CMS Hub
- A/B testing different versions
- Custom domain support
- Auto SSL/HTTPS
- Forms with Netlify Forms (free)
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, List


def create_netlify_config():
    """Create netlify.toml configuration."""
    
    config = """# Netlify Configuration
[build]
  publish = "output/html"
  
[[redirects]]
  from = "/medical"
  to = "/medical_landing_page_a.html"
  status = 200

[[redirects]]
  from = "/legal"
  to = "/legal_landing_page_a.html"
  status = 200

[[redirects]]
  from = "/realestate"
  to = "/realestate_landing_page_a.html"
  status = 200

[[redirects]]
  from = "/agencies"
  to = "/agencies_landing_page_a.html"
  status = 200

# Form submissions
[[plugins]]
  package = "@netlify/plugin-form-submissions"
"""
    
    config_path = Path(__file__).parent / 'netlify.toml'
    with open(config_path, 'w') as f:
        f.write(config)
    
    return config_path


def prepare_netlify_forms(html_dir: Path):
    """Add Netlify Forms support to HTML files."""
    
    for html_file in html_dir.glob('*.html'):
        with open(html_file, 'r', encoding='utf-8') as f:
            html = f.read()
        
        # Add netlify form attributes
        html = html.replace(
            '<form id="audit-form" action="#" method="POST">',
            '<form id="audit-form" name="audit-request" method="POST" data-netlify="true" netlify-honeypot="bot-field">'
        )
        
        # Add honeypot field (spam protection)
        html = html.replace(
            '<div class="form-group">',
            '<p style="display:none;"><label>Don\'t fill this out: <input name="bot-field" /></label></p>\n                    <div class="form-group">',
            1  # Only replace first occurrence
        )
        
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"   ✅ {html_file.name}")


def deploy_to_netlify():
    """Deploy to Netlify."""
    
    print("🚀 Deploying Landing Pages to Netlify\n")
    print("=" * 60)
    
    # Check if Netlify CLI is installed
    try:
        result = subprocess.run(['netlify', '--version'], 
                              capture_output=True, text=True, check=True)
        print(f"✅ Netlify CLI: {result.stdout.strip()}\n")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Netlify CLI not installed\n")
        print("Install it:")
        print("   npm install -g netlify-cli")
        print("\nOr deploy manually:")
        print("   1. Go to https://app.netlify.com")
        print("   2. Drag & drop the 'output/html' folder")
        print("   3. Done!")
        return False
    
    html_dir = Path(__file__).parent / 'output' / 'html'
    
    # Prepare files
    print("1️⃣  Preparing files for Netlify...")
    create_netlify_config()
    prepare_netlify_forms(html_dir)
    
    # Deploy
    print("\n2️⃣  Deploying to Netlify...")
    print("   (You'll need to login if first time)\n")
    
    try:
        # Change to landing-pages directory
        os.chdir(Path(__file__).parent)
        
        # Deploy to Netlify
        result = subprocess.run(
            ['netlify', 'deploy', '--prod', '--dir=output/html'],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("\n✅ Deployment successful!")
            print(f"\n{result.stdout}")
            
            # Extract URL from output
            for line in result.stdout.split('\n'):
                if 'Website URL:' in line or 'Live URL:' in line:
                    print(f"\n🌐 Your landing pages are live:")
                    print(f"   {line.split(':', 1)[1].strip()}")
            
            return True
        else:
            print(f"❌ Deployment failed:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def show_manual_instructions():
    """Show manual deployment instructions."""
    
    print("\n📖 Manual Deployment to Netlify:")
    print("=" * 60)
    print("\nOption 1: Drag & Drop (Easiest)")
    print("   1. Go to https://app.netlify.com")
    print("   2. Click 'Add new site' → 'Deploy manually'")
    print("   3. Drag the 'output/html' folder")
    print("   4. Done! You'll get a live URL")
    
    print("\nOption 2: Netlify CLI")
    print("   1. Install: npm install -g netlify-cli")
    print("   2. Run: python3 landing-pages/deploy_netlify.py")
    
    print("\nOption 3: GitHub + Netlify (Best for production)")
    print("   1. Push to GitHub")
    print("   2. Connect Netlify to your repo")
    print("   3. Auto-deploy on every push")
    
    print("\n💡 Benefits of Netlify:")
    print("   • Free hosting with custom domain")
    print("   • Automatic HTTPS")
    print("   • Built-in form submissions")
    print("   • Global CDN")
    print("   • A/B testing support")


if __name__ == "__main__":
    success = deploy_to_netlify()
    
    if not success:
        show_manual_instructions()
    
    sys.exit(0 if success else 1)


