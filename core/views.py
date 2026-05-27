from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_control
from products.models import Product

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def home(request):
    featured_products = Product.objects.filter(is_active=True)[:4]
    return render(request, "core/home.html", {'featured_products': featured_products})

def about(request):
    return render(request, "core/about.html")

def philosophy(request):
    context = {
        'title': 'Philosophy',
        'icon': '🧠',
        'heading': 'Our Core Philosophy',
        'subheading': 'Sneakers are a form of personal expression, fine art, and global culture.',
        'content_html': """
            <h3 style="font-size: 18px; font-weight: 700; margin-bottom: 12px; color: var(--text);">1. Culture First</h3>
            <p style="margin-bottom: 20px; color: var(--text-muted);">
                We believe sneaker collecting is more than a hobby; it's a global language. Every silhouette represents a unique narrative, a cultural shift, and a designer's creative journey. We build with sneakerheads in mind, curating a catalog that honors sneaker heritage.
            </p>
            <h3 style="font-size: 18px; font-weight: 700; margin-bottom: 12px; color: var(--text);">2. Absolute Authenticity</h3>
            <p style="margin-bottom: 20px; color: var(--text-muted);">
                In a market filled with replicas, trust is our primary currency. Our double-verification protocol guarantees that every single item processed through our vaults is fully vetted, verified, and certified genuine.
            </p>
            <h3 style="font-size: 18px; font-weight: 700; margin-bottom: 12px; color: var(--text);">3. Fair Play</h3>
            <p style="margin-bottom: 0px; color: var(--text-muted);">
                We oppose price manipulation and bot abuse. Through optimized coupon distribution, dynamic Product & Category Offers, and transparent referrals, we ensure that premium products remain accessible to true sneaker enthusiasts.
            </p>
        """
    }
    return render(request, 'core/info.html', context)

def careers(request):
    context = {
        'title': 'Careers',
        'icon': '💼',
        'heading': 'Join the Vault',
        'subheading': 'Work with a passionate group of designers, authenticators, and engineers.',
        'content_html': """
            <h3 style="font-size: 18px; font-weight: 700; margin-bottom: 15px; color: var(--text);">Active Openings</h3>
            
            <div style="border-bottom: 1px solid var(--border); padding-bottom: 15px; margin-bottom: 15px;">
                <h4 style="font-size: 15px; font-weight: 700; color: var(--blue); margin: 0 0 5px 0;">Sneaker Authenticator</h4>
                <p style="font-size: 13px; color: var(--text-muted); margin: 0 0 10px 0;">New York, NY | Full-Time</p>
                <p style="font-size: 13.5px; margin: 0; color: var(--text);">Inspect high-end releases and check stitching, labels, packaging, and composite materials against catalog databases.</p>
            </div>

            <div style="border-bottom: 1px solid var(--border); padding-bottom: 15px; margin-bottom: 15px;">
                <h4 style="font-size: 15px; font-weight: 700; color: var(--blue); margin: 0 0 5px 0;">Senior Python Developer</h4>
                <p style="font-size: 13px; color: var(--text-muted); margin: 0 0 10px 0;">Remote (IST/EST) | Full-Time</p>
                <p style="font-size: 13.5px; margin: 0; color: var(--text);">Optimize core transaction flows, wallet ledgers, coupon rules, and integrate Razorpay gateway workflows.</p>
            </div>

            <div style="padding-bottom: 15px;">
                <h4 style="font-size: 15px; font-weight: 700; color: var(--blue); margin: 0 0 5px 0;">Brand Partnership Manager</h4>
                <p style="font-size: 13px; color: var(--text-muted); margin: 0 0 10px 0;">London, UK | Hybrid</p>
                <p style="font-size: 13.5px; margin: 0; color: var(--text);">Establish direct partnerships with globally recognized sneaker manufacturers and designers.</p>
            </div>
            
            <p style="margin-top: 30px; border-top: 1px solid var(--border); padding-top: 20px; font-size: 13.5px; color: var(--text-muted); text-align: center;">
                Interested in another position? Drop your resume at <a href="mailto:careers@solevault.com" style="color: var(--blue); font-weight:700; text-decoration:none;">careers@solevault.com</a>
            </p>
        """
    }
    return render(request, 'core/info.html', context)

