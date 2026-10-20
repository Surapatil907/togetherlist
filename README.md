# TogetherList 💕
> **"Your wishlist, their perfect surprise."**

A free, private personal gift wishlist web application designed specifically for couples to curate wishlists, track special relationship dates, and secretly plan gift surprises without spoiling the moment.

Built with **Python**, **Streamlit**, and **Supabase Free Tier** (PostgreSQL, Authentication, and Storage).

---

## Features

- 🔐 **Couple Authentication & Pairing:**
  - Secure email/password registration, login, logout, and password recovery.
  - Partner 1 creates a private space and generates an invite code (e.g. `TOGETHER-9K4X2P`).
  - Partner 2 joins using the code.
  - Enforces a strict 2-member limit, prevents self-joining, and blocks unauthorized reuse.
- 🎁 **Personal Wishlists:**
  - Product title, description, retailer/shop name, direct URL, price, and currency (default GBP `£`).
  - Priority levels (*Must-have*, *Really want*, *Nice to have*) and categories.
  - Preference attributes: size, colour, model/brand, and notes.
  - Product photo upload (saved directly to Supabase Storage) or direct image URL.
  - Search, category filter, priority filter, and sorting (by price or date).
  - Ownership security: Only the item creator can edit or delete their gifts.
- 📅 **Special Dates & Milestones:**
  - Birthday, anniversary, Valentine's Day, Christmas, and custom occasion tracking.
  - Automatic annual recurring countdowns (days remaining).
  - Target celebration budgets and gift association.
- 🤫 **Secret Gift Planner:**
  - When viewing your partner's wishlist, privately record your intention to buy items.
  - Track statuses: *Considering*, *Reserved*, *Purchased*, *Ordered*, *Delivered*, *Revealed*.
  - Private notes (order tracking, size secrets) and spending budget tracking.
  - **Confidentiality:** Stored separately and isolated by Row Level Security (RLS) so the recipient cannot see your plans before the reveal.
  - Deliberate **"Reveal to Partner"** action to unveil the surprise when gifted.
- 📊 **Romantic Couple Dashboard:**
  - Partner connection status & avatars.
  - Wishlist item counters and total wishlist values.
  - Upcoming celebration countdown banner.
  - Recent wishlist items preview.

---

## Architecture & Technology Stack

```
togetherlist/
│
├── app.py                      # Main entrypoint, auth routing, pairing, & dashboard
├── requirements.txt            # Python dependencies (Streamlit, Supabase, etc.)
├── README.md                   # Documentation and setup guide
├── .gitignore                  # Git ignore rules
├── .env.example                # Template for environment variables
│
├── .streamlit/
│   └── config.toml             # Custom warm cream & soft rose design theme
│
├── components/
│   ├── gift_card.py            # Responsive gift card component with HTML/CSS
│   └── navigation.py           # Header, couple status banner, & sidebar
│
├── pages/
│   ├── 1_My_Wishlist.py        # Manage own wishlist (add, edit, archive, delete)
│   ├── 2_Partner_Wishlist.py   # View partner's wishlist & plan secret gifts
│   ├── 3_Special_Dates.py      # Relationship anniversaries, birthdays, & countdowns
│   ├── 4_Secret_Gift_Planner.py# Buyer's confidential gift purchase workspace
│   └── 5_Settings.py           # Profile settings, couple status, & disconnect
│
├── services/
│   ├── auth_service.py         # Supabase Auth integration & profile management
│   ├── couple_service.py       # Pairing logic, invitation generator, & member limits
│   ├── wishlist_service.py     # Wishlist CRUD, image upload, filters, & sorting
│   ├── occasion_service.py     # Special dates & annual countdown calculations
│   ├── gift_planning_service.py# Secret purchase planner & privacy enforcement
│   ├── supabase_client.py      # Session-scoped client initialization
│   └── demo_store.py           # Local in-memory store for instant zero-config preview
│
├── database/
│   └── schema.sql              # PostgreSQL schema, triggers, RLS policies, & bucket
│
└── tests/
    ├── test_validation.py      # Form, price, and date calculation unit tests
    └── test_permissions.py     # Membership, invitation, and privacy isolation tests
```

---

## Free-Tier Setup Instructions (Supabase)

