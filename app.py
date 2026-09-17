import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import uuid

# =========================================================
# SAYFA AYARLARI
# =========================================================
st.set_page_config(
    page_title="Solak Ailesi Bütçe",
    page_icon="💰",
    layout="centered",
    initial_sidebar_state="collapsed",
)

USERS = ["Kenan", "Tabibe", "Nilgün", "Ozan"]

USER_COLORS = {
    "Kenan": ("#AEE1F9", "#3A6EA5"),
    "Tabibe": ("#F9C9D6", "#B5495B"),
    "Nilgün": ("#D9C9F9", "#6C4A9C"),
    "Ozan": ("#C9F9D6", "#3A8C5A"),
}

CATEGORIES = [
    {"key": "market", "label": "Market", "emoji": "🛒", "color": "#DFF3E3"},
    {"key": "giyim", "label": "Giyim", "emoji": "👕", "color": "#FDE7EF"},
    {"key": "teknoloji", "label": "Teknoloji", "emoji": "💻", "color": "#E3ECFB"},
    {"key": "disarida_yemek", "label": "Dışarıda Yemek", "emoji": "🍔", "color": "#FFF3D6"},
    {"key": "ulasim", "label": "Ulaşım", "emoji": "🚗", "color": "#E9E3FB"},
    {"key": "saglik", "label": "Sağlık", "emoji": "💊", "color": "#FDE2E2"},
    {"key": "fatura", "label": "Fatura", "emoji": "🧾", "color": "#E2F6F6"},
    {"key": "eglence", "label": "Eğlence", "emoji": "🎉", "color": "#FCEBD6"},
    {"key": "diger", "label": "Diğer", "emoji": "🔖", "color": "#ECECEC"},
]
CATEGORY_LABELS = [f'{c["emoji"]} {c["label"]}' for c in CATEGORIES]

AYLAR = {1: "Ocak", 2: "Şubat", 3: "Mart", 4: "Nisan", 5: "Mayıs", 6: "Haziran",
         7: "Temmuz", 8: "Ağustos", 9: "Eylül", 10: "Ekim", 11: "Kasım", 12: "Aralık"}

