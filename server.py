#!/usr/bin/env python3
"""
UtmFlow - High-Performance AdTech, UTM Attribution & Meta Ads Management Platform
Pure Python Standard Library Server (Zero External PIP Dependencies)
"""

import http.server
import json
import sqlite3
import urllib.request
import urllib.parse
import urllib.error
import hashlib
import uuid
from datetime import datetime, timedelta
import threading
import os
import sys
import time
import re
import traceback

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "utmflow.db")
LEGACY_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "nexustrack.db")
STATIC_DIR = os.path.dirname(os.path.abspath(__file__))

# If legacy db exists and new db doesn't, migrate automatically
if os.path.exists(LEGACY_DB) and not os.path.exists(DB_PATH):
    try:
        import shutil
        shutil.copy2(LEGACY_DB, DB_PATH)
    except Exception:
        pass

def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes tables and performs automated migrations."""
    conn = get_db()
    cursor = conn.cursor()

    # 1. Orders table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id TEXT PRIMARY KEY,
            external_id TEXT,
            platform TEXT,
            status TEXT,
            amount REAL,
            currency TEXT DEFAULT 'BRL',
            customer_name TEXT,
            customer_email TEXT,
            customer_phone TEXT,
            customer_ip TEXT,
            customer_user_agent TEXT,
            utm_source TEXT,
            utm_medium TEXT,
            utm_campaign TEXT,
            utm_content TEXT,
            utm_term TEXT,
            src TEXT,
            sck TEXT,
            fbc TEXT,
            fbp TEXT,
            product_name TEXT,
            product_id TEXT,
            created_at TEXT,
            paid_at TEXT,
            raw_payload TEXT
        )
    """)

    # 2. Tracking events table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tracking_events (
            id TEXT PRIMARY KEY,
            event_name TEXT,
            event_id TEXT,
            url TEXT,
            referrer TEXT,
            utm_source TEXT,
            utm_medium TEXT,
            utm_campaign TEXT,
            utm_content TEXT,
            utm_term TEXT,
            src TEXT,
            sck TEXT,
            fbc TEXT,
            fbp TEXT,
            ip TEXT,
            user_agent TEXT,
            created_at TEXT
        )
    """)

    # 3. Facebook Connections
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS facebook_connections (
            id TEXT PRIMARY KEY,
            connection_type TEXT,
            name TEXT,
            access_token TEXT,
            token_type TEXT,
            expires_at TEXT,
            created_at TEXT,
            status TEXT DEFAULT 'active'
        )
    """)

    # 4. Facebook Ad Accounts
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS facebook_ad_accounts (
            id TEXT PRIMARY KEY,
            connection_id TEXT,
            name TEXT,
            account_status INTEGER,
            currency TEXT,
            timezone_name TEXT,
            is_selected INTEGER DEFAULT 1,
            last_synced_at TEXT
        )
    """)

    # 5. Meta OAuth Configuration
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS meta_oauth_config (
            id TEXT PRIMARY KEY DEFAULT 'default',
            app_id TEXT,
            app_secret TEXT,
            redirect_uri TEXT,
            updated_at TEXT
        )
    """)

    # 6. Meta Campaign Insights
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS meta_campaign_insights (
            id TEXT PRIMARY KEY,
            account_id TEXT,
            campaign_id TEXT,
            campaign_name TEXT,
            date_start TEXT,
            date_stop TEXT,
            spend REAL DEFAULT 0,
            impressions INTEGER DEFAULT 0,
            clicks INTEGER DEFAULT 0,
            cpc REAL DEFAULT 0,
            cpm REAL DEFAULT 0,
            ctr REAL DEFAULT 0,
            conversions INTEGER DEFAULT 0,
            updated_at TEXT
        )
    """)

    # 7. Campaigns
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS campaigns (
            id TEXT PRIMARY KEY,
            account_id TEXT,
            name TEXT,
            status TEXT,
            effective_status TEXT,
            objective TEXT,
            daily_budget REAL DEFAULT 0,
            lifetime_budget REAL DEFAULT 0,
            spend REAL DEFAULT 0,
            impressions INTEGER DEFAULT 0,
            clicks INTEGER DEFAULT 0,
            ctr REAL DEFAULT 0,
            cpc REAL DEFAULT 0,
            conversions INTEGER DEFAULT 0,
            cpa REAL DEFAULT 0,
            roas REAL DEFAULT 0,
            updated_at TEXT
        )
    """)

    # 8. Ad Sets
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ad_sets (
            id TEXT PRIMARY KEY,
            account_id TEXT,
            campaign_id TEXT,
            name TEXT,
            status TEXT,
            effective_status TEXT,
            daily_budget REAL DEFAULT 0,
            spend REAL DEFAULT 0,
            impressions INTEGER DEFAULT 0,
            clicks INTEGER DEFAULT 0,
            ctr REAL DEFAULT 0,
            cpc REAL DEFAULT 0,
            conversions INTEGER DEFAULT 0,
            cpa REAL DEFAULT 0,
            roas REAL DEFAULT 0,
            updated_at TEXT
        )
    """)

    # 9. Ads
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ads (
            id TEXT PRIMARY KEY,
            account_id TEXT,
            campaign_id TEXT,
            adset_id TEXT,
            name TEXT,
            status TEXT,
            effective_status TEXT,
            creative_name TEXT,
            creative_thumbnail TEXT,
            spend REAL DEFAULT 0,
            impressions INTEGER DEFAULT 0,
            clicks INTEGER DEFAULT 0,
            ctr REAL DEFAULT 0,
            cpc REAL DEFAULT 0,
            conversions INTEGER DEFAULT 0,
            cpa REAL DEFAULT 0,
            roas REAL DEFAULT 0,
            updated_at TEXT
        )
    """)

    # 10. Financial Settings
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS financial_settings (
            id TEXT PRIMARY KEY DEFAULT 'default',
            tax_rate REAL DEFAULT 6.0,
            gateway_rate REAL DEFAULT 8.9,
            gateway_fixed_fee REAL DEFAULT 2.49,
            product_cost_rate REAL DEFAULT 15.0,
            updated_at TEXT
        )
    """)

    # 11. Meta Pixels (CAPI multi-pixel)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS meta_pixels (
            id TEXT PRIMARY KEY,
            name TEXT,
            pixel_id TEXT,
            access_token TEXT,
            test_event_code TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TEXT
        )
    """)

    # 12. Automated Rules
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS automated_rules (
            id TEXT PRIMARY KEY,
            name TEXT,
            rule_type TEXT,
            condition_metric TEXT,
            threshold_value REAL,
            action_type TEXT,
            action_value REAL,
            target_account_id TEXT,
            is_active INTEGER DEFAULT 1,
            last_run_at TEXT,
            created_at TEXT
        )
    """)

    # 13. Rule Logs
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rule_logs (
            id TEXT PRIMARY KEY,
            rule_id TEXT,
            rule_name TEXT,
            action_taken TEXT,
            details TEXT,
            status TEXT,
            created_at TEXT
        )
    """)

    # 14. Custom Dashboards Layout
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS custom_dashboards (
            id TEXT PRIMARY KEY DEFAULT 'default',
            layout_json TEXT,
            updated_at TEXT
        )
    """)

    # 15. User Preferences
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_preferences (
            id TEXT PRIMARY KEY DEFAULT 'default',
            columns_config TEXT,
            theme TEXT DEFAULT 'dark',
            updated_at TEXT
        )
    """)

    # 16. OAuth State table (Anti-CSRF)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS oauth_states (
            state TEXT PRIMARY KEY,
            created_at TEXT,
            is_used INTEGER DEFAULT 0
        )
    """)

    # Seed Default Financial Settings if empty
    cursor.execute("SELECT id FROM financial_settings WHERE id = 'default'")
    if not cursor.fetchone():
        now = datetime.utcnow().isoformat()
        cursor.execute("""
            INSERT INTO financial_settings (id, tax_rate, gateway_rate, gateway_fixed_fee, product_cost_rate, updated_at)
            VALUES ('default', 6.0, 8.9, 2.49, 15.0, ?)
        """, (now,))

    # Seed initial demo data if empty
    cursor.execute("SELECT COUNT(*) as cnt FROM orders")
    order_cnt = cursor.fetchone()["cnt"]
    if order_cnt == 0:
        seed_sample_data(cursor)

    conn.commit()
    conn.close()

def seed_sample_data(cursor):
    """Populates realistic demo campaigns, ad sets, ads and recent orders."""
    now = datetime.utcnow()
    act_id = "act_1092837482"
    conn_id = "conn_demo_default"

    cursor.execute("""
        INSERT OR REPLACE INTO facebook_connections (id, connection_type, name, access_token, token_type, expires_at, created_at, status)
        VALUES (?, 'demo', 'Conta Demonstração UtmFlow', 'EAADEMOTOKEN12345', 'DEMO', ?, ?, 'active')
    """, (conn_id, (now + timedelta(days=60)).isoformat(), now.isoformat()))

    cursor.execute("""
        INSERT OR REPLACE INTO facebook_ad_accounts (id, connection_id, name, account_status, currency, timezone_name, is_selected, last_synced_at)
        VALUES (?, ?, 'UtmFlow Scaling | E-com & Infoprodutos', 1, 'BRL', 'America/Sao_Paulo', 1, ?)
    """, (act_id, conn_id, now.isoformat()))

    # Sample Campaigns
    sample_campaigns = [
        ("camp_01", act_id, "[ESCALA] Oferta Principal - VSL V2 (CBO)", "ACTIVE", "ACTIVE", "OUTCOME_SALES", 250.00, 0, 840.50, 42100, 1145, 2.72, 0.73, 28, 30.01, 3.42),
        ("camp_02", act_id, "[REMARKETING] Carrinho Abandonado 7D", "ACTIVE", "ACTIVE", "OUTCOME_SALES", 80.00, 0, 195.40, 11300, 482, 4.26, 0.40, 16, 12.21, 6.18),
        ("camp_03", act_id, "[TESTE] Novos Criativos Ângulo Emocional", "ACTIVE", "ACTIVE", "OUTCOME_TRAFFIC", 120.00, 0, 245.10, 18500, 520, 2.81, 0.47, 4, 61.27, 1.48),
        ("camp_04", act_id, "[PAUSADA] Black Friday Antecipada", "PAUSED", "PAUSED", "OUTCOME_SALES", 0.00, 0, 450.00, 26000, 680, 2.61, 0.66, 9, 50.00, 2.10)
    ]
    for c in sample_campaigns:
        cursor.execute("""
            INSERT OR REPLACE INTO campaigns (id, account_id, name, status, effective_status, objective, daily_budget, lifetime_budget, spend, impressions, clicks, ctr, cpc, conversions, cpa, roas, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (c[0], c[1], c[2], c[3], c[4], c[5], c[6], c[7], c[8], c[9], c[10], c[11], c[12], c[13], c[14], c[15], now.isoformat()))

    # Sample AdSets
    sample_adsets = [
        ("adset_01", act_id, "camp_01", "[ABERTO] Brasil 25-54 | Excluir Compradores", "ACTIVE", "ACTIVE", 150.0, 520.30, 26100, 712, 2.73, 0.73, 18, 28.90, 3.65),
        ("adset_02", act_id, "camp_01", "[LOOKALIKE 1%] Compradores 180D", "ACTIVE", "ACTIVE", 100.0, 320.20, 16000, 433, 2.70, 0.74, 10, 32.02, 3.05),
        ("adset_03", act_id, "camp_02", "[ENGAGEMENT] Instagram 30D + View Video 75%", "ACTIVE", "ACTIVE", 80.0, 195.40, 11300, 482, 4.26, 0.40, 16, 12.21, 6.18),
        ("adset_04", act_id, "camp_03", "[INTERESSES] Empreendedorismo + Marketing", "ACTIVE", "ACTIVE", 120.0, 245.10, 18500, 520, 2.81, 0.47, 4, 61.27, 1.48)
    ]
    for a in sample_adsets:
        cursor.execute("""
            INSERT OR REPLACE INTO ad_sets (id, account_id, campaign_id, name, status, effective_status, daily_budget, spend, impressions, clicks, ctr, cpc, conversions, cpa, roas, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (a[0], a[1], a[2], a[3], a[4], a[5], a[6], a[7], a[8], a[9], a[10], a[11], a[12], a[13], a[14], now.isoformat()))

    # Sample Ads
    sample_ads = [
        ("ad_01", act_id, "camp_01", "adset_01", "AD01_VSL_HookDor_MulherChorando", "ACTIVE", "ACTIVE", "Video VSL V2 Cortado", "https://images.unsplash.com/photo-1551836022-d5d88e9218df?w=150&auto=format&fit=crop&q=80", 280.10, 14200, 395, 2.78, 0.71, 11, 25.46, 3.92),
        ("ad_02", act_id, "camp_01", "adset_01", "AD02_Carrossel_3ErrosComuns", "ACTIVE", "ACTIVE", "Carrossel Dinâmico 5 Telas", "https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=150&auto=format&fit=crop&q=80", 240.20, 11900, 317, 2.66, 0.76, 7, 34.31, 3.12),
        ("ad_03", act_id, "camp_01", "adset_02", "AD03_Depoimento_ProvaSocialAlunos", "ACTIVE", "ACTIVE", "UGC Aluno Resultado 10k", "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150&auto=format&fit=crop&q=80", 320.20, 16000, 433, 2.70, 0.74, 10, 32.02, 3.05),
        ("ad_04", act_id, "camp_02", "adset_03", "AD04_CupomExclusivo_Desconto10", "ACTIVE", "ACTIVE", "Static Cupom 10 OFF", "https://images.unsplash.com/photo-1526304640581-d334cdbbf45e?w=150&auto=format&fit=crop&q=80", 195.40, 11300, 482, 4.26, 0.40, 16, 12.21, 6.18)
    ]
    for ad in sample_ads:
        cursor.execute("""
            INSERT OR REPLACE INTO ads (id, account_id, campaign_id, adset_id, name, status, effective_status, creative_name, creative_thumbnail, spend, impressions, clicks, ctr, cpc, conversions, cpa, roas, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (ad[0], ad[1], ad[2], ad[3], ad[4], ad[5], ad[6], ad[7], ad[8], ad[9], ad[10], ad[11], ad[12], ad[13], ad[14], ad[15], ad[16], now.isoformat()))

    # Sample Realistic Orders
    buyers = [
        ("João Marcelo Silva", "joao.marcelo@gmail.com", "+5511988887766", 197.00, "paid", "facebook", "cpc", "[ESCALA] Oferta Principal - VSL V2 (CBO)", "AD01_VSL_HookDor_MulherChorando", "kiwify", 2),
        ("Mariana Vasconcelos", "mari.vasconcelos@outlook.com", "+5521977774433", 297.00, "paid", "facebook", "cpc", "[REMARKETING] Carrinho Abandonado 7D", "AD04_CupomExclusivo_Desconto10", "hotmart", 4),
        ("Carlos Alberto Prado", "carlos.prado@bol.com.br", "+5531991234567", 97.00, "waiting_payment", "facebook", "cpc", "[ESCALA] Oferta Principal - VSL V2 (CBO)", "AD02_Carrossel_3ErrosComuns", "greenn", 1),
        ("Renata Bittencourt", "renatabittencourt@gmail.com", "+5541999881122", 197.00, "paid", "instagram", "cpc", "[ESCALA] Oferta Principal - VSL V2 (CBO)", "AD01_VSL_HookDor_MulherChorando", "kiwify", 6),
        ("Felipe Nogueira", "felipe.nog@terra.com.br", "+5561981112233", 497.00, "paid", "facebook", "cpc", "[REMARKETING] Carrinho Abandonado 7D", "AD04_CupomExclusivo_Desconto10", "cakto", 12),
        ("Juliana Mendes", "jumendes@yahoo.com.br", "+5571994445566", 197.00, "waiting_payment", "google", "search", "Campanha Fundo de Funil", "Anuncio_Texto_01", "wiapy", 18),
        ("Lucas Guimarães", "lucas.gm@gmail.com", "+5581987654321", 197.00, "paid", "tiktok", "cpc", "TikTok Ads Escala", "Video_Spark_03", "kiwify", 24),
        ("Beatriz Souza Costa", "bia.costa@hotmail.com", "+5519992345678", 297.00, "paid", "direto", "organico", "Site Institucional", "Link_Bio_Instagram", "hotmart", 30),
        ("Rodrigo Fontes", "rodrigo.fontes@gmail.com", "+5511976543210", 197.00, "paid", "facebook", "cpc", "[ESCALA] Oferta Principal - VSL V2 (CBO)", "AD03_Depoimento_ProvaSocialAlunos", "kiwify", 38),
        ("Camila Diniz", "camila.diniz@gmail.com", "+5521998765432", 197.00, "paid", "facebook", "cpc", "[ESCALA] Oferta Principal - VSL V2 (CBO)", "AD01_VSL_HookDor_MulherChorando", "kiwify", 45),
        ("Tiago Fernandes", "tiago.fernandes@live.com", "+5531988889999", 97.00, "paid", "instagram", "cpc", "[REMARKETING] Carrinho Abandonado 7D", "AD04_CupomExclusivo_Desconto10", "greenn", 50),
        ("Aline Rocha", "aline.rocha@uol.com.br", "+5548991238877", 297.00, "paid", "facebook", "cpc", "[ESCALA] Oferta Principal - VSL V2 (CBO)", "AD01_VSL_HookDor_MulherChorando", "cakto", 72)
    ]

    for i, b in enumerate(buyers):
        ord_id = f"ord_{uuid.uuid4().hex[:10]}"
        ord_time = (now - timedelta(hours=b[9])).isoformat()
        cursor.execute("""
            INSERT OR REPLACE INTO orders (
                id, external_id, platform, status, amount, currency, customer_name, customer_email,
                customer_phone, customer_ip, customer_user_agent, utm_source, utm_medium, utm_campaign,
                utm_content, utm_term, src, sck, fbc, fbp, product_name, product_id, created_at, paid_at
            ) VALUES (?, ?, ?, ?, ?, 'BRL', ?, ?, ?, '189.40.12.55', 'Mozilla/5.0 UtmFlowBrowser', ?, ?, ?, ?, '', ?, '', 'fb.1.17112345678.98765', 'fb.1.17112345678.12345', 'Método UtmFlow Escala 10X', 'prod_uf_01', ?, ?)
        """, (
            ord_id, f"ext_{100000+i}", b[8], b[4], b[3], b[0], b[1], b[2],
            b[5], b[6], b[7], b[8], b[5], ord_time, ord_time if b[4] == 'paid' else None
        ))

    # Sample Tracking events
    for _ in range(120):
        t_time = (now - timedelta(hours=3)).isoformat()
        cursor.execute("""
            INSERT INTO tracking_events (id, event_name, event_id, url, referrer, utm_source, utm_medium, utm_campaign, ip, user_agent, created_at)
            VALUES (?, 'PageView', ?, 'https://meusite.com/vsl', 'https://facebook.com', 'facebook', 'cpc', '[ESCALA] Oferta Principal - VSL V2 (CBO)', '189.40.12.55', 'Mozilla/5.0', ?)
        """, (str(uuid.uuid4()), str(uuid.uuid4()), t_time))

    for _ in range(35):
        t_time = (now - timedelta(hours=2)).isoformat()
        cursor.execute("""
            INSERT INTO tracking_events (id, event_name, event_id, url, referrer, utm_source, utm_medium, utm_campaign, ip, user_agent, created_at)
            VALUES (?, 'InitiateCheckout', ?, 'https://checkout.kiwify.com.br/pay', 'https://meusite.com/vsl', 'facebook', 'cpc', '[ESCALA] Oferta Principal - VSL V2 (CBO)', '189.40.12.55', 'Mozilla/5.0', ?)
        """, (str(uuid.uuid4()), str(uuid.uuid4()), t_time))

    # Sample Automated Rules
    cursor.execute("""
        INSERT OR REPLACE INTO automated_rules (id, name, rule_type, condition_metric, threshold_value, action_type, action_value, target_account_id, is_active, created_at)
        VALUES ('rule_01', 'Stop Loss: Gasto > R$ 150 sem vendas', 'stop_loss', 'spend_no_sales', 150.0, 'pause_campaign', 0, 'all', 1, ?)
    """, (now.isoformat(),))

    cursor.execute("""
        INSERT OR REPLACE INTO automated_rules (id, name, rule_type, condition_metric, threshold_value, action_type, action_value, target_account_id, is_active, created_at)
        VALUES ('rule_02', 'Escala Inteligente: ROAS > 3.0X (+20% Orçamento)', 'scale', 'roas_greater_than', 3.0, 'increase_budget', 20.0, 'all', 1, ?)
    """, (now.isoformat(),))

    # Sample Meta Pixel
    cursor.execute("""
        INSERT OR REPLACE INTO meta_pixels (id, name, pixel_id, access_token, test_event_code, is_active, created_at)
        VALUES ('pix_01', 'Pixel Principal Contingência 01', '984729103847291', 'EAABdemoTokenPixelCAPI', 'TEST83921', 1, ?)
    """, (now.isoformat(),))

# -------------------------------------------------------------
# GRAPH API HELPER FUNCTIONS (Meta OAuth & CAPI Server-Side)
# -------------------------------------------------------------

def fetch_all_meta_pages(base_url, access_token, params=None):
    if params is None:
        params = {}
    params['access_token'] = access_token

    all_data = []
    current_url = base_url + "?" + urllib.parse.urlencode(params)

    while current_url:
        try:
            req = urllib.request.Request(current_url, headers={"User-Agent": "UtmFlow-AdTech/2.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                items = data.get('data', [])
                all_data.extend(items)

                paging = data.get('paging', {})
                current_url = paging.get('next')
                if not items or len(all_data) > 500:
                    break
        except Exception as e:
            print(f"[Meta API Error] {e}")
            break

    return all_data

def meta_api_get(url_path, access_token, params=None):
    if params is None:
        params = {}
    params['access_token'] = access_token
    query_str = urllib.parse.urlencode(params)
    full_url = f"https://graph.facebook.com/v19.0/{url_path}?{query_str}"
    req = urllib.request.Request(full_url, headers={"User-Agent": "UtmFlow-AdTech/2.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode('utf-8'))

def send_capi_event(pixel_id, access_token, event_name, event_data, test_code=None):
    url = f"https://graph.facebook.com/v19.0/{pixel_id}/events"

    user_data = {}
    if 'email' in event_data and event_data['email']:
        cleaned_email = event_data['email'].strip().lower()
        user_data['em'] = [hashlib.sha256(cleaned_email.encode('utf-8')).hexdigest()]

    if 'phone' in event_data and event_data['phone']:
        cleaned_phone = re.sub(r'[^0-9]', '', str(event_data['phone']))
        user_data['ph'] = [hashlib.sha256(cleaned_phone.encode('utf-8')).hexdigest()]

    if 'ip' in event_data and event_data['ip']:
        user_data['client_ip_address'] = event_data['ip']

    if 'user_agent' in event_data and event_data['user_agent']:
        user_data['client_user_agent'] = event_data['user_agent']

    if 'fbc' in event_data and event_data['fbc']:
        user_data['fbc'] = event_data['fbc']

    if 'fbp' in event_data and event_data['fbp']:
        user_data['fbp'] = event_data['fbp']

    payload_event = {
        "event_name": event_name,
        "event_time": int(time.time()),
        "event_id": event_data.get('event_id', str(uuid.uuid4())),
        "event_source_url": event_data.get('url', 'https://utmflow.app'),
        "action_source": "website",
        "user_data": user_data,
        "custom_data": {
            "currency": event_data.get('currency', 'BRL'),
            "value": float(event_data.get('value', 0.0))
        }
    }

    body = {
        "data": [payload_event],
        "access_token": access_token
    }
    if test_code:
        body["test_event_code"] = test_code

    json_data = json.dumps(body).encode('utf-8')
    req = urllib.request.Request(url, data=json_data, headers={
        "Content-Type": "application/json",
        "User-Agent": "UtmFlow-CAPI/2.0"
    })

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode('utf-8')
        return {"error": True, "http_status": e.code, "message": err_msg}
    except Exception as e:
        return {"error": True, "message": str(e)}

# -------------------------------------------------------------
# AUTOMATED RULE ENGINE (Background Worker Thread)
# -------------------------------------------------------------

def automated_rules_worker():
    while True:
        try:
            time.sleep(60)
            conn = get_db()
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM automated_rules WHERE is_active = 1")
            rules = cursor.fetchall()
            now_iso = datetime.utcnow().isoformat()

            for rule in rules:
                rule_id = rule["id"]
                rule_name = rule["name"]
                rule_type = rule["rule_type"]
                threshold = float(rule["threshold_value"] or 0)
                action_value = float(rule["action_value"] or 0)

                if rule_type == 'stop_loss':
                    cursor.execute("""
                        SELECT id, name, spend, conversions FROM campaigns
                        WHERE status = 'ACTIVE' AND spend >= ? AND conversions = 0
                    """, (threshold,))
                    culprits = cursor.fetchall()
                    for camp in culprits:
                        cursor.execute("UPDATE campaigns SET status = 'PAUSED', effective_status = 'PAUSED' WHERE id = ?", (camp["id"],))
                        detail_msg = f"Campanha '{camp['name']}' atingiu R$ {camp['spend']:.2f} de gasto sem vendas. Status alterado para PAUSADA."
                        cursor.execute("""
                            INSERT INTO rule_logs (id, rule_id, rule_name, action_taken, details, status, created_at)
                            VALUES (?, ?, ?, 'PAUSE_CAMPAIGN', ?, 'SUCCESS', ?)
                        """, (str(uuid.uuid4()), rule_id, rule_name, detail_msg, now_iso))

                elif rule_type == 'scale':
                    cursor.execute("""
                        SELECT id, name, daily_budget, roas FROM campaigns
                        WHERE status = 'ACTIVE' AND roas >= ? AND daily_budget > 0
                    """, (threshold,))
                    scale_camps = cursor.fetchall()
                    for camp in scale_camps:
                        old_budget = camp["daily_budget"]
                        new_budget = round(old_budget * (1.0 + (action_value / 100.0)), 2)
                        cursor.execute("UPDATE campaigns SET daily_budget = ? WHERE id = ?", (new_budget, camp["id"]))
                        detail_msg = f"Campanha '{camp['name']}' com ROAS de {camp['roas']:.2f}x superou a meta ({threshold}x). Orçamento escalado de R$ {old_budget:.2f} para R$ {new_budget:.2f} (+{action_value}%)."
                        cursor.execute("""
                            INSERT INTO rule_logs (id, rule_id, rule_name, action_taken, details, status, created_at)
                            VALUES (?, ?, ?, 'INCREASE_BUDGET', ?, 'SUCCESS', ?)
                        """, (str(uuid.uuid4()), rule_id, rule_name, detail_msg, now_iso))

                cursor.execute("UPDATE automated_rules SET last_run_at = ? WHERE id = ?", (now_iso, rule_id))

            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[Rules Engine Worker Error] {e}")

# -------------------------------------------------------------
# HTTP REQUEST HANDLER (Pure Python Standard Library)
# -------------------------------------------------------------

class UtmFlowHandler(http.server.BaseHTTPRequestHandler):

    def send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS, PUT, DELETE")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Requested-With")

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_cors_headers()
        self.end_headers()

    def send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_cors_headers()
        self.end_headers()
        self.wfile.write(body)

    def send_file_response(self, file_path, content_type="text/html; charset=utf-8"):
        if not os.path.exists(file_path):
            self.send_json({"error": "File not found"}, 404)
            return
        with open(file_path, "rb") as f:
            content = f.read()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.send_cors_headers()
        self.end_headers()
        self.wfile.write(content)

    def parse_body(self):
        content_len = int(self.headers.get("Content-Length", 0))
        if content_len == 0:
            return {}
        raw = self.rfile.read(content_len).decode('utf-8', errors='ignore')
        try:
            return json.loads(raw)
        except Exception:
            try:
                return dict(urllib.parse.parse_qsl(raw))
            except Exception:
                return {}

    # ------------------ GET ROUTES ------------------
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        # Static assets
        if path == "/" or path == "/index.html":
            html_path = os.path.join(STATIC_DIR, "index.html")
            self.send_file_response(html_path, "text/html; charset=utf-8")
            return

        # Serve both /utmflow.js and /nexustrack.js
        if path == "/utmflow.js" or path == "/nexustrack.js":
            js_path = os.path.join(STATIC_DIR, "utmflow.js")
            self.send_file_response(js_path, "application/javascript; charset=utf-8")
            return

        try:
            conn = get_db()
            cursor = conn.cursor()

            if path == "/api/live/check":
                since_time = query.get('since', [None])[0]
                if since_time:
                    cursor.execute("""
                        SELECT id, amount, customer_name, product_name, utm_source, utm_campaign, created_at
                        FROM orders
                        WHERE status = 'paid' AND created_at > ?
                        ORDER BY created_at DESC LIMIT 5
                    """, (since_time,))
                else:
                    cursor.execute("""
                        SELECT id, amount, customer_name, product_name, utm_source, utm_campaign, created_at
                        FROM orders
                        WHERE status = 'paid'
                        ORDER BY created_at DESC LIMIT 1
                    """)
                rows = [dict(r) for r in cursor.fetchall()]
                conn.close()
                self.send_json({"success": True, "sales": rows, "server_time": datetime.utcnow().isoformat()})
                return

            elif path == "/api/dashboard/stats":
                period = query.get('period', ['today'])[0]
                start_date = query.get('start_date', [None])[0]
                end_date = query.get('end_date', [None])[0]

                now = datetime.utcnow()
                date_filter_sql = ""
                params = []

                if period == 'today':
                    today_str = now.strftime('%Y-%m-%d')
                    date_filter_sql = "WHERE created_at >= ?"
                    params = [today_str + "T00:00:00"]
                elif period == 'yesterday':
                    yest = now - timedelta(days=1)
                    yest_str = yest.strftime('%Y-%m-%d')
                    date_filter_sql = "WHERE created_at >= ? AND created_at < ?"
                    params = [yest_str + "T00:00:00", now.strftime('%Y-%m-%d') + "T00:00:00"]
                elif period == 'last_7d':
                    d7 = now - timedelta(days=7)
                    date_filter_sql = "WHERE created_at >= ?"
                    params = [d7.isoformat()]
                elif period == 'this_month':
                    month_start = now.replace(day=1).strftime('%Y-%m-%d')
                    date_filter_sql = "WHERE created_at >= ?"
                    params = [month_start + "T00:00:00"]
                elif period == 'custom' and start_date and end_date:
                    date_filter_sql = "WHERE created_at >= ? AND created_at <= ?"
                    params = [start_date + "T00:00:00", end_date + "T23:59:59"]
                else:
                    date_filter_sql = ""
                    params = []

                cursor.execute("SELECT * FROM financial_settings WHERE id = 'default'")
                fin_row = cursor.fetchone()
                tax_rate = fin_row["tax_rate"] if fin_row else 6.0
                gateway_rate = fin_row["gateway_rate"] if fin_row else 8.9
                gateway_fixed_fee = fin_row["gateway_fixed_fee"] if fin_row else 2.49
                product_cost_rate = fin_row["product_cost_rate"] if fin_row else 15.0

                order_query = f"SELECT status, amount, utm_source FROM orders {date_filter_sql}"
                cursor.execute(order_query, params)
                orders = cursor.fetchall()

                gross_revenue = 0.0
                approved_sales = 0
                pending_revenue = 0.0
                pending_sales = 0
                sources_breakdown = {}

                for o in orders:
                    amt = float(o["amount"] or 0)
                    st = (o["status"] or "").lower()
                    src = (o["utm_source"] or "direto").lower()

                    if st in ['paid', 'approved']:
                        gross_revenue += amt
                        approved_sales += 1
                        sources_breakdown[src] = sources_breakdown.get(src, 0.0) + amt
                    elif st in ['waiting_payment', 'pending']:
                        pending_revenue += amt
                        pending_sales += 1

                tax_total = gross_revenue * (tax_rate / 100.0)
                gateway_total = (gross_revenue * (gateway_rate / 100.0)) + (approved_sales * gateway_fixed_fee)
                net_revenue = max(0.0, gross_revenue - tax_total - gateway_total)
                product_costs = gross_revenue * (product_cost_rate / 100.0)

                cursor.execute("""
                    SELECT SUM(spend) as total_spend, SUM(clicks) as total_clicks,
                           SUM(impressions) as total_impressions
                    FROM campaigns
                    WHERE account_id IN (SELECT id FROM facebook_ad_accounts WHERE is_selected = 1)
                """)
                camp_stats = cursor.fetchone()
                total_spend = float(camp_stats["total_spend"] or 0)
                total_clicks = int(camp_stats["total_clicks"] or 0)
                total_impressions = int(camp_stats["total_impressions"] or 0)

                real_profit = net_revenue - total_spend - product_costs
                real_roas = (gross_revenue / total_spend) if total_spend > 0 else 0.0
                real_cpa = (total_spend / approved_sales) if approved_sales > 0 else 0.0
                ticket_medio = (gross_revenue / approved_sales) if approved_sales > 0 else 0.0

                track_query = f"SELECT event_name, COUNT(*) as cnt FROM tracking_events {date_filter_sql} GROUP BY event_name"
                cursor.execute(track_query, params)
                ev_counts = {r["event_name"]: r["cnt"] for r in cursor.fetchall()}

                page_views = ev_counts.get("PageView", total_clicks * 2 if total_clicks > 0 else 150)
                init_checkouts = ev_counts.get("InitiateCheckout", approved_sales * 3 if approved_sales > 0 else 45)
                vendas_iniciadas = int(init_checkouts * 0.75) if init_checkouts > 0 else (approved_sales + pending_sales)

                connect_rate = ((page_views / total_clicks) * 100.0) if total_clicks > 0 else 85.0
                pv_to_ic = ((init_checkouts / page_views) * 100.0) if page_views > 0 else 24.5
                ic_to_init = ((vendas_iniciadas / init_checkouts) * 100.0) if init_checkouts > 0 else 68.0
                overall_conversion = ((approved_sales / total_clicks) * 100.0) if total_clicks > 0 else (approved_sales / max(1, page_views) * 100.0)

                conn.close()

                response_payload = {
                    "success": True,
                    "financial": {
                        "gross_revenue": round(gross_revenue, 2),
                        "net_revenue": round(net_revenue, 2),
                        "real_profit": round(real_profit, 2),
                        "pending_revenue": round(pending_revenue, 2),
                        "approved_sales": approved_sales,
                        "pending_sales": pending_sales,
                        "ticket_medio": round(ticket_medio, 2),
                        "real_roas": round(real_roas, 2),
                        "real_cpa": round(real_cpa, 2),
                        "total_spend": round(total_spend, 2),
                        "mrr": round(gross_revenue * 0.85, 2),
                        "ltv": round(ticket_medio * 1.6, 2),
                        "churn": 3.8
                    },
                    "traffic": {
                        "impressions": total_impressions,
                        "clicks": total_clicks,
                        "ctr": round(((total_clicks / total_impressions) * 100.0), 2) if total_impressions > 0 else 2.65,
                        "cpc": round((total_spend / total_clicks), 2) if total_clicks > 0 else 0.72
                    },
                    "funnel": {
                        "clicks": total_clicks or 1145,
                        "page_views": page_views,
                        "connect_rate": round(connect_rate, 1),
                        "initiate_checkouts": init_checkouts,
                        "pv_to_ic": round(pv_to_ic, 1),
                        "vendas_iniciadas": vendas_iniciadas,
                        "ic_to_init": round(ic_to_init, 1),
                        "approved_sales": approved_sales,
                        "overall_conversion": round(overall_conversion, 2)
                    },
                    "sources": sources_breakdown,
                    "settings": {
                        "tax_rate": tax_rate,
                        "gateway_rate": gateway_rate,
                        "gateway_fixed_fee": gateway_fixed_fee,
                        "product_cost_rate": product_cost_rate
                    }
                }
                self.send_json(response_payload)
                return

            elif path == "/api/campaigns":
                account_id = query.get('account_id', [None])[0]
                status_filter = query.get('status', [None])[0]
                search = query.get('search', [None])[0]

                where_clauses = []
                params = []
                if account_id and account_id != 'all':
                    where_clauses.append("account_id = ?")
                    params.append(account_id)
                else:
                    where_clauses.append("account_id IN (SELECT id FROM facebook_ad_accounts WHERE is_selected = 1)")

                if status_filter and status_filter != 'ALL':
                    where_clauses.append("status = ?")
                    params.append(status_filter)

                if search:
                    where_clauses.append("name LIKE ?")
                    params.append(f"%{search}%")

                where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""
                cursor.execute(f"SELECT * FROM campaigns {where_sql} ORDER BY spend DESC", params)
                camps = [dict(r) for r in cursor.fetchall()]
                conn.close()
                self.send_json({"success": True, "campaigns": camps})
                return

            elif path == "/api/adsets":
                account_id = query.get('account_id', [None])[0]
                campaign_ids = query.get('campaign_ids', [None])[0]
                status_filter = query.get('status', [None])[0]
                search = query.get('search', [None])[0]

                where_clauses = []
                params = []
                if campaign_ids:
                    id_list = campaign_ids.split(',')
                    placeholders = ','.join(['?'] * len(id_list))
                    where_clauses.append(f"campaign_id IN ({placeholders})")
                    params.extend(id_list)
                elif account_id and account_id != 'all':
                    where_clauses.append("account_id = ?")
                    params.append(account_id)
                else:
                    where_clauses.append("account_id IN (SELECT id FROM facebook_ad_accounts WHERE is_selected = 1)")

                if status_filter and status_filter != 'ALL':
                    where_clauses.append("status = ?")
                    params.append(status_filter)

                if search:
                    where_clauses.append("name LIKE ?")
                    params.append(f"%{search}%")

                where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""
                cursor.execute(f"SELECT * FROM ad_sets {where_sql} ORDER BY spend DESC", params)
                adsets = [dict(r) for r in cursor.fetchall()]
                conn.close()
                self.send_json({"success": True, "ad_sets": adsets})
                return

            elif path == "/api/ads":
                account_id = query.get('account_id', [None])[0]
                campaign_ids = query.get('campaign_ids', [None])[0]
                adset_ids = query.get('adset_ids', [None])[0]
                status_filter = query.get('status', [None])[0]
                search = query.get('search', [None])[0]

                where_clauses = []
                params = []
                if adset_ids:
                    id_list = adset_ids.split(',')
                    placeholders = ','.join(['?'] * len(id_list))
                    where_clauses.append(f"adset_id IN ({placeholders})")
                    params.extend(id_list)
                elif campaign_ids:
                    id_list = campaign_ids.split(',')
                    placeholders = ','.join(['?'] * len(id_list))
                    where_clauses.append(f"campaign_id IN ({placeholders})")
                    params.extend(id_list)
                elif account_id and account_id != 'all':
                    where_clauses.append("account_id = ?")
                    params.append(account_id)
                else:
                    where_clauses.append("account_id IN (SELECT id FROM facebook_ad_accounts WHERE is_selected = 1)")

                if status_filter and status_filter != 'ALL':
                    where_clauses.append("status = ?")
                    params.append(status_filter)

                if search:
                    where_clauses.append("name LIKE ?")
                    params.append(f"%{search}%")

                where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""
                cursor.execute(f"SELECT * FROM ads {where_sql} ORDER BY spend DESC", params)
                ads_list = [dict(r) for r in cursor.fetchall()]
                conn.close()
                self.send_json({"success": True, "ads": ads_list})
                return

            elif path == "/api/integrations/meta/accounts":
                cursor.execute("""
                    SELECT a.id, a.connection_id, a.name, a.account_status, a.currency,
                           a.timezone_name, a.is_selected, a.last_synced_at,
                           c.connection_type, c.status as connection_status
                    FROM facebook_ad_accounts a
                    LEFT JOIN facebook_connections c ON a.connection_id = c.id
                    ORDER BY a.name ASC
                """)
                accounts = [dict(r) for r in cursor.fetchall()]
                conn.close()
                self.send_json({"success": True, "accounts": accounts})
                return

            elif path == "/api/integrations/meta/config":
                cursor.execute("SELECT id, app_id, redirect_uri, updated_at FROM meta_oauth_config WHERE id = 'default'")
                cfg = cursor.fetchone()
                conn.close()
                if cfg:
                    self.send_json({"success": True, "config": dict(cfg)})
                else:
                    self.send_json({"success": True, "config": {"app_id": "", "redirect_uri": ""}})
                return

            elif path == "/api/integrations/meta/oauth/start":
                cursor.execute("SELECT app_id, redirect_uri FROM meta_oauth_config WHERE id = 'default'")
                cfg = cursor.fetchone()
                if not cfg or not cfg["app_id"]:
                    conn.close()
                    self.send_json({"success": False, "error": "App ID da Meta não configurado no painel!"}, 400)
                    return

                state_token = uuid.uuid4().hex
                now_iso = datetime.utcnow().isoformat()
                cursor.execute("INSERT INTO oauth_states (state, created_at, is_used) VALUES (?, ?, 0)", (state_token, now_iso))
                conn.commit()
                conn.close()

                scope = "ads_read,public_profile"
                oauth_url = (
                    "https://www.facebook.com/v19.0/dialog/oauth?"
                    f"client_id={urllib.parse.quote(cfg['app_id'])}"
                    f"&redirect_uri={urllib.parse.quote(cfg['redirect_uri'])}"
                    f"&state={state_token}"
                    f"&scope={scope}"
                    "&response_type=code"
                )
                self.send_json({"success": True, "oauth_url": oauth_url, "state": state_token})
                return

            elif path == "/api/integrations/meta/callback":
                code = query.get('code', [None])[0]
                state = query.get('state', [None])[0]
                error = query.get('error_message', query.get('error', [None]))[0]

                if error:
                    conn.close()
                    self.send_file_response_html_message("Erro no Login Meta", f"A Meta retornou um erro: {error}")
                    return

                cursor.execute("SELECT state FROM oauth_states WHERE state = ? AND is_used = 0", (state,))
                if not cursor.fetchone():
                    conn.close()
                    self.send_file_response_html_message("Falha Anti-CSRF", "Token de segurança de uso único inválido ou expirado.")
                    return

                cursor.execute("UPDATE oauth_states SET is_used = 1 WHERE state = ?", (state,))

                cursor.execute("SELECT app_id, app_secret, redirect_uri FROM meta_oauth_config WHERE id = 'default'")
                cfg = cursor.fetchone()
                if not cfg or not cfg["app_id"] or not cfg["app_secret"]:
                    conn.close()
                    self.send_file_response_html_message("Configuração Incompleta", "App ID ou App Secret ausente no banco.")
                    return

                app_id = cfg["app_id"]
                app_secret = cfg["app_secret"]
                redirect_uri = cfg["redirect_uri"]

                try:
                    token_url = "https://graph.facebook.com/v19.0/oauth/access_token"
                    token_params = {
                        "client_id": app_id,
                        "client_secret": app_secret,
                        "redirect_uri": redirect_uri,
                        "code": code
                    }
                    req = urllib.request.Request(f"{token_url}?{urllib.parse.urlencode(token_params)}")
                    with urllib.request.urlopen(req, timeout=15) as resp:
                        token_resp = json.loads(resp.read().decode('utf-8'))
                    short_token = token_resp.get("access_token")

                    exchange_params = {
                        "grant_type": "fb_exchange_token",
                        "client_id": app_id,
                        "client_secret": app_secret,
                        "fb_exchange_token": short_token
                    }
                    req_exchange = urllib.request.Request(f"{token_url}?{urllib.parse.urlencode(exchange_params)}")
                    with urllib.request.urlopen(req_exchange, timeout=15) as resp:
                        long_resp = json.loads(resp.read().decode('utf-8'))
                    long_token = long_resp.get("access_token", short_token)
                    expires_in = long_resp.get("expires_in", 5184000)

                    expires_at = (datetime.utcnow() + timedelta(seconds=expires_in)).isoformat()
                    conn_id = f"meta_oauth_{uuid.uuid4().hex[:8]}"

                    cursor.execute("""
                        INSERT INTO facebook_connections (id, connection_type, name, access_token, token_type, expires_at, created_at, status)
                        VALUES (?, 'oauth_60d', 'Conexão Meta 1-Clique (60 Dias)', ?, 'BEARER', ?, ?, 'active')
                    """, (conn_id, long_token, expires_at, datetime.utcnow().isoformat()))

                    accounts_data = fetch_all_meta_pages(
                        "https://graph.facebook.com/v19.0/me/adaccounts",
                        long_token,
                        {"fields": "id,name,account_status,currency,timezone_name"}
                    )

                    for acc in accounts_data:
                        acc_id = acc.get("id")
                        acc_name = acc.get("name", "Conta de Anúncios")
                        status = acc.get("account_status", 1)
                        curr = acc.get("currency", "BRL")
                        tz = acc.get("timezone_name", "America/Sao_Paulo")
                        cursor.execute("""
                            INSERT OR REPLACE INTO facebook_ad_accounts (id, connection_id, name, account_status, currency, timezone_name, is_selected, last_synced_at)
                            VALUES (?, ?, ?, ?, ?, ?, 1, ?)
                        """, (acc_id, conn_id, acc_name, status, curr, tz, datetime.utcnow().isoformat()))

                    conn.commit()
                    conn.close()

                    self.send_file_response_html_message(
                        "Conexão Realizada com Sucesso!",
                        f"{len(accounts_data)} conta(s) de anúncios sincronizada(s)! Redirecionando para o UtmFlow...",
                        redirect_to="/"
                    )
                    return
                except Exception as e:
                    conn.close()
                    traceback.print_exc()
                    self.send_file_response_html_message("Erro na Troca de Token", f"Falha ao validar com a Meta Graph API: {e}")
                    return

            elif path == "/api/pixels":
                cursor.execute("SELECT id, name, pixel_id, test_event_code, is_active, created_at FROM meta_pixels ORDER BY created_at DESC")
                pix = [dict(r) for r in cursor.fetchall()]
                conn.close()
                self.send_json({"success": True, "pixels": pix})
                return

            elif path == "/api/rules":
                cursor.execute("SELECT * FROM automated_rules ORDER BY created_at DESC")
                rules = [dict(r) for r in cursor.fetchall()]
                conn.close()
                self.send_json({"success": True, "rules": rules})
                return

            elif path == "/api/rules/logs":
                cursor.execute("SELECT * FROM rule_logs ORDER BY created_at DESC LIMIT 50")
                logs = [dict(r) for r in cursor.fetchall()]
                conn.close()
                self.send_json({"success": True, "logs": logs})
                return

            elif path == "/api/preferences":
                cursor.execute("SELECT * FROM user_preferences WHERE id = 'default'")
                pref = cursor.fetchone()
                conn.close()
                if pref:
                    cols = json.loads(pref["columns_config"]) if pref["columns_config"] else None
                    self.send_json({"success": True, "preferences": {"columns": cols, "theme": pref["theme"]}})
                else:
                    self.send_json({"success": True, "preferences": {"columns": None, "theme": "dark"}})
                return

            elif path == "/api/dashboard/layout":
                cursor.execute("SELECT layout_json FROM custom_dashboards WHERE id = 'default'")
                row = cursor.fetchone()
                conn.close()
                layout = json.loads(row["layout_json"]) if (row and row["layout_json"]) else None
                self.send_json({"success": True, "layout": layout})
                return

            elif path == "/api/financial/settings":
                cursor.execute("SELECT * FROM financial_settings WHERE id = 'default'")
                row = cursor.fetchone()
                conn.close()
                self.send_json({"success": True, "settings": dict(row) if row else {}})
                return

            else:
                conn.close()
                self.send_json({"error": "Route not found"}, 404)
                return

        except Exception as e:
            traceback.print_exc()
            self.send_json({"success": False, "error": str(e)}, 500)

    # ------------------ POST ROUTES ------------------
    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        body = self.parse_body()

        try:
            conn = get_db()
            cursor = conn.cursor()

            if path == "/api/track":
                ev_id = str(uuid.uuid4())
                now_iso = datetime.utcnow().isoformat()
                cursor.execute("""
                    INSERT INTO tracking_events (
                        id, event_name, event_id, url, referrer, utm_source, utm_medium,
                        utm_campaign, utm_content, utm_term, src, sck, fbc, fbp, ip, user_agent, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    ev_id,
                    body.get('event_name', 'PageView'),
                    body.get('event_id', ev_id),
                    body.get('url', ''),
                    body.get('referrer', ''),
                    body.get('utm_source', ''),
                    body.get('utm_medium', ''),
                    body.get('utm_campaign', ''),
                    body.get('utm_content', ''),
                    body.get('utm_term', ''),
                    body.get('src', ''),
                    body.get('sck', ''),
                    body.get('fbc', ''),
                    body.get('fbp', ''),
                    self.client_address[0],
                    self.headers.get('User-Agent', ''),
                    now_iso
                ))
                conn.commit()
                conn.close()
                self.send_json({"success": True, "event_id": ev_id})
                return

            elif path.startswith("/api/webhook/"):
                platform = path.split("/")[-1]
                order_data = self.normalize_webhook_payload(platform, body)

                ord_id = f"ord_{uuid.uuid4().hex[:10]}"
                now_iso = datetime.utcnow().isoformat()

                cursor.execute("""
                    INSERT OR REPLACE INTO orders (
                        id, external_id, platform, status, amount, currency, customer_name, customer_email,
                        customer_phone, customer_ip, customer_user_agent, utm_source, utm_medium, utm_campaign,
                        utm_content, utm_term, src, sck, fbc, fbp, product_name, product_id, created_at, paid_at, raw_payload
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    ord_id,
                    order_data.get('external_id', ord_id),
                    platform,
                    order_data.get('status', 'paid'),
                    order_data.get('amount', 0.0),
                    order_data.get('currency', 'BRL'),
                    order_data.get('customer_name', 'Cliente'),
                    order_data.get('customer_email', ''),
                    order_data.get('customer_phone', ''),
                    order_data.get('customer_ip', self.client_address[0]),
                    order_data.get('customer_user_agent', self.headers.get('User-Agent', '')),
                    order_data.get('utm_source', 'direto'),
                    order_data.get('utm_medium', ''),
                    order_data.get('utm_campaign', ''),
                    order_data.get('utm_content', ''),
                    order_data.get('utm_term', ''),
                    order_data.get('src', ''),
                    order_data.get('sck', ''),
                    order_data.get('fbc', ''),
                    order_data.get('fbp', ''),
                    order_data.get('product_name', 'Produto UtmFlow'),
                    order_data.get('product_id', ''),
                    now_iso,
                    now_iso if order_data.get('status') == 'paid' else None,
                    json.dumps(body)
                ))
                conn.commit()

                if order_data.get('status') == 'paid':
                    cursor.execute("SELECT pixel_id, access_token, test_event_code FROM meta_pixels WHERE is_active = 1")
                    active_pixels = cursor.fetchall()
                    for px in active_pixels:
                        send_capi_event(
                            px["pixel_id"],
                            px["access_token"],
                            "Purchase",
                            {
                                "event_id": ord_id,
                                "email": order_data.get('customer_email'),
                                "phone": order_data.get('customer_phone'),
                                "ip": order_data.get('customer_ip', self.client_address[0]),
                                "user_agent": self.headers.get('User-Agent', ''),
                                "value": order_data.get('amount', 0.0),
                                "currency": order_data.get('currency', 'BRL'),
                                "fbc": order_data.get('fbc'),
                                "fbp": order_data.get('fbp')
                            },
                            test_code=px["test_event_code"]
                        )

                conn.close()
                self.send_json({"success": True, "message": f"Webhook {platform} processado com sucesso", "order_id": ord_id})
                return

            elif path == "/api/demo/simulate_sale":
                ord_id = f"ord_{uuid.uuid4().hex[:10]}"
                now_iso = datetime.utcnow().isoformat()
                amount = float(body.get('amount', 197.00))
                customer_name = body.get('customer_name', 'Comprador Teste VIP')
                platform = body.get('platform', 'kiwify')
                source = body.get('utm_source', 'facebook')

                cursor.execute("""
                    INSERT INTO orders (
                        id, external_id, platform, status, amount, currency, customer_name, customer_email,
                        customer_phone, customer_ip, customer_user_agent, utm_source, utm_medium, utm_campaign,
                        utm_content, product_name, created_at, paid_at
                    ) VALUES (?, ?, ?, 'paid', ?, 'BRL', ?, 'teste@utmflow.com', '+5511999998888',
                              '189.40.12.55', 'UtmFlowDemoAgent/1.0', ?, 'cpc', '[ESCALA] Oferta Principal - VSL V2 (CBO)',
                              'AD01_VSL_HookDor_MulherChorando', 'Treinamento UtmFlow Escala 10X', ?, ?)
                """, (ord_id, f"sim_{uuid.uuid4().hex[:6]}", platform, amount, customer_name, source, now_iso, now_iso))
                conn.commit()
                conn.close()
                self.send_json({"success": True, "order_id": ord_id, "amount": amount, "customer_name": customer_name})
                return

            elif path == "/api/integrations/meta/config":
                app_id = body.get('app_id', '').strip()
                app_secret = body.get('app_secret', '').strip()
                redirect_uri = body.get('redirect_uri', '').strip()
                now_iso = datetime.utcnow().isoformat()

                cursor.execute("""
                    INSERT OR REPLACE INTO meta_oauth_config (id, app_id, app_secret, redirect_uri, updated_at)
                    VALUES ('default', ?, ?, ?, ?)
                """, (app_id, app_secret, redirect_uri, now_iso))
                conn.commit()
                conn.close()
                self.send_json({"success": True, "message": "Configurações de OAuth salvas com sucesso!"})
                return

            elif path == "/api/integrations/meta/manual_token":
                token = body.get('access_token', '').strip()
                custom_name = body.get('name', 'Token Permanente BM').strip()
                if not token:
                    conn.close()
                    self.send_json({"success": False, "error": "Token de acesso é obrigatório"}, 400)
                    return

                try:
                    accounts_data = fetch_all_meta_pages(
                        "https://graph.facebook.com/v19.0/me/adaccounts",
                        token,
                        {"fields": "id,name,account_status,currency,timezone_name"}
                    )

                    conn_id = f"meta_perm_{uuid.uuid4().hex[:8]}"
                    now_iso = datetime.utcnow().isoformat()

                    cursor.execute("""
                        INSERT INTO facebook_connections (id, connection_type, name, access_token, token_type, expires_at, created_at, status)
                        VALUES (?, 'system_user_permanent', ?, ?, 'PERMANENT', 'NEVER', ?, 'active')
                    """, (conn_id, custom_name, token, now_iso))

                    for acc in accounts_data:
                        acc_id = acc.get("id")
                        acc_name = acc.get("name", "Conta BM")
                        status = acc.get("account_status", 1)
                        curr = acc.get("currency", "BRL")
                        tz = acc.get("timezone_name", "America/Sao_Paulo")
                        cursor.execute("""
                            INSERT OR REPLACE INTO facebook_ad_accounts (id, connection_id, name, account_status, currency, timezone_name, is_selected, last_synced_at)
                            VALUES (?, ?, ?, ?, ?, ?, 1, ?)
                        """, (acc_id, conn_id, acc_name, status, curr, tz, now_iso))

                    conn.commit()
                    conn.close()
                    self.send_json({"success": True, "message": f"Token Permanente validado! {len(accounts_data)} contas importadas."})
                    return
                except Exception as e:
                    conn.close()
                    self.send_json({"success": False, "error": f"Token inválido ou sem permissões da Meta: {str(e)}"}, 400)
                    return

            elif path == "/api/integrations/meta/accounts/toggle":
                account_id = body.get('account_id')
                is_selected = 1 if body.get('is_selected') else 0
                cursor.execute("UPDATE facebook_ad_accounts SET is_selected = ? WHERE id = ?", (is_selected, account_id))
                conn.commit()
                conn.close()
                self.send_json({"success": True})
                return

            elif path == "/api/integrations/meta/accounts/toggle_all":
                select_all = 1 if body.get('select_all') else 0
                cursor.execute("UPDATE facebook_ad_accounts SET is_selected = ?", (select_all,))
                conn.commit()
                conn.close()
                self.send_json({"success": True})
                return

            elif path == "/api/integrations/meta/disconnect":
                cursor.execute("SELECT access_token FROM facebook_connections WHERE status = 'active' LIMIT 1")
                row = cursor.fetchone()
                if row and row["access_token"]:
                    try:
                        req = urllib.request.Request(
                            f"https://graph.facebook.com/v19.0/me/permissions?access_token={row['access_token']}",
                            method='DELETE'
                        )
                        urllib.request.urlopen(req, timeout=10)
                    except Exception as e:
                        print(f"[Revoke Warning] {e}")

                cursor.execute("DELETE FROM facebook_connections")
                cursor.execute("DELETE FROM facebook_ad_accounts")
                cursor.execute("DELETE FROM campaigns WHERE account_id NOT IN ('act_1092837482')")
                conn.commit()
                conn.close()
                self.send_json({"success": True, "message": "Conta desconectada e permissões revogadas com sucesso."})
                return

            elif path == "/api/campaigns/sync":
                period = body.get('period', 'today')
                start_date = body.get('start_date')
                end_date = body.get('end_date')

                cursor.execute("SELECT access_token FROM facebook_connections WHERE status = 'active' LIMIT 1")
                conn_row = cursor.fetchone()
                if not conn_row:
                    conn.close()
                    self.send_json({"success": False, "error": "Nenhuma conexão Meta ativa."}, 400)
                    return

                token = conn_row["access_token"]
                cursor.execute("SELECT id FROM facebook_ad_accounts WHERE is_selected = 1")
                accounts = cursor.fetchall()
                now_iso = datetime.utcnow().isoformat()

                total_synced = 0
                for acc in accounts:
                    acc_id = acc["id"]
                    clean_id = acc_id if acc_id.startswith("act_") else f"act_{acc_id}"
                    try:
                        camps = fetch_all_meta_pages(
                            f"https://graph.facebook.com/v19.0/{clean_id}/campaigns",
                            token,
                            {"fields": "id,name,status,effective_status,objective,daily_budget,lifetime_budget"}
                        )
                        for c in camps:
                            c_id = c.get("id")
                            c_name = c.get("name")
                            c_stat = c.get("status", "ACTIVE")
                            c_eff = c.get("effective_status", "ACTIVE")
                            c_obj = c.get("objective", "OUTCOME_SALES")
                            dbudget = float(c.get("daily_budget", 0)) / 100.0 if c.get("daily_budget") else 0.0

                            insights_params = {"fields": "spend,impressions,clicks,cpc,ctr"}
                            if period == 'custom' and start_date and end_date:
                                insights_params["time_range"] = json.dumps({"since": start_date, "until": end_date})
                            else:
                                insights_params["date_preset"] = "today" if period == 'today' else "last_7d"

                            try:
                                in_res = meta_api_get(f"{c_id}/insights", token, insights_params)
                                in_data = in_res.get("data", [{}])[0] if in_res.get("data") else {}
                                sp = float(in_data.get("spend", 0.0))
                                imp = int(in_data.get("impressions", 0))
                                clk = int(in_data.get("clicks", 0))
                                ctr = float(in_data.get("ctr", 0.0))
                                cpc = float(in_data.get("cpc", 0.0))
                            except Exception:
                                sp, imp, clk, ctr, cpc = 0.0, 0, 0, 0.0, 0.0

                            cursor.execute("""
                                INSERT OR REPLACE INTO campaigns (id, account_id, name, status, effective_status, objective, daily_budget, spend, impressions, clicks, ctr, cpc, updated_at)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (c_id, acc_id, c_name, c_stat, c_eff, c_obj, dbudget, sp, imp, clk, ctr, cpc, now_iso))
                            total_synced += 1
                    except Exception as e:
                        print(f"[Sync Error {acc_id}] {e}")

                conn.commit()
                conn.close()
                self.send_json({"success": True, "message": f"{total_synced} campanhas sincronizadas com a Meta API."})
                return

            elif path == "/api/campaigns/batch":
                ids = body.get('ids', [])
                action = body.get('action')
                budget = float(body.get('budget', 0.0))

                if not ids:
                    conn.close()
                    self.send_json({"success": False, "error": "Nenhum item selecionado"}, 400)
                    return

                placeholders = ','.join(['?'] * len(ids))
                if action == 'activate':
                    cursor.execute(f"UPDATE campaigns SET status = 'ACTIVE', effective_status = 'ACTIVE' WHERE id IN ({placeholders})", ids)
                elif action == 'pause':
                    cursor.execute(f"UPDATE campaigns SET status = 'PAUSED', effective_status = 'PAUSED' WHERE id IN ({placeholders})", ids)
                elif action == 'delete':
                    cursor.execute(f"DELETE FROM campaigns WHERE id IN ({placeholders})", ids)
                    cursor.execute(f"DELETE FROM ad_sets WHERE campaign_id IN ({placeholders})", ids)
                    cursor.execute(f"DELETE FROM ads WHERE campaign_id IN ({placeholders})", ids)
                elif action == 'set_budget':
                    cursor.execute(f"UPDATE campaigns SET daily_budget = ? WHERE id IN ({placeholders})", [budget] + ids)

                conn.commit()
                conn.close()
                self.send_json({"success": True})
                return

            elif path == "/api/campaigns/duplicate":
                source_id = body.get('campaign_id')
                cursor.execute("SELECT * FROM campaigns WHERE id = ?", (source_id,))
                camp = cursor.fetchone()
                if not camp:
                    conn.close()
                    self.send_json({"success": False, "error": "Campanha original não encontrada"}, 404)
                    return

                new_camp_id = f"camp_{uuid.uuid4().hex[:8]}"
                now_iso = datetime.utcnow().isoformat()
                cursor.execute("""
                    INSERT INTO campaigns (id, account_id, name, status, effective_status, objective, daily_budget, updated_at)
                    VALUES (?, ?, ?, 'PAUSED', 'PAUSED', ?, ?, ?)
                """, (new_camp_id, camp["account_id"], f"{camp['name']} (Cópia)", camp["objective"], camp["daily_budget"], now_iso))

                cursor.execute("SELECT * FROM ad_sets WHERE campaign_id = ?", (source_id,))
                adsets = cursor.fetchall()
                for adset in adsets:
                    new_adset_id = f"adset_{uuid.uuid4().hex[:8]}"
                    cursor.execute("""
                        INSERT INTO ad_sets (id, account_id, campaign_id, name, status, effective_status, daily_budget, updated_at)
                        VALUES (?, ?, ?, ?, 'PAUSED', 'PAUSED', ?, ?)
                    """, (new_adset_id, adset["account_id"], new_camp_id, f"{adset['name']} (Cópia)", adset["daily_budget"], now_iso))

                    cursor.execute("SELECT * FROM ads WHERE adset_id = ?", (adset["id"],))
                    ads_list = cursor.fetchall()
                    for ad in ads_list:
                        new_ad_id = f"ad_{uuid.uuid4().hex[:8]}"
                        cursor.execute("""
                            INSERT INTO ads (id, account_id, campaign_id, adset_id, name, status, effective_status, creative_name, creative_thumbnail, updated_at)
                            VALUES (?, ?, ?, ?, ?, 'PAUSED', 'PAUSED', ?, ?, ?)
                        """, (new_ad_id, ad["account_id"], new_camp_id, new_adset_id, f"{ad['name']} (Cópia)", ad["creative_name"], ad["creative_thumbnail"], now_iso))

                conn.commit()
                conn.close()
                self.send_json({"success": True, "new_campaign_id": new_camp_id})
                return

            elif path == "/api/adsets/batch":
                ids = body.get('ids', [])
                action = body.get('action')
                budget = float(body.get('budget', 0.0))
                if not ids:
                    conn.close()
                    self.send_json({"success": False, "error": "Nenhum conjunto selecionado"}, 400)
                    return
                placeholders = ','.join(['?'] * len(ids))
                if action == 'activate':
                    cursor.execute(f"UPDATE ad_sets SET status = 'ACTIVE', effective_status = 'ACTIVE' WHERE id IN ({placeholders})", ids)
                elif action == 'pause':
                    cursor.execute(f"UPDATE ad_sets SET status = 'PAUSED', effective_status = 'PAUSED' WHERE id IN ({placeholders})", ids)
                elif action == 'delete':
                    cursor.execute(f"DELETE FROM ad_sets WHERE id IN ({placeholders})", ids)
                    cursor.execute(f"DELETE FROM ads WHERE adset_id IN ({placeholders})", ids)
                elif action == 'set_budget':
                    cursor.execute(f"UPDATE ad_sets SET daily_budget = ? WHERE id IN ({placeholders})", [budget] + ids)
                conn.commit()
                conn.close()
                self.send_json({"success": True})
                return

            elif path == "/api/ads/batch":
                ids = body.get('ids', [])
                action = body.get('action')
                if not ids:
                    conn.close()
                    self.send_json({"success": False, "error": "Nenhum anúncio selecionado"}, 400)
                    return
                placeholders = ','.join(['?'] * len(ids))
                if action == 'activate':
                    cursor.execute(f"UPDATE ads SET status = 'ACTIVE', effective_status = 'ACTIVE' WHERE id IN ({placeholders})", ids)
                elif action == 'pause':
                    cursor.execute(f"UPDATE ads SET status = 'PAUSED', effective_status = 'PAUSED' WHERE id IN ({placeholders})", ids)
                elif action == 'delete':
                    cursor.execute(f"DELETE FROM ads WHERE id IN ({placeholders})", ids)
                conn.commit()
                conn.close()
                self.send_json({"success": True})
                return

            elif path == "/api/pixels":
                name = body.get('name', 'Novo Pixel')
                pixel_id = body.get('pixel_id', '').strip()
                access_token = body.get('access_token', '').strip()
                test_event_code = body.get('test_event_code', '').strip()
                new_id = f"pix_{uuid.uuid4().hex[:8]}"
                cursor.execute("""
                    INSERT INTO meta_pixels (id, name, pixel_id, access_token, test_event_code, is_active, created_at)
                    VALUES (?, ?, ?, ?, ?, 1, ?)
                """, (new_id, name, pixel_id, access_token, test_event_code, datetime.utcnow().isoformat()))
                conn.commit()
                conn.close()
                self.send_json({"success": True, "id": new_id})
                return

            elif path == "/api/pixels/test_capi":
                pixel_db_id = body.get('id')
                cursor.execute("SELECT * FROM meta_pixels WHERE id = ?", (pixel_db_id,))
                px = cursor.fetchone()
                conn.close()
                if not px:
                    self.send_json({"success": False, "error": "Pixel não encontrado"}, 404)
                    return

                test_res = send_capi_event(
                    px["pixel_id"],
                    px["access_token"],
                    "Purchase",
                    {
                        "email": "teste.capi@utmflow.com",
                        "phone": "+5511999999999",
                        "ip": "189.40.12.55",
                        "user_agent": "Mozilla/5.0 UtmFlowTest",
                        "value": 197.00,
                        "currency": "BRL"
                    },
                    test_code=px["test_event_code"]
                )
                self.send_json({"success": True, "capi_response": test_res})
                return

            elif path == "/api/rules":
                new_id = f"rule_{uuid.uuid4().hex[:8]}"
                cursor.execute("""
                    INSERT INTO automated_rules (id, name, rule_type, condition_metric, threshold_value, action_type, action_value, target_account_id, is_active, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
                """, (
                    new_id,
                    body.get('name', 'Nova Regra'),
                    body.get('rule_type', 'stop_loss'),
                    body.get('condition_metric', 'spend_no_sales'),
                    float(body.get('threshold_value', 100)),
                    body.get('action_type', 'pause_campaign'),
                    float(body.get('action_value', 0)),
                    body.get('target_account_id', 'all'),
                    datetime.utcnow().isoformat()
                ))
                conn.commit()
                conn.close()
                self.send_json({"success": True, "id": new_id})
                return

            elif path == "/api/rules/toggle":
                rule_id = body.get('id')
                is_active = 1 if body.get('is_active') else 0
                cursor.execute("UPDATE automated_rules SET is_active = ? WHERE id = ?", (is_active, rule_id))
                conn.commit()
                conn.close()
                self.send_json({"success": True})
                return

            elif path == "/api/preferences":
                cols = json.dumps(body.get('columns', []))
                theme = body.get('theme', 'dark')
                cursor.execute("""
                    INSERT OR REPLACE INTO user_preferences (id, columns_config, theme, updated_at)
                    VALUES ('default', ?, ?, ?)
                """, (cols, theme, datetime.utcnow().isoformat()))
                conn.commit()
                conn.close()
                self.send_json({"success": True})
                return

            elif path == "/api/dashboard/layout":
                layout_json = json.dumps(body.get('layout', []))
                cursor.execute("""
                    INSERT OR REPLACE INTO custom_dashboards (id, layout_json, updated_at)
                    VALUES ('default', ?, ?)
                """, (layout_json, datetime.utcnow().isoformat()))
                conn.commit()
                conn.close()
                self.send_json({"success": True})
                return

            elif path == "/api/financial/settings":
                cursor.execute("""
                    UPDATE financial_settings
                    SET tax_rate = ?, gateway_rate = ?, gateway_fixed_fee = ?, product_cost_rate = ?, updated_at = ?
                    WHERE id = 'default'
                """, (
                    float(body.get('tax_rate', 6.0)),
                    float(body.get('gateway_rate', 8.9)),
                    float(body.get('gateway_fixed_fee', 2.49)),
                    float(body.get('product_cost_rate', 15.0)),
                    datetime.utcnow().isoformat()
                ))
                conn.commit()
                conn.close()
                self.send_json({"success": True})
                return

            else:
                conn.close()
                self.send_json({"error": "Route not found"}, 404)
                return

        except Exception as e:
            traceback.print_exc()
            self.send_json({"success": False, "error": str(e)}, 500)

    # ------------------ DELETE ROUTES ------------------
    def do_DELETE(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        try:
            conn = get_db()
            cursor = conn.cursor()

            if path == "/api/pixels":
                px_id = query.get('id', [None])[0]
                if px_id:
                    cursor.execute("DELETE FROM meta_pixels WHERE id = ?", (px_id,))
                    conn.commit()
                conn.close()
                self.send_json({"success": True})
                return

            elif path == "/api/rules":
                rule_id = query.get('id', [None])[0]
                if rule_id:
                    cursor.execute("DELETE FROM automated_rules WHERE id = ?", (rule_id,))
                    conn.commit()
                conn.close()
                self.send_json({"success": True})
                return

            else:
                conn.close()
                self.send_json({"error": "Route not found"}, 404)
                return
        except Exception as e:
            traceback.print_exc()
            self.send_json({"success": False, "error": str(e)}, 500)

    # ------------------ WEBHOOK NORMALIZER ------------------
    def normalize_webhook_payload(self, platform, payload):
        norm = {
            "external_id": None,
            "status": "paid",
            "amount": 0.0,
            "currency": "BRL",
            "customer_name": "Cliente",
            "customer_email": "",
            "customer_phone": "",
            "utm_source": "direto",
            "utm_medium": "",
            "utm_campaign": "",
            "utm_content": "",
            "utm_term": "",
            "src": "",
            "sck": "",
            "fbc": "",
            "fbp": "",
            "product_name": "Produto"
        }

        if platform == "kiwify":
            norm["external_id"] = payload.get("order_id", payload.get("order_ref"))
            st = payload.get("order_status", "").lower()
            norm["status"] = "paid" if st in ["paid", "approved", "completed"] else ("waiting_payment" if st in ["waiting_payment", "billet_printed"] else st)
            norm["amount"] = float(payload.get("order_amount", payload.get("Commissions", {}).get("charge_amount", 0))) / 100.0 if "order_amount" in payload and payload.get("order_amount", 0) > 1000 else float(payload.get("order_amount", 0))
            cust = payload.get("Customer", {})
            norm["customer_name"] = cust.get("full_name", "Cliente Kiwify")
            norm["customer_email"] = cust.get("email", "")
            norm["customer_phone"] = cust.get("mobile", "")
            trk = payload.get("TrackingParameters", {})
            norm["utm_source"] = trk.get("utm_source", payload.get("utm_source", "direto"))
            norm["utm_medium"] = trk.get("utm_medium", payload.get("utm_medium", ""))
            norm["utm_campaign"] = trk.get("utm_campaign", payload.get("utm_campaign", ""))
            norm["utm_content"] = trk.get("utm_content", payload.get("utm_content", ""))
            norm["utm_term"] = trk.get("utm_term", payload.get("utm_term", ""))
            norm["src"] = trk.get("src", payload.get("src", ""))
            norm["sck"] = trk.get("sck", payload.get("sck", ""))
            norm["fbc"] = trk.get("fbc", payload.get("fbc", ""))
            norm["fbp"] = trk.get("fbp", payload.get("fbp", ""))
            prod = payload.get("Product", {})
            norm["product_name"] = prod.get("product_name", "Produto Kiwify")

        elif platform == "hotmart":
            data = payload.get("data", payload)
            pur = data.get("purchase", {})
            buyer = data.get("buyer", {})
            norm["external_id"] = pur.get("transaction", payload.get("transaction"))
            ev = payload.get("event", "").upper()
            norm["status"] = "paid" if ev in ["PURCHASE_APPROVED", "PURCHASE_COMPLETE"] else ("waiting_payment" if ev == "PURCHASE_OUT_OF_DATE" else "paid")
            norm["amount"] = float(pur.get("price", {}).get("value", payload.get("price", 0)))
            norm["customer_name"] = buyer.get("name", "Cliente Hotmart")
            norm["customer_email"] = buyer.get("email", "")
            norm["customer_phone"] = buyer.get("checkout_phone", "")
            trk = pur.get("tracking", {})
            norm["utm_source"] = trk.get("source", trk.get("utm_source", "direto"))
            norm["sck"] = trk.get("source_sck", "")
            norm["product_name"] = data.get("product", {}).get("name", "Produto Hotmart")

        elif platform == "greenn":
            sale = payload.get("sale", payload)
            norm["external_id"] = str(sale.get("id", payload.get("id")))
            st_code = str(payload.get("status", sale.get("status", "2")))
            norm["status"] = "paid" if st_code in ["2", "paid"] else ("waiting_payment" if st_code in ["1", "waiting"] else "refused")
            norm["amount"] = float(sale.get("amount", payload.get("amount", 0)))
            norm["customer_name"] = sale.get("client_name", payload.get("client_name", "Cliente Greenn"))
            norm["customer_email"] = sale.get("client_email", payload.get("client_email", ""))
            norm["customer_phone"] = sale.get("client_cellphone", "")
            norm["utm_source"] = sale.get("utm_source", payload.get("utm_source", "direto"))
            norm["utm_campaign"] = sale.get("utm_campaign", payload.get("utm_campaign", ""))
            norm["utm_medium"] = sale.get("utm_medium", payload.get("utm_medium", ""))

        elif platform == "cakto":
            norm["external_id"] = str(payload.get("transaction_id", payload.get("id")))
            st = payload.get("status", "paid").lower()
            norm["status"] = "paid" if st in ["approved", "paid"] else "waiting_payment"
            norm["amount"] = float(payload.get("amount", payload.get("total", 0)))
            cust = payload.get("customer", {})
            norm["customer_name"] = cust.get("name", "Cliente Cakto")
            norm["customer_email"] = cust.get("email", "")
            norm["customer_phone"] = cust.get("phone", "")
            trk = payload.get("tracking", payload)
            norm["utm_source"] = trk.get("utm_source", "direto")
            norm["utm_campaign"] = trk.get("utm_campaign", "")

        elif platform == "wiapy":
            norm["external_id"] = str(payload.get("order_id", payload.get("id")))
            st = payload.get("status", "paid").lower()
            norm["status"] = "paid" if st in ["approved", "paid"] else "waiting_payment"
            norm["amount"] = float(payload.get("value", payload.get("amount", 0)))
            cli = payload.get("client", {})
            norm["customer_name"] = cli.get("name", "Cliente Wiapy")
            norm["customer_email"] = cli.get("email", "")
            norm["customer_phone"] = cli.get("phone", "")
            utms = payload.get("utms", payload)
            norm["utm_source"] = utms.get("utm_source", "direto")

        else:
            norm["external_id"] = str(payload.get("id", payload.get("order_id", uuid.uuid4().hex[:8])))
            norm["amount"] = float(payload.get("amount", payload.get("value", payload.get("total", 0))))
            norm["status"] = "paid" if str(payload.get("status", "paid")).lower() in ["paid", "approved", "completed"] else "waiting_payment"
            norm["customer_name"] = payload.get("customer_name", payload.get("name", "Cliente"))
            norm["customer_email"] = payload.get("customer_email", payload.get("email", ""))
            norm["utm_source"] = payload.get("utm_source", "direto")
            norm["utm_campaign"] = payload.get("utm_campaign", "")

        return norm

    def send_file_response_html_message(self, title, message, redirect_to=None):
        redirect_tag = f'<meta http-equiv="refresh" content="3;url={redirect_to}">' if redirect_to else ''
        html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>{title} - UtmFlow</title>
    {redirect_tag}
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-[#0B0F19] text-white flex items-center justify-center min-h-screen p-4">
    <div class="bg-[#111827] border border-slate-800 p-8 rounded-2xl max-w-md w-full text-center shadow-2xl">
        <div class="w-16 h-16 bg-blue-600/20 text-blue-500 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>
        </div>
        <h1 class="text-2xl font-bold mb-2">{title}</h1>
        <p class="text-slate-400 mb-6">{message}</p>
        <a href="/" class="inline-block w-full py-3 px-4 bg-[#1877F2] hover:bg-blue-600 font-semibold rounded-xl transition shadow-lg shadow-blue-500/20">Ir para o Dashboard UtmFlow</a>
    </div>
</body>
</html>"""
        body = html.encode('utf-8')
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

# -------------------------------------------------------------
# MAIN SERVER RUNNER
# -------------------------------------------------------------

def run_server():
    init_db()

    rules_thread = threading.Thread(target=automated_rules_worker, daemon=True)
    rules_thread.start()

    port = 8000
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            pass
    elif "PORT" in os.environ:
        try:
            port = int(os.environ["PORT"])
        except ValueError:
            pass

    server_address = ("0.0.0.0", port)
    httpd = http.server.ThreadingHTTPServer(server_address, UtmFlowHandler)
    print("=" * 60)
    print(f"🚀 UtmFlow Platform rodando com sucesso!")
    print(f"📍 Endereço Local: http://localhost:{port}")
    print(f"📍 Endereço de Rede: http://0.0.0.0:{port}")
    print(f"📦 Zero Dependências Externas (Pure Python Standard Library)")
    print(f"🛡️  ThreadedHTTPServer + SQLite3 Migrations + CAPI Ready")
    print("=" * 60)

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[UtmFlow] Servidor encerrado graciosamente.")
        httpd.server_close()

if __name__ == "__main__":
    run_server()
