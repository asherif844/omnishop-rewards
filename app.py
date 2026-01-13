import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random
import os

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

# Initialize session state
if 'member' not in st.session_state:
    st.session_state.member = {
        'id': 'MEM-001',
        'name': 'Alex Johnson',
        'email': 'alex.johnson@email.com',
        'tier': 'Silver',
        'points': 2450,
        'lifetime_points': 8750,
        'annual_spend': 1250.00,
        'member_since': '2024-03-15',
        'badges': ['First Purchase', 'Review Writer', 'Social Sharer', 'Streak Master'],
        'streak_days': 12,
        'redeemed_rewards': []
    }

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

# Sample reward catalog
REWARDS_CATALOG = [
    {'id': 1, 'name': '$10 Store Gift Card', 'category': 'Gift Cards', 'points': 500, 'image': '🎁', 'tier_exclusive': None, 'stock': 100},
    {'id': 2, 'name': '$25 Store Gift Card', 'category': 'Gift Cards', 'points': 1200, 'image': '🎁', 'tier_exclusive': None, 'stock': 75},
    {'id': 3, 'name': '$50 Store Gift Card', 'category': 'Gift Cards', 'points': 2300, 'image': '🎁', 'tier_exclusive': None, 'stock': 50},
    {'id': 4, 'name': 'Premium Headphones', 'category': 'Merchandise', 'points': 5000, 'image': '🎧', 'tier_exclusive': None, 'stock': 25},
    {'id': 5, 'name': 'Wireless Charger', 'category': 'Merchandise', 'points': 1500, 'image': '🔌', 'tier_exclusive': None, 'stock': 60},
    {'id': 6, 'name': 'Smart Watch Band', 'category': 'Merchandise', 'points': 800, 'image': '⌚', 'tier_exclusive': None, 'stock': 80},
    {'id': 7, 'name': 'VIP Shopping Experience', 'category': 'Experiences', 'points': 3500, 'image': '👔', 'tier_exclusive': 'Platinum', 'stock': 10},
    {'id': 8, 'name': 'Personal Styling Session', 'category': 'Experiences', 'points': 2000, 'image': '✨', 'tier_exclusive': 'Silver', 'stock': 20},
    {'id': 9, 'name': 'Streaming Subscription (1 month)', 'category': 'Digital', 'points': 600, 'image': '📺', 'tier_exclusive': None, 'stock': 200},
    {'id': 10, 'name': 'E-Book Bundle', 'category': 'Digital', 'points': 400, 'image': '📚', 'tier_exclusive': None, 'stock': 150},
    {'id': 11, 'name': '20% Off Coupon', 'category': 'Discounts', 'points': 300, 'image': '🏷️', 'tier_exclusive': None, 'stock': 500},
    {'id': 12, 'name': 'Free Express Shipping (3 uses)', 'category': 'Discounts', 'points': 450, 'image': '🚚', 'tier_exclusive': None, 'stock': 300},
    {'id': 13, 'name': 'Charity Donation - $10', 'category': 'Charitable', 'points': 500, 'image': '💝', 'tier_exclusive': None, 'stock': 999},
    {'id': 14, 'name': 'Limited Edition Tote Bag', 'category': 'Merchandise', 'points': 1800, 'image': '👜', 'tier_exclusive': None, 'stock': 30, 'limited': True},
    {'id': 15, 'name': 'Exclusive Member Event Access', 'category': 'Experiences', 'points': 4000, 'image': '🎉', 'tier_exclusive': 'Platinum', 'stock': 15},
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

    with col1:
        st.metric("Points Balance", f"{member['points']:,}", "+150 this week")
    with col2:
        st.metric("Annual Spend", f"${member['annual_spend']:,.2f}", "+$125.00")
    with col3:
        st.metric("Rewards Redeemed", len(member['redeemed_rewards']), "+1 this month")
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
                    st.session_state.member['points'] -= reward['points']
                    st.session_state.member['redeemed_rewards'].append(reward)
                    st.success(f"Redeemed {reward['name']}!")
                    st.rerun()
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

                # Category
                st.caption(reward['category'])

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
                        st.session_state.member['points'] -= reward['points']
                        st.session_state.member['redeemed_rewards'].append(reward)
                        st.success(f"Successfully redeemed {reward['name']}!")
                        st.balloons()
                        st.rerun()

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

            # Build context for AI with responsible AI guidelines
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
            - Points: {member['points']:,}
            - Annual spend: ${member['annual_spend']:.2f}
            - Streak: {member['streak_days']} days

            Tier thresholds: Gold ($0-499), Silver ($500-1999), Platinum ($2000+)
            Earning rates: Gold 1x, Silver 1.25x, Platinum 1.5x

            Help them maximize their rewards experience. Be friendly and helpful.
            Always explain WHY you're making a recommendation."""

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
    """Render transaction history"""
    st.title("Transaction History")

    # Sample transaction data
    transactions = [
        {'date': '2026-01-13', 'type': 'Earned', 'description': 'Purchase at OmniShop Online', 'points': 125, 'balance': 2450},
        {'date': '2026-01-12', 'type': 'Earned', 'description': 'Review bonus', 'points': 50, 'balance': 2325},
        {'date': '2026-01-10', 'type': 'Redeemed', 'description': '$10 Gift Card', 'points': -500, 'balance': 2275},
        {'date': '2026-01-08', 'type': 'Earned', 'description': 'Purchase at Store #142', 'points': 200, 'balance': 2775},
        {'date': '2026-01-05', 'type': 'Bonus', 'description': 'Streak bonus (7 days)', 'points': 100, 'balance': 2575},
        {'date': '2026-01-03', 'type': 'Earned', 'description': 'Purchase at OmniShop Online', 'points': 175, 'balance': 2475},
        {'date': '2025-12-28', 'type': 'Earned', 'description': 'Holiday bonus 2x points', 'points': 300, 'balance': 2300},
        {'date': '2025-12-25', 'type': 'Bonus', 'description': 'Birthday reward', 'points': 250, 'balance': 2000},
    ]

    # Filter options
    col1, col2 = st.columns(2)
    with col1:
        type_filter = st.selectbox("Transaction Type", ["All", "Earned", "Redeemed", "Bonus"])
    with col2:
        date_range = st.selectbox("Date Range", ["Last 7 days", "Last 30 days", "Last 90 days", "All time"])

    # Display transactions
    df = pd.DataFrame(transactions)

    if type_filter != "All":
        df = df[df['type'] == type_filter]

    st.markdown("---")

    for _, tx in df.iterrows():
        col1, col2, col3 = st.columns([2, 3, 1])
        with col1:
            st.caption(tx['date'])
            color = '#28a745' if tx['points'] > 0 else '#dc3545'
            st.markdown(f"<span style='color: {color}; font-weight: bold;'>{'+' if tx['points'] > 0 else ''}{tx['points']} pts</span>", unsafe_allow_html=True)
        with col2:
            st.markdown(f"**{tx['type']}**")
            st.caption(tx['description'])
        with col3:
            st.caption("Balance")
            st.markdown(f"**{tx['balance']:,}**")
        st.markdown("---")

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