def press(request):
    context = {
        'title': 'Press',
        'icon': '📰',
        'heading': 'Press & Media Center',
        'subheading': 'Read about our latest funding rounds, drops, and partnership updates.',
        'content_html': """
            <h3 style="font-size: 18px; font-weight: 700; margin-bottom: 15px; color: var(--text);">Press Releases</h3>
            
            <div style="margin-bottom: 20px;">
                <span style="font-size: 12px; color: var(--text-muted); font-weight: 600; display: block; margin-bottom: 4px;">May 15, 2026</span>
                <h4 style="font-size: 15px; font-weight: 700; color: var(--text); margin: 0 0 8px 0;">SoleVault Unveils Next-Gen AI Authentication Framework</h4>
                <p style="font-size: 13.5px; color: var(--text-muted); margin: 0;">We are scaling our inspection speeds by introducing specialized image alignment models to match micro-textures and material grains.</p>
            </div>

            <div style="margin-bottom: 20px;">
                <span style="font-size: 12px; color: var(--text-muted); font-weight: 600; display: block; margin-bottom: 4px;">April 02, 2026</span>
                <h4 style="font-size: 15px; font-weight: 700; color: var(--text); margin: 0 0 8px 0;">SoleVault Secures Series A Funding for Global Expansion</h4>
                <p style="font-size: 13.5px; color: var(--text-muted); margin: 0;">With over 1.2M active users in our ecosystem, we are establishing dedicated logistics vaults in Mumbai and London.</p>
            </div>
            
            <p style="margin-top: 30px; border-top: 1px solid var(--border); padding-top: 20px; font-size: 13px; color: var(--text-muted);">
                For press inquiries, brand assets, or interview requests, reach out to <a href="mailto:press@solevault.com" style="color: var(--blue); font-weight: 700; text-decoration: none;">press@solevault.com</a>
            </p>
        """
    }
    return render(request, 'core/info.html', context)

def contact(request):
    context = {
        'title': 'Contact',
        'icon': '✉️',
        'heading': 'Contact Customer Support',
        'subheading': 'Have questions about your order, wallet, or returns? We are here to help.',
        'content_html': """
            <p style="margin-bottom: 25px; color: var(--text);">
                Our support team is active 24/7 to solve your logistics and order issues. Please use the contact details below or email our support ticket system.
            </p>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 25px;">
                <div style="background: var(--surface); border: 1px solid var(--border); padding: 18px; border-radius: 10px;">
                    <strong style="display: block; font-size: 14px; margin-bottom: 6px; color: var(--blue);">General Inquiries</strong>
                    <span style="font-size: 13px; color: var(--text-muted);">Email: <a href="mailto:info@solevault.com" style="color: var(--text); font-weight:600; text-decoration:none;">info@solevault.com</a></span>
                </div>
                <div style="background: var(--surface); border: 1px solid var(--border); padding: 18px; border-radius: 10px;">
                    <strong style="display: block; font-size: 14px; margin-bottom: 6px; color: var(--blue);">Help &amp; Orders</strong>
                    <span style="font-size: 13px; color: var(--text-muted);">Email: <a href="mailto:support@solevault.com" style="color: var(--text); font-weight:600; text-decoration:none;">support@solevault.com</a></span>
                </div>
            </div>
            <div style="background: var(--surface); border: 1px solid var(--border); padding: 20px; border-radius: 10px; margin-bottom: 25px;">
                <strong style="display: block; font-size: 14.5px; margin-bottom: 6px; color: var(--text);">Headquarters Address</strong>
                <p style="font-size: 13.5px; color: var(--text-muted); margin: 0; line-height: 1.6;">
                    SoleVault Inc.<br>
                    123 Main Street, Suite 500<br>
                    New York, NY 10000
                </p>
            </div>
            
            <div style="text-align: center; border-top: 1px solid var(--border); padding-top: 20px;">
                <strong style="display: block; font-size: 13px; text-transform: uppercase; color: var(--text-muted); margin-bottom: 12px; letter-spacing: 0.5px;">Connect on Social Channels</strong>
                <div style="display: flex; justify-content: center; gap: 12px;">
                    <div style="width: 38px; height: 38px; border-radius: 50%; background: var(--surface); border: 1px solid var(--border); display: flex; align-items: center; justify-content: center; color: var(--text-muted); cursor: pointer;" title="Instagram">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width: 16px; height: 16px;">
                            <rect x="2" y="2" width="20" height="20" rx="5" ry="5"></rect>
                            <path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z"></path>
                            <line x1="17.5" y1="6.5" x2="17.51" y2="6.5"></line>
                        </svg>
                    </div>
                    <div style="width: 38px; height: 38px; border-radius: 50%; background: var(--surface); border: 1px solid var(--border); display: flex; align-items: center; justify-content: center; color: var(--text-muted); cursor: pointer;" title="Facebook">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width: 16px; height: 16px;">
                            <path d="M18 2h-3a5 5 0 0 0-5 5v3H7v4h3v8h4v-8h3l1-4h-4V7a1 1 0 0 1 1-1h3z"></path>
                        </svg>
                    </div>
                    <div style="width: 38px; height: 38px; border-radius: 50%; background: var(--surface); border: 1px solid var(--border); display: flex; align-items: center; justify-content: center; color: var(--text-muted); cursor: pointer;" title="LinkedIn">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width: 16px; height: 16px;">
                            <path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6z"></path>
                            <rect x="2" y="9" width="4" height="12"></rect>
                            <circle cx="4" cy="4" r="2"></circle>
                        </svg>
                    </div>
                </div>
            </div>
        """
    }
    return render(request, 'core/info.html', context)

