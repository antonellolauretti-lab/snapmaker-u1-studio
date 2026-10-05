-- ==============================================================================
-- SCHEMA DATABASE SUPABASE PER STOREFRONT SNAPMAKER U1
-- Database: PostgreSQL (Supabase Free Tier)
-- ==============================================================================

-- Abilita l'estensione per gli UUID se non già presente
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ------------------------------------------------------------------------------
-- 1. TABELLA INVENTARIO FILAMENTI (filaments)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.filaments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sku VARCHAR(20) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    group_name VARCHAR(50) NOT NULL, -- 'SnapSpeed PLA', 'Silk Dual-Color', 'PETG/TPU'
    material_type VARCHAR(20) NOT NULL DEFAULT 'PLA', -- 'PLA', 'PETG', 'TPU'
    hex_color VARCHAR(7) NOT NULL, -- Colore primario (es. '#080A0D')
    secondary_hex_color VARCHAR(7) NULL, -- Opzionale per Silk Bicolore (es. '#CC434F')
    icon VARCHAR(10) DEFAULT '⚫',
    is_available BOOLEAN NOT NULL DEFAULT true, -- Toggle [Disponibile / Esaurito]
    sort_order INT DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indici per performance
CREATE INDEX IF NOT EXISTS idx_filaments_available ON public.filaments (is_available);
CREATE INDEX IF NOT EXISTS idx_filaments_sku ON public.filaments (sku);

-- ------------------------------------------------------------------------------
-- 2. TABELLA ORDINI CLIENTI (orders)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.orders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    order_number VARCHAR(32) NOT NULL UNIQUE, -- es. 'U1-202610-0001'
    customer_name VARCHAR(120) NOT NULL,
    customer_email VARCHAR(120) NOT NULL,
    customer_phone VARCHAR(30) NOT NULL, -- Obbligatorio per lettera di vettura BRT/SDA
    shipping_address TEXT NOT NULL, -- Via e Numero Civico
    shipping_city VARCHAR(80) NOT NULL,
    shipping_zip VARCHAR(10) NOT NULL, -- CAP
    shipping_province VARCHAR(4) NOT NULL, -- Provincia (es. 'RM', 'MI')
    shipping_country VARCHAR(10) NOT NULL DEFAULT 'IT',
    order_notes TEXT NULL,
    
    -- Calcoli Economici
    subtotal_amount NUMERIC(10, 2) NOT NULL CHECK (subtotal_amount >= 0),
    discount_amount NUMERIC(10, 2) NOT NULL DEFAULT 0.00 CHECK (discount_amount >= 0), -- Sconto Promo 3x2
    shipping_amount NUMERIC(10, 2) NOT NULL DEFAULT 5.00 CHECK (shipping_amount >= 0), -- Fisso 5,00 € BRT/SDA
    total_amount NUMERIC(10, 2) NOT NULL CHECK (total_amount >= 0),
    
    -- Gestione Pagamento PayPal
    payment_provider VARCHAR(30) NOT NULL DEFAULT 'paypal',
    paypal_order_id VARCHAR(64) NULL,
    paypal_capture_id VARCHAR(64) NULL,
    payment_status VARCHAR(30) NOT NULL DEFAULT 'pending' 
        CHECK (payment_status IN ('pending', 'paid', 'failed', 'refunded')),
    
    -- Flusso Operativo Stampante Snapmaker U1
    order_status VARCHAR(30) NOT NULL DEFAULT 'da_stampare' 
        CHECK (order_status IN ('da_stampare', 'in_stampa', 'spedito', 'annullato')),
    courier VARCHAR(50) NOT NULL DEFAULT 'BRT / SDA',
    tracking_number VARCHAR(100) NULL,
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indici per lookup ordini
CREATE INDEX IF NOT EXISTS idx_orders_status ON public.orders (order_status);
CREATE INDEX IF NOT EXISTS idx_orders_customer_email ON public.orders (customer_email);
CREATE INDEX IF NOT EXISTS idx_orders_paypal_order_id ON public.orders (paypal_order_id);
CREATE INDEX IF NOT EXISTS idx_orders_created_at ON public.orders (created_at DESC);