# =========================================================
# SESSION STATE BAŞLANGICI
# =========================================================
def init_state():
    defaults = {
        "current_user": None,
        "page": "Ana Sayfa",
        "transactions": [],   
        "wishlist": [],       
        "entry_mode": None,
        "edit_txn_id": None,
        "edit_wish_id": None,
        "delete_confirm_id": None,
        "birikim_mode": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# =========================================================
# CSS 
# =========================================================
st.markdown(
    """
    <style>
    @media (max-width: 640px) {
        .block-container { padding-left: 1rem !important; padding-right: 1rem !important; padding-top: 1rem !important; }
        html, body, [class*="css"] { font-size: 15px; }
    }
    .stApp { background: linear-gradient(180deg, #FBFAF7 0%, #F4F6FB 100%); }
    
    div.stButton > button, div.stFormSubmitButton > button {
        border-radius: 16px; border: none; padding: 0.7rem 1rem; font-weight: 600;
        transition: transform 0.08s ease-in-out, box-shadow 0.15s ease;
        box-shadow: 0 3px 8px rgba(0,0,0,0.06); background: #EAF0FB; color: #33415C;
    }
    div.stButton > button:active { transform: scale(0.94); box-shadow: 0 1px 3px rgba(0,0,0,0.10); }
    div[role="radiogroup"] label {
        border-radius: 999px !important; padding: 0.45rem 0.9rem !important; margin: 0.2rem !important;
        background: #F1F3F8; border: 1px solid #E5E8F0;
    }
    .login-title { text-align: center; font-size: 2.1rem; font-weight: 700; color: #33415C; margin-top: 2.5rem; }
    .topbar { text-align: right; padding: 0.2rem 0.3rem 0.8rem 0.3rem; line-height: 1.25; }
    .topbar .family { font-size: 1.15rem; font-weight: 700; color: #33415C; }
    .topbar .user { font-size: 0.95rem; color: #7C8AA5; font-weight: 500; }
    div[data-testid="stNumberInput"] input { font-size: 2.1rem !important; font-weight: 700 !important; text-align: center; border-radius: 16px !important; }
    .kasa-total { text-align: center; background: linear-gradient(135deg, #DFF3E3, #E3ECFB); border-radius: 20px; padding: 1.4rem 1rem; margin-bottom: 1.2rem; }
    .kasa-total .amount { font-size: 2.3rem; font-weight: 800; color: #2F5233; }
    .kasa-total .label { font-size: 0.95rem; color: #567A5B; font-weight: 600; }
    .edit-box { background: #F8F9FA; border: 2px dashed #D2D6DC; border-radius: 16px; padding: 1rem; margin-bottom: 0.6rem; }
    .delete-box { background: #FDF2F2; border: 2px dashed #B5495B; border-radius: 16px; padding: 1rem; margin-bottom: 0.6rem; text-align: center;}
    
    /* Expander şıklaştırması */
    div[data-testid="stExpander"] { background: #FFFFFF; border-radius: 16px !important; border: 1px solid #E5E8F0 !important; box-shadow: 0 2px 6px rgba(0,0,0,0.03); margin-bottom: 0.8rem !important; }
    div[data-testid="stExpander"] summary { font-weight: 600; color: #33415C; }
    </style>
    """, unsafe_allow_html=True
)

# =========================================================
# YARDIMCI FONKSİYONLAR
# =========================================================
def get_df():
    if not st.session_state.transactions:
        df = pd.DataFrame(columns=["id", "type", "amount", "category", "note", "user", "date"])
        df["date"] = pd.to_datetime(df["date"])
        return df
    df = pd.DataFrame(st.session_state.transactions)
    df["date"] = pd.to_datetime(df["date"])
    return df

def update_txn(t_id, amount, cat, note):
    for i, t in enumerate(st.session_state.transactions):
        if t['id'] == t_id:
            st.session_state.transactions[i]['amount'] = float(amount)
            st.session_state.transactions[i]['category'] = cat
            st.session_state.transactions[i]['note'] = note
            break

def delete_txn(t_id):
    st.session_state.transactions = [t for t in st.session_state.transactions if t['id'] != t_id]

# =========================================================
# SAYFALAR
# =========================================================
def login_screen():
    st.markdown('<div class="login-title">👨‍👩‍👧‍👦 Kim giriş yapıyor?</div>', unsafe_allow_html=True)
    cols = st.columns(len(USERS))
    for i, (col, user) in enumerate(zip(cols, USERS)):
        bg, fg = USER_COLORS[user]
        col.markdown(f"""<style>div[data-testid="column"]:nth-of-type({i+1}) div.stButton > button {{ background: {bg}; color: {fg}; height: 130px; width: 100%; font-size: 1.15rem; font-weight: 800; border-radius: 22px; }}</style>""", unsafe_allow_html=True)
        with col:
            if st.button(f"👤\n\n{user}", key=f"login_{user}", use_container_width=True):
                st.session_state.current_user = user
                st.session_state.page = "Ana Sayfa"
                st.rerun()

def page_ana_sayfa():
    st.markdown("## 🏠 Ana Sayfa")
    df = get_df()
    now = datetime.now()
    
    # Anlık Durum
    c1, c2 = st.columns([0.7, 0.3])
    with c1: st.markdown("<div style='color: #7C8AA5; font-size: 1.1rem; font-weight:bold; margin-top:5px;'>Anlık Durum</div>", unsafe_allow_html=True)
    with c2: durum_tipi = st.selectbox("Seç", ["Aylık", "Toplam"], label_visibility="collapsed")
    
    if durum_tipi == "Aylık":
        df_kasa = df[(df['date'].dt.month == now.month) & (df['date'].dt.year == now.year)]
    else:
        df_kasa = df
        
    gelir_toplam = df_kasa[df_kasa["type"] == "gelir"]["amount"].sum()
    gider_toplam = df_kasa[df_kasa["type"] == "gider"]["amount"].sum()
    net_balance = gelir_toplam - gider_toplam
    
    bakiye_renk = "#2F8C4A" if net_balance >= 0 else "#B5495B"
    st.markdown(f"""
        <div class="kasa-total" style="background: #FFFFFF; border: 1px solid #E5E8F0; padding: 1rem; margin-bottom: 1.5rem; text-align:left;">
            <span style="font-size: 0.9rem; color:#7C8AA5;">{durum_tipi} Bakiye:</span><br>
            <span style="color: {bakiye_renk}; font-size: 2.2rem; font-weight:800;">₺{net_balance:,.2f}</span>
        </div>
    """, unsafe_allow_html=True)

    # Butonlar
    colA, colB = st.columns(2)
    with colA:
        if st.button("💚 Gelir Gir", use_container_width=True): st.session_state.entry_mode = "gelir"
    with colB:
        if st.button("💸 Harcama Gir", use_container_width=True): st.session_state.entry_mode = "gider"
    st.markdown("---")

    # Giriş Formları
    if st.session_state.entry_mode == "gelir":
        with st.form("gelir_form", clear_on_submit=True):
            amount = st.number_input("Tutar (₺)", min_value=0.0, step=10.0, format="%.2f")
            note = st.text_input("Not (opsiyonel)")
            if st.form_submit_button("✅ Kaydet", use_container_width=True):
                if amount > 0:
                    st.session_state.transactions.append({"id": str(uuid.uuid4()), "type": "gelir", "amount": float(amount), "category": "💚 Gelir", "note": note, "user": st.session_state.current_user, "date": datetime.now()})
                    st.session_state.entry_mode = None
                    st.rerun()
    elif st.session_state.entry_mode == "gider":
        amount = st.number_input("₺ Tutar", min_value=0.0, step=10.0, format="%.2f")
        selected_label = st.radio("Kategori", CATEGORY_LABELS, horizontal=True)
        note = st.text_input("Not (opsiyonel)")
        if st.button("✅ Kaydet", use_container_width=True):
            if amount > 0:
                st.session_state.transactions.append({"id": str(uuid.uuid4()), "type": "gider", "amount": float(amount), "category": selected_label, "note": note, "user": st.session_state.current_user, "date": datetime.now()})
                st.session_state.entry_mode = None
                st.rerun()

    # Son İşlemler (AÇILIR KAPANIR LİSTE - MOBİL UYUMLU)
    if not df.empty:
        st.markdown("#### 🕓 Son İşlemler")
        recent = df[(df["type"]=="gelir") | (df["type"]=="gider")].sort_values("date", ascending=False).head(10)
        for _, row in recent.iterrows():
            
            # Silme Onay Kutusu
            if st.session_state.delete_confirm_id == row['id']:
                st.markdown("<div class='delete-box'><b>Bu işlemi silmek istediğine emin misin?</b></div>", unsafe_allow_html=True)
                c_y, c_n = st.columns(2)
                with c_y:
                    if st.button("Evet, Sil", key=f"dy_{row['id']}", use_container_width=True):
                        delete_txn(row['id'])
                        st.session_state.delete_confirm_id = None
                        st.rerun()
                with c_n:
                    if st.button("İptal", key=f"dn_{row['id']}", use_container_width=True):
                        st.session_state.delete_confirm_id = None
                        st.rerun()
            
            # Düzenleme Kutusu
            elif st.session_state.edit_txn_id == row['id']:
                st.markdown("<div class='edit-box'>", unsafe_allow_html=True)
                new_amt = st.number_input("Tutar (₺)", value=float(row['amount']), key=f"amt_{row['id']}")
                cats = CATEGORY_LABELS if row['type'] == 'gider' else ["💚 Gelir"]
                idx = cats.index(row['category']) if row['category'] in cats else 0
                new_cat = st.selectbox("Kategori", cats, index=idx, key=f"cat_{row['id']}")
                new_note = st.text_input("Not", value=row['note'], key=f"not_{row['id']}")
                
                c_sv, c_cx = st.columns(2)
                with c_sv:
                    if st.button("💾 Kaydet", key=f"sv_{row['id']}", use_container_width=True):
                        update_txn(row['id'], new_amt, new_cat, new_note)
                        st.session_state.edit_txn_id = None
                        st.rerun()
                with c_cx:
                    if st.button("❌ İptal", key=f"cx_{row['id']}", use_container_width=True):
                        st.session_state.edit_txn_id = None
                        st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)
                
            # Normal Görünüm (AÇILIR KUTU İÇİNDE)
            else:
                ikon = "🟢" if row["type"] == "gelir" else "🔴"
                isaret = "+" if row["type"] == "gelir" else "-"
                baslik = f"{ikon} {row['category']} | {row['user']} | {isaret}₺{row['amount']:,.2f}"
                
                with st.expander(baslik):
                    st.markdown(f"<span style='color:#7C8AA5; font-size:0.95rem;'><b>Tarih:</b> {row['date'].strftime('%d %B - %H:%M')}</span>", unsafe_allow_html=True)
                    if row['note']:
                        st.markdown(f"**Not:** {row['note']}")
                    
                    st.write("") # Görsel boşluk
                    c_ed, c_del = st.columns(2)
                    with c_ed:
                        if st.button("✏️ Düzenle", key=f"ed_{row['id']}", use_container_width=True):
                            st.session_state.edit_txn_id = row['id']
                            st.rerun()
                    with c_del:
                        if st.button("🗑️ Sil", key=f"del_{row['id']}", use_container_width=True):
                            st.session_state.delete_confirm_id = row['id']
                            st.rerun()