def shipping_returns(request):
    context = {
        'title': 'Shipping & Returns',
        'icon': '📦',
        'heading': 'Shipping & Returns Policy',
        'subheading': 'Standardized delivery timelines, tracking instructions, and return verification policies.',
        'content_html': """
            <h3 style="font-size: 17px; font-weight: 700; margin-bottom: 10px; color: var(--text);">1. Shipping Speeds & Rates</h3>
            <p style="margin-bottom: 20px; color: var(--text-muted);">
                We offer free standard shipping on all orders exceeding ₹10,000. For other orders, a flat ₹150 shipping fee is applied at checkout. Delivery typically takes <b>3 to 5 business days</b> following our quality check verification process.
            </p>
            <h3 style="font-size: 17px; font-weight: 700; margin-bottom: 10px; color: var(--text);">2. Double authenticity check delay</h3>
            <p style="margin-bottom: 20px; color: var(--text-muted);">
                Since every pair is inspected before dispatch, we spend 24 to 48 hours to complete safety checklists before giving packages to shipping partners.
            </p>
            <h3 style="font-size: 17px; font-weight: 700; margin-bottom: 10px; color: var(--text);">3. Returns and Refunds Flow</h3>
            <p style="margin-bottom: 0px; color: var(--text-muted);">
                You can request a return from your profile details within <b>30 days of delivery</b>. Once returned to our inventory, the administrative team checks the item state. Upon approval, 100% of purchase costs are credited back to your **SoleVault wallet balance** immediately, and stocks are updated automatically.
            </p>
        """
    }
    return render(request, 'core/info.html', context)

def faq(request):
    context = {
        'title': 'FAQ',
        'icon': '❓',
        'heading': 'Frequently Asked Questions',
        'subheading': 'Find answers to common queries regarding shoe authenticity, order cancellations, and referrals.',
        'content_html': """
            <div style="margin-bottom: 20px;">
                <h4 style="font-size: 15px; font-weight: 700; color: var(--blue); margin: 0 0 6px 0;">Q: How do you verify sneaker authenticity?</h4>
                <p style="font-size: 13.5px; color: var(--text-muted); margin: 0; line-height: 1.6;">A: We have a dedicated team of authenticators who examine every detail—from box labels, inner soles, tag barcodes, stitching, and glue spots—to confirm that every shoe is genuine.</p>
            </div>

            <div style="margin-bottom: 20px;">
                <h4 style="font-size: 15px; font-weight: 700; color: var(--blue); margin: 0 0 6px 0;">Q: Can I use multiple coupons at checkout?</h4>
                <p style="font-size: 13.5px; color: var(--text-muted); margin: 0; line-height: 1.6;">A: No, only one valid coupon code can be applied per order. However, coupon deductions can be stacked with any active Product or Category Offers.</p>
            </div>

            <div style="margin-bottom: 20px;">
                <h4 style="font-size: 15px; font-weight: 700; color: var(--blue); margin: 0 0 6px 0;">Q: How does the referral program credit my wallet?</h4>
                <p style="font-size: 13.5px; color: var(--text-muted); margin: 0; line-height: 1.6;">A: Share your unique invite link from your profile. Once your friend registers and verifies their OTP, they get ₹100 and you get ₹200 credited instantly to your wallets.</p>
            </div>

            <div>
                <h4 style="font-size: 15px; font-weight: 700; color: var(--blue); margin: 0 0 6px 0;">Q: What is your return policy?</h4>
                <p style="font-size: 13.5px; color: var(--text-muted); margin: 0; line-height: 1.6;">A: Delivered items can be returned within 30 days of delivery. Upon approval, funds are refunded to your Wallet instantly.</p>
            </div>
        """
    }
    return render(request, 'core/info.html', context)

