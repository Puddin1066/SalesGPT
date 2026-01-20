"""
Build and deploy rich, conversion-optimized landing pages to HubSpot.

This script:
1. Reads existing markdown content
2. Generates beautiful HTML/CSS landing pages
3. Deploys to HubSpot via CMS API (or exports for manual upload)
"""

import os
import sys
import json
import re
from typing import Dict, List, Optional
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

load_dotenv('.env.local')

try:
    import requests
except ImportError:
    print("❌ Error: requests library not found")
    print("   Install with: pip3 install requests")
    sys.exit(1)


# Market-specific configurations
MARKET_CONFIG = {
    'medical': {
        'name': 'Medical Clinics',
        'color_primary': '#0066CC',
        'color_secondary': '#00A3E0',
        'icon': '🏥',
        'cta_primary': 'Get Your Free AI Audit',
        'cta_secondary': 'See How You Rank'
    },
    'legal': {
        'name': 'Legal Firms',
        'color_primary': '#1C3D5A',
        'color_secondary': '#4A90E2',
        'icon': '⚖️',
        'cta_primary': 'Get Your Free AI Audit',
        'cta_secondary': 'Check Your Visibility'
    },
    'realestate': {
        'name': 'Real Estate',
        'color_primary': '#D4AF37',
        'color_secondary': '#FFA500',
        'icon': '🏘️',
        'cta_primary': 'Get Your Free AI Audit',
        'cta_secondary': 'Analyze Your Listings'
    },
    'agencies': {
        'name': 'Marketing Agencies',
        'color_primary': '#6B46C1',
        'color_secondary': '#9B59B6',
        'icon': '🚀',
        'cta_primary': 'Book 15-Min Demo',
        'cta_secondary': 'See The Platform'
    }
}


