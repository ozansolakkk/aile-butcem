import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date
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

USERS = ["Kenan", "Tabibe", "Abla", "Ozan"]

USER_COLORS = {
    "Kenan": ("#AEE1F9", "#3A6EA5"),
    "Tabibe": ("#F9C9D6", "#B5495B"),
    "Abla": ("#D9C9F9", "#6C4A9C"),
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
    {"key": "birikim", "label": "Birikim", "emoji": "🐷", "color": "#F3E9DC"},
    {"key": "diger", "label": "Diğer", "emoji": "🔖", "color": "#ECECEC"},
]
CATEGORY_LABELS = [f'{c["emoji"]} {c["label"]}' for c in CATEGORIES]
CATEGORY_BY_LABEL = {f'{c["emoji"]} {c["label"]}': c for c in CATEGORIES}

# =========================================================
# SESSION STATE BAŞLANGICI
# =========================================================
def init_state():
    defaults = {
        "current_user": None,
        "page": "Ana Sayfa",
        "transactions": [],   # {id,type(gelir/gider),amount,category,note,user,date}
        "wishlist": [],       # {id,user,item,category,amount,date,seen}
        "entry_mode": None,   # "gelir" / "gider"
        "chart_mode": "Bar",  # "Bar" / "Pasta"
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

    .stApp {
        background: linear-gradient(180deg, #FBFAF7 0%, #F4F6FB 100%);
    }

    /* Genel buton hissi - tıklama animasyonu */
    div.stButton > button, div.stFormSubmitButton > button {
        border-radius: 16px;
        border: none;
        padding: 0.7rem 1rem;
        font-weight: 600;
        transition: transform 0.08s ease-in-out, box-shadow 0.15s ease;
        box-shadow: 0 3px 8px rgba(0,0,0,0.06);
        background: #EAF0FB;
        color: #33415C;
    }
    div.stButton > button:active, div.stFormSubmitButton > button:active {
        transform: scale(0.94);
        box-shadow: 0 1px 3px rgba(0,0,0,0.10);
    }
    div.stButton > button:hover, div.stFormSubmitButton > button:hover {
        filter: brightness(0.97);
    }

    /* Kategori chip'leri (radio) */
    div[role="radiogroup"] label {
        border-radius: 999px !important;
        padding: 0.45rem 0.9rem !important;
        margin: 0.2rem !important;
        background: #F1F3F8;
        border: 1px solid #E5E8F0;
        transition: transform 0.08s ease-in-out;
    }
    div[role="radiogroup"] label:active {
        transform: scale(0.94);
    }

    /* Giriş ekranı kartları */
    .login-title {
        text-align: center;
        font-size: 2.1rem;
        font-weight: 700;
        color: #33415C;
        margin-top: 2.5rem;
        margin-bottom: 2.2rem;
        letter-spacing: 0.5px;
    }

    /* Üst sağ bilgi bandı */
    .topbar {
        text-align: right;
        padding: 0.2rem 0.3rem 0.8rem 0.3rem;
        line-height: 1.25;
    }
    .topbar .family {
        font-size: 1.15rem;
        font-weight: 700;
        color: #33415C;
    }
    .topbar .user {
        font-size: 0.95rem;
        color: #7C8AA5;
        font-weight: 500;
    }

    /* Büyük tutar inputu */
    div[data-testid="stNumberInput"] input {
        font-size: 2.1rem !important;
        font-weight: 700 !important;
        text-align: center;
        color: #33415C;
        border-radius: 16px !important;
    }

    .kasa-total {
        text-align: center;
        background: linear-gradient(135deg, #DFF3E3, #E3ECFB);
        border-radius: 20px;
        padding: 1.4rem 1rem;
        margin-bottom: 1.2rem;
    }
    .kasa-total .amount {
        font-size: 2.3rem;
        font-weight: 800;
        color: #2F5233;
    }
    .kasa-total .label {
        font-size: 0.95rem;
        color: #567A5B;
        font-weight: 600;
    }

    .soft-card {
        background: #FFFFFF;
        border-radius: 16px;
        padding: 0.9rem 1.1rem;
        margin-bottom: 0.6rem;
        box-shadow: 0 2px 6px rgba(0,0,0,0.05);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# =========================================================
# YARDIMCI FONKSİYONLAR
# =========================================================
def add_transaction(t_type, amount, category_label, note, user):
    st.session_state.transactions.append(
        {
            "id": str(uuid.uuid4()),
            "type": t_type,  # "gelir" / "gider"
            "amount": float(amount),
            "category": category_label,
            "note": note,
            "user": user,
            "date": datetime.now(),
        }
    )


def get_df():
    if not st.session_state.transactions:
        return pd.DataFrame(
            columns=["id", "type", "amount", "category", "note", "user", "date"]
        )
    return pd.DataFrame(st.session_state.transactions)


def total_savings():
    df = get_df()
    if df.empty:
        return 0.0
    mask = (df["type"] == "gider") & (df["category"].str.contains("Birikim", na=False))
    return df.loc[mask, "amount"].sum()


def has_unseen_wishlist():
    return any(not item["seen"] for item in st.session_state.wishlist)


def logout():
    st.session_state.current_user = None
    st.session_state.page = "Ana Sayfa"
    st.session_state.entry_mode = None
    st.rerun()


# =========================================================
# GİRİŞ (PROFİL SEÇİM) EKRANI
# =========================================================
def login_screen():
    st.markdown('<div class="login-title">👨‍👩‍👧‍👦 Kim giriş yapıyor?</div>', unsafe_allow_html=True)

    cols = st.columns(len(USERS))
    for i, (col, user) in enumerate(zip(cols, USERS)):
        bg, fg = USER_COLORS[user]
        col.markdown(
            f"""
            <style>
            div[data-testid="column"]:nth-of-type({i+1}) div.stButton > button {{
                background: {bg};
                color: {fg};
                height: 130px;
                width: 100%;
                font-size: 1.15rem;
                font-weight: 800;
                border-radius: 22px;
            }}
            </style>
            """,
            unsafe_allow_html=True,
        )
        with col:
            if st.button(f"👤\n\n{user}", key=f"login_{user}", use_container_width=True):
                st.session_state.current_user = user
                st.session_state.page = "Ana Sayfa"
                st.rerun()


# =========================================================
# ÜST BAR
# =========================================================
def top_bar():
    st.markdown(
        f"""
        <div class="topbar">
            <div class="family">Solak Ailesi</div>
            <div class="user">👤 {st.session_state.current_user}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# SIDEBAR
# =========================================================
def sidebar_nav():
    with st.sidebar:
        st.markdown("### 📋 Menü")
        wishlist_label = "🎁 İstek Listesi"
        if has_unseen_wishlist():
            wishlist_label += " 🔴"

        options = ["🏠 Ana Sayfa", "📊 Özetler", "🐷 Birikim", wishlist_label]
        current_map = {
            "Ana Sayfa": 0,
            "Özetler": 1,
            "Birikim": 2,
            "İstek Listesi": 3,
        }
        choice = st.radio(
            "Sayfa seç",
            options,
            index=current_map.get(st.session_state.page, 0),
            label_visibility="collapsed",
        )

        if choice.endswith("Ana Sayfa"):
            st.session_state.page = "Ana Sayfa"
        elif choice.endswith("Özetler"):
            st.session_state.page = "Özetler"
        elif choice.endswith("Birikim"):
            st.session_state.page = "Birikim"
        else:
            st.session_state.page = "İstek Listesi"
            for item in st.session_state.wishlist:
                item["seen"] = True

        st.markdown("---")
        if st.button("🚪 Çıkış Yap", use_container_width=True):
            logout()


# =========================================================
# ANA SAYFA
# =========================================================
def page_ana_sayfa():
    st.markdown("## 🏠 Ana Sayfa")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("💚 Gelir Gir", use_container_width=True):
            st.session_state.entry_mode = "gelir"
    with col2:
        if st.button("💸 Harcama Gir", use_container_width=True):
            st.session_state.entry_mode = "gider"

    st.markdown("---")

    if st.session_state.entry_mode == "gelir":
        st.markdown("#### 💚 Gelir Girişi")
        with st.form("gelir_form", clear_on_submit=True):
            amount = st.number_input("Tutar (₺)", min_value=0.0, step=10.0, format="%.2f")
            note = st.text_input("Not (opsiyonel)")
            submitted = st.form_submit_button("✅ Kaydet", use_container_width=True)
            if submitted:
                if amount > 0:
                    add_transaction("gelir", amount, "💚 Gelir", note, st.session_state.current_user)
                    st.success(f"₺{amount:,.2f} gelir kaydedildi.")
                    st.session_state.entry_mode = None
                    st.rerun()
                else:
                    st.warning("Lütfen 0'dan büyük bir tutar girin.")

    elif st.session_state.entry_mode == "gider":
        st.markdown("#### 💸 Harcama Girişi")
        amount = st.number_input("₺ Tutar", min_value=0.0, step=10.0, format="%.2f", key="gider_amount")

        st.markdown("**Kategori seç:**")
        selected_label = st.radio(
            "Kategori",
            CATEGORY_LABELS,
            horizontal=True,
            label_visibility="collapsed",
            key="gider_kategori",
        )

        note = st.text_input("Not (opsiyonel)", key="gider_not")

        if st.button("✅ Kaydet", use_container_width=True, key="gider_kaydet"):
            if amount > 0:
                add_transaction(
                    "gider", amount, selected_label, note, st.session_state.current_user
                )
                st.success(f"₺{amount:,.2f} harcama ({selected_label}) kaydedildi.")
                st.session_state.entry_mode = None
                st.rerun()
            else:
                st.warning("Lütfen 0'dan büyük bir tutar girin.")

    # Son işlemler
    df = get_df()
    if not df.empty:
        st.markdown("---")
        st.markdown("#### 🕓 Son İşlemler")
        recent = df.sort_values("date", ascending=False).head(6)
        for _, row in recent.iterrows():
            renk = "#2F8C4A" if row["type"] == "gelir" else "#B5495B"
            isaret = "+" if row["type"] == "gelir" else "-"
            st.markdown(
                f"""
                <div class="soft-card">
                    <b>{row['category']}</b> — {row['user']}<br>
                    <span style="color:{renk}; font-weight:700;">{isaret}₺{row['amount']:,.2f}</span>
                    <span style="color:#9AA5B8; font-size:0.85rem;"> · {row['date'].strftime('%d %b %H:%M')}</span>
                    {f"<br><i>{row['note']}</i>" if row['note'] else ""}
                </div>
                """,
                unsafe_allow_html=True,
            )


# =========================================================
# ÖZETLER
# =========================================================
def page_ozetler():
    st.markdown("## 📊 Özetler")
    df = get_df()
    df = df[df["type"] == "gider"].copy()

    if df.empty:
        st.info("Henüz harcama verisi yok.")
        return

    df["date"] = pd.to_datetime(df["date"])

    colf1, colf2 = st.columns(2)
    with colf1:
        donem = st.selectbox("📅 Dönem", ["Aylık", "Yıllık", "Tüm Zamanlar"])
    with colf2:
        kullanici_secenekleri = ["Tüm Aile"] + USERS
        secili_kullanici = st.selectbox("👤 Kullanıcı", kullanici_secenekleri)

    now = datetime.now()
    if donem == "Aylık":
        df = df[(df["date"].dt.month == now.month) & (df["date"].dt.year == now.year)]
    elif donem == "Yıllık":
        df = df[df["date"].dt.year == now.year]

    if secili_kullanici != "Tüm Aile":
        df = df[df["user"] == secili_kullanici]

    if df.empty:
        st.info("Bu filtreye uygun harcama bulunamadı.")
        return

    st.metric("Toplam Harcama", f"₺{df['amount'].sum():,.2f}")

    chart_mode = st.radio(
        "Grafik türü", ["Bar", "Pasta"], horizontal=True, label_visibility="collapsed"
    )

    grouped = df.groupby("category", as_index=False)["amount"].sum().sort_values(
        "amount", ascending=False
    )

    pastel_palette = px.colors.qualitative.Pastel

    if chart_mode == "Bar":
        fig = px.bar(
            grouped,
            x="category",
            y="amount",
            color="category",
            color_discrete_sequence=pastel_palette,
            labels={"category": "Kategori", "amount": "Tutar (₺)"},
        )
        fig.update_layout(showlegend=False, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    else:
        fig = px.pie(
            grouped,
            names="category",
            values="amount",
            color_discrete_sequence=pastel_palette,
            hole=0.45,
        )
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)")

    st.plotly_chart(fig, use_container_width=True)


# =========================================================
# BİRİKİM
# =========================================================
def page_birikim():
    st.markdown("## 🐷 Birikim")

    toplam = total_savings()
    st.markdown(
        f"""
        <div class="kasa-total">
            <div class="label">Toplam Birikim</div>
            <div class="amount">₺{toplam:,.2f}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    df = get_df()
    df = df[(df["type"] == "gider") & (df["category"].str.contains("Birikim", na=False))].copy()

    if df.empty:
        st.info("Henüz birikim eklenmedi. Harcama girişinde 🐷 Birikim kategorisini seçerek ekleyebilirsin.")
        return

    df["date"] = pd.to_datetime(df["date"])
    df["ay"] = df["date"].dt.strftime("%B %Y")
    aylik = df.groupby("ay", as_index=False)["amount"].sum()
    aylik["_sort"] = pd.to_datetime(aylik["ay"], format="%B %Y", errors="coerce")
    aylik = aylik.sort_values("_sort", ascending=False)

    st.markdown("#### 📅 Aylık Birikim Dökümü")
    for _, row in aylik.iterrows():
        st.markdown(
            f"""
            <div class="soft-card">
                <b>{row['ay']}</b>
                <span style="float:right; font-weight:700; color:#2F5233;">₺{row['amount']:,.2f}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )


# =========================================================
# İSTEK LİSTESİ
# =========================================================
def page_istek_listesi():
    st.markdown("## 🎁 İstek Listesi")

    with st.form("istek_form", clear_on_submit=True):
        item = st.text_input("İstek")
        colA, colB = st.columns(2)
        with colA:
            kategori = st.selectbox("Kategori", CATEGORY_LABELS)
        with colB:
            tutar = st.number_input("Tahmini Tutar (₺)", min_value=0.0, step=10.0, format="%.2f")
        submitted = st.form_submit_button("➕ İsteği Ekle", use_container_width=True)
        if submitted:
            if item.strip():
                st.session_state.wishlist.append(
                    {
                        "id": str(uuid.uuid4()),
                        "user": st.session_state.current_user,
                        "item": item.strip(),
                        "category": kategori,
                        "amount": tutar,
                        "date": datetime.now(),
                        "seen": False,
                    }
                )
                st.success("İstek eklendi! 🎉")
                st.rerun()
            else:
                st.warning("Lütfen bir istek adı girin.")

    st.markdown("---")
    if not st.session_state.wishlist:
        st.info("Henüz istek eklenmedi.")
        return

    for wl in sorted(st.session_state.wishlist, key=lambda x: x["date"], reverse=True):
        st.markdown(
            f"""
            <div class="soft-card">
                <b>{wl['item']}</b> — {wl['category']}<br>
                <span style="color:#7C8AA5;">👤 {wl['user']}</span>
                <span style="float:right; font-weight:700; color:#33415C;">₺{wl['amount']:,.2f}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )


# =========================================================
# ANA AKIŞ
# =========================================================
if st.session_state.current_user is None:
    login_screen()
else:
    sidebar_nav()
    top_bar()

    if st.session_state.page == "Ana Sayfa":
        page_ana_sayfa()
    elif st.session_state.page == "Özetler":
        page_ozetler()
    elif st.session_state.page == "Birikim":
        page_birikim()
    elif st.session_state.page == "İstek Listesi":
        page_istek_listesi()
