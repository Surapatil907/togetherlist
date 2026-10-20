-- ====================================================================
-- TogetherList — Supabase PostgreSQL Database Schema
-- A Free Personal Gift Wishlist App for Couples
-- ====================================================================

-- 1. Enable UUID Extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 2. Profiles Table (Extends auth.users)
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    display_name TEXT NOT NULL,
    avatar_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Trigger to auto-create profile on Supabase auth.users signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.profiles (id, display_name, avatar_url)
    VALUES (
        NEW.id,
        COALESCE(NEW.raw_user_meta_data->>'display_name', split_part(NEW.email, '@', 1)),
        COALESCE(NEW.raw_user_meta_data->>'avatar_url', NULL)
    )
    ON CONFLICT (id) DO UPDATE SET
        display_name = EXCLUDED.display_name,
        updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- 3. Couples Table
CREATE TABLE IF NOT EXISTS public.couples (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT DEFAULT 'Our Couple Space',
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'disconnected')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. Couple Members Table
CREATE TABLE IF NOT EXISTS public.couple_members (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    couple_id UUID NOT NULL REFERENCES public.couples(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    role TEXT DEFAULT 'partner' CHECK (role IN ('creator', 'partner')),
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'disconnected')),
    joined_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(couple_id, user_id)
);

-- Index for quick lookup of active couple membership
CREATE INDEX IF NOT EXISTS idx_couple_members_user ON public.couple_members(user_id, status);
CREATE INDEX IF NOT EXISTS idx_couple_members_couple ON public.couple_members(couple_id, status);

-- Trigger Function: Enforce strict maximum of 2 active members per couple
CREATE OR REPLACE FUNCTION public.enforce_couple_max_two_members()
RETURNS TRIGGER AS $$
DECLARE
    active_count INT;
BEGIN
    IF NEW.status = 'active' THEN
        SELECT COUNT(*) INTO active_count
        FROM public.couple_members
        WHERE couple_id = NEW.couple_id AND status = 'active' AND id != COALESCE(NEW.id, '00000000-0000-0000-0000-000000000000');
        
        IF active_count >= 2 THEN
            RAISE EXCEPTION 'A couple space can have at most 2 active partners.';
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_check_couple_members ON public.couple_members;
CREATE TRIGGER trg_check_couple_members
    BEFORE INSERT OR UPDATE ON public.couple_members
    FOR EACH ROW EXECUTE FUNCTION public.enforce_couple_max_two_members();

-- 5. Couple Invitations Table
CREATE TABLE IF NOT EXISTS public.couple_invitations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    couple_id UUID NOT NULL REFERENCES public.couples(id) ON DELETE CASCADE,
    created_by UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    code TEXT NOT NULL UNIQUE,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'accepted', 'expired', 'cancelled')),
    expires_at TIMESTAMPTZ NOT NULL DEFAULT (NOW() + INTERVAL '7 days'),
    accepted_by UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
    accepted_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_invitations_code ON public.couple_invitations(code);

-- 6. Special Occasions Table
CREATE TABLE IF NOT EXISTS public.occasions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    couple_id UUID NOT NULL REFERENCES public.couples(id) ON DELETE CASCADE,
    created_by UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    event_date DATE NOT NULL,
    is_recurring BOOLEAN DEFAULT FALSE,
    occasion_type TEXT DEFAULT 'custom' CHECK (occasion_type IN ('birthday', 'anniversary', 'valentines', 'christmas', 'custom')),
    description TEXT,
    budget NUMERIC(10, 2),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_occasions_couple_date ON public.occasions(couple_id, event_date);

-- 7. Wishlist Items Table
CREATE TABLE IF NOT EXISTS public.wishlist_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    couple_id UUID NOT NULL REFERENCES public.couples(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT,
    image_url TEXT,
    price NUMERIC(10, 2) DEFAULT 0.00,
    currency TEXT DEFAULT 'GBP',
    retailer TEXT,
    url TEXT,
    category TEXT DEFAULT 'General',
    priority TEXT DEFAULT 'Really want' CHECK (priority IN ('Must-have', 'Really want', 'Nice to have')),
    preferred_size TEXT,
    preferred_color TEXT,
    brand_or_model TEXT,
    notes TEXT,
    occasion_id UUID REFERENCES public.occasions(id) ON DELETE SET NULL,
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'archived', 'no_longer_wanted')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_wishlist_couple_user ON public.wishlist_items(couple_id, user_id, status);

