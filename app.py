import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from collections import Counter
import random
import os
import requests

# API Configuration
API_BASE_URL = "https://f66597fa63dc.ngrok-free.app/api"
CUSTOMER_ID = "CUST001"

@st.cache_data(ttl=60)
def fetch_customer_data():
    """Fetch customer balance and info from API"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/customers/{CUSTOMER_ID}/balance/",
            headers={"ngrok-skip-browser-warning": "true"},
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        st.error(f"Error fetching customer data: {e}")
    return None

@st.cache_data(ttl=60)
def fetch_transactions():
    """Fetch customer transactions from API"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/customers/{CUSTOMER_ID}/transactions/",
            headers={"ngrok-skip-browser-warning": "true"},
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        st.error(f"Error fetching transactions: {e}")
    return None

def post_redemption(customer_id, reward_name, points_cost, reward_category, reward_value):
    """Post a redemption to the API"""
    try:
        payload = {
            "customerId": customer_id,
            "rewardName": reward_name,
            "pointsRedeemed": points_cost,
            "category": reward_category,
            "rewardValue": reward_value,
            "redeemedAt": datetime.now().isoformat()
        }
        response = requests.post(
            f"{API_BASE_URL}/redemptions/",
            headers={
                "ngrok-skip-browser-warning": "true",
                "Content-Type": "application/json"
            },
            json=payload,
            timeout=10
        )
        if response.status_code in [200, 201]:
            return True, response.json() if response.text else {"status": "success"}
        else:
            return False, f"API returned status {response.status_code}"
    except Exception as e:
        return False, str(e)

def analyze_purchase_patterns(transactions):
    """Analyze purchase history to identify patterns and preferences"""
    if not transactions:
        return {}

    categories = []
    items = []
    total_spent = 0
    total_points = 0

    for tx in transactions:
        if tx.get('category'):
            categories.append(tx['category'])
        if tx.get('productName'):
            items.append(tx['productName'])
        if tx.get('purchaseAmount') is not None:
            total_spent += tx.get('purchaseAmount', 0) or 0
        if tx.get('points') is not None:
            total_points += tx.get('points', 0) or 0

    category_counts = Counter(categories)
    top_categories = category_counts.most_common(5)

    return {
        'top_categories': top_categories,
        'total_transactions': len(transactions),
        'total_spent': total_spent,
        'total_points_earned': total_points,
        'recent_items': items[:10],
        'favorite_category': top_categories[0][0] if top_categories else None
    }

def get_personalized_recommendations(transactions, rewards_catalog, member_points):
    """Generate personalized recommendations based on purchase history"""
    patterns = analyze_purchase_patterns(transactions)
    recommendations = []

    # Category-based recommendations
    category_mapping = {
        'Electronics': ['Merchandise', 'Digital'],
        'Health': ['Experiences', 'Merchandise'],
        'Groceries': ['Gift Cards', 'Discounts'],
        'Food': ['Gift Cards', 'Discounts'],
        'Home': ['Merchandise', 'Gift Cards'],
        'Clothing': ['Gift Cards', 'Discounts']
    }

    favorite_cat = patterns.get('favorite_category', 'Electronics')
    preferred_reward_types = category_mapping.get(favorite_cat, ['Gift Cards'])

    for reward in rewards_catalog:
        score = 0
        reasons = []

        # Affordability score
        if reward['points'] <= member_points:
            score += 30
            reasons.append("Within your points balance")

        # Category match score
        if reward['category'] in preferred_reward_types:
            score += 25
            reasons.append(f"Matches your {favorite_cat} shopping preference")

        # Value score (points per dollar equivalent)
        if reward['points'] < 1000:
            score += 15
            reasons.append("Great value redemption")
        elif reward['points'] < 2000:
            score += 10
            reasons.append("Good value for points")

        # Stock urgency
        if reward['stock'] < 30:
            score += 10
            reasons.append("Limited availability")

        recommendations.append({
            'reward': reward,
            'score': score,
            'reasons': reasons
        })

    # Sort by score
    recommendations.sort(key=lambda x: x['score'], reverse=True)
    return recommendations[:5], patterns