-- ------------------------------------------------------------------------------
-- 3. TABELLA ARTICOLI ORDINATI (order_items)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.order_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    order_id UUID NOT NULL REFERENCES public.orders(id) ON DELETE CASCADE,
    product_type VARCHAR(50) NOT NULL, -- 'keychain_standard', 'keychain_complex', 'desk_sign'
    product_title VARCHAR(120) NOT NULL, -- es. 'Portachiavi Personalizzato'
    unit_price NUMERIC(10, 2) NOT NULL CHECK (unit_price >= 0),
    is_free_promo BOOLEAN NOT NULL DEFAULT false, -- True se l'articolo è quello omaggiato dalla promo 3x2
    
    -- Personalizzazioni visibili al cliente
    custom_text_line1 VARCHAR(50) NOT NULL,
    custom_text_line2 VARCHAR(50) NULL,
    font_id VARCHAR(50) NOT NULL,
    icon_id VARCHAR(50) NULL,
    
    -- Riferimenti Colori Filamento Snapmaker
    base_filament_id UUID REFERENCES public.filaments(id) ON DELETE SET NULL,
    base_color_name VARCHAR(80) NOT NULL,
    base_color_hex VARCHAR(7) NOT NULL,
    
    text_filament_id UUID REFERENCES public.filaments(id) ON DELETE SET NULL,
    text_color_name VARCHAR(80) NOT NULL,
    text_color_hex VARCHAR(7) NOT NULL,
    
    -- Anteprima 3D catturata da Three.js (Thumbnail data URL / URL Supabase Storage)
    preview_thumbnail_url TEXT NULL,
    
    -- Payload JSON completo per compilatore 3MF nativo (Snapmaker3MFPackager)
    generator_params JSONB NOT NULL,
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_order_items_order_id ON public.order_items (order_id);

-- ------------------------------------------------------------------------------
-- 4. TRIGGER PER AUTO-AGGIORNAMENTO updated_at
-- ------------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION update_timestamp_column()
RETURNS TRIGGER AS $$
BEGIN
   NEW.updated_at = NOW();
   RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS trg_filaments_updated_at ON public.filaments;
CREATE TRIGGER trg_filaments_updated_at
BEFORE UPDATE ON public.filaments
FOR EACH ROW EXECUTE PROCEDURE update_timestamp_column();

DROP TRIGGER IF EXISTS trg_orders_updated_at ON public.orders;
CREATE TRIGGER trg_orders_updated_at
BEFORE UPDATE ON public.orders
FOR EACH ROW EXECUTE PROCEDURE update_timestamp_column();

-- ------------------------------------------------------------------------------
-- 5. ROW LEVEL SECURITY (RLS) POLICIES
-- ------------------------------------------------------------------------------
ALTER TABLE public.filaments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.order_items ENABLE ROW LEVEL SECURITY;

-- filaments: lettura pubblica consentita per tutti
CREATE POLICY "Public read available filaments"
ON public.filaments FOR SELECT
TO anon, authenticated
USING (true);

-- filaments: aggiornamenti consentiti solo con service_role (Admin Panel)
CREATE POLICY "Admin update filaments"
ON public.filaments FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

-- orders: creazione consentita a tutti durante il checkout
CREATE POLICY "Public insert orders"
ON public.orders FOR INSERT
TO anon, authenticated
WITH CHECK (true);

-- orders: lettura pubblica del proprio ordine tramite ID/Order Number
CREATE POLICY "Public read own order"
ON public.orders FOR SELECT
TO anon, authenticated
USING (true);

-- orders: gestione completa (update stato, cancellazione) consentita ad admin/service_role
CREATE POLICY "Admin manage orders"
ON public.orders FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

-- order_items: inserimento pubblico durante il checkout
CREATE POLICY "Public insert order items"
ON public.order_items FOR INSERT
TO anon, authenticated
WITH CHECK (true);

-- order_items: lettura consentita
CREATE POLICY "Public read order items"
ON public.order_items FOR SELECT
TO anon, authenticated
USING (true);

-- order_items: gestione completa solo service_role
CREATE POLICY "Admin manage order items"
ON public.order_items FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

