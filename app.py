import pandas as pd
import streamlit as st

st.set_page_config(page_title="Amphipoda Taxonomic Key", layout="wide")

# ── โหลดข้อมูล Key to Species ─────────────────────────────────────
@st.cache_data
def load_species_data():
    species = pd.read_csv("species.csv")
    traits = pd.read_csv("trait_id.csv")
    species_traits = pd.read_csv("species_traits.csv")

    traits = traits.rename(columns={"trait id": "trait_id", "state options": "state_options"})
    species_traits = species_traits.rename(columns={
        "species id": "species_id",
        "trait id": "trait_id",
        "trait value": "trait_value",
        "observation note": "observation_note"
    })
    species = species.rename(columns={
        "species id": "species_id",
        "Species": "scientific_name"
    })
    species_traits = species_traits.loc[:, ~species_traits.columns.str.startswith("Unnamed")]
    traits = traits.dropna(subset=["trait_id"])
    species_traits = species_traits.dropna(subset=["trait_id"])
    merged = species_traits.merge(traits, on="trait_id").merge(species, on="species_id")
    return merged

# ── โหลดข้อมูล Key to Family ──────────────────────────────────────
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
    return family_rows


def filter_species(merged, selected_traits):
    """กรอง species ตาม traits ที่เลือกสะสม"""
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
        ["Genus", "scientific_name", "Author", "Family", "Order"]
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


# ── UI หลัก ───────────────────────────────────────────────────────
st.title("🦐 Amphipoda Taxonomic Key")
st.caption("Thai Coastal & Estuarine Amphipoda — Interactive Identification Tool")

mode = st.radio(
    "**เลือกจุดเริ่มต้น:**",
    [
        "🔬 Key to Species — ระบุถึงระดับชนิด",
        "📂 Key to Family — ยังไม่ทราบ Family เริ่มจากตรงนี้"
    ],
    horizontal=True
)

st.divider()