# Page configuration
st.set_page_config(
    page_title="OmniShop Rewards",
    page_icon="🎁",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for tier colors and styling
st.markdown("""
<style>
    .gold-badge {
        background: linear-gradient(135deg, #FFD700, #FFA500);
        color: #333;
        padding: 8px 16px;
        border-radius: 20px;
        font-weight: bold;
        display: inline-block;
    }
    .silver-badge {
        background: linear-gradient(135deg, #C0C0C0, #A8A8A8);
        color: #333;
        padding: 8px 16px;
        border-radius: 20px;
        font-weight: bold;
        display: inline-block;
    }
    .platinum-badge {
        background: linear-gradient(135deg, #E5E4E2, #B4B4B4);
        color: #1a1a2e;
        padding: 8px 16px;
        border-radius: 20px;
        font-weight: bold;
        display: inline-block;
        border: 2px solid #8B8B8B;
    }
    .metric-card {
        background: #f8f9fa;
        padding: 20px;
        border-radius: 10px;
        border-left: 4px solid #667eea;
    }
    .reward-card {
        background: white;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 10px 0;
    }
    .challenge-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #667eea, #764ba2);
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state with API data
if 'member' not in st.session_state:
    # Fetch real data from API
    customer_data = fetch_customer_data()
    transactions_data = fetch_transactions()

    if customer_data:
        # Calculate tier based on total spent
        patterns = analyze_purchase_patterns(transactions_data) if transactions_data else {}
        total_spent = patterns.get('total_spent', 0)

        if total_spent >= 2000:
            tier = 'Platinum'
        elif total_spent >= 500:
            tier = 'Silver'
        else:
            tier = 'Gold'

        st.session_state.member = {
            'id': customer_data.get('customerId', 'CUST001'),
            'name': customer_data.get('customerName', 'Alex D.'),
            'email': 'alex.d@email.com',
            'tier': tier,
            'points': customer_data.get('pointsBalance', 0),
            'lifetime_points': patterns.get('total_points_earned', 0),
            'annual_spend': total_spent,
            'member_since': customer_data.get('createdAt', '2026-01-13')[:10],
            'badges': ['First Purchase', 'Review Writer', 'Social Sharer', 'Streak Master', 'Big Spender', 'Early Bird'],
            'streak_days': 12,
            'redeemed_rewards': []
        }
    else:
        # Fallback to defaults if API fails
        st.session_state.member = {
            'id': 'CUST001',
            'name': 'Alex D.',
            'email': 'alex.d@email.com',
            'tier': 'Silver',
            'points': 18574,
            'lifetime_points': 19222,
            'annual_spend': 1531.58,
            'member_since': '2026-01-13',
            'badges': ['First Purchase', 'Review Writer', 'Social Sharer', 'Streak Master', 'Big Spender'],
            'streak_days': 12,
            'redeemed_rewards': []
        }

# Store transactions in session state
if 'transactions_data' not in st.session_state:
    st.session_state.transactions_data = fetch_transactions()

if 'cart' not in st.session_state:
    st.session_state.cart = []

# Responsible AI session state
if 'ai_preferences' not in st.session_state:
    st.session_state.ai_preferences = {
        'ai_enabled': True,
        'personalization_enabled': True,
        'data_collection_consent': True
    }

if 'ai_feedback' not in st.session_state:
    st.session_state.ai_feedback = []

if 'ai_interactions' not in st.session_state:
    st.session_state.ai_interactions = []

# Redemption tracking
if 'redemption_stats' not in st.session_state:
    st.session_state.redemption_stats = {
        'total_redemptions': 0,
        'total_points_redeemed': 0,
        'total_value_redeemed': 0.0,
        'redemption_history': []
    }

# Tier configuration
TIERS = {
    'Gold': {
        'color': '#FFD700',
        'earning_rate': 1.0,
        'min_spend': 0,
        'max_spend': 499,
        'benefits': ['Birthday rewards', 'Early access to sales (24h)', 'Standard returns (30 days)', 'Member-only promotions']
    },
    'Silver': {
        'color': '#C0C0C0',
        'earning_rate': 1.25,
        'min_spend': 500,
        'max_spend': 1999,
        'benefits': ['All Gold benefits', 'Free standard shipping', 'Priority customer service', 'Extended returns (60 days)', 'Quarterly bonus points']
    },
    'Platinum': {
        'color': '#E5E4E2',
        'earning_rate': 1.5,
        'min_spend': 2000,
        'max_spend': float('inf'),
        'benefits': ['All Silver benefits', 'Free express shipping', 'Dedicated concierge', 'Exclusive events', 'Personal shopper access', 'Monthly bonus points']
    }
}

# Sample reward catalog with dollar values
REWARDS_CATALOG = [
    {'id': 1, 'name': '$10 Store Gift Card', 'category': 'Gift Cards', 'points': 500, 'value': 10.00, 'image': '🎁', 'tier_exclusive': None, 'stock': 100},
    {'id': 2, 'name': '$25 Store Gift Card', 'category': 'Gift Cards', 'points': 1200, 'value': 25.00, 'image': '🎁', 'tier_exclusive': None, 'stock': 75},
    {'id': 3, 'name': '$50 Store Gift Card', 'category': 'Gift Cards', 'points': 2300, 'value': 50.00, 'image': '🎁', 'tier_exclusive': None, 'stock': 50},
    {'id': 4, 'name': 'Premium Headphones', 'category': 'Merchandise', 'points': 5000, 'value': 149.99, 'image': '🎧', 'tier_exclusive': None, 'stock': 25},
    {'id': 5, 'name': 'Wireless Charger', 'category': 'Merchandise', 'points': 1500, 'value': 39.99, 'image': '🔌', 'tier_exclusive': None, 'stock': 60},
    {'id': 6, 'name': 'Smart Watch Band', 'category': 'Merchandise', 'points': 800, 'value': 24.99, 'image': '⌚', 'tier_exclusive': None, 'stock': 80},
    {'id': 7, 'name': 'VIP Shopping Experience', 'category': 'Experiences', 'points': 3500, 'value': 150.00, 'image': '👔', 'tier_exclusive': 'Platinum', 'stock': 10},
    {'id': 8, 'name': 'Personal Styling Session', 'category': 'Experiences', 'points': 2000, 'value': 75.00, 'image': '✨', 'tier_exclusive': 'Silver', 'stock': 20},
    {'id': 9, 'name': 'Streaming Subscription (1 month)', 'category': 'Digital', 'points': 600, 'value': 15.99, 'image': '📺', 'tier_exclusive': None, 'stock': 200},
    {'id': 10, 'name': 'E-Book Bundle', 'category': 'Digital', 'points': 400, 'value': 12.99, 'image': '📚', 'tier_exclusive': None, 'stock': 150},
    {'id': 11, 'name': '20% Off Coupon', 'category': 'Discounts', 'points': 300, 'value': 20.00, 'image': '🏷️', 'tier_exclusive': None, 'stock': 500},
    {'id': 12, 'name': 'Free Express Shipping (3 uses)', 'category': 'Discounts', 'points': 450, 'value': 29.97, 'image': '🚚', 'tier_exclusive': None, 'stock': 300},
    {'id': 13, 'name': 'Charity Donation - $10', 'category': 'Charitable', 'points': 500, 'value': 10.00, 'image': '💝', 'tier_exclusive': None, 'stock': 999},
    {'id': 14, 'name': 'Limited Edition Tote Bag', 'category': 'Merchandise', 'points': 1800, 'value': 45.00, 'image': '👜', 'tier_exclusive': None, 'stock': 30, 'limited': True},
    {'id': 15, 'name': 'Exclusive Member Event Access', 'category': 'Experiences', 'points': 4000, 'value': 200.00, 'image': '🎉', 'tier_exclusive': 'Platinum', 'stock': 15},
]

# Sample challenges
CHALLENGES = [
    {'id': 1, 'name': 'Weekend Warrior', 'description': 'Make a purchase this weekend', 'points': 100, 'progress': 0, 'target': 1, 'ends': 'Sunday'},
    {'id': 2, 'name': 'Category Explorer', 'description': 'Shop from 3 different categories', 'points': 250, 'progress': 2, 'target': 3, 'ends': '5 days'},
    {'id': 3, 'name': 'Social Butterfly', 'description': 'Share 2 products on social media', 'points': 150, 'progress': 1, 'target': 2, 'ends': '3 days'},
    {'id': 4, 'name': 'Review Champion', 'description': 'Write 5 product reviews', 'points': 300, 'progress': 3, 'target': 5, 'ends': '7 days'},
]

# All available badges
ALL_BADGES = {
    'First Purchase': {'icon': '🛒', 'description': 'Made your first purchase'},
    'Review Writer': {'icon': '✍️', 'description': 'Wrote your first review'},
    'Social Sharer': {'icon': '📱', 'description': 'Shared a product on social media'},
    'Streak Master': {'icon': '🔥', 'description': 'Maintained a 7-day streak'},
    'Big Spender': {'icon': '💰', 'description': 'Spent over $500 in a month'},
    'Eco Warrior': {'icon': '🌱', 'description': 'Purchased sustainable products'},
    'Early Bird': {'icon': '🌅', 'description': 'Shopped during early access sale'},
    'Referral King': {'icon': '👑', 'description': 'Referred 5 friends'},
    'Category Master': {'icon': '🏆', 'description': 'Purchased from all categories'},
    'Loyal Member': {'icon': '💎', 'description': '1 year membership anniversary'},
}

# Content guardrails - blocked topics and patterns
BLOCKED_PATTERNS = [
    'personal financial advice',
    'investment advice',
    'medical advice',
    'legal advice',
    'discriminat',
    'hate speech',
]

RESPONSIBLE_AI_PRINCIPLES = [
    {"name": "Transparency", "icon": "🔍", "description": "We clearly disclose when AI is being used and how it influences recommendations."},
    {"name": "Fairness", "icon": "⚖️", "description": "Our AI treats all members equitably regardless of demographics or background."},
    {"name": "Privacy", "icon": "🔒", "description": "Your data is protected and you control how it's used for personalization."},
    {"name": "Accountability", "icon": "📋", "description": "Human oversight ensures AI recommendations are appropriate and helpful."},
    {"name": "Safety", "icon": "🛡️", "description": "Content guardrails prevent harmful or inappropriate AI responses."},
    {"name": "Explainability", "icon": "💡", "description": "We explain why recommendations are made so you can make informed decisions."},
]

def render_ai_transparency_banner():
    """Display AI transparency notice"""
    st.info("""
    **🤖 AI-Powered Feature**
    This feature uses artificial intelligence to provide personalized recommendations.
    AI suggestions are based on your purchase history, preferences, and tier status.
    You can disable AI personalization in your preferences.
    """)

def check_content_safety(text):
    """Check if content passes safety guardrails"""
    text_lower = text.lower()
    for pattern in BLOCKED_PATTERNS:
        if pattern in text_lower:
            return False, f"Content flagged for review: {pattern}"
    return True, "Content passed safety check"

def get_recommendation_explanation(reward, member):
    """Generate explainable reasoning for a recommendation"""
    reasons = []

    # Point affordability
    if member['points'] >= reward['points']:
        reasons.append(f"✓ You have enough points ({member['points']:,} pts)")
    else:
        reasons.append(f"○ Need {reward['points'] - member['points']:,} more points")

    # Tier match
    if reward.get('tier_exclusive'):
        if reward['tier_exclusive'] == member['tier']:
            reasons.append(f"✓ Exclusive for your {member['tier']} tier")
        else:
            reasons.append(f"○ Requires {reward['tier_exclusive']} tier")
    else:
        reasons.append("✓ Available to all members")

    # Value score
    value_score = (reward['points'] / 100) if reward['points'] > 0 else 0
    if value_score < 10:
        reasons.append("✓ Great value redemption")
    elif value_score < 25:
        reasons.append("✓ Good value for points")
    else:
        reasons.append("○ Premium reward")

    # Popularity (simulated)
    if reward['stock'] < 30:
        reasons.append("🔥 Popular - limited stock!")

    return reasons

def log_ai_interaction(interaction_type, input_text, output_text, was_filtered=False):
    """Log AI interaction for audit trail"""
    from datetime import datetime
    st.session_state.ai_interactions.append({
        'timestamp': datetime.now().isoformat(),
        'type': interaction_type,
        'input': input_text[:100] + '...' if len(input_text) > 100 else input_text,
        'output_length': len(output_text),
        'was_filtered': was_filtered,
        'member_tier': st.session_state.member['tier']
    })

def calculate_fairness_metrics():
    """Calculate fairness metrics for AI recommendations"""
    # Simulated fairness data across tiers
    return {
        'recommendation_distribution': {
            'Gold': {'count': 145, 'avg_points': 850},
            'Silver': {'count': 132, 'avg_points': 1200},
            'Platinum': {'count': 98, 'avg_points': 2100}
        },
        'redemption_success_rate': {
            'Gold': 0.72,
            'Silver': 0.78,
            'Platinum': 0.85
        },
        'response_time_ms': {
            'Gold': 245,
            'Silver': 238,
            'Platinum': 241
        },
        'fairness_score': 0.94,
        'bias_flags': 0,
        'total_interactions': 375
    }

def get_tier_badge_html(tier):
    """Generate HTML for tier badge"""
    return f'<span class="{tier.lower()}-badge">{tier}</span>'

def calculate_next_tier_progress(member):
    """Calculate progress to next tier"""
    current_tier = member['tier']
    annual_spend = member['annual_spend']

    if current_tier == 'Gold':
        target = 500
        return min(100, (annual_spend / target) * 100), target - annual_spend
    elif current_tier == 'Silver':
        target = 2000
        return min(100, ((annual_spend - 500) / (target - 500)) * 100), target - annual_spend
    else:
        return 100, 0

def render_sidebar():
    """Render the sidebar with member info"""
    member = st.session_state.member

    # Display logo
    st.sidebar.image("logo.jpeg", use_container_width=True)
    st.sidebar.markdown("---")

    # Member info
    st.sidebar.markdown(f"### Welcome, {member['name'].split()[0]}!")
    st.sidebar.markdown(get_tier_badge_html(member['tier']), unsafe_allow_html=True)

    st.sidebar.markdown("---")

    # Points display
    st.sidebar.metric("Available Points", f"{member['points']:,}")
    st.sidebar.caption(f"Lifetime: {member['lifetime_points']:,} points")

    # Tier progress
    progress, remaining = calculate_next_tier_progress(member)
    if member['tier'] != 'Platinum':
        next_tier = 'Silver' if member['tier'] == 'Gold' else 'Platinum'
        st.sidebar.markdown(f"**Progress to {next_tier}**")
        st.sidebar.progress(progress / 100)
        st.sidebar.caption(f"${remaining:.2f} more to reach {next_tier}")
    else:
        st.sidebar.success("You've reached the highest tier!")

    st.sidebar.markdown("---")

    # Streak
    st.sidebar.markdown(f"### 🔥 {member['streak_days']}-Day Streak!")
    st.sidebar.caption("Keep shopping to maintain your streak")

    # Navigation
    st.sidebar.markdown("---")
    return st.sidebar.radio(
        "Navigate",
        ["Dashboard", "Rewards Catalog", "My Badges", "Challenges", "AI Advisor", "Transaction History", "Responsible AI"],
        label_visibility="collapsed"
    )

def render_dashboard():
    """Render the main dashboard"""
    member = st.session_state.member

    st.title("Your Rewards Dashboard")

    # Top metrics
    col1, col2, col3, col4 = st.columns(4)

    redemption_stats = st.session_state.redemption_stats

    with col1:
        st.metric("Points Balance", f"{member['points']:,}", "+150 this week")
    with col2:
        st.metric("Total Value Redeemed", f"${redemption_stats['total_value_redeemed']:,.2f}", f"{redemption_stats['total_redemptions']} items")
    with col3:
        st.metric("Points Redeemed", f"{redemption_stats['total_points_redeemed']:,}", f"{len(member['redeemed_rewards'])} rewards")
    with col4:
        earning_rate = TIERS[member['tier']]['earning_rate']
        st.metric("Earning Rate", f"{earning_rate}x", f"+{int((earning_rate-1)*100)}% bonus")

    st.markdown("---")

    # Two columns: Benefits and Activity
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader(f"{member['tier']} Member Benefits")
        for benefit in TIERS[member['tier']]['benefits']:
            st.markdown(f"✓ {benefit}")

    with col2:
        st.subheader("Points Activity (Last 30 Days)")
        # Sample activity data
        dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
        points_data = pd.DataFrame({
            'Date': dates,
            'Points': [random.randint(0, 200) for _ in range(30)]
        })
        fig = px.area(points_data, x='Date', y='Points',
                      color_discrete_sequence=['#667eea'])
        fig.update_layout(height=250, margin=dict(l=0, r=0, t=0, b=0))
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Personalized recommendations
    st.subheader("Recommended For You")
    rec_cols = st.columns(4)
    recommended = random.sample(REWARDS_CATALOG[:10], 4)

    for i, reward in enumerate(recommended):
        with rec_cols[i]:
            st.markdown(f"""
            <div style="text-align: center; padding: 20px; background: #f8f9fa; border-radius: 10px;">
                <div style="font-size: 48px;">{reward['image']}</div>
                <h4>{reward['name']}</h4>
                <p style="color: #667eea; font-weight: bold;">{reward['points']:,} pts</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Quick Redeem", key=f"rec_{reward['id']}"):
                if member['points'] >= reward['points']:
                    # Post to redemption API with value
                    reward_value = reward.get('value', 0.0)
                    success, result = post_redemption(
                        member['id'],
                        reward['name'],
                        reward['points'],
                        reward['category'],
                        reward_value
                    )
                    if success:
                        st.session_state.member['points'] -= reward['points']
                        st.session_state.member['redeemed_rewards'].append(reward)
                        # Track redemption stats
                        st.session_state.redemption_stats['total_redemptions'] += 1
                        st.session_state.redemption_stats['total_points_redeemed'] += reward['points']
                        st.session_state.redemption_stats['total_value_redeemed'] += reward_value
                        st.session_state.redemption_stats['redemption_history'].append({
                            'reward': reward['name'],
                            'points': reward['points'],
                            'value': reward_value,
                            'timestamp': datetime.now().isoformat()
                        })
                        st.success(f"Redeemed {reward['name']} (${reward_value:.2f})! Saved to your account.")
                        st.rerun()
                    else:
                        st.error(f"Redemption failed: {result}")
                else:
                    st.error("Not enough points!")

def render_rewards_catalog():
    """Render the rewards catalog"""
    member = st.session_state.member

    st.title("Rewards Catalog")
    st.markdown(f"You have **{member['points']:,} points** available to redeem")

    # Filters
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        category_filter = st.selectbox(
            "Category",
            ["All Categories", "Gift Cards", "Merchandise", "Experiences", "Digital", "Discounts", "Charitable"]
        )
    with col2:
        sort_by = st.selectbox("Sort By", ["Points: Low to High", "Points: High to Low", "Name A-Z"])
    with col3:
        affordable_only = st.checkbox("Affordable", value=False)

    # Filter rewards
    filtered_rewards = REWARDS_CATALOG.copy()

    if category_filter != "All Categories":
        filtered_rewards = [r for r in filtered_rewards if r['category'] == category_filter]

    if affordable_only:
        filtered_rewards = [r for r in filtered_rewards if r['points'] <= member['points']]

    # Sort
    if sort_by == "Points: Low to High":
        filtered_rewards.sort(key=lambda x: x['points'])
    elif sort_by == "Points: High to Low":
        filtered_rewards.sort(key=lambda x: x['points'], reverse=True)
    else:
        filtered_rewards.sort(key=lambda x: x['name'])

    st.markdown("---")

    # Display rewards in grid
    cols = st.columns(3)
    for i, reward in enumerate(filtered_rewards):
        with cols[i % 3]:
            # Check tier exclusivity
            is_locked = reward['tier_exclusive'] and reward['tier_exclusive'] != member['tier']
            if reward['tier_exclusive'] == 'Platinum' and member['tier'] in ['Gold', 'Silver']:
                is_locked = True
            elif reward['tier_exclusive'] == 'Silver' and member['tier'] == 'Gold':
                is_locked = True
            else:
                is_locked = False

            can_afford = member['points'] >= reward['points']

            with st.container(border=True):
                # Emoji icon centered
                st.markdown(f"<div style='text-align: center; font-size: 48px;'>{reward['image']}</div>", unsafe_allow_html=True)

                # Tags row
                tags = []
                if reward.get('limited'):
                    tags.append(":red[LIMITED]")
                if reward['tier_exclusive']:
                    tags.append(f":violet[{reward['tier_exclusive']} Only]")
                if tags:
                    st.markdown(" ".join(tags))

                # Reward name
                st.markdown(f"**{reward['name']}**")

                # Category and Value
                reward_value = reward.get('value', 0)
                st.caption(f"{reward['category']} • Value: ${reward_value:.2f}")

                # Points
                if can_afford:
                    st.markdown(f":violet[**{reward['points']:,} points**]")
                else:
                    st.markdown(f":red[**{reward['points']:,} points**]")

                # Stock
                st.caption(f"{reward['stock']} available")

                # Action button
                if is_locked:
                    st.button(f"🔒 {reward['tier_exclusive']} Only", disabled=True, key=f"cat_{reward['id']}")
                elif not can_afford:
                    st.button(f"Need {reward['points'] - member['points']:,} more pts", disabled=True, key=f"cat_{reward['id']}")
                else:
                    if st.button("Redeem Now", key=f"cat_{reward['id']}", type="primary"):
                        # Post to redemption API with value
                        reward_value = reward.get('value', 0.0)
                        success, result = post_redemption(
                            member['id'],
                            reward['name'],
                            reward['points'],
                            reward['category'],
                            reward_value
                        )
                        if success:
                            st.session_state.member['points'] -= reward['points']
                            st.session_state.member['redeemed_rewards'].append(reward)
                            # Track redemption stats
                            st.session_state.redemption_stats['total_redemptions'] += 1
                            st.session_state.redemption_stats['total_points_redeemed'] += reward['points']
                            st.session_state.redemption_stats['total_value_redeemed'] += reward_value
                            st.session_state.redemption_stats['redemption_history'].append({
                                'reward': reward['name'],
                                'points': reward['points'],
                                'value': reward_value,
                                'timestamp': datetime.now().isoformat()
                            })
                            st.success(f"Successfully redeemed {reward['name']} (${reward_value:.2f})! Saved to your account.")
                            st.balloons()
                            st.rerun()
                        else:
                            st.error(f"Redemption failed: {result}")

def render_badges():
    """Render badges page"""
    member = st.session_state.member

    st.title("My Badges & Achievements")

    earned_count = len(member['badges'])
    total_count = len(ALL_BADGES)

    st.progress(earned_count / total_count)
    st.markdown(f"**{earned_count}/{total_count}** badges earned")

    st.markdown("---")

    # Earned badges
    st.subheader("Earned Badges")
    earned_cols = st.columns(4)
    for i, badge_name in enumerate(member['badges']):
        badge = ALL_BADGES[badge_name]
        with earned_cols[i % 4]:
            st.markdown(f"""
            <div style="text-align: center; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        border-radius: 10px; color: white; margin: 5px;">
                <div style="font-size: 48px;">{badge['icon']}</div>
                <h4>{badge_name}</h4>
                <p style="font-size: 12px;">{badge['description']}</p>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")

    # Locked badges
    st.subheader("Badges to Unlock")
    locked_badges = [b for b in ALL_BADGES.keys() if b not in member['badges']]
    locked_cols = st.columns(4)
    for i, badge_name in enumerate(locked_badges):
        badge = ALL_BADGES[badge_name]
        with locked_cols[i % 4]:
            st.markdown(f"""
            <div style="text-align: center; padding: 20px; background: #e0e0e0;
                        border-radius: 10px; color: #999; margin: 5px;">
                <div style="font-size: 48px; filter: grayscale(100%);">{badge['icon']}</div>
                <h4>{badge_name}</h4>
                <p style="font-size: 12px;">{badge['description']}</p>
            </div>
            """, unsafe_allow_html=True)

def render_challenges():
    """Render challenges page"""
    st.title("Challenges & Quests")
    st.markdown("Complete challenges to earn bonus points!")

    st.markdown("---")

    # Active challenges
    st.subheader("Active Challenges")

    for challenge in CHALLENGES:
        progress_pct = (challenge['progress'] / challenge['target']) * 100

        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        padding: 20px; border-radius: 10px; color: white; margin: 10px 0;">
                <h3>{challenge['name']}</h3>
                <p>{challenge['description']}</p>
                <p><strong>Reward:</strong> {challenge['points']} bonus points</p>
                <p style="font-size: 12px;">Ends in: {challenge['ends']}</p>
            </div>
            """, unsafe_allow_html=True)
            st.progress(progress_pct / 100)
            st.caption(f"{challenge['progress']}/{challenge['target']} completed")

        with col2:
            if progress_pct >= 100:
                if st.button("Claim Reward!", key=f"challenge_{challenge['id']}"):
                    st.session_state.member['points'] += challenge['points']
                    st.success(f"+{challenge['points']} points!")
                    st.rerun()
            else:
                st.button("In Progress", disabled=True, key=f"challenge_{challenge['id']}")

    st.markdown("---")

    # Streak bonus
    st.subheader("Streak Bonus")
    streak = st.session_state.member['streak_days']

    st.markdown(f"""
    <div style="text-align: center; padding: 30px; background: #fff3cd; border-radius: 10px;">
        <div style="font-size: 64px;">🔥</div>
        <h2>{streak}-Day Streak!</h2>
        <p>Keep it going! At 14 days you'll earn <strong>500 bonus points</strong></p>
    </div>
    """, unsafe_allow_html=True)

    streak_progress = min(100, (streak / 14) * 100)
    st.progress(streak_progress / 100)
    st.caption(f"{14 - streak} days until streak bonus")

def render_ai_advisor():
    """Render AI advisor page with Responsible AI features"""
    st.title("AI Rewards Advisor")

    member = st.session_state.member
    prefs = st.session_state.ai_preferences

    # AI Transparency Banner
    render_ai_transparency_banner()

    # AI Preferences sidebar
    with st.expander("⚙️ AI Preferences & Privacy Controls", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            ai_enabled = st.toggle("Enable AI Features", value=prefs['ai_enabled'], key="ai_toggle")
            st.session_state.ai_preferences['ai_enabled'] = ai_enabled

            personalization = st.toggle("Personalized Recommendations", value=prefs['personalization_enabled'], key="personalization_toggle")
            st.session_state.ai_preferences['personalization_enabled'] = personalization

        with col2:
            data_consent = st.toggle("Data Collection for Improvement", value=prefs['data_collection_consent'], key="data_toggle")
            st.session_state.ai_preferences['data_collection_consent'] = data_consent

            if st.button("Clear My AI History"):
                st.session_state.messages = []
                st.session_state.ai_interactions = []
                st.success("AI history cleared!")

        st.caption("Your preferences are respected. Disabling AI will show rule-based recommendations instead.")

    st.markdown("---")

    # Check if AI is disabled by user
    if not prefs['ai_enabled']:
        st.warning("🚫 AI features are disabled. Showing rule-based recommendations.")
        st.markdown("### Rule-Based Recommendations")

        # Show non-AI recommendations
        affordable_rewards = [r for r in REWARDS_CATALOG if r['points'] <= member['points']]
        affordable_rewards.sort(key=lambda x: x['points'], reverse=True)

        for reward in affordable_rewards[:3]:
            with st.container(border=True):
                col1, col2 = st.columns([1, 3])
                with col1:
                    st.markdown(f"<div style='font-size: 48px; text-align: center;'>{reward['image']}</div>", unsafe_allow_html=True)
                with col2:
                    st.markdown(f"**{reward['name']}** - {reward['points']:,} pts")
                    reasons = get_recommendation_explanation(reward, member)
                    for reason in reasons:
                        st.caption(reason)
        return

    # Check for API key
    api_key = os.getenv("ANTHROPIC_API_KEY", "")

    if not api_key:
        st.warning("Set your ANTHROPIC_API_KEY environment variable for AI-powered recommendations")
        st.markdown("---")
        st.markdown("### Demo Recommendations")

        st.markdown(f"""
        Based on your **{member['tier']}** status and **{member['points']:,}** points:

        **Top Picks for You:**
        1. **$25 Store Gift Card** (1,200 pts) - Great value for your point balance
        2. **Personal Styling Session** (2,000 pts) - Available at your tier level
        3. **Wireless Charger** (1,500 pts) - Popular with members like you

        **Strategy Tip:** You're only ${2000 - member['annual_spend']:.2f} away from Platinum status!
        """)
    else:
        st.markdown("Ask me anything about your rewards, points strategy, or recommendations!")

        if 'messages' not in st.session_state:
            st.session_state.messages = []

        # Display chat history with feedback buttons
        for idx, message in enumerate(st.session_state.messages):
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

                # Add feedback buttons for assistant messages
                if message["role"] == "assistant":
                    feedback_col1, feedback_col2, feedback_col3 = st.columns([1, 1, 4])
                    with feedback_col1:
                        if st.button("👍", key=f"thumbs_up_{idx}", help="This was helpful"):
                            st.session_state.ai_feedback.append({
                                'message_idx': idx,
                                'feedback': 'positive',
                                'timestamp': datetime.now().isoformat()
                            })
                            st.toast("Thanks for your feedback!")
                    with feedback_col2:
                        if st.button("👎", key=f"thumbs_down_{idx}", help="This wasn't helpful"):
                            st.session_state.ai_feedback.append({
                                'message_idx': idx,
                                'feedback': 'negative',
                                'timestamp': datetime.now().isoformat()
                            })
                            st.toast("Thanks for your feedback! We'll improve.")
                    with feedback_col3:
                        if st.button("🚩 Report", key=f"report_{idx}", help="Report inappropriate content"):
                            st.session_state.ai_feedback.append({
                                'message_idx': idx,
                                'feedback': 'reported',
                                'timestamp': datetime.now().isoformat()
                            })
                            st.warning("Content reported for review. Thank you!")

        # Chat input
        if prompt := st.chat_input("Ask about your rewards..."):
            # Content safety check on input
            is_safe, safety_message = check_content_safety(prompt)

            st.session_state.messages.append({"role": "user", "content": prompt})

            with st.chat_message("user"):
                st.markdown(prompt)

            # Get purchase patterns for personalized context
            transactions_data = st.session_state.get('transactions_data', [])
            patterns = analyze_purchase_patterns(transactions_data)

            # Build recent purchases string
            recent_purchases = ""
            if transactions_data:
                for tx in transactions_data[:5]:
                    recent_purchases += f"- {tx.get('productName', 'Item')} (${tx.get('purchaseAmount', 0):.2f}, {tx.get('category', 'Other')})\n"

            # Get personalized recommendations
            recommendations, _ = get_personalized_recommendations(transactions_data, REWARDS_CATALOG, member['points'])
            rec_text = ""
            for rec in recommendations[:3]:
                rec_text += f"- {rec['reward']['name']} ({rec['reward']['points']:,} pts): {', '.join(rec['reasons'][:2])}\n"

            # Build context for AI with responsible AI guidelines and purchase history
            context = f"""You are an AI rewards advisor for OmniShop loyalty program.

            RESPONSIBLE AI GUIDELINES:
            - Never provide personal financial, investment, medical, or legal advice
            - Treat all members fairly regardless of their tier status
            - Be transparent about limitations of your recommendations
            - If unsure, acknowledge uncertainty rather than guessing
            - Keep responses focused on the rewards program only
            - Be inclusive and respectful in all responses

            Current member info:
            - Name: {member['name']}
            - Tier: {member['tier']}
            - Points Balance: {member['points']:,}
            - Total Spent: ${member['annual_spend']:.2f}
            - Streak: {member['streak_days']} days

            PURCHASE HISTORY ANALYSIS:
            - Total Transactions: {patterns.get('total_transactions', 0)}
            - Total Points Earned: {patterns.get('total_points_earned', 0):,}
            - Favorite Category: {patterns.get('favorite_category', 'Unknown')}
            - Top Categories: {', '.join([f"{cat} ({count})" for cat, count in patterns.get('top_categories', [])[:3]])}

            Recent Purchases:
            {recent_purchases}

            PERSONALIZED REWARD RECOMMENDATIONS (based on purchase history):
            {rec_text}

            Tier thresholds: Gold ($0-499), Silver ($500-1999), Platinum ($2000+)
            Earning rates: Gold 1x, Silver 1.25x, Platinum 1.5x

            Use the purchase history to make personalized recommendations.
            Reference specific past purchases when suggesting rewards.
            Help them maximize their rewards experience. Be friendly and helpful.
            Always explain WHY you're making a recommendation based on their shopping behavior."""

            try:
                import anthropic
                client = anthropic.Anthropic(api_key=api_key)

                with st.chat_message("assistant"):
                    response = client.messages.create(
                        model="claude-sonnet-4-20250514",
                        max_tokens=500,
                        system=context,
                        messages=[{"role": m["role"], "content": m["content"]}
                                  for m in st.session_state.messages]
                    )
                    assistant_message = response.content[0].text

                    # Content safety check on output
                    output_safe, output_message = check_content_safety(assistant_message)

                    if output_safe:
                        st.markdown(assistant_message)
                        log_ai_interaction("chat", prompt, assistant_message, was_filtered=False)
                    else:
                        filtered_response = "I apologize, but I can't provide that type of advice. Let me help you with your rewards questions instead. What would you like to know about earning or redeeming points?"
                        st.markdown(filtered_response)
                        log_ai_interaction("chat", prompt, filtered_response, was_filtered=True)
                        assistant_message = filtered_response

                st.session_state.messages.append({"role": "assistant", "content": assistant_message})

            except Exception as e:
                st.error(f"Error connecting to AI: {str(e)}")

def render_transaction_history():
    """Render transaction history from API"""
    st.title("Transaction History")

    member = st.session_state.member

    # Fetch real transactions from API
    api_transactions = st.session_state.get('transactions_data', [])

    if api_transactions:
        st.success(f"Showing {len(api_transactions)} transactions from your account")

        # Convert API data to display format
        transactions = []
        running_balance = member['points']

        for tx in reversed(api_transactions):  # Most recent first
            transactions.append({
                'date': tx.get('timestamp', '')[:10] if tx.get('timestamp') else 'N/A',
                'type': 'Earned',
                'description': tx.get('productName', 'Purchase'),
                'category': tx.get('category', 'Other'),
                'amount': tx.get('purchaseAmount', 0),
                'points': tx.get('points', 0),
                'balance': running_balance
            })
            running_balance -= tx.get('points', 0)

        transactions.reverse()  # Back to chronological order
    else:
        st.warning("Unable to fetch transactions from API. Showing sample data.")
        transactions = [
            {'date': '2026-01-13', 'type': 'Earned', 'description': 'Purchase', 'category': 'Electronics', 'amount': 100, 'points': 150, 'balance': 18574},
        ]

    # Summary metrics
    total_earned = sum(tx['points'] for tx in transactions)
    total_spent = sum(tx['amount'] for tx in transactions)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Transactions", len(transactions))
    with col2:
        st.metric("Points Earned", f"{total_earned:,}")
    with col3:
        st.metric("Total Spent", f"${total_spent:,.2f}")
    with col4:
        st.metric("Current Balance", f"{member['points']:,}")

    st.markdown("---")

    # Filter options
    col1, col2 = st.columns(2)
    with col1:
        categories = ['All'] + list(set(tx.get('category', 'Other') for tx in transactions))
        category_filter = st.selectbox("Category", categories)
    with col2:
        sort_order = st.selectbox("Sort By", ["Newest First", "Oldest First", "Highest Points", "Highest Amount"])

    # Filter and sort
    filtered_tx = transactions.copy()
    if category_filter != "All":
        filtered_tx = [tx for tx in filtered_tx if tx.get('category') == category_filter]

    if sort_order == "Newest First":
        filtered_tx.reverse()
    elif sort_order == "Highest Points":
        filtered_tx.sort(key=lambda x: x['points'], reverse=True)
    elif sort_order == "Highest Amount":
        filtered_tx.sort(key=lambda x: x['amount'], reverse=True)

    st.markdown("---")

    # Display transactions
    for tx in filtered_tx:
        with st.container(border=True):
            col1, col2, col3, col4 = st.columns([2, 3, 1, 1])
            with col1:
                st.caption(tx['date'])
                st.markdown(f"**{tx.get('category', 'Purchase')}**")
            with col2:
                st.markdown(f"**{tx['description']}**")
                st.caption(f"${tx['amount']:.2f}")
            with col3:
                st.markdown(f":green[**+{tx['points']:,} pts**]")
            with col4:
                st.caption("Balance")
                st.markdown(f"**{tx['balance']:,}**")

def render_responsible_ai():
    """Render Responsible AI dashboard"""
    st.title("Responsible AI Dashboard")
    st.markdown("Our commitment to ethical, fair, and transparent AI")

    # Principles section
    st.subheader("Our AI Principles")
    cols = st.columns(3)
    for idx, principle in enumerate(RESPONSIBLE_AI_PRINCIPLES):
        with cols[idx % 3]:
            with st.container(border=True):
                st.markdown(f"### {principle['icon']} {principle['name']}")
                st.markdown(principle['description'])

    st.markdown("---")

    # Fairness Metrics
    st.subheader("Fairness Metrics")
    metrics = calculate_fairness_metrics()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Fairness Score", f"{metrics['fairness_score']:.0%}", "+2%")
    with col2:
        st.metric("Total Interactions", metrics['total_interactions'], "+45 today")
    with col3:
        st.metric("Bias Flags", metrics['bias_flags'], "0 this week")
    with col4:
        st.metric("Content Filtered", len([i for i in st.session_state.ai_interactions if i.get('was_filtered')]), "")

    st.markdown("---")

    # Recommendation Distribution by Tier
    st.subheader("Recommendation Distribution by Tier")
    st.markdown("Ensuring fair treatment across all membership levels")

    dist = metrics['recommendation_distribution']

    col1, col2 = st.columns(2)

    with col1:
        # Bar chart for recommendation counts
        tier_data = pd.DataFrame({
            'Tier': list(dist.keys()),
            'Recommendations': [d['count'] for d in dist.values()],
            'Avg Points': [d['avg_points'] for d in dist.values()]
        })
        fig = px.bar(tier_data, x='Tier', y='Recommendations',
                     color='Tier', color_discrete_map={'Gold': '#FFD700', 'Silver': '#C0C0C0', 'Platinum': '#E5E4E2'},
                     title="Recommendations by Tier")
        fig.update_layout(showlegend=False, height=300)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Success rate by tier
        success_data = pd.DataFrame({
            'Tier': list(metrics['redemption_success_rate'].keys()),
            'Success Rate': [v * 100 for v in metrics['redemption_success_rate'].values()]
        })
        fig = px.bar(success_data, x='Tier', y='Success Rate',
                     color='Tier', color_discrete_map={'Gold': '#FFD700', 'Silver': '#C0C0C0', 'Platinum': '#E5E4E2'},
                     title="Redemption Success Rate (%)")
        fig.update_layout(showlegend=False, height=300, yaxis_range=[0, 100])
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Response Time Equity
    st.subheader("Response Time Equity")
    st.markdown("AI response times should be equal across all tiers")

    response_times = metrics['response_time_ms']
    rt_data = pd.DataFrame({
        'Tier': list(response_times.keys()),
        'Response Time (ms)': list(response_times.values())
    })

    col1, col2, col3 = st.columns(3)
    for idx, (tier, time) in enumerate(response_times.items()):
        with [col1, col2, col3][idx]:
            variance = abs(time - 241) / 241 * 100  # variance from mean
            status = "✅" if variance < 5 else "⚠️"
            st.metric(f"{tier} Tier", f"{time}ms", f"{status} {variance:.1f}% variance")

    st.markdown("---")

    # User Feedback Summary
    st.subheader("User Feedback Summary")

    feedback = st.session_state.ai_feedback
    if feedback:
        positive = len([f for f in feedback if f['feedback'] == 'positive'])
        negative = len([f for f in feedback if f['feedback'] == 'negative'])
        reported = len([f for f in feedback if f['feedback'] == 'reported'])

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("👍 Positive", positive)
        with col2:
            st.metric("👎 Negative", negative)
        with col3:
            st.metric("🚩 Reported", reported)

        if positive + negative > 0:
            satisfaction = positive / (positive + negative) * 100
            st.progress(satisfaction / 100)
            st.caption(f"User Satisfaction: {satisfaction:.1f}%")
    else:
        st.info("No feedback collected yet. Feedback helps us improve AI quality.")

    st.markdown("---")

    # AI Interaction Audit Log
    st.subheader("AI Interaction Audit Log")
    st.markdown("All AI interactions are logged for accountability")

    interactions = st.session_state.ai_interactions
    if interactions:
        df = pd.DataFrame(interactions)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No AI interactions logged in this session.")

    st.markdown("---")

    # Data Privacy Controls
    st.subheader("Your Data & Privacy")

    with st.expander("View Your AI Data", expanded=False):
        st.json({
            'ai_preferences': st.session_state.ai_preferences,
            'feedback_count': len(st.session_state.ai_feedback),
            'interaction_count': len(st.session_state.ai_interactions),
            'messages_count': len(st.session_state.get('messages', []))
        })

        if st.button("Download My Data"):
            import json
            data = {
                'preferences': st.session_state.ai_preferences,
                'feedback': st.session_state.ai_feedback,
                'interactions': st.session_state.ai_interactions
            }
            st.download_button(
                "Download JSON",
                json.dumps(data, indent=2),
                file_name="my_ai_data.json",
                mime="application/json"
            )

        if st.button("Delete All My AI Data", type="primary"):
            st.session_state.ai_feedback = []
            st.session_state.ai_interactions = []
            st.session_state.messages = []
            st.success("All AI data deleted!")
            st.rerun()

# Main app
def main():
    page = render_sidebar()

    if page == "Dashboard":
        render_dashboard()
    elif page == "Rewards Catalog":
        render_rewards_catalog()
    elif page == "My Badges":
        render_badges()
    elif page == "Challenges":
        render_challenges()
    elif page == "AI Advisor":
        render_ai_advisor()
    elif page == "Transaction History":
        render_transaction_history()
    elif page == "Responsible AI":
        render_responsible_ai()

if __name__ == "__main__":
    main()