class LandingPageBuilder:
    """Build rich, conversion-optimized landing pages."""
    
    def __init__(self, hubspot_token: Optional[str] = None):
        """Initialize the builder."""
        self.hubspot_token = hubspot_token
        self.base_url = "https://api.hubapi.com"
        
    def parse_markdown_content(self, filepath: str) -> Dict:
        """Parse markdown file and extract structured content."""
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract title
        title_match = re.search(r'^# (.+)$', content, re.MULTILINE)
        title = title_match.group(1) if title_match else "GemFlush - AI Visibility"
        
        # Extract hero headline (first H1 after title)
        hero_match = re.search(r'^# ([^#\n].+)$', content[content.find('\n', 100):], re.MULTILINE)
        hero = hero_match.group(1) if hero_match else title
        
        # Extract hero subheadline (first H2)
        subhero_match = re.search(r'^## (.+)$', content, re.MULTILINE)
        subhero = subhero_match.group(1) if subhero_match else ""
        
        # Extract problem sections (H4 headers with content)
        problems = []
        problem_matches = re.finditer(r'#### \*\*(.+?)\*\*\n(.+?)(?=####|\n###|\Z)', content, re.DOTALL)
        for match in problem_matches:
            problems.append({
                'title': match.group(1),
                'content': match.group(2).strip()
            })
        
        # Extract how it works (numbered list)
        how_it_works = []
        how_matches = re.finditer(r'(\d+)\.\s+\*\*(.+?)\*\*\n\s+.+?\n\s+(.+?)(?=\n\d+\.|\n###|\Z)', content, re.DOTALL)
        for match in how_matches:
            how_it_works.append({
                'step': match.group(1),
                'title': match.group(2),
                'content': match.group(3).strip()
            })
        
        # Extract testimonial
        testimonial_match = re.search(r'> "(.+?)"\s*>\s*>\s*\*\*- (.+?)\*\*', content, re.DOTALL)
        testimonial = None
        if testimonial_match:
            testimonial = {
                'quote': testimonial_match.group(1).strip(),
                'author': testimonial_match.group(2).strip()
            }
        
        # Extract CTA text
        cta_match = re.search(r'#### \*\*(.+?)\*\*\n(?:.*?\n)?.*?\[\*\*(.+?)\*\*\]', content, re.DOTALL)
        cta_title = cta_match.group(1) if cta_match else "Get Started"
        cta_button = cta_match.group(2) if cta_match else "Get Your Free Audit"
        
        return {
            'title': title,
            'hero': hero,
            'subhero': subhero,
            'problems': problems[:3],  # Limit to 3
            'how_it_works': how_it_works[:3],  # Limit to 3
            'testimonial': testimonial,
            'cta_title': cta_title,
            'cta_button': cta_button
        }
    
    def generate_html(self, content: Dict, market: str, variant: str) -> str:
        """Generate beautiful HTML from parsed content."""
        config = MARKET_CONFIG[market]
        
        # Generate HTML with modern, conversion-optimized design
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{content['title']} | GemFlush</title>
    <meta name="description" content="{content['subhero'][:160]}">
    
    <style>
        /* Modern, Conversion-Optimized Landing Page Styles */
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        :root {{
            --primary: {config['color_primary']};
            --secondary: {config['color_secondary']};
            --text: #2D3748;
            --text-light: #4A5568;
            --bg: #FFFFFF;
            --bg-alt: #F7FAFC;
            --border: #E2E8F0;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            color: var(--text);
            line-height: 1.6;
            background: var(--bg);
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 20px;
        }}
        
        /* Header */
        .header {{
            padding: 20px 0;
            background: var(--bg);
            border-bottom: 1px solid var(--border);
        }}
        
        .logo {{
            font-size: 24px;
            font-weight: bold;
            color: var(--primary);
        }}
        
        /* Hero Section */
        .hero {{
            padding: 80px 0;
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
            color: white;
            text-align: center;
        }}
        
        .hero h1 {{
            font-size: 48px;
            font-weight: 700;
            line-height: 1.2;
            margin-bottom: 24px;
            max-width: 900px;
            margin-left: auto;
            margin-right: auto;
        }}
        
        .hero h2 {{
            font-size: 24px;
            font-weight: 400;
            line-height: 1.5;
            margin-bottom: 40px;
            opacity: 0.95;
            max-width: 800px;
            margin-left: auto;
            margin-right: auto;
        }}
        
        /* CTA Button */
        .cta-button {{
            display: inline-block;
            padding: 18px 48px;
            font-size: 18px;
            font-weight: 600;
            color: var(--primary);
            background: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            text-decoration: none;
            transition: transform 0.2s, box-shadow 0.2s;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }}
        
        .cta-button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(0,0,0,0.25);
        }}
        
        .cta-button-secondary {{
            background: transparent;
            color: white;
            border: 2px solid white;
            margin-left: 16px;
        }}
        
        /* Problems Section */
        .problems {{
            padding: 80px 0;
            background: var(--bg-alt);
        }}
        
        .section-title {{
            text-align: center;
            font-size: 36px;
            font-weight: 700;
            margin-bottom: 60px;
            color: var(--text);
        }}
        
        .problem-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
            gap: 40px;
        }}
        
        .problem-card {{
            background: white;
            padding: 40px;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        
        .problem-card:hover {{
            transform: translateY(-4px);
            box-shadow: 0 8px 24px rgba(0,0,0,0.12);
        }}
        
        .problem-card h3 {{
            font-size: 24px;
            font-weight: 700;
            margin-bottom: 16px;
            color: var(--primary);
        }}
        
        .problem-card p {{
            font-size: 16px;
            line-height: 1.7;
            color: var(--text-light);
        }}
        
        /* How It Works Section */
        .how-it-works {{
            padding: 80px 0;
            background: var(--bg);
        }}
        
        .steps {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
            gap: 48px;
            margin-top: 60px;
        }}
        
        .step {{
            text-align: center;
            position: relative;
        }}
        
        .step-number {{
            width: 64px;
            height: 64px;
            background: var(--primary);
            color: white;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 28px;
            font-weight: 700;
            margin: 0 auto 24px;
        }}
        
        .step h3 {{
            font-size: 22px;
            font-weight: 700;
            margin-bottom: 16px;
            color: var(--text);
        }}
        
        .step p {{
            font-size: 16px;
            line-height: 1.7;
            color: var(--text-light);
        }}
        
        /* Testimonial Section */
        .testimonial {{
            padding: 80px 0;
            background: var(--bg-alt);
        }}
        
        .testimonial-card {{
            max-width: 800px;
            margin: 0 auto;
            background: white;
            padding: 48px;
            border-radius: 12px;
            box-shadow: 0 4px 16px rgba(0,0,0,0.08);
            text-align: center;
        }}
        
        .testimonial-quote {{
            font-size: 20px;
            line-height: 1.7;
            color: var(--text);
            font-style: italic;
            margin-bottom: 24px;
        }}
        
        .testimonial-author {{
            font-size: 16px;
            font-weight: 600;
            color: var(--primary);
        }}
        
        /* CTA Section */
        .cta-section {{
            padding: 100px 0;
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
            color: white;
            text-align: center;
        }}
        
        .cta-section h2 {{
            font-size: 40px;
            font-weight: 700;
            margin-bottom: 24px;
        }}
        
        .cta-section p {{
            font-size: 20px;
            margin-bottom: 40px;
            opacity: 0.95;
        }}
        
        /* Form */
        .form-container {{
            max-width: 600px;
            margin: 40px auto 0;
            background: white;
            padding: 40px;
            border-radius: 12px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.12);
        }}
        
        .form-group {{
            margin-bottom: 24px;
            text-align: left;
        }}
        
        .form-group label {{
            display: block;
            font-size: 14px;
            font-weight: 600;
            color: var(--text);
            margin-bottom: 8px;
        }}
        
        .form-group input,
        .form-group select {{
            width: 100%;
            padding: 14px 16px;
            font-size: 16px;
            border: 2px solid var(--border);
            border-radius: 8px;
            transition: border-color 0.2s;
        }}
        
        .form-group input:focus,
        .form-group select:focus {{
            outline: none;
            border-color: var(--primary);
        }}
        
        .submit-button {{
            width: 100%;
            padding: 18px;
            font-size: 18px;
            font-weight: 600;
            color: white;
            background: var(--primary);
            border: none;
            border-radius: 8px;
            cursor: pointer;
            transition: background 0.2s, transform 0.2s;
        }}
        
        .submit-button:hover {{
            background: var(--secondary);
            transform: translateY(-2px);
        }}
        
        /* Footer */
        .footer {{
            padding: 40px 0;
            background: var(--text);
            color: white;
            text-align: center;
        }}
        
        /* Responsive */
        @media (max-width: 768px) {{
            .hero h1 {{
                font-size: 32px;
            }}
            
            .hero h2 {{
                font-size: 18px;
            }}
            
            .section-title {{
                font-size: 28px;
            }}
            
            .cta-button-secondary {{
                margin-left: 0;
                margin-top: 16px;
            }}
            
            .problem-grid,
            .steps {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <!-- Header -->
    <header class="header">
        <div class="container">
            <div class="logo">{config['icon']} GemFlush</div>
        </div>
    </header>
    
    <!-- Hero Section -->
    <section class="hero">
        <div class="container">
            <h1>{content['hero']}</h1>
            <h2>{content['subhero']}</h2>
            <a href="#get-started" class="cta-button">{config['cta_primary']}</a>
            <a href="#how-it-works" class="cta-button cta-button-secondary">{config['cta_secondary']}</a>
        </div>
    </section>
    
    <!-- Problems Section -->
    <section class="problems">
        <div class="container">
            <h2 class="section-title">The Challenge Facing {config['name']}</h2>
            <div class="problem-grid">
"""
        
        # Add problem cards
        for problem in content['problems']:
            html += f"""                <div class="problem-card">
                    <h3>{problem['title']}</h3>
                    <p>{problem['content']}</p>
                </div>
"""
        
        html += """            </div>
        </div>
    </section>
    
    <!-- How It Works Section -->
    <section class="how-it-works" id="how-it-works">
        <div class="container">
            <h2 class="section-title">How GemFlush Works</h2>
            <div class="steps">
"""
        
        # Add steps
        for step in content['how_it_works']:
            html += f"""                <div class="step">
                    <div class="step-number">{step['step']}</div>
                    <h3>{step['title']}</h3>
                    <p>{step['content']}</p>
                </div>
"""
        
        html += """            </div>
        </div>
    </section>
"""
        
        # Add testimonial if available
        if content['testimonial']:
            html += f"""    
    <!-- Testimonial Section -->
    <section class="testimonial">
        <div class="container">
            <div class="testimonial-card">
                <p class="testimonial-quote">"{content['testimonial']['quote']}"</p>
                <p class="testimonial-author">— {content['testimonial']['author']}</p>
            </div>
        </div>
    </section>
"""
        
        # Add CTA section with form
        html += f"""    
    <!-- CTA Section with Form -->
    <section class="cta-section" id="get-started">
        <div class="container">
            <h2>{content['cta_title']}</h2>
            <p>Join hundreds of {config['name'].lower()} already improving their AI visibility</p>
            
            <div class="form-container">
                <!-- HubSpot Form Placeholder - Will be replaced with actual HubSpot form -->
                <form id="audit-form" action="#" method="POST">
                    <div class="form-group">
                        <label for="firstname">First Name *</label>
                        <input type="text" id="firstname" name="firstname" required>
                    </div>
                    
                    <div class="form-group">
                        <label for="lastname">Last Name *</label>
                        <input type="text" id="lastname" name="lastname" required>
                    </div>
                    
                    <div class="form-group">
                        <label for="email">Email Address *</label>
                        <input type="email" id="email" name="email" required>
                    </div>
                    
                    <div class="form-group">
                        <label for="company">Company Name *</label>
                        <input type="text" id="company" name="company" required>
                    </div>
                    
                    <div class="form-group">
                        <label for="phone">Phone Number</label>
                        <input type="tel" id="phone" name="phone">
                    </div>
                    
                    <button type="submit" class="submit-button">{content['cta_button']}</button>
                </form>
            </div>
        </div>
    </section>
    
    <!-- Footer -->
    <footer class="footer">
        <div class="container">
            <p>&copy; 2026 GemFlush. All rights reserved.</p>
            <p>AI Visibility Solutions for {config['name']}</p>
        </div>
    </footer>
    
    <!-- HubSpot Tracking Code -->
    <script type="text/javascript" id="hs-script-loader" async defer src="//js.hs-scripts.com/YOUR_HUB_ID.js"></script>
</body>
</html>
"""
        
        return html
    
    def save_html(self, html: str, market: str, variant: str) -> str:
        """Save HTML to file."""
        output_dir = Path(__file__).parent / 'output' / 'html'
        output_dir.mkdir(parents=True, exist_ok=True)
        
        filename = f"{market}_landing_page_{variant.lower()}.html"
        filepath = output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html)
        
        return str(filepath)
    
    def deploy_to_hubspot(self, html: str, market: str, variant: str) -> Optional[str]:
        """Deploy landing page to HubSpot via CMS API."""
        if not self.hubspot_token:
            print("⚠️  No HubSpot token provided - skipping API deployment")
            return None
        
        # HubSpot CMS API endpoint
        url = f"{self.base_url}/cms/v3/pages/landing-pages"
        
        headers = {
            "Authorization": f"Bearer {self.hubspot_token}",
            "Content-Type": "application/json"
        }
        
        # Prepare page data
        config = MARKET_CONFIG[market]
        page_name = f"GemFlush - {config['name']} - Variant {variant.upper()}"
        
        # Note: HubSpot's CMS API requires specific structure
        # This is a simplified version - may need adjustment based on your HubSpot plan
        data = {
            "name": page_name,
            "htmlTitle": page_name,
            "domain": "",  # Will use default domain
            "slug": f"gemflush-{market}-{variant.lower()}",
            "campaign": "",
            "state": "DRAFT",  # Start as draft
            "pageExpiryEnabled": False,
            "widgets": {
                "html_content": {
                    "body": {
                        "html": html
                    }
                }
            }
        }
        
        try:
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code in [200, 201]:
                result = response.json()
                page_url = result.get('url', 'N/A')
                print(f"   ✅ Deployed to HubSpot: {page_url}")
                return page_url
            elif response.status_code == 403:
                print(f"   ⚠️  API deployment requires CMS Hub (paid tier)")
                print(f"   💡 HTML saved locally - upload manually to HubSpot")
                return None
            else:
                print(f"   ❌ Deployment failed: {response.status_code}")
                print(f"   Error: {response.text}")
                return None
                
        except Exception as e:
            print(f"   ❌ Deployment error: {e}")
            return None


def build_all_landing_pages():
    """Build all landing pages from existing markdown content."""
    
    # Get HubSpot token (optional for HTML generation)
    hubspot_token = os.getenv('HUBSPOT_ACCESS_TOKEN')
    
    builder = LandingPageBuilder(hubspot_token)
    
    # Path to markdown files
    content_dir = Path(__file__).parent.parent / 'content-generation' / 'output' / 'landing-pages'
    
    print("🏗️  Building Rich Landing Pages for GemFlush\n")
    print("=" * 60)
    
    markets = ['medical', 'legal', 'realestate', 'agencies']
    variants = ['a', 'b']
    
    built_pages = []
    deployed_pages = []
    
    for market in markets:
        print(f"\n📄 {MARKET_CONFIG[market]['name']}:")
        
        for variant in variants:
            md_filename = f"{market}_landing_page_{variant}.md"
            md_filepath = content_dir / md_filename
            
            if not md_filepath.exists():
                print(f"   ⚠️  Variant {variant.upper()}: Markdown not found")
                continue
            
            print(f"   Building Variant {variant.upper()}...", end=" ", flush=True)
            
            try:
                # Parse markdown content
                content = builder.parse_markdown_content(str(md_filepath))
                
                # Generate HTML
                html = builder.generate_html(content, market, variant)
                
                # Save HTML locally
                html_path = builder.save_html(html, market, variant)
                built_pages.append(html_path)
                print(f"✅ HTML saved")
                
                # Try to deploy to HubSpot (if token available and CMS Hub)
                if hubspot_token:
                    page_url = builder.deploy_to_hubspot(html, market, variant)
                    if page_url:
                        deployed_pages.append(page_url)
                
            except Exception as e:
                print(f"❌ Error: {e}")
    
    # Summary
    print("\n" + "=" * 60)
    print(f"\n📊 Build Summary:")
    print(f"   • Pages built: {len(built_pages)}/8")
    print(f"   • Pages deployed to HubSpot: {len(deployed_pages)}/8")
    
    if built_pages:
        print(f"\n📁 HTML files saved to:")
        output_dir = Path(__file__).parent / 'output' / 'html'
        print(f"   {output_dir}")
        
        print(f"\n💡 Next Steps:")
        if not hubspot_token:
            print(f"   1. Set HUBSPOT_ACCESS_TOKEN in .env.local to enable API deployment")
        elif len(deployed_pages) == 0:
            print(f"   1. Your HubSpot plan may not include CMS API access")
            print(f"   2. Upload HTML files manually to HubSpot:")
            print(f"      • Marketing → Landing Pages → Create from HTML")
        
        print(f"   {'2' if not hubspot_token or len(deployed_pages) == 0 else '1'}. Alternative: Deploy to Netlify/Vercel (instant, free)")
        print(f"   {'3' if not hubspot_token or len(deployed_pages) == 0 else '2'}. Add HubSpot form ID to forms in HTML")
        print(f"   {'4' if not hubspot_token or len(deployed_pages) == 0 else '3'}. Test conversion tracking")
        
        return True
    else:
        print(f"\n❌ No pages were built")
        return False


if __name__ == "__main__":
    success = build_all_landing_pages()
    sys.exit(0 if success else 1)