# ══════════════════════════════════════════════════════════════════
# KEY TO SPECIES — multi-step filter ด้วย session state
# ══════════════════════════════════════════════════════════════════
if mode == "🔬 Key to Species — ระบุถึงระดับชนิด":
    merged = load_species_data()

    # ── init session state ──
    if "selected_traits" not in st.session_state:
        st.session_state.selected_traits = {}   # {trait_id: trait_value}
    if "step_history" not in st.session_state:
        st.session_state.step_history = []      # [(trait_id, trait_value, segment, description)]

    selected_traits = st.session_state.selected_traits

    # ── คำนวณ candidates จาก traits ที่เลือกไปแล้ว ──
    candidates = filter_species(merged, selected_traits)

    # ── Header ──
    st.subheader("Key to Species")
    col1, col2 = st.columns([3, 1])
    with col1:
        st.write(f"ฐานข้อมูล: **{merged['species_id'].nunique()} species** | เหลือ: **{len(candidates)} species**")
    with col2:
        if st.button("🔄 เริ่มใหม่", use_container_width=True):
            st.session_state.selected_traits = {}
            st.session_state.step_history = []
            st.rerun()

    # ── แสดง traits ที่เลือกไปแล้ว ──
    if st.session_state.step_history:
        st.markdown("**ลักษณะที่เลือกไปแล้ว:**")
        for i, (tid, val, seg, desc) in enumerate(st.session_state.step_history):
            col_h, col_del = st.columns([5, 1])
            with col_h:
                st.markdown(f"&nbsp;&nbsp;{i+1}. **{seg}** — {desc}: `{val}`")
            with col_del:
                if st.button("✕", key=f"del_{i}"):
                    # ลบ trait นี้และทุก trait ที่เลือกหลังจากนี้ออก
                    st.session_state.step_history = st.session_state.step_history[:i]
                    st.session_state.selected_traits = {
                        t: v for t, v, _, _ in st.session_state.step_history[:i]
                    }
                    st.rerun()
        st.divider()

    # ── ถ้า candidates เหลือ 0 ──
    if len(candidates) == 0:
        st.error("⚠️ ไม่พบ species ที่ตรงกับเงื่อนไขทั้งหมด — กด 'เริ่มใหม่' หรือลบลักษณะที่เลือกผิดออก")

    # ── ถ้า candidates เหลือ 1 ── แสดงผลลัพธ์ทันที
    elif len(candidates) == 1:
        st.success("✅ ระบุได้ **1 species**")
        result_df = get_result_df(merged, candidates)
        st.dataframe(result_df, use_container_width=True)

    # ── ยังมีหลาย candidates — ให้เลือก trait ต่อ ──
    else:
        # กรอง merged เฉพาะ candidates ที่เหลือ
        avail = merged[merged["species_id"].isin(candidates)]

        # กรอง trait ที่ยังไม่ได้เลือก
        used_traits = set(selected_traits.keys())
        avail_traits = avail[~avail["trait_id"].isin(used_traits)]

        # ── เลือก segment ──
        seg_order = [
            "antenna 1", "accessory flagellum", "antenna 2", "peduncle",
            "compound eye", "rostrum", "antennal sinus notch",
            "mandible", "maxilla 1", "maxilla 2", "maxilliped",
            "gnathopod 1", "gnathopod 2",
            "pereopod 1", "pereopod 2", "pereopod 7",
            "basis", "carpus", "merus", "propodus", "dactyl",
            "coxa 1", "coxa 2", "coxa 6",
            "epimera 1", "epimera 3",
            "pleon 1", "pleon 2", "pleon 3",
            "urosome 1", "urosome 2", "urosome 3",
            "uropod 1", "uropod 2", "uropod 3", "telson"
        ]

        avail_segs = avail_traits["segment"].dropna().unique()
        # เรียงตาม seg_order ก่อน ที่เหลือต่อท้าย
        ordered_segs = [s for s in seg_order if s in avail_segs]
        remaining_segs = [s for s in avail_segs if s not in seg_order]
        segments = ordered_segs + sorted(remaining_segs)

        if not segments:
            st.info(f"🔍 ไม่มี trait เพิ่มเติมแล้ว — พบ **{len(candidates)} species** ที่เป็นไปได้")
            result_df = get_result_df(merged, candidates)
            st.dataframe(result_df, use_container_width=True)
        else:
            st.markdown(f"**เลือก Segment ที่จะตรวจสอบ** (เหลือ {len(candidates)} species):")
            sel_seg = st.selectbox(
                "Segment:",
                ["-- เลือก --"] + segments,
                key=f"seg_{len(selected_traits)}"
            )

            if sel_seg != "-- เลือก --":
                # ── ดึง traits ของ segment นั้น ──
                seg_traits = avail_traits[avail_traits["segment"] == sel_seg][
                    ["trait_id", "character", "description"]
                ].drop_duplicates("trait_id")

                # สร้าง label แบบ "description (trait_id)"
                # ลบขั้นตอน character ออก — แสดง trait โดยตรง
                trait_labels = []
                trait_map = {}
                for _, row in seg_traits.iterrows():
                    desc = str(row["description"]) if pd.notna(row["description"]) else row["character"]
                    if desc == "nan":
                        desc = row["character"]
                    label = desc
                    # ถ้า label ซ้ำให้เพิ่ม trait_id กำกับ
                    if label in trait_map:
                        label = f"{desc} ({row['trait_id']})"
                    trait_labels.append(label)
                    trait_map[label] = row["trait_id"]

                sel_trait_label = st.selectbox(
                    "ลักษณะที่จะตรวจ:",
                    ["-- เลือก --"] + trait_labels,
                    key=f"trait_{len(selected_traits)}"
                )

                if sel_trait_label != "-- เลือก --":
                    sel_trait_id = trait_map[sel_trait_label]

                    # ── เลือก state value ──
                    values = sorted(
                        avail[avail["trait_id"] == sel_trait_id]["trait_value"].dropna().unique()
                    )

                    # แสดงจำนวน species ต่อ option
                    value_labels = []
                    for v in values:
                        n = len(avail[
                            (avail["trait_id"] == sel_trait_id) &
                            (avail["trait_value"] == v)
                        ]["species_id"].unique())
                        value_labels.append(f"{v}  ({n} species)")

                    sel_val_label = st.selectbox(
                        "ลักษณะที่พบ:",
                        ["-- เลือก --"] + value_labels,
                        key=f"val_{len(selected_traits)}"
                    )

                    if sel_val_label != "-- เลือก --":
                        sel_val = values[value_labels.index(sel_val_label)]

                        if st.button("✅ ยืนยันการเลือก", use_container_width=True):
                            st.session_state.selected_traits[sel_trait_id] = sel_val
                            st.session_state.step_history.append(
                                (sel_trait_id, sel_val, sel_seg, sel_trait_label)
                            )
                            st.rerun()

        # ── แสดงผลลัพธ์ปัจจุบันเสมอ (ถึงแม้จะยังมีหลาย species) ──
        if selected_traits and len(candidates) > 1:
            st.divider()
            st.info(f"🔍 ผลลัพธ์ปัจจุบัน: **{len(candidates)} species** — เลือก trait เพิ่มเพื่อแยกให้ชัดขึ้น")
            result_df = get_result_df(merged, candidates)
            st.dataframe(result_df, use_container_width=True)