def page_ozetler():
    st.markdown("## 📊 Özetler")
    df = get_df()
    if df.empty:
        st.info("Henüz veri yok.")
        return

    c1, c2 = st.columns(2)
    with c1: donem = st.selectbox("📅 Dönem", ["Aylık", "Yıllık", "Tüm Zamanlar"])
    with c2: secili_kullanici = st.selectbox("👤 Kullanıcı", ["Tüm Aile"] + USERS)

    now = datetime.now()
    if donem == "Aylık": df = df[(df["date"].dt.month == now.month) & (df["date"].dt.year == now.year)]
    elif donem == "Yıllık": df = df[df["date"].dt.year == now.year]
    
    if secili_kullanici != "Tüm Aile": df = df[df["user"] == secili_kullanici]

    tab1, tab2 = st.tabs(["💸 Harcamalar", "💚 Gelirler"])
    
    # HARCAMALAR
    with tab1:
        df_gider = df[df["type"] == "gider"]
        if not df_gider.empty:
            st.metric("Toplam Harcama", f"₺{df_gider['amount'].sum():,.2f}")
            chart_mode = st.radio("Grafik", ["Bar", "Pasta"], horizontal=True, key="gr_harcama")
            grouped = df_gider.groupby("category", as_index=False)["amount"].sum().sort_values("amount", ascending=False)
            if chart_mode == "Bar": fig = px.bar(grouped, x="category", y="amount", color="category", color_discrete_sequence=px.colors.qualitative.Pastel)
            else: fig = px.pie(grouped, names="category", values="amount", hole=0.45, color_discrete_sequence=px.colors.qualitative.Pastel)
            fig.update_layout(showlegend=False, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)
        else: st.info("Bu dönem için harcama yok.")
            
    # GELİRLER
    with tab2:
        df_gelir = df[df["type"] == "gelir"]
        if not df_gelir.empty:
            st.metric("Toplam Gelir", f"₺{df_gelir['amount'].sum():,.2f}")
            if donem == "Aylık":
                st.write("**Kişi Bazlı Gelir Dağılımı**")
                grp = df_gelir.groupby("user", as_index=False)["amount"].sum()
                fig2 = px.pie(grp, names="user", values="amount", hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
            else:
                st.write("**Aylara Göre Gelir Toplamı**")
                df_gelir["Ay"] = df_gelir["date"].dt.month.map(AYLAR)
                grp = df_gelir.groupby("Ay", as_index=False)["amount"].sum()
                # Aylar sırası
                ay_sirasi = list(AYLAR.values())
                grp['Ay'] = pd.Categorical(grp['Ay'], categories=ay_sirasi, ordered=True)
                grp = grp.sort_values("Ay")
                fig2 = px.bar(grp, x="Ay", y="amount", text="amount", color_discrete_sequence=["#2F8C4A"])
                fig2.update_traces(texttemplate='₺%{text:,.0f}', textposition='outside')
            
            fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig2, use_container_width=True)
        else: st.info("Bu dönem için gelir yok.")

