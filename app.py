import pandas as pd
import streamlit as st
from pathlib import Path
import io
import re
import base64
from PIL import Image

BASE_DIR = Path(__file__).parent

def find_image(rel_path):
    """หาไฟล์รูป: ล้าง space, แปลง \\ เป็น /, ไม่สนตัวพิมพ์ใหญ่/เล็ก"""
    p = str(rel_path).strip().replace("\\", "/")
    full = BASE_DIR / p
    if full.exists():
        return full
    folder = full.parent
    if folder.exists():
        for f in folder.iterdir():
            if f.name.lower() == full.name.lower():
                return f
    return None

st.set_page_config(page_title="Amphidex — Thai Amphipoda Key", page_icon="🦐", layout="wide")
st.markdown("""
<style>
[class*="st-key-sp_btn_"] button,
[class*="st-key-sp_btn_"] button > div,
[class*="st-key-sp_btn_"] button [data-testid="stMarkdownContainer"],
[class*="st-key-sp_btn_"] button p {
    justify-content: flex-start !important;
    text-align: left !important;
    width: 100%;
}

/* ── Amphidex brand (ปุ่มโลโก้ซ้ายบน) ── */
[class*="st-key-brand_btn"] button {
    background: none !important; border: none !important; box-shadow: none !important;
    padding: 0 !important; justify-content: flex-start !important;
}
[class*="st-key-brand_btn"] button p {
    font-size: 2rem !important; font-weight: 800 !important;
    color: #0E7C86 !important; text-align: left !important; letter-spacing: -0.5px;
}
[class*="st-key-brand_btn"] button:hover p { color: #0A5A62 !important; }
/* ── ที่ว่างด้านบน/ล่างของ card ── */
.noimg {
    background: #EEF4F5; border-radius: 12px; height: 140px;
    display: flex; align-items: center; justify-content: center;
    flex-direction: column; color: #7A9A9E; font-size: 0.85rem; margin-bottom: 0.5rem;
}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# ตั้งค่าที่แก้เองได้ (ข้อมูลติดต่อ / ชื่อผู้พัฒนา / ขนาดโลโก้)
# ══════════════════════════════════════════════════════════════════
CONTACT_WHATSAPP_TEXT = "+66 XX XXX XXXX"   # ← ข้อความที่แสดงข้างโลโก้ WhatsApp
CONTACT_WHATSAPP_URL = ""                   # ← ลิงก์ เช่น "https://wa.me/66XXXXXXXXX" (เว้นว่าง = ไม่เป็นลิงก์)
CONTACT_PHONE_TH = "0X-XXX-XXXX"            # ← เบอร์โทรในประเทศไทย
AUTHOR_NAME = {"th": "ธชาพัฒน์", "en": "Thachaphat"}   # ← ชื่อผู้พัฒนา (แก้ตัวสะกดอังกฤษได้)
LOGO_PX = 80                                # ← ขนาดโลโก้ (px)

FLAG_TH = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 600"><rect width="900" height="600" fill="#A51931"/><rect y="100" width="900" height="400" fill="#F4F5F8"/><rect y="200" width="900" height="200" fill="#2D2A4A"/></svg>'
FLAG_UK = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 60 30"><clipPath id="s"><path d="M0,0 v30 h60 v-30 z"/></clipPath><clipPath id="t"><path d="M30,15 h30 v15 z v15 h-30 z h-30 v-15 z v-15 h30 z"/></clipPath><g clip-path="url(#s)"><path d="M0,0 v30 h60 v-30 z" fill="#012169"/><path d="M0,0 L60,30 M60,0 L0,30" stroke="#fff" stroke-width="6"/><path d="M0,0 L60,30 M60,0 L0,30" clip-path="url(#t)" stroke="#C8102E" stroke-width="4"/><path d="M30,0 v30 M0,15 h60" stroke="#fff" stroke-width="10"/><path d="M30,0 v30 M0,15 h60" stroke="#C8102E" stroke-width="6"/></g></svg>'
ICON_WA = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="#25D366" d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413Z"/></svg>'


def _svg_b64(svg):
    return base64.b64encode(svg.encode("utf-8")).decode()


# ══════════════════════════════════════════════════════════════════
# ภาษา (ค่าเริ่มต้น = ไทย) — ข้อความทั้งหมดอยู่ในตารางนี้
# ══════════════════════════════════════════════════════════════════
if "lang" not in st.session_state:
    st.session_state["lang"] = "th"

TEXT = {
    "th": {
        "no_extra_info": "ยังไม่มีข้อมูลเพิ่มเติม",
        "file_not_found": "⚠️ ไม่พบไฟล์: {path}",
        "no_image": "ยังไม่มีรูป",
        "view_details": "ดูรายละเอียด",
        "back_home": "← กลับหน้าแรก",
        "related_species": "ชนิดที่เกี่ยวข้อง",
        "same_genus_family": "สกุลหรือวงศ์เดียวกัน",
        "hero_title": "ระบุชนิดแอมฟิพอดในประเทศไทย ด้วยการไล่ key ทีละขั้น",
        "hero_caption": "เลือกลักษณะที่เห็นจากตัวอย่าง แล้วระบบจะค่อยๆ ตัดชนิดที่ไม่ตรงออก — หรือพิมพ์ชื่อที่ช่องค้นหาด้านบน",
        "cta_family": "📂 ไม่รู้ว่าเป็น Family อะไร — เริ่มจาก Key to Family",
        "cta_species": "🔬 ระบุถึงระดับชนิด — Key to Species",
        "db_stats": "ฐานข้อมูลตอนนี้: **{sp}** ชนิด · **{gn}** สกุล · **{fm}** วงศ์",
        "recently_viewed": "ที่คุณดูล่าสุด",
        "related_to_viewed": "เกี่ยวข้องกับที่คุณดู",
        "same_genus_family_viewed": "สกุลหรือวงศ์เดียวกับชนิดที่เปิดดู",
        "explore_all": "สำรวจทั้งหมด",
        "filter_family": "กรองตาม Family",
        "all_families": "ทุก Family",
        "disclaimer": "⚠️ Amphidex เป็นเครื่องมือช่วยระบุเบื้องต้น ควรตรวจสอบผลกับเอกสารต้นฉบับ (ลิงก์ Reference/PDF/Plazi ในหน้าแต่ละชนิด) ก่อนนำไปใช้ในงานวิจัย",
        "developed_by": "กำลังพัฒนาโดย{name}",
        "search_placeholder": "🔍 ค้นหาชื่อชนิด สกุล หรือ Family …",
        "search_results": "**ผลการค้นหา “{q}” — {n} รายการ**",
        "clear_search": "✕ ล้างการค้นหา",
        "no_match": "ไม่พบชื่อที่ตรงกัน ลองพิมพ์สั้นลง เช่น ชื่อสกุล หรือ Family",
        "db_remaining_sp": "ฐานข้อมูล: **{n} species** | เหลือ: **{m} species**",
        "reset": "🔄 เริ่มใหม่",
        "chosen": "**ลักษณะที่เลือกไปแล้ว:**",
        "err_no_species": "⚠️ ไม่พบ species ที่ตรงกับเงื่อนไข — กด 'เริ่มใหม่' หรือลบลักษณะที่เลือกผิดออก",
        "one_species": "✅ ระบุได้ **1 species**",
        "no_more_traits_sp": "🔍 ไม่มี trait เพิ่มเติม — พบ **{n} species**",
        "choose_group": "**เลือกกลุ่ม Segment** (เหลือ {n} species):",
        "group": "กลุ่ม:",
        "choose": "-- เลือก --",
        "char_to_check": "ลักษณะที่จะตรวจสอบ:",
        "state_found": "ลักษณะที่พบ:",
        "confirm": "✅ ยืนยันการเลือก",
        "current_results_sp": "🔍 ผลลัพธ์ปัจจุบัน: **{n} species** — กดชื่อเพื่อดูรายละเอียด",
        "family_intro": "เลือกลักษณะที่สังเกตได้เพื่อระบุ Family ก่อน แล้วค่อยไปใช้ Key to Species",
        "db_remaining_fam": "ฐานข้อมูล: **{n} families** | เหลือ: **{m} families**",
        "err_no_family": "⚠️ ไม่พบ Family — กด 'เริ่มใหม่' หรือลบลักษณะที่เลือกผิดออก",
        "one_family": "✅ ระบุได้ **1 Family: {fam}**",
        "go_species_key": "💡 กลับไปใช้ **Key to Species** เพื่อระบุชนิดต่อ",
        "others": "📋 อื่นๆ",
        "no_more_traits_fam": "🔍 ไม่มี trait เพิ่มเติม — พบ **{n} families**",
        "choose_group_fam": "**เลือกกลุ่ม Segment** (เหลือ {n} families):",
        "current_results_fam": "🔍 ผลลัพธ์ปัจจุบัน: **{n} families**",
        "know_family_hint": "💡 เมื่อทราบ Family แล้ว กลับไปใช้ **Key to Species** เพื่อระบุชนิดต่อ",
        "err_load_family": "ไม่สามารถโหลด Key to Family ได้: {e}",
        "check_file": "ตรวจสอบว่าไฟล์ keytofamily.csv อยู่ใน folder เดียวกันกับ app.py",
        "contact_us": "ติดต่อเรา",
        "phone_th": "โทรศัพท์ (ประเทศไทย)",
    },
    "en": {
        "no_extra_info": "No additional information yet",
        "file_not_found": "⚠️ File not found: {path}",
        "no_image": "No image yet",
        "view_details": "View details",
        "back_home": "← Back to home",
        "related_species": "Related species",
        "same_genus_family": "Same genus or family",
        "hero_title": "Identify Thai amphipods step by step with an interactive key",
        "hero_caption": "Pick the characters you see on your specimen and the key will narrow down the possible species — or type a name in the search box above.",
        "cta_family": "📂 Don't know the family? Start with Key to Family",
        "cta_species": "🔬 Identify to species — Key to Species",
        "db_stats": "Database now: **{sp}** species · **{gn}** genera · **{fm}** families",
        "recently_viewed": "Recently viewed",
        "related_to_viewed": "Related to what you viewed",
        "same_genus_family_viewed": "Same genus or family as the species you opened",
        "explore_all": "Explore all",
        "filter_family": "Filter by Family",
        "all_families": "All families",
        "disclaimer": "⚠️ Amphidex is a preliminary identification aid. Please verify results against the original literature (Reference/PDF/Plazi links on each species page) before using them in research.",
        "developed_by": "Under development by {name}",
        "search_placeholder": "🔍 Search species, genus or Family …",
        "search_results": "**Search results for “{q}” — {n} found**",
        "clear_search": "✕ Clear search",
        "no_match": "No matching names. Try a shorter query, e.g. a genus or Family name.",
        "db_remaining_sp": "Database: **{n} species** | Remaining: **{m} species**",
        "reset": "🔄 Start over",
        "chosen": "**Characters selected so far:**",
        "err_no_species": "⚠️ No species match these conditions — press 'Start over' or remove the wrong character.",
        "one_species": "✅ Identified: **1 species**",
        "no_more_traits_sp": "🔍 No more characters to check — **{n} species** remain",
        "choose_group": "**Choose a segment group** ({n} species remaining):",
        "group": "Group:",
        "choose": "-- Select --",
        "char_to_check": "Character to examine:",
        "state_found": "Observed state:",
        "confirm": "✅ Confirm",
        "current_results_sp": "🔍 Current results: **{n} species** — click a name for details",
        "family_intro": "Choose the characters you can observe to identify the Family first, then continue with Key to Species.",
        "db_remaining_fam": "Database: **{n} families** | Remaining: **{m} families**",
        "err_no_family": "⚠️ No Family found — press 'Start over' or remove the wrong character.",
        "one_family": "✅ Identified: **1 Family: {fam}**",
        "go_species_key": "💡 Continue with **Key to Species** to identify the species.",
        "others": "📋 Others",
        "no_more_traits_fam": "🔍 No more characters to check — **{n} families** remain",
        "choose_group_fam": "**Choose a segment group** ({n} families remaining):",
        "current_results_fam": "🔍 Current results: **{n} families**",
        "know_family_hint": "💡 Once you know the Family, continue with **Key to Species**.",
        "err_load_family": "Could not load Key to Family: {e}",
        "check_file": "Check that keytofamily.csv is in the same folder as app.py.",
        "contact_us": "Contact us",
        "phone_th": "Phone (Thailand)",
    },
}


def t(key, **kw):
    s = TEXT[st.session_state.get("lang", "th")][key]
    return s.format(**kw) if kw else s


def set_lang(code):
    st.session_state["lang"] = code


CHOOSE = t("choose")

# ── ปุ่มธงเปลี่ยนภาษา (รูปธงเป็นพื้นหลังปุ่ม) ──
_active_lang = st.session_state.get("lang", "th")
st.markdown(f"""
<style>
/* กล่องที่ใส่ธง 2 อัน: เรียงแนวนอน ชิดกัน ชิดขวาสุด */
.st-key-langbar {{
    display: flex !important; flex-direction: row !important;
    justify-content: flex-end !important; align-items: center !important;
    gap: 6px !important; width: 100% !important;
}}
.st-key-langbar > div {{ width: auto !important; flex: 0 0 auto !important; min-width: 0 !important; }}
[class*="st-key-lang_th"] button, [class*="st-key-lang_en"] button {{
    width: 38px !important; min-width: 38px !important;
    height: 26px !important; min-height: 26px !important;
    padding: 0 !important; border: 1px solid #C9D1D3 !important; border-radius: 4px !important;
    background-size: cover !important; background-position: center !important;
    background-repeat: no-repeat !important; opacity: 0.45;
}}
[class*="st-key-lang_th"] button p, [class*="st-key-lang_en"] button p {{ display: none !important; }}
[class*="st-key-lang_th"] button {{ background-image: url("data:image/svg+xml;base64,{_svg_b64(FLAG_TH)}") !important; }}
[class*="st-key-lang_en"] button {{ background-image: url("data:image/svg+xml;base64,{_svg_b64(FLAG_UK)}") !important; }}
[class*="st-key-lang_th"] button:hover, [class*="st-key-lang_en"] button:hover {{ opacity: 1; }}
[class*="st-key-lang_{_active_lang}"] button {{ opacity: 1 !important; border: 2px solid #0E7C86 !important; }}
</style>
""", unsafe_allow_html=True)


# ── โลโก้ซ้ายบน (ย่อรูปก่อนฝัง กันเว็บหนัก) ──
def find_logo():
    folder = BASE_DIR / "assets"
    if folder.exists():
        for f in sorted(folder.iterdir()):
            if f.stem.lower() == "logo" and f.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff"):
                return f
    return None


@st.cache_data
def logo_b64(px):
    p = find_logo()
    if not p:
        return None
    im = Image.open(p).convert("RGBA")
    im.thumbnail((px * 2, px * 2))
    buf = io.BytesIO()
    im.save(buf, format="PNG", optimize=True)
    return base64.b64encode(buf.getvalue()).decode()


_lb = logo_b64(LOGO_PX)
if _lb:
    st.markdown(f"""
<style>
[class*="st-key-brand_btn"] button {{
    background-image: url("data:image/png;base64,{_lb}") !important;
    background-repeat: no-repeat !important;
    background-position: left center !important;
    background-size: {LOGO_PX}px auto !important;
    padding-left: {LOGO_PX + 12}px !important;
    min-height: {LOGO_PX}px !important;
    white-space: nowrap !important;
}}
</style>
""", unsafe_allow_html=True)

# ── โหลดข้อมูล ─────────────────────────────────────────────────────
@st.cache_data
def load_species_data():
    species = pd.read_csv("species.csv")
    traits = pd.read_csv("trait_id.csv")
    species_traits = pd.read_csv("species_traits.csv")
    # ทำชื่อคอลัมน์ให้เป็นรูปเดียวกัน (ตัวเล็ก ไม่มีช่องว่าง) กัน error จากการสะกด/เว้นวรรค
    def _norm(df):
        df.columns = (df.columns.astype(str).str.strip().str.lower()
                      .str.replace(r"\s+", "_", regex=True))
        return df.loc[:, ~df.columns.str.startswith("unnamed")]
    traits = _norm(traits)
    species_traits = _norm(species_traits)
    species = species.rename(columns={"species id": "species_id", "Species": "scientific_name"})

    # คอลัมน์ที่ขาดได้ (ไม่จำเป็นต่อการกรอง) → เติมว่างให้ ไม่ให้แอปล้ม
    for c in ["state_options", "description"]:
        if c not in traits.columns:
            traits[c] = None
    for c in ["trait_id", "segment", "character"]:
        if c not in traits.columns:
            raise ValueError(f"trait_id.csv ไม่มีคอลัมน์ '{c}' — คอลัมน์ที่มีอยู่: {list(traits.columns)}")
    if "observation_note" not in species_traits.columns:
        species_traits["observation_note"] = None
    traits = traits.dropna(subset=["trait_id"])
    species_traits = species_traits.dropna(subset=["trait_id"])
    merged = species_traits.merge(traits, on="trait_id").merge(species, on="species_id")
    return merged

@st.cache_data
def load_family_data():
    df = pd.read_csv("keytofamily.csv", header=None)
    header_mask = df[0] == "suborder numbers"
    header_idx = df[header_mask].index.tolist()
    if header_idx:
        df.columns = df.iloc[header_idx[0]].tolist()
        df = df.drop(header_idx)
    df.columns = ["step", "result", "superfamily", "family", "trait_id", "trait_value", "observation_note"]
    df = df.dropna(subset=["trait_id", "trait_value"])
    family_rows = df[df["family"].notna() & ~df["family"].str.match(r"^\d+$", na=False)].copy()
    family_rows = family_rows[~family_rows["family"].str.contains("Section|return", na=False)]
    seg_order_fam = [
        "antenna 1", "accessory flagellum", "antenna 2", "antennae",
        "eyes", "rostrum", "head", "mouthpart", "lower lip", "labium",
        "mandible", "maxilla 1", "maxilla 2", "maxilliped",
        "gnathopod 1", "gnathopod 1 carpus", "gnathopod 1 propodus",
        "gnathopod 2", "gnathopod 2 carpus", "gnathopod 2 propodus",
        "pereopod 3", "pereopod 3 merus", "pereopod 4", "pereopod 4 merus",
        "pereopod 5", "pereopod 5 basis", "pereopod 5 merus",
        "pereopod 6", "pereopod 6 merus",
        "pereopod 7", "pereopod 7 basis", "pereopod 7 dactyl",
        "coxa 1", "coxa 2", "coxa 3", "coxa 4", "coxa 5", "coxa 6", "coxae",
        "body", "pereonite", "pleonite", "pleon 3",
        "urosome", "urosome 1", "urosome 2", "urosome 3",
        "uropod 1", "uropod 2", "uropod 3", "telson"
    ]
    family_rows["_ord"] = family_rows["observation_note"].apply(
        lambda x: seg_order_fam.index(x) if x in seg_order_fam else 999
    )
    family_rows = family_rows.sort_values("_ord").drop(columns=["_ord"])
    return family_rows

@st.cache_data
def load_species_info():
    df = pd.read_csv("species_info_expander.csv")
    df = df.rename(columns={"species id": "species_id"})
    return df

# ── helper functions ────────────────────────────────────────────────
def filter_species(merged, selected_traits):
    candidates = set(merged["species_id"].unique())
    for trait_id, trait_value in selected_traits.items():
        match = merged[
            (merged["trait_id"] == trait_id) &
            (merged["trait_value"] == trait_value)
        ]["species_id"]
        candidates &= set(match)
        if not candidates:
            break
    return candidates

def get_result_df(merged, candidates):
    return merged[merged["species_id"].isin(candidates)][
        ["species_id", "Genus", "scientific_name", "Author", "Family", "Order"]
    ].drop_duplicates().reset_index(drop=True)

def filter_family(family_data, selected_traits):
    candidates = set(family_data["family"].unique())
    for trait_id, trait_value in selected_traits.items():
        match = family_data[
            (family_data["trait_id"] == trait_id) &
            (family_data["trait_value"] == trait_value)
        ]["family"]
        candidates &= set(match)
        if not candidates:
            break
    return sorted(candidates)

HOME = "🏠 Home"
SPECIES = "🔬 Key to Species"
FAMILY = "📂 Key to Family"


def add_viewed(species_id, limit=12):
    """จำชนิดที่เปิดดู (ล่าสุดอยู่หน้าสุด) — เก็บใน session ของผู้ใช้คนนั้นเท่านั้น"""
    v = [x for x in st.session_state.get("viewed", []) if x != species_id]
    st.session_state["viewed"] = [species_id] + v[:limit - 1]


def render_species_body(species_id, genus, sci_name, author, family, order,
                        merged, info_df):
    with st.container(border=True):
        st.markdown(f"**Order:** {order} | **Family:** {family} | **Genus:** *{genus}*")
        st.divider()

        row = info_df[info_df["species_id"] == species_id]
        if row.empty:
            st.caption(t("no_extra_info"))
            return
        r = row.iloc[0]

        def has(col):
            return col in r.index and pd.notna(r[col]) and str(r[col]).strip() not in ("", "nan")

        # รูปภาพ
        if has("image_main"):
            found = find_image(r["image_main"])
            if found:
                st.image(str(found), use_container_width=True)
            else:
                st.caption(t("file_not_found", path=r['image_main']))

        for col in ["Diagnosis", "Description", "Remarks"]:
            if has(col):
                st.markdown(f"**{col}**")
                st.markdown(r[col])

        st.divider()

        # Key characters ดึงจาก species_traits อัตโนมัติ
        sp_traits = merged[merged["species_id"] == species_id][
            ["segment", "character", "trait_value"]
        ].drop_duplicates().sort_values("segment")
        if not sp_traits.empty:
            st.markdown("**Key Characters**")
            for _, t in sp_traits.iterrows():
                st.markdown(f"- **{t['segment']}** — {t['character']}: `{t['trait_value']}`")
            st.divider()

        if has("Reference"):
            st.markdown("**Reference**")
            st.markdown(r["Reference"])

        links = []
        if has("PDF"):
            links.append(f"[📄 PDF]({r['PDF']})")
        if has("Plazi"):
            links.append(f"[🔬 Plazi]({r['Plazi']})")
        if has("WoRMs"):
            links.append(f"[🌊 WoRMS]({r['WoRMs']})")
        if links:
            st.markdown("  |  ".join(links))
        else:
            st.caption(t("no_extra_info"))



def show_species_expander(species_id, genus, sci_name, author, family, order,
                          merged, info_df, default_open=False):
    """กดชื่อ → เปิดรายละเอียดใต้ชื่อ | กดชื่ออื่น → อันเก่าหุบ | กดซ้ำ → หุบ"""
    is_open = default_open or (st.session_state.get("open_sp") == species_id)
    arrow = "▼" if is_open else "▶"

    if st.button(f"{arrow}  *{genus} {sci_name}* {author}",
                 key=f"sp_btn_{species_id}", use_container_width=True):
        st.session_state["open_sp"] = None if is_open else species_id
        st.rerun()

    if not is_open:
        return

    add_viewed(species_id)
    render_species_body(species_id, genus, sci_name, author, family, order,
                        merged, info_df)


# ══════════════════════════════════════════════════════════════════
# HOME / SEARCH helpers
# ══════════════════════════════════════════════════════════════════
@st.cache_data
def load_species_list():
    sp = pd.read_csv("species.csv")
    sp = sp.rename(columns={"species id": "species_id", "Species": "scientific_name"})
    for c in ["Genus", "scientific_name", "Author", "Family", "Order"]:
        if c not in sp.columns:
            sp[c] = ""
        sp[c] = sp[c].fillna("").astype(str)
    return sp[["species_id", "Genus", "scientific_name", "Author", "Family", "Order"]]


def get_image_path(species_id, info_df):
    row = info_df[info_df["species_id"] == species_id]
    if row.empty or "image_main" not in row.columns:
        return None
    v = row.iloc[0]["image_main"]
    if pd.isna(v) or str(v).strip() in ("", "nan"):
        return None
    return find_image(v)


def go_to(m):
    st.session_state["mode"] = m


def open_species(sid):
    """callback ของปุ่มบน card: เปิดหน้ารายละเอียดใน Home + บันทึกประวัติ"""
    st.session_state["detail_sp"] = sid
    st.session_state["q"] = ""
    st.session_state["mode"] = HOME
    add_viewed(sid)


def close_detail():
    st.session_state["detail_sp"] = None


def clear_search():
    st.session_state["q"] = ""


def search_species(sp_df, q):
    q = q.strip().lower()
    hay = (sp_df["Genus"] + " " + sp_df["scientific_name"] + " "
           + sp_df["Family"] + " " + sp_df["Author"]).str.lower()
    return sp_df[hay.str.contains(q, regex=False)]


def related_species(sp_df, base_ids, exclude_ids, n=8):
    base = sp_df[sp_df["species_id"].isin(base_ids)]
    genera, fams = set(base["Genus"]), set(base["Family"])
    cand = sp_df[~sp_df["species_id"].isin(exclude_ids)
                 & (sp_df["Genus"].isin(genera) | sp_df["Family"].isin(fams))].copy()
    cand["_s"] = cand["Genus"].isin(genera).astype(int)
    return cand.sort_values("_s", ascending=False).head(n).drop(columns="_s")


def species_card(r, info_df, prefix):
    with st.container(border=True):
        img = get_image_path(r.species_id, info_df)
        if img:
            st.image(str(img), use_container_width=True)
        else:
            st.markdown(f'<div class="noimg">🦐<br>{t("no_image")}</div>', unsafe_allow_html=True)
        st.markdown(f"**_{r.Genus} {r.scientific_name}_**")
        st.caption(f"{r.Author} · {r.Family}")
        st.button(t("view_details"), key=f"{prefix}_{r.species_id}",
                  on_click=open_species, args=(r.species_id,), use_container_width=True)


def render_grid(df, info_df, prefix, ncols=4):
    rows = list(df.itertuples(index=False))
    for i in range(0, len(rows), ncols):
        cols = st.columns(ncols)
        for col, r in zip(cols, rows[i:i + ncols]):
            with col:
                species_card(r, info_df, prefix)


def render_footer():
    """ท้ายเว็บ (ทุกหน้า): Contact us / WhatsApp / เบอร์โทรในไทย / ผู้พัฒนา — กึ่งกลาง"""
    st.divider()
    wa_icon = (f'<img src="data:image/svg+xml;base64,{_svg_b64(ICON_WA)}" alt="WhatsApp" '
               f'style="height:22px;vertical-align:middle;margin-right:8px;">')
    wa_html = f'{wa_icon}<span style="vertical-align:middle;">{CONTACT_WHATSAPP_TEXT}</span>'
    if CONTACT_WHATSAPP_URL:
        wa_html = (f'<a href="{CONTACT_WHATSAPP_URL}" target="_blank" '
                   f'style="text-decoration:none;color:inherit;">{wa_html}</a>')
    digits = re.sub(r"\D", "", CONTACT_PHONE_TH)
    phone_html = f"📞 {CONTACT_PHONE_TH}"
    if len(digits) >= 8:
        phone_html = f'<a href="tel:{digits}" style="text-decoration:none;color:inherit;">{phone_html}</a>'
    lang = st.session_state.get("lang", "th")
    st.markdown(f"""
<div style="text-align:center;margin:0.5rem 0 1.5rem 0;line-height:2;">
<div style="font-weight:700;font-size:1.15rem;">{t("contact_us")}</div>
<div>{wa_html}</div>
<div>{t("phone_th")}: {phone_html}</div>
<div style="font-size:0.8rem;opacity:0.65;">{t("developed_by", name=AUTHOR_NAME[lang])}</div>
</div>
""", unsafe_allow_html=True)


def render_home(sp_df, info_df):
    viewed = [v for v in st.session_state.get("viewed", []) if v in set(sp_df["species_id"])]
    detail = st.session_state.get("detail_sp")

    # ── หน้ารายละเอียดของชนิดที่กด ──
    if detail and detail in set(sp_df["species_id"]):
        r = sp_df[sp_df["species_id"] == detail].iloc[0]
        st.button(t("back_home"), on_click=close_detail, key="back_btn")
        st.markdown(f"## *{r.Genus} {r.scientific_name}*")
        st.caption(r.Author)
        merged = load_species_data()   # โหลดเฉพาะตอนเปิดหน้ารายละเอียด
        render_species_body(detail, r.Genus, r.scientific_name, r.Author,
                            r.Family, r.Order, merged, info_df)
        rel = related_species(sp_df, [detail], [detail])
        if not rel.empty:
            st.markdown("### " + t("related_species"))
            st.caption(t("same_genus_family"))
            render_grid(rel, info_df, "reldetail")
        return

    # ── Hero ──
    hc1, hc2 = st.columns([9, 2], vertical_alignment="center")
    with hc1:
        st.markdown("### " + t("hero_title"))
    with hc2:
        with st.container(key="langbar"):
            st.button("TH", key="lang_th", help="ภาษาไทย", on_click=set_lang, args=("th",))
            st.button("EN", key="lang_en", help="English", on_click=set_lang, args=("en",))
    st.caption(t("hero_caption"))
    c1, c2 = st.columns(2)
    with c1:
        st.button(t("cta_family"),
                  on_click=go_to, args=(FAMILY,), use_container_width=True, type="primary")
    with c2:
        st.button(t("cta_species"),
                  on_click=go_to, args=(SPECIES,), use_container_width=True)
    st.caption(t("db_stats", sp=len(sp_df), gn=sp_df['Genus'].nunique(), fm=sp_df['Family'].nunique()))

    # ── ที่ผู้ใช้เคยกดดู ──
    if viewed:
        st.markdown("### " + t("recently_viewed"))
        recent = sp_df.set_index("species_id").loc[viewed[:8]].reset_index()
        render_grid(recent, info_df, "recent")

        rel = related_species(sp_df, viewed[:3], viewed)
        if not rel.empty:
            st.markdown("### " + t("related_to_viewed"))
            st.caption(t("same_genus_family_viewed"))
            render_grid(rel, info_df, "related")

    # ── สำรวจทั้งหมด ──
    st.markdown("### " + t("explore_all"))
    fams = sorted(f for f in sp_df["Family"].unique() if f)
    sel = st.multiselect(t("filter_family"), fams, placeholder=t("all_families"), key="home_fam")
    explore = sp_df[sp_df["Family"].isin(sel)] if sel else sp_df
    explore = explore.assign(_img=[get_image_path(s, info_df) is not None
                                   for s in explore["species_id"]])
    explore = explore.sort_values(["_img", "Family", "Genus", "scientific_name"],
                                  ascending=[False, True, True, True]).drop(columns="_img")
    render_grid(explore, info_df, "explore")

    st.caption(t("disclaimer"))


# ══════════════════════════════════════════════════════════════════
# TOP BAR: โลโก้ (ซ้าย) | ค้นหา (กลาง) | เมนู (ขวา)
# ══════════════════════════════════════════════════════════════════
if "mode" not in st.session_state:
    st.session_state["mode"] = HOME

top1, top2, top3 = st.columns([2, 3, 3.2], vertical_alignment="center")
with top1:
    st.button("Amphidex" if _lb else "🦐 Amphidex", key="brand_btn", on_click=go_to, args=(HOME,))
with top2:
    query = st.text_input("Search", key="q", label_visibility="collapsed",
                          placeholder=t("search_placeholder"))
with top3:
    mode = st.radio("Menu", [HOME, SPECIES, FAMILY], key="mode",
                    horizontal=True, label_visibility="collapsed")
st.divider()

_sp_df = load_species_list()
_info_df = load_species_info()

# ── ถ้ามีคำค้น → แสดงผลค้นหาแทนหน้าปัจจุบัน ──
if query.strip():
    results = search_species(_sp_df, query)
    h1, h2 = st.columns([4, 1], vertical_alignment="center")
    with h1:
        st.markdown(t("search_results", q=query.strip(), n=len(results)))
    with h2:
        st.button(t("clear_search"), on_click=clear_search, use_container_width=True)
    if results.empty:
        st.info(t("no_match"))
    else:
        render_grid(results.sort_values(["Family", "Genus", "scientific_name"]),
                    _info_df, "search")
    render_footer()
    st.stop()

if mode == HOME:
    render_home(_sp_df, _info_df)

# ══════════════════════════════════════════════════════════════════
# KEY TO SPECIES
# ══════════════════════════════════════════════════════════════════
elif mode == SPECIES:
    merged = load_species_data()
    info_df = load_species_info()

    if "selected_traits" not in st.session_state:
        st.session_state.selected_traits = {}
    if "step_history" not in st.session_state:
        st.session_state.step_history = []
    if "open_sp" not in st.session_state:
        st.session_state.open_sp = None

    selected_traits = st.session_state.selected_traits
    candidates = filter_species(merged, selected_traits)

    st.subheader("Key to Species")
    col1, col2 = st.columns([3, 1])
    with col1:
        st.write(t("db_remaining_sp", n=merged['species_id'].nunique(), m=len(candidates)))
    with col2:
        if st.button(t("reset"), use_container_width=True):
            st.session_state.selected_traits = {}
            st.session_state.step_history = []
            st.session_state.open_sp = None
            st.rerun()

    if st.session_state.step_history:
        st.markdown(t("chosen"))
        for i, (tid, val, seg, desc) in enumerate(st.session_state.step_history):
            col_h, col_del = st.columns([5, 1])
            with col_h:
                st.markdown(f"&nbsp;&nbsp;{i+1}. **{seg}** — {desc}: `{val}`")
            with col_del:
                if st.button("✕", key=f"del_{i}"):
                    st.session_state.step_history = st.session_state.step_history[:i]
                    st.session_state.selected_traits = {
                        t: v for t, v, _, _ in st.session_state.step_history[:i]
                    }
                    st.session_state.open_sp = None
                    st.rerun()
        st.divider()

    if len(candidates) == 0:
        st.error(t("err_no_species"))

    elif len(candidates) == 1:
        st.success(t("one_species"))
        result_df = get_result_df(merged, candidates)
        r = result_df.iloc[0]
        show_species_expander(
            r["species_id"], r["Genus"], r["scientific_name"],
            r["Author"], r["Family"], r["Order"], merged, info_df
        )

    else:
        avail = merged[merged["species_id"].isin(candidates)]
        used_traits = set(selected_traits.keys())
        avail_traits = avail[~avail["trait_id"].isin(used_traits)]

        seg_groups = {
            "🦐 Head & Antennae": [
                "antenna 1", "accessory flagellum", "antenna 2",
                "peduncle", "peduncle vs antenna1", "antennae",
                "compound eye", "rostrum", "antennal sinus notch", "head"
            ],
            "👄 Mouthparts": [
                "mouthpart", "upper lip", "lower lip", "labium",
                "mandible", "mandibular", "maxilla 1", "maxilla 2", "maxiliped"
            ],
            "🦾 Gnathopods": ["gnathopod 1", "gnathopod 2"],
            "🦵 Pereopods": [
                "pereopod 1", "pereopod 2", "pereopod 3",
                "pereopod 4", "pereopod 5", "pereopod 6", "pereopod 7", "pereopods"
            ],
            "🔩 Limb segments": [
                "basis", "ischium", "carpus", "merus", "propodus", "dactyl", "proximal"
            ],
            "📦 Coxae": [
                "coxa 1", "coxa 2", "coxa 3", "coxa 4",
                "coxa 5", "coxa 6", "coxa 7", "coxae"
            ],
            "🫁 Body & Gills": ["body", "pereonites", "gills", "oostegites"],
            "🔵 Epimera & Pleon": [
                "epimera 1", "epimera 2", "epimera 3",
                "pleon 1", "pleon 2", "pleon 3", "pleonites",
                "pleopod 1", "pleopod 2", "pleopod 3", "pleopods"
            ],
            "🔚 Urosome & Uropods": [
                "urosome 1", "urosome 2", "urosome 3", "urosomites",
                "uropod 1", "uropod 2", "uropod 3", "telson"
            ]
        }

        avail_segs = set(avail_traits["segment"].dropna().unique())
        active_groups = {
            grp: [s for s in segs if s in avail_segs]
            for grp, segs in seg_groups.items()
        }
        active_groups = {g: s for g, s in active_groups.items() if s}

        if not active_groups:
            st.info(t("no_more_traits_sp", n=len(candidates)))
        else:
            st.markdown(t("choose_group", n=len(candidates)))
            sel_group = st.selectbox(t("group"), [CHOOSE] + list(active_groups.keys()),
                                     key=f"grp_{len(selected_traits)}")

            if sel_group != CHOOSE:
                sel_seg = st.selectbox("Segment:", [CHOOSE] + active_groups[sel_group],
                                       key=f"seg_{len(selected_traits)}")

                if sel_seg != CHOOSE:
                    seg_traits = avail_traits[avail_traits["segment"] == sel_seg][
                        ["trait_id", "character", "description", "state_options"]
                    ].drop_duplicates("trait_id")

                    trait_labels, trait_map = [], {}
                    for _, row in seg_traits.iterrows():
                        char = str(row["character"]) if pd.notna(row["character"]) else ""
                        states = str(row["state_options"]) if pd.notna(row["state_options"]) else ""
                        label = f"{char}: {states}" if states else char
                        base = label
                        while label in trait_map:
                            label = f"{base} [{row['trait_id']}]"
                        trait_labels.append(label)
                        trait_map[label] = row["trait_id"]

                    sel_trait_label = st.selectbox(t("char_to_check"),
                                                   [CHOOSE] + trait_labels,
                                                   key=f"trait_{len(selected_traits)}")

                    if sel_trait_label != CHOOSE:
                        sel_trait_id = trait_map[sel_trait_label]
                        values = sorted(avail[avail["trait_id"] == sel_trait_id]["trait_value"].dropna().unique())
                        value_labels = []
                        for v in values:
                            n = len(avail[
                                (avail["trait_id"] == sel_trait_id) &
                                (avail["trait_value"] == v)
                            ]["species_id"].unique())
                            value_labels.append(f"{v}  ({n} species)")

                        sel_val_label = st.selectbox(t("state_found"),
                                                     [CHOOSE] + value_labels,
                                                     key=f"val_{len(selected_traits)}")

                        if sel_val_label != CHOOSE:
                            sel_val = values[value_labels.index(sel_val_label)]
                            if st.button(t("confirm"), use_container_width=True):
                                st.session_state.selected_traits[sel_trait_id] = sel_val
                                st.session_state.step_history.append(
                                    (sel_trait_id, sel_val, sel_seg, sel_trait_label)
                                )
                                st.session_state.open_sp = None
                                st.rerun()

        # ── ผลลัพธ์ปัจจุบัน — แสดง expander แต่ละ species ──
        if selected_traits and len(candidates) > 1:
            st.divider()
            st.info(t("current_results_sp", n=len(candidates)))
            result_df = get_result_df(merged, candidates)
            for _, r in result_df.iterrows():
                show_species_expander(
                    r["species_id"], r["Genus"], r["scientific_name"],
                    r["Author"], r["Family"], r["Order"], merged, info_df
                )


# ══════════════════════════════════════════════════════════════════
# KEY TO FAMILY
# ══════════════════════════════════════════════════════════════════
elif mode == FAMILY:
    st.subheader("Key to Family")
    st.write(t("family_intro"))

    try:
        family_data = load_family_data()

        if "fam_selected_traits" not in st.session_state:
            st.session_state.fam_selected_traits = {}
        if "fam_step_history" not in st.session_state:
            st.session_state.fam_step_history = []

        fam_selected = st.session_state.fam_selected_traits
        fam_candidates = filter_family(family_data, fam_selected)

        col1, col2 = st.columns([3, 1])
        with col1:
            st.write(t("db_remaining_fam", n=family_data['family'].nunique(), m=len(fam_candidates)))
        with col2:
            if st.button(t("reset"), key="fam_reset", use_container_width=True):
                st.session_state.fam_selected_traits = {}
                st.session_state.fam_step_history = []
                st.rerun()

        if st.session_state.fam_step_history:
            st.markdown(t("chosen"))
            for i, (tid, val, seg, desc) in enumerate(st.session_state.fam_step_history):
                col_h, col_del = st.columns([5, 1])
                with col_h:
                    st.markdown(f"&nbsp;&nbsp;{i+1}. **{seg}** — {desc}: `{val}`")
                with col_del:
                    if st.button("✕", key=f"fam_del_{i}"):
                        st.session_state.fam_step_history = st.session_state.fam_step_history[:i]
                        st.session_state.fam_selected_traits = {
                            t: v for t, v, _, _ in st.session_state.fam_step_history[:i]
                        }
                        st.rerun()
            st.divider()

        if len(fam_candidates) == 0:
            st.error(t("err_no_family"))

        elif len(fam_candidates) == 1:
            st.success(t("one_family", fam=list(fam_candidates)[0]))
            st.info(t("go_species_key"))

        else:
            avail_fam = family_data[family_data["family"].isin(fam_candidates)]
            used_fam_traits = set(fam_selected.keys())
            avail_fam_traits = avail_fam[~avail_fam["trait_id"].isin(used_fam_traits)]

            seg_groups_fam = {
                "🦐 Head & Antennae": [
                    "antenna 1", "accessory flagellum", "antenna 2", "antennae",
                    "eyes", "rostrum", "head"
                ],
                "👄 Mouthparts": [
                    "mouthpart", "lower lip", "labium",
                    "mandible", "maxilla 1", "maxilla 2", "maxilliped"
                ],
                "🦾 Gnathopods": [
                    "gnathopod 1", "gnathopod 1 carpus", "gnathopod 1 propodus",
                    "gnathopod 2", "gnathopod 2 carpus", "gnathopod 2 propodus"
                ],
                "🦵 Pereopods": [
                    "pereopod 3", "pereopod 3 merus", "pereopod 4", "pereopod 4 merus",
                    "pereopod 5", "pereopod 5 basis", "pereopod 5 merus",
                    "pereopod 6", "pereopod 6 merus",
                    "pereopod 7", "pereopod 7 basis", "pereopod 7 dactyl"
                ],
                "📦 Coxae": ["coxa 1", "coxa 2", "coxa 3", "coxa 4", "coxa 5", "coxa 6", "coxae"],
                "🫁 Body": ["body", "pereonite", "pleonite", "pleon 3"],
                "🔚 Urosome & Uropods": [
                    "urosome", "urosome 1", "urosome 2", "urosome 3",
                    "uropod 1", "uropod 2", "uropod 3", "telson"
                ]
            }

            avail_fam_segs = set(avail_fam_traits["observation_note"].dropna().unique())
            active_fam_groups = {
                grp: [s for s in segs if s in avail_fam_segs]
                for grp, segs in seg_groups_fam.items()
            }
            active_fam_groups = {g: s for g, s in active_fam_groups.items() if s}
            all_grouped = {s for segs in seg_groups_fam.values() for s in segs}
            ungrouped = sorted(avail_fam_segs - all_grouped)
            if ungrouped:
                active_fam_groups[t("others")] = ungrouped

            if not active_fam_groups:
                st.info(t("no_more_traits_fam", n=len(fam_candidates)))
            else:
                st.markdown(t("choose_group_fam", n=len(fam_candidates)))
                sel_fam_group = st.selectbox(t("group"), [CHOOSE] + list(active_fam_groups.keys()),
                                             key=f"fam_grp_{len(fam_selected)}")

                if sel_fam_group != CHOOSE:
                    sel_fam_seg = st.selectbox("Segment:",
                                               [CHOOSE] + active_fam_groups[sel_fam_group],
                                               key=f"fam_seg_{len(fam_selected)}")

                    if sel_fam_seg != CHOOSE:
                        fam_seg_traits = avail_fam_traits[
                            avail_fam_traits["observation_note"] == sel_fam_seg
                        ][["trait_id", "trait_value"]].drop_duplicates("trait_id")

                        fam_trait_labels, fam_trait_map = [], {}
                        for _, row in fam_seg_traits.iterrows():
                            vals = family_data[
                                family_data["trait_id"] == row["trait_id"]
                            ]["trait_value"].dropna().unique()
                            state_preview = ", ".join(sorted(vals)[:3])
                            label = f"{state_preview}..." if len(vals) > 3 else state_preview
                            base = label
                            while label in fam_trait_map:
                                label = f"{base} [{row['trait_id']}]"
                            fam_trait_labels.append(label)
                            fam_trait_map[label] = row["trait_id"]

                        sel_fam_trait_label = st.selectbox(t("char_to_check"),
                                                           [CHOOSE] + fam_trait_labels,
                                                           key=f"fam_trait_{len(fam_selected)}")

                        if sel_fam_trait_label != CHOOSE:
                            sel_fam_trait_id = fam_trait_map[sel_fam_trait_label]
                            fam_values = sorted(
                                avail_fam[avail_fam["trait_id"] == sel_fam_trait_id]["trait_value"].dropna().unique()
                            )
                            fam_value_labels = []
                            for v in fam_values:
                                n = len(avail_fam[
                                    (avail_fam["trait_id"] == sel_fam_trait_id) &
                                    (avail_fam["trait_value"] == v)
                                ]["family"].unique())
                                fam_value_labels.append(f"{v}  ({n} families)")

                            sel_fam_val_label = st.selectbox(t("state_found"),
                                                             [CHOOSE] + fam_value_labels,
                                                             key=f"fam_val_{len(fam_selected)}")

                            if sel_fam_val_label != CHOOSE:
                                sel_fam_val = fam_values[fam_value_labels.index(sel_fam_val_label)]
                                if st.button(t("confirm"), key="fam_confirm", use_container_width=True):
                                    st.session_state.fam_selected_traits[sel_fam_trait_id] = sel_fam_val
                                    st.session_state.fam_step_history.append(
                                        (sel_fam_trait_id, sel_fam_val, sel_fam_seg, sel_fam_trait_label)
                                    )
                                    st.rerun()

            if fam_selected and len(fam_candidates) > 1:
                st.divider()
                st.info(t("current_results_fam", n=len(fam_candidates)))
                for fam in sorted(fam_candidates):
                    st.write(f"• {fam}")
                st.info(t("know_family_hint"))

    except Exception as e:
        st.error(t("err_load_family", e=e))
        st.caption(t("check_file"))


render_footer()