def size_guide(request):
    context = {
        'title': 'Size Guide',
        'icon': '📐',
        'heading': 'Sneaker Size & Fit Guide',
        'subheading': 'Standardized sneaker size charts. Find your perfect fit.',
        'content_html': """
            <p style="margin-bottom: 20px; color: var(--text);">
                Sneaker sizing varies between brands. Use the comparison table below to convert your sneaker sizing between US, UK, and European standards.
            </p>
            <table style="width:100%; border-collapse:collapse; font-size:13.5px; color:var(--text); text-align:center; border: 1px solid var(--border);">
                <thead>
                    <tr style="background:var(--surface); border-bottom:1px solid var(--border); font-weight:700;">
                        <th style="padding:10px;">US Men</th>
                        <th style="padding:10px;">US Women</th>
                        <th style="padding:10px;">UK</th>
                        <th style="padding:10px;">Europe</th>
                        <th style="padding:10px;">Inches</th>
                    </tr>
                </thead>
                <tbody>
                    <tr style="border-bottom:1px solid var(--border);">
                        <td style="padding:10px;">7.0</td><td style="padding:10px;">8.5</td><td style="padding:10px;">6.0</td><td style="padding:10px;">40.0</td><td style="padding:10px;">9.6"</td>
                    </tr>
                    <tr style="border-bottom:1px solid var(--border);">
                        <td style="padding:10px;">8.0</td><td style="padding:10px;">9.5</td><td style="padding:10px;">7.0</td><td style="padding:10px;">41.0</td><td style="padding:10px;">9.9"</td>
                    </tr>
                    <tr style="border-bottom:1px solid var(--border);">
                        <td style="padding:10px;">9.0</td><td style="padding:10px;">10.5</td><td style="padding:10px;">8.0</td><td style="padding:10px;">42.5</td><td style="padding:10px;">10.2"</td>
                    </tr>
                    <tr style="border-bottom:1px solid var(--border);">
                        <td style="padding:10px;">10.0</td><td style="padding:10px;">11.5</td><td style="padding:10px;">9.0</td><td style="padding:10px;">44.0</td><td style="padding:10px;">10.6"</td>
                    </tr>
                    <tr>
                        <td style="padding:10px;">11.0</td><td style="padding:10px;">12.5</td><td style="padding:10px;">10.0</td><td style="padding:10px;">45.0</td><td style="padding:10px;">10.9"</td>
                    </tr>
                </tbody>
            </table>
        """
    }
    return render(request, 'core/info.html', context)

def privacy(request):
    context = {
        'title': 'Privacy Policy',
        'icon': '🛡️',
        'heading': 'SoleVault Privacy Policy',
        'subheading': 'Learn how we collect, process, and protect your personal financial and profile details.',
        'content_html': """
            <h3 style="font-size:17px; font-weight:700; color:var(--text); margin-bottom:10px;">1. Information We Collect</h3>
            <p style="margin-bottom:20px; color:var(--text-muted);">
                We collect your email, full name, profile image, phone number, and shipping addresses when you edit your profile. Payment details (e.g. card credentials during Razorpay checkouts) are encrypted directly by secure payment processors and never stored in our systems.
            </p>
            <h3 style="font-size:17px; font-weight:700; color:var(--text); margin-bottom:10px;">2. How We Protect Your Data</h3>
            <p style="margin-bottom:20px; color:var(--text-muted);">
                All profile edits, password modifications, OTP validations, and checkout operations use secure 256-bit SSL encrypted channels. Wallet transactions are written to a secure relational database using ACID properties to prevent data corruption.
            </p>
            <h3 style="font-size:17px; font-weight:700; color:var(--text); margin-bottom:10px;">3. Cookies Preference</h3>
            <p style="margin-bottom:0px; color:var(--text-muted);">
                We utilize session-based cookies strictly to manage user logins, hold cart contents, and preserve filters state.
            </p>
        """
    }
    return render(request, 'core/info.html', context)