-- ------------------------------------------------------------------------------
-- 6. SEED DATA CATALOGO FILAMENTI SNAPMAKER U1
-- Con codici HEX e SKU ufficiali posseduti
-- ------------------------------------------------------------------------------
INSERT INTO public.filaments (sku, name, group_name, material_type, hex_color, secondary_hex_color, icon, is_available, sort_order)
VALUES
    -- SnapSpeed PLA
    ('34062', 'SnapSpeed PLA Black', 'SnapSpeed PLA', 'PLA', '#080A0D', NULL, '⚫', true, 1),
    ('34073', 'SnapSpeed PLA Cool White', 'SnapSpeed PLA', 'PLA', '#D9DFE5', NULL, '⚪', true, 2),
    ('34061', 'SnapSpeed PLA Pearl White', 'SnapSpeed PLA', 'PLA', '#E2DEDB', NULL, '◽', true, 3),
    ('34065', 'SnapSpeed PLA Red', 'SnapSpeed PLA', 'PLA', '#E72F1D', NULL, '🔴', true, 4),
    ('34064', 'SnapSpeed PLA Blue', 'SnapSpeed PLA', 'PLA', '#003776', NULL, '🔵', true, 5),
    ('34112', 'SnapSpeed PLA Bright Yellow', 'SnapSpeed PLA', 'PLA', '#F8F81C', NULL, '🟡', true, 6),
    ('34067', 'SnapSpeed PLA Orange', 'SnapSpeed PLA', 'PLA', '#F97429', NULL, '🟠', true, 7),
    ('34068', 'SnapSpeed PLA Green', 'SnapSpeed PLA', 'PLA', '#2D9E59', NULL, '🟢', true, 8),
    ('34074', 'SnapSpeed PLA Magenta', 'SnapSpeed PLA', 'PLA', '#F24574', NULL, '🌺', true, 9),

    -- Silk Dual-Color PLA
    ('34202', 'Silk Sunset Ember', 'Silk Dual-Color', 'PLA', '#D9A63A', '#CC434F', '✨', true, 10),
    ('34203', 'Silk Aurora Gold', 'Silk Dual-Color', 'PLA', '#D9A63A', '#9675CD', '✨', true, 11),
    ('34204', 'Silk Solar Alloy', 'Silk Dual-Color', 'PLA', '#D9A63A', '#C4C7D9', '✨', true, 12),
    ('34205', 'Silk Mint Lemonade', 'Silk Dual-Color', 'PLA', '#ECED17', '#44ADE5', '✨', true, 13),
    ('34206', 'Silk Sea Glass', 'Silk Dual-Color', 'PLA', '#44ADE5', '#18CCAF', '✨', true, 14),
    ('34207', 'Silk Ice Lake', 'Silk Dual-Color', 'PLA', '#C4C7D9', '#44ADE5', '✨', true, 15),
    ('34208', 'Silk City Billboard', 'Silk Dual-Color', 'PLA', '#CBF914', '#D623AA', '✨', true, 16),

    -- PETG / TPU
    ('34157', 'PETG HF Black', 'PETG/TPU', 'PETG', '#16171B', NULL, '⬛', true, 17),
    ('34176', 'TPU 95A HF Black', 'PETG/TPU', 'TPU', '#000000', NULL, '⬛', true, 18),
    ('34220', 'PETG Translucent Green', 'PETG/TPU', 'PETG', '#537A37', NULL, '🧪', true, 19),
    ('34222', 'PETG Translucent Orange', 'PETG/TPU', 'PETG', '#FB8D02', NULL, '🧪', true, 20),
    ('34223', 'PETG Translucent Pink', 'PETG/TPU', 'PETG', '#E68FBD', NULL, '🧪', true, 21),
    ('34218', 'PETG Translucent Blue', 'PETG/TPU', 'PETG', '#338CC4', NULL, '🧪', true, 22)
ON CONFLICT (sku) DO UPDATE SET
    name = EXCLUDED.name,
    group_name = EXCLUDED.group_name,
    hex_color = EXCLUDED.hex_color,
    secondary_hex_color = EXCLUDED.secondary_hex_color,
    icon = EXCLUDED.icon;