def page_birikim():
    st.markdown("## 🪙 Birikim Kasası")
    df = get_df()
    
    toplam = 0.0
    if not df.empty:
        arti = df[df["type"] == "birikim_arti"]["amount"].sum()
        eksi = df[df["type"] == "birikim_eksi"]["amount"].sum()
        toplam = arti - eksi

    st.markdown(f"""
        <div class="kasa-total">
            <div class="label">Kasada Bulunan Toplam Birikim</div>
            <div class="amount">₺{toplam:,.2f}</div>
        </div>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        if st.button("➕ Kasaya Ekle", use_container_width=True): st.session_state.birikim_mode = "ekle"
    with c2:
        if st.button("➖ Kasadan Harca", use_container_width=True): st.session_state.birikim_mode = "harca"
        
    if st.session_state.birikim_mode == "ekle":
        st.markdown("#### ➕ Birikime Para Ekle")
        with st.form("b_arti"):
            amt = st.number_input("Tutar (₺)", min_value=0.0, step=10.0)
            note = st.text_input("Açıklama (Hangi ayın birikimi vb.)")
            if st.form_submit_button("Ekle", use_container_width=True):
                if amt>0:
                    st.session_state.transactions.append({"id": str(uuid.uuid4()), "type": "birikim_arti", "amount": float(amt), "category": "➕ Birikim Eklendi", "note": note, "user": st.session_state.current_user, "date": datetime.now()})
                    st.session_state.birikim_mode = None
                    st.rerun()
                    
    elif st.session_state.birikim_mode == "harca":
        st.markdown("#### ➖ Birikimden Para Harca")
        with st.form("b_eksi"):
            amt = st.number_input("Tutar (₺)", min_value=0.0, step=10.0)
            note = st.text_input("Ne için harcandı? (Örn: Bilgisayar)")
            if st.form_submit_button("Harca", use_container_width=True):
                if amt>0:
                    st.session_state.transactions.append({"id": str(uuid.uuid4()), "type": "birikim_eksi", "amount": float(amt), "category": "➖ Birikim Harcandı", "note": note, "user": st.session_state.current_user, "date": datetime.now()})
                    st.session_state.birikim_mode = None
                    st.rerun()

    if not df.empty:
        df_b = df[(df["type"] == "birikim_arti") | (df["type"] == "birikim_eksi")].sort_values("date", ascending=False)
        if not df_b.empty:
            st.write("---")
            st.markdown("#### 📜 Birikim Geçmişi")
            for _, row in df_b.iterrows():
                
                # Silme Onay Kutusu
                if st.session_state.delete_confirm_id == row['id']:
                    st.markdown("<div class='delete-box'><b>Bu işlemi silmek istediğine emin misin?</b></div>", unsafe_allow_html=True)
                    c_y, c_n = st.columns(2)
                    with c_y:
                        if st.button("Evet, Sil", key=f"dy_{row['id']}", use_container_width=True):
                            delete_txn(row['id'])
                            st.session_state.delete_confirm_id = None
                            st.rerun()
                    with c_n:
                        if st.button("İptal", key=f"dn_{row['id']}", use_container_width=True):
                            st.session_state.delete_confirm_id = None
                            st.rerun()
                
                # Düzenleme Kutusu
                elif st.session_state.edit_txn_id == row['id']:
                    st.markdown("<div class='edit-box'>", unsafe_allow_html=True)
                    new_amt = st.number_input("Tutar (₺)", value=float(row['amount']), key=f"amt_{row['id']}")
                    new_note = st.text_input("Açıklama", value=row['note'], key=f"not_{row['id']}")
                    c_sv, c_cx = st.columns(2)
                    with c_sv:
                        if st.button("💾 Kaydet", key=f"sv_{row['id']}", use_container_width=True):
                            update_txn(row['id'], new_amt, row['category'], new_note)
                            st.session_state.edit_txn_id = None
                            st.rerun()
                    with c_cx:
                        if st.button("❌ İptal", key=f"cx_{row['id']}", use_container_width=True):
                            st.session_state.edit_txn_id = None
                            st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)
                    
                # Normal Görünüm (AÇILIR KUTU İÇİNDE)
                else:
                    ikon = "🟢" if row["type"] == "birikim_arti" else "🔴"
                    isaret = "+" if row["type"] == "birikim_arti" else "-"
                    baslik = f"{ikon} {row['category']} | {isaret}₺{row['amount']:,.2f}"
                    
                    with st.expander(baslik):
                        st.markdown(f"<span style='color:#7C8AA5; font-size:0.95rem;'><b>Tarih:</b> {row['date'].strftime('%d %B - %H:%M')}</span>", unsafe_allow_html=True)
                        if row['note']:
                            st.markdown(f"**Not:** {row['note']}")
                        
                        st.write("") 
                        c_ed, c_del = st.columns(2)
                        with c_ed:
                            if st.button("✏️ Düzenle", key=f"eb_{row['id']}", use_container_width=True): st.session_state.edit_txn_id = row['id']; st.rerun()
                        with c_del:
                            if st.button("🗑️ Sil", key=f"db_{row['id']}", use_container_width=True): 
                                st.session_state.delete_confirm_id = row['id']; st.rerun()

def page_istek_listesi():
    st.markdown("## 🎁 İstek Listesi")
    with st.form("istek_form", clear_on_submit=True):
        item = st.text_input("İstek")
        c1, c2 = st.columns(2)
        with c1: kategori = st.selectbox("Kategori", CATEGORY_LABELS)
        with c2: tutar = st.number_input("Tahmini Tutar (₺)", min_value=0.0, step=10.0)
        if st.form_submit_button("➕ İsteği Ekle", use_container_width=True):
            if item.strip():
                st.session_state.wishlist.append({"id": str(uuid.uuid4()), "user": st.session_state.current_user, "item": item.strip(), "category": kategori, "amount": tutar, "date": datetime.now(), "seen": False})
                st.rerun()
                
    if st.session_state.wishlist:
        st.write("---")
        for i, wl in enumerate(sorted(st.session_state.wishlist, key=lambda x: x["date"], reverse=True)):
            
            # Silme Onay Kutusu
            if st.session_state.delete_confirm_id == wl['id']:
                st.markdown("<div class='delete-box'><b>Bu isteği silmek istediğine emin misin?</b></div>", unsafe_allow_html=True)
                c_y, c_n = st.columns(2)
                with c_y:
                    if st.button("Evet, Sil", key=f"dy_{wl['id']}", use_container_width=True):
                        st.session_state.wishlist = [w for w in st.session_state.wishlist if w['id'] != wl['id']]
                        st.session_state.delete_confirm_id = None
                        st.rerun()
                with c_n:
                    if st.button("İptal", key=f"dn_{wl['id']}", use_container_width=True):
                        st.session_state.delete_confirm_id = None
                        st.rerun()
                        
            # Düzenleme Kutusu
            elif st.session_state.edit_wish_id == wl['id']:
                st.markdown("<div class='edit-box'>", unsafe_allow_html=True)
                new_item = st.text_input("İstek", value=wl['item'], key=f"wi_{wl['id']}")
                new_amt = st.number_input("Tutar (₺)", value=float(wl['amount']), key=f"wa_{wl['id']}")
                c_sv, c_cx = st.columns(2)
                with c_sv:
                    if st.button("💾 Kaydet", key=f"ws_{wl['id']}", use_container_width=True):
                        for k, w in enumerate(st.session_state.wishlist):
                            if w['id'] == wl['id']:
                                st.session_state.wishlist[k]['item'] = new_item
                                st.session_state.wishlist[k]['amount'] = float(new_amt)
                        st.session_state.edit_wish_id = None
                        st.rerun()
                with c_cx:
                    if st.button("❌ İptal", key=f"wc_{wl['id']}", use_container_width=True):
                        st.session_state.edit_wish_id = None
                        st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)
                
            # Normal Görünüm (AÇILIR KUTU İÇİNDE)
            else:
                baslik = f"🎁 {wl['item']} | {wl['user']} | ₺{wl['amount']:,.2f}"
                with st.expander(baslik):
                    st.markdown(f"**Kategori:** {wl['category']}")
                    st.markdown(f"<span style='color:#7C8AA5; font-size:0.95rem;'><b>Eklenme:</b> {wl['date'].strftime('%d %B - %H:%M')}</span>", unsafe_allow_html=True)
                    
                    st.write("")
                    c_ed, c_del = st.columns(2)
                    with c_ed:
                        if st.button("✏️ Düzenle", key=f"ew_{wl['id']}", use_container_width=True): st.session_state.edit_wish_id = wl['id']; st.rerun()
                    with c_del:
                        if st.button("🗑️ Sil", key=f"dw_{wl['id']}", use_container_width=True): 
                            st.session_state.delete_confirm_id = wl['id']; st.rerun()

# =========================================================
# ANA YAPI & MENÜ ÇAĞIRMA
# =========================================================
if st.session_state.current_user is None:
    login_screen()
else:
    with st.sidebar:
        st.markdown("### 📋 Menü")
        w_label = "🎁 İstek Listesi 🔴" if any(not w["seen"] for w in st.session_state.wishlist) else "🎁 İstek Listesi"
        options = ["🏠 Ana Sayfa", "📊 Özetler", "🪙 Birikim", w_label]
        c_map = {"Ana Sayfa": 0, "Özetler": 1, "Birikim": 2, "İstek Listesi": 3}
        ch = st.radio("Menü", options, index=c_map.get(st.session_state.page, 0), label_visibility="collapsed")
        
        if ch.endswith("Ana Sayfa"): st.session_state.page = "Ana Sayfa"
        elif ch.endswith("Özetler"): st.session_state.page = "Özetler"
        elif ch.endswith("Birikim"): st.session_state.page = "Birikim"
        else:
            st.session_state.page = "İstek Listesi"
            for w in st.session_state.wishlist: w["seen"] = True
            
        st.markdown("---")
        if st.button("🚪 Çıkış Yap", use_container_width=True):
            st.session_state.current_user = None
            st.session_state.page = "Ana Sayfa"
            st.rerun()

    st.markdown(f"<div class='topbar'><div class='family'>Solak Ailesi</div><div class='user'>👤 {st.session_state.current_user}</div></div>", unsafe_allow_html=True)

    if st.session_state.page == "Ana Sayfa": page_ana_sayfa()
    elif st.session_state.page == "Özetler": page_ozetler()
    elif st.session_state.page == "Birikim": page_birikim()
    elif st.session_state.page == "İstek Listesi": page_istek_listesi()