### Step 1: Create a Free Supabase Project
1. Go to [supabase.com](https://supabase.com) and sign up for a free account.
2. Click **"New Project"**.
3. Choose a name (e.g. `togetherlist`), set a database password, and pick a region close to you.
4. Wait ~2 minutes for the database to provision.

### Step 2: Run the Database Schema
1. In your Supabase dashboard, go to the **SQL Editor** tab (left sidebar).
2. Click **"New Query"**.
3. Copy the entire contents of [`database/schema.sql`](file:///Users/surajpatil/.gemini/antigravity-ide/scratch/togetherlist/database/schema.sql) and paste it into the editor.
4. Click **"Run"**.
   - This creates all 8 tables, indexes, triggers (including the 2-member limit trigger), Row Level Security policies, and the `wishlist-images` storage bucket.

### Step 3: Configure Authentication
1. In Supabase, go to **Authentication** -> **Providers** -> **Email**.
2. For convenience in personal testing, you can disable **"Confirm email"** if you want instant login without clicking confirmation emails.

### Step 4: Get API Credentials
1. In Supabase, go to **Project Settings** -> **API**.
2. Copy:
   - **Project URL** (e.g., `https://xyzcompany.supabase.co`)
   - **Project API Keys** -> `anon` `public` key. *(Never use the `service_role` secret key!)*

---

## Local Installation & Running

### 1. Clone & Navigate to Project Directory
```bash
cd /Users/surajpatil/.gemini/antigravity-ide/scratch/togetherlist
```

### 2. Install Dependencies
```bash
python3 -m pip install -r requirements.txt
```

### 3. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Open `.env` and fill in your Supabase credentials:
```ini
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your_supabase_anon_key_here
```

*(Note: If you run the app without `.env`, TogetherList automatically launches in **Local Demonstration Mode**, allowing you to test the entire application workflow immediately without setup!)*

### 4. Run the Streamlit App
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

---

## User Journey & Verification (Testing Both Partners)

To test the complete workflow:

1. **Partner 1 (You):**
   - Open browser at `http://localhost:8501`.
   - Go to **Create Account** tab: register as `Suraj` (`suraj@example.com`).
   - On the welcome screen, click **"Create Space & Invite Partner"**.
   - You will see a unique invitation code: e.g. `TOGETHER-9K4X2P`.
   - Go to **🎁 My Wishlist** and add a gift (e.g. *Mechanical Keyboard*, £120.00, priority *Must-have*).

2. **Partner 2 (Your Partner / Incognito Window):**
   - Open an **Incognito / Private Browsing** window at `http://localhost:8501`.
   - Go to **Create Account**: register as `Emma` (`emma@example.com`).
   - Under **Join Partner's Space**, enter the invitation code `TOGETHER-9K4X2P` and click **"Connect with Partner"**.
   - The couple space is now paired!

3. **Browse & Secret Planner Verification:**
   - Partner 2 navigates to **👀 Suraj's Wishlist**.
   - Partner 2 sees the *Mechanical Keyboard*.
   - Partner 2 clicks **"🤫 Plan Secret Surprise"**, selects status *Ordered*, adds private note *"Keychron K2 arriving Friday"*, and clicks Save.
   - Switch back to Partner 1's window: Partner 1 **cannot see** any secret status, note, or price details.
   - When the occasion arrives, Partner 2 goes to **🤫 Secret Gift Planner** and clicks **"🎉 Reveal to Partner"**. Now both partners celebrate!

---

## Running Automated Tests

Run the test suite with `pytest`:
```bash
python3 -m pytest tests/ -v
```

All 7 test cases verify:
- Registration validation (email format, password length, required fields).
- Wishlist validation (non-empty title, non-negative price).
- Annual recurrence and countdown logic for birthdays and anniversaries.
- Invitation pairing rules (prevent self-joining, prevent code reuse).
- Couple capacity enforcement (maximum 2 partners).
- Wishlist edit/delete authorization (only owner can modify).
- Secret gift privacy isolation (confidential until deliberately revealed).

---

## Free Cloud Deployment (Streamlit Community Cloud)

1. Push your repository to GitHub:
   ```bash
   git init
   git add .
   git commit -m "Initial TogetherList commit"
   git remote add origin https://github.com/your-username/togetherlist.git
   git push -u origin main
   ```
2. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.
3. Click **"New app"**, select your repository, branch (`main`), and main file path (`app.py`).
4. Click **"Advanced settings..."** -> **Secrets** and paste:
   ```toml
   SUPABASE_URL = "https://your-project-id.supabase.co"
   SUPABASE_KEY = "your_supabase_anon_key_here"
   ```
5. Click **"Deploy!"**. Your free personal wishlist app is now live with 24/7 HTTPS access!

---

## Free-Tier Limits & Practical Notes

- **Supabase Free Tier:**
  - 500 MB PostgreSQL database storage (enough for millions of wishlist items).
  - 1 GB Storage for product photos.
  - 50,000 monthly active users.
  - Pause policy: Free Supabase projects pause after 1 week of complete inactivity; opening the app unpauses it.
- **No Paid APIs:**
  - In-app countdowns and dashboard reminders replace costly SMS or email APIs.
  - Manual image uploads to Supabase Storage or direct web URLs eliminate paid image generation or web scraping proxies.