-- 8. Private Gift Plans (Buyer's Private Workspace)
CREATE TABLE IF NOT EXISTS public.private_gift_plans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    couple_id UUID NOT NULL REFERENCES public.couples(id) ON DELETE CASCADE,
    buyer_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    partner_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    title TEXT DEFAULT 'Secret Plan',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(couple_id, buyer_id)
);

-- 9. Private Gift Plan Items (Specific Item Intentions)
CREATE TABLE IF NOT EXISTS public.private_gift_plan_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    plan_id UUID NOT NULL REFERENCES public.private_gift_plans(id) ON DELETE CASCADE,
    buyer_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    wishlist_item_id UUID NOT NULL REFERENCES public.wishlist_items(id) ON DELETE CASCADE,
    status TEXT DEFAULT 'Considering' CHECK (status IN ('Considering', 'Reserved', 'Purchased', 'Ordered', 'Delivered', 'Revealed')),
    private_notes TEXT,
    purchase_date DATE,
    reveal_date DATE,
    is_revealed BOOLEAN DEFAULT FALSE,
    estimated_spend NUMERIC(10, 2) DEFAULT 0.00,
    actual_spend NUMERIC(10, 2) DEFAULT 0.00,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(plan_id, wishlist_item_id)
);

CREATE INDEX IF NOT EXISTS idx_plan_items_buyer ON public.private_gift_plan_items(buyer_id);
CREATE INDEX IF NOT EXISTS idx_plan_items_wishlist ON public.private_gift_plan_items(wishlist_item_id);

-- ====================================================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- ====================================================================

ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.couples ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.couple_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.couple_invitations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.occasions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.wishlist_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.private_gift_plans ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.private_gift_plan_items ENABLE ROW LEVEL SECURITY;

-- Helper security function: Check if current authenticated user belongs to couple
CREATE OR REPLACE FUNCTION public.is_couple_member(target_couple_id UUID)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM public.couple_members
        WHERE couple_id = target_couple_id
          AND user_id = auth.uid()
          AND status = 'active'
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 1. PROFILES POLICIES
CREATE POLICY "Users can read own profile and partner profile"
ON public.profiles FOR SELECT
USING (
    id = auth.uid()
    OR id IN (
        SELECT cm2.user_id
        FROM public.couple_members cm1
        JOIN public.couple_members cm2 ON cm1.couple_id = cm2.couple_id
        WHERE cm1.user_id = auth.uid()
          AND cm1.status = 'active'
          AND cm2.status = 'active'
    )
);

CREATE POLICY "Users can insert their own profile"
ON public.profiles FOR INSERT
WITH CHECK (id = auth.uid());

CREATE POLICY "Users can update their own profile"
ON public.profiles FOR UPDATE
USING (id = auth.uid())
WITH CHECK (id = auth.uid());

-- 2. COUPLES POLICIES
CREATE POLICY "Active couple members can view couple"
ON public.couples FOR SELECT
USING (public.is_couple_member(id));

CREATE POLICY "Authenticated users can create a couple"
ON public.couples FOR INSERT
WITH CHECK (auth.uid() IS NOT NULL);

CREATE POLICY "Active couple members can update couple"
ON public.couples FOR UPDATE
USING (public.is_couple_member(id))
WITH CHECK (public.is_couple_member(id));

-- 3. COUPLE MEMBERS POLICIES
CREATE POLICY "Members can view members of their couple"
ON public.couple_members FOR SELECT
USING (public.is_couple_member(couple_id) OR user_id = auth.uid());

CREATE POLICY "Authenticated user can join as couple member"
ON public.couple_members FOR INSERT
WITH CHECK (user_id = auth.uid());

CREATE POLICY "User can update their own membership or couple status"
ON public.couple_members FOR UPDATE
USING (user_id = auth.uid() OR public.is_couple_member(couple_id))
WITH CHECK (user_id = auth.uid() OR public.is_couple_member(couple_id));

-- 4. INVITATIONS POLICIES
CREATE POLICY "View invitation if creator, member, or pending code lookup"
ON public.couple_invitations FOR SELECT
USING (
    created_by = auth.uid() 
    OR public.is_couple_member(couple_id)
    OR status = 'pending'
);

CREATE POLICY "Couple creator can insert invitation"
ON public.couple_invitations FOR INSERT
WITH CHECK (
    created_by = auth.uid()
    AND public.is_couple_member(couple_id)
);