# ══════════════════════════════════════════════════════════════════
# KEY TO FAMILY
# ══════════════════════════════════════════════════════════════════
else:
    st.subheader("Key to Family")
    st.write("เลือกลักษณะที่สังเกตได้เพื่อระบุ Family ก่อน แล้วค่อยไปใช้ Key to Species")

    try:
        family_data = load_family_data()

        segments_fam = sorted(family_data["observation_note"].dropna().unique())
        sel_seg_fam = st.selectbox(
            "**1. เลือก Segment/Appendage ที่สังเกต:**",
            ["-- เลือก --"] + list(segments_fam),
            key="fam_seg"
        )

        if sel_seg_fam != "-- เลือก --":
            seg_fam_traits = family_data[family_data["observation_note"] == sel_seg_fam][
                ["trait_id", "trait_value"]
            ].drop_duplicates("trait_id")

            # แสดง trait_value แทน trait_id
            trait_descs = seg_fam_traits["trait_id"].tolist()
            sel_trait_fam = st.selectbox(
                "**2. เลือกลักษณะที่ตรวจสอบ:**",
                ["-- เลือก --"] + trait_descs,
                key="fam_trait"
            )

            if sel_trait_fam != "-- เลือก --":
                values_fam = sorted(
                    family_data[family_data["trait_id"] == sel_trait_fam]["trait_value"].dropna().unique()
                )
                sel_val_fam = st.selectbox(
                    "**3. เลือกลักษณะ:**",
                    ["-- เลือก --"] + list(values_fam),
                    key="fam_val"
                )

                if sel_val_fam != "-- เลือก --":
                    result_fam = filter_family(family_data, {sel_trait_fam: sel_val_fam})

                    st.divider()
                    if not result_fam:
                        st.warning("⚠️ ไม่พบ Family ที่ตรงกับลักษณะนี้")
                    else:
                        st.success(f"🔍 Family ที่เป็นไปได้: **{len(result_fam)} families**")
                        for fam in result_fam:
                            st.write(f"• {fam}")
                        st.info("💡 เมื่อทราบ Family แล้ว กลับไปใช้ **Key to Species** เพื่อระบุชนิดต่อ")

    except Exception as e:
        st.error(f"ไม่สามารถโหลด Key to Family ได้: {e}")
        st.caption("ตรวจสอบว่าไฟล์ keytofamily.csv อยู่ใน folder เดียวกันกับ app.py")