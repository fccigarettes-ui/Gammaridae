import pandas as pd
import streamlit as st

st.set_page_config(page_title="Amphipoda Taxonomic Key", layout="wide")

# ── โหลดข้อมูล Key to Species ──────────────────────────────────────
@st.cache_data
def load_species_data():
    species = pd.read_csv("species.csv")
    traits = pd.read_csv("trait_id.csv")
    species_traits = pd.read_csv("species_traits.csv")

    # แก้ชื่อคอลัมน์ที่มี space
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

# ── โหลดข้อมูล Key to Family ───────────────────────────────────────
@st.cache_data
def load_family_data():
    df = pd.read_csv("keytofamily.csv", header=None)

    # หา header rows (rows ที่มี "suborder numbers" ในคอลัมน์แรก)
    header_mask = df[0] == "suborder numbers"
    header_idx = df[header_mask].index.tolist()

    # ใช้ header row แรกเป็น column names
    if header_idx:
        df.columns = df.iloc[header_idx[0]].tolist()
        df = df.drop(header_idx)  # ลบ header rows ออก

    # เปลี่ยนชื่อคอลัมน์ให้ใช้งานได้
    df.columns = ["step", "result", "superfamily", "family", "trait_id", "trait_value", "observation_note"]
    df = df.dropna(subset=["trait_id", "trait_value"])

    # กรองเฉพาะ rows ที่มี family จริงๆ (ไม่ใช่เลข step ต่อไป)
    family_rows = df[df["family"].notna() & ~df["family"].str.match(r"^\d+$", na=False)].copy()
    family_rows = family_rows[~family_rows["family"].str.contains("Section|return", na=False)]

    return family_rows


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


# ── UI หลัก ────────────────────────────────────────────────────────
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
# KEY TO SPECIES
# ══════════════════════════════════════════════════════════════════
if mode == "🔬 Key to Species — ระบุถึงระดับชนิด":
    merged = load_species_data()

    st.subheader("Key to Species")
    st.write(f"ฐานข้อมูล: **{merged['species_id'].nunique()} species** | **{merged['segment'].nunique()} segments**")

    # ── เลือก segment ──
    segments = sorted(merged["segment"].dropna().unique())
    sel_seg = st.selectbox("**1. เลือก Segment:**", ["-- เลือก --"] + list(segments))

    if sel_seg != "-- เลือก --":
        # ── เลือก character ──
        seg_traits = merged[merged["segment"] == sel_seg][
            ["trait_id", "character", "description"]
        ].drop_duplicates("trait_id")

        char_labels = []
        char_map = {}
        for _, row in seg_traits.iterrows():
            label = row["character"]
            if pd.notna(row["description"]) and str(row["description"]) != "nan":
                label = f"{row['character']} — {row['description']}"
            char_labels.append(label)
            char_map[label] = row["trait_id"]

        sel_char_label = st.selectbox("**2. เลือก Character:**", ["-- เลือก --"] + char_labels)

        if sel_char_label != "-- เลือก --":
            sel_trait_id = char_map[sel_char_label]

            # ── เลือก state ──
            values = sorted(merged[merged["trait_id"] == sel_trait_id]["trait_value"].dropna().unique())
            sel_val = st.selectbox("**3. เลือกลักษณะ:**", ["-- เลือก --"] + list(values))

            if sel_val != "-- เลือก --":
                result = filter_species(merged, {sel_trait_id: sel_val})

                st.divider()
                if len(result) == 0:
                    st.warning("⚠️ ไม่พบ species ที่ตรงกับลักษณะนี้ — อาจมีข้อมูลไม่ครบ")
                elif len(result) == 1:
                    st.success(f"✅ ระบุได้ **1 species**")
                    st.dataframe(result, use_container_width=True)
                else:
                    st.info(f"🔍 พบ **{len(result)} species** ที่ตรงเงื่อนไข — ลองเพิ่ม character อื่นเพื่อแยกเพิ่มเติม")
                    st.dataframe(result, use_container_width=True)

                    # ── แนะนำ segment อื่นที่อาจช่วยแยกได้ ──
                    remaining_species = set(result["species_id"])
                    remaining_merged = merged[merged["species_id"].isin(remaining_species)]
                    other_segs = sorted(remaining_merged[
                        remaining_merged["segment"] != sel_seg
                    ]["segment"].dropna().unique())
                    if other_segs:
                        st.caption(f"💡 ลองดู segment อื่น: {', '.join(other_segs[:5])}")


# ══════════════════════════════════════════════════════════════════
# GAMMARIDEAN AMPHIPODA: KEY TO FAMILY
# ══════════════════════════════════════════════════════════════════
else:
    st.subheader("Key to Family")
    st.write("เลือกลักษณะที่สังเกตได้เพื่อระบุ Family ก่อน แล้วค่อยไปใช้ Key to Species")

    try:
        family_data = load_family_data()

        # ── เลือก segment/observation_note ──
        segments_fam = sorted(family_data["observation_note"].dropna().unique())
        sel_seg_fam = st.selectbox(
            "**1. เลือก Segment/Appendage ที่สังเกต:**",
            ["-- เลือก --"] + list(segments_fam),
            key="fam_seg"
        )

        if sel_seg_fam != "-- เลือก --":
            # ── เลือก trait ──
            seg_fam_traits = family_data[family_data["observation_note"] == sel_seg_fam][
                ["trait_id"]
            ].drop_duplicates()

            trait_ids_fam = seg_fam_traits["trait_id"].tolist()
            sel_trait_fam = st.selectbox(
                "**2. เลือก Trait ID:**",
                ["-- เลือก --"] + trait_ids_fam,
                key="fam_trait"
            )

            if sel_trait_fam != "-- เลือก --":
                # ── เลือก state ──
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