CREATE POLICY "Update invitation upon acceptance or cancellation"
ON public.couple_invitations FOR UPDATE
USING (
    created_by = auth.uid()
    OR (status = 'pending' AND auth.uid() IS NOT NULL)
);

-- 5. OCCASIONS POLICIES
CREATE POLICY "Couple members can view occasions"
ON public.occasions FOR SELECT
USING (public.is_couple_member(couple_id));

CREATE POLICY "Couple members can insert occasions"
ON public.occasions FOR INSERT
WITH CHECK (public.is_couple_member(couple_id) AND created_by = auth.uid());

CREATE POLICY "Couple members can update occasions"
ON public.occasions FOR UPDATE
USING (public.is_couple_member(couple_id))
WITH CHECK (public.is_couple_member(couple_id));

CREATE POLICY "Couple members can delete occasions"
ON public.occasions FOR DELETE
USING (public.is_couple_member(couple_id));

-- 6. WISHLIST ITEMS POLICIES
CREATE POLICY "Couple members can view wishlist items in their couple"
ON public.wishlist_items FOR SELECT
USING (public.is_couple_member(couple_id));

CREATE POLICY "Users can insert their own wishlist items"
ON public.wishlist_items FOR INSERT
WITH CHECK (user_id = auth.uid() AND public.is_couple_member(couple_id));

CREATE POLICY "Users can only update their own wishlist items"
ON public.wishlist_items FOR UPDATE
USING (user_id = auth.uid())
WITH CHECK (user_id = auth.uid());

CREATE POLICY "Users can only delete their own wishlist items"
ON public.wishlist_items FOR DELETE
USING (user_id = auth.uid());

-- 7. PRIVATE GIFT PLANS POLICIES (Strict Buyer-Only Access)
CREATE POLICY "Buyer can view their own private gift plans"
ON public.private_gift_plans FOR SELECT
USING (buyer_id = auth.uid());

CREATE POLICY "Buyer can insert their own private gift plans"
ON public.private_gift_plans FOR INSERT
WITH CHECK (buyer_id = auth.uid() AND public.is_couple_member(couple_id));

CREATE POLICY "Buyer can update their own private gift plans"
ON public.private_gift_plans FOR UPDATE
USING (buyer_id = auth.uid())
WITH CHECK (buyer_id = auth.uid());

CREATE POLICY "Buyer can delete their own private gift plans"
ON public.private_gift_plans FOR DELETE
USING (buyer_id = auth.uid());

-- 8. PRIVATE GIFT PLAN ITEMS POLICIES
-- Recipient cannot view private purchase details UNLESS explicitly revealed!
CREATE POLICY "Buyer can view all plan items, partner can view ONLY revealed"
ON public.private_gift_plan_items FOR SELECT
USING (
    buyer_id = auth.uid()
    OR (
        is_revealed = TRUE
        AND wishlist_item_id IN (
            SELECT id FROM public.wishlist_items WHERE user_id = auth.uid()
        )
    )
);

CREATE POLICY "Buyer can insert plan items"
ON public.private_gift_plan_items FOR INSERT
WITH CHECK (buyer_id = auth.uid());

CREATE POLICY "Buyer can update plan items"
ON public.private_gift_plan_items FOR UPDATE
USING (buyer_id = auth.uid())
WITH CHECK (buyer_id = auth.uid());

CREATE POLICY "Buyer can delete plan items"
ON public.private_gift_plan_items FOR DELETE
USING (buyer_id = auth.uid());

-- ====================================================================
-- STORAGE BUCKET CONFIGURATION FOR PRODUCT IMAGES
-- (Run in Supabase Storage or Dashboard SQL Editor)
-- ====================================================================
INSERT INTO storage.buckets (id, name, public) 
VALUES ('wishlist-images', 'wishlist-images', true)
ON CONFLICT (id) DO NOTHING;

-- Storage RLS: Authenticated users can upload product photos
CREATE POLICY "Authenticated users can upload wishlist images"
ON storage.objects FOR INSERT
WITH CHECK (
    bucket_id = 'wishlist-images'
    AND auth.role() = 'authenticated'
);

-- Anyone can read public wishlist images
CREATE POLICY "Public read access for wishlist images"
ON storage.objects FOR SELECT
USING (bucket_id = 'wishlist-images');

-- User can delete their own uploaded images
CREATE POLICY "Users can delete own uploaded wishlist images"
ON storage.objects FOR DELETE
USING (
    bucket_id = 'wishlist-images'
    AND auth.uid() = owner
);