def terms(request):
    context = {
        'title': 'Terms & Conditions',
        'icon': '📜',
        'heading': 'Terms & Conditions of Service',
        'subheading': 'Governing policies, rules, and guidelines for shopping on SoleVault.',
        'content_html': """
            <h3 style="font-size:17px; font-weight:700; color:var(--text); margin-bottom:10px;">1. Account Registration</h3>
            <p style="margin-bottom:20px; color:var(--text-muted);">
                Users must register using a unique email address and complete mobile OTP verification to place orders or earn referral rewards. Providing false credentials will result in account suspension.
            </p>
            <h3 style="font-size:17px; font-weight:700; color:var(--text); margin-bottom:10px;">2. Pricing and Promotions</h3>
            <p style="margin-bottom:20px; color:var(--text-muted);">
                Our platform applies dynamic Product and Category Offers. The largest active offer is automatically determined and applied at checkout. Coupon abuse, including multiple parallel coupon applications, is strictly prohibited.
            </p>
            <h3 style="font-size:17px; font-weight:700; color:var(--text); margin-bottom:10px;">3. Limitation of Liability</h3>
            <p style="margin-bottom:0px; color:var(--text-muted);">
                SoleVault is not liable for indirect financial losses due to server downtime or test Razorpay checkout transaction hiccups. Wallet credits cannot be exchanged for cash currency outside the application ecosystem.
            </p>
        """
    }
    return render(request, 'core/info.html', context)

def blog(request):
    context = {
        'title': 'Blog',
        'icon': '✍️',
        'heading': 'SoleVault Streetwear Blog',
        'subheading': 'Read articles about hot sneaker trends, vintage fashion, and drop lists.',
        'content_html': """
            <div style="border-bottom:1px solid var(--border); padding-bottom:20px; margin-bottom:20px;">
                <span style="font-size:12px; color:var(--text-muted); font-weight:600; display:block; margin-bottom:4px;">June 01, 2026</span>
                <h4 style="font-size:16px; font-weight:700; color:var(--text); margin:0 0-8px 0;">Top 5 Retro Silhouettes Dominating Summer 2026</h4>
                <p style="font-size:13.5px; color:var(--text-muted); margin:12px 0 0 0;">Vintage suede cuts and off-white midsoles are ruling the streets. We look at the rise of running classics and why neutral earth tones are making a big comeback this season.</p>
            </div>
            
            <div>
                <span style="font-size:12px; color:var(--text-muted); font-weight:600; display:block; margin-bottom:4px;">May 24, 2026</span>
                <h4 style="font-size:16px; font-weight:700; color:var(--text); margin:0 0-8px 0;">A Deep Dive Into Deconstructed Designs</h4>
                <p style="font-size:13.5px; color:var(--text-muted); margin:12px 0 0 0;">Exposed stitch work, raw tongue edges, and bold helvetica labeling has reshaped footwear. Read our exploration of how post-modern designs transitioned from art galleries to retail shelves.</p>
            </div>
        """
    }
    return render(request, 'core/info.html', context)

def lookbook(request):
    context = {
        'title': 'Lookbook',
        'icon': '📸',
        'heading': 'Seasonal Lookbook',
        'subheading': 'Visual streetwear inspirations featuring SoleVault limited-edition items.',
        'content_html': """
            <p style="margin-bottom: 25px; color: var(--text);">
                Our Summer 2026 Lookbook explores the convergence of modular streetwear and high-top athletic footwear. Shot in urban concrete spaces, our models wear oversized linen sets contrasted with neon-accented sneaker variants.
            </p>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px;">
                <div style="background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 25px; text-align: center; font-weight: 700;">
                    <span style="font-size: 32px; display: block; margin-bottom: 10px;">🛹</span>
                    Urban Concrete Set
                </div>
                <div style="background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 25px; text-align: center; font-weight: 700;">
                    <span style="font-size: 32px; display: block; margin-bottom: 10px;">🏀</span>
                    Court Heritage Series
                </div>
            </div>
            <p style="font-size:13.5px; color:var(--text-muted); line-height:1.6; text-align:center;">
                Discover the showcased collections in our shop and filter by <b>New Drops</b> to find matching items.
            </p>
        """
    }
    return render(request, 'core/info.html', context)