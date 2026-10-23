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
st.title("🦐 Thai Amphipoda Taxonomic Key")
st.caption("Thai Coastal & Estuarine Amphipoda — Interactive Identification Tool กำลังพัฒนาโดยธชาพัฒน์")

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

                # ── จัดกลุ่ม segment ──
        seg_groups = {
            "🦐 Head & Antennae": [
                "antenna 1", "accessory flagellum", "antenna 2",
                "peduncle", "peduncle vs antenna1", "antennae",
                "compound eye", "rostrum", "antennal sinus notch", "head"
            ],
            "👄 Mouthparts": [
                "mouthpart", "upper lip", "lower lip", "labium",
                "mandible", "mandibular",
                "maxilla 1", "maxilla 2", "maxiliped"
            ],
            "🦾 Gnathopods": [
                "gnathopod 1", "gnathopod 2"
            ],
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
            "🫁 Body & Gills": [
                "body", "pereonites", "gills", "oostegites"
            ],
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

        # กรองเฉพาะกลุ่มที่มี segment อยู่ใน candidates จริงๆ
        avail_segs = set(avail_traits["segment"].dropna().unique())
        active_groups = {
            grp: [s for s in segs if s in avail_segs]
            for grp, segs in seg_groups.items()
        }
        active_groups = {g: s for g, s in active_groups.items() if s}

        if not active_groups:
            st.info(f"🔍 ไม่มี trait เพิ่มเติมแล้ว — พบ **{len(candidates)} species** ที่เป็นไปได้")
            result_df = get_result_df(merged, candidates)
            st.dataframe(result_df, use_container_width=True)
        else:
            st.markdown(f"**เลือกกลุ่ม Segment** (เหลือ {len(candidates)} species):")

            sel_group = st.selectbox(
                "กลุ่ม:",
                ["-- เลือก --"] + list(active_groups.keys()),
                key=f"grp_{len(selected_traits)}"
            )

            if sel_group != "-- เลือก --":
                group_segs = active_groups[sel_group]

                sel_seg = st.selectbox(
                    "Segment:",
                    ["-- เลือก --"] + group_segs,
                    key=f"seg_{len(selected_traits)}"
                )

                if sel_seg != "-- เลือก --":
                    seg_traits = avail_traits[avail_traits["segment"] == sel_seg][
                        ["trait_id", "character", "description", "state_options"]
                    ].drop_duplicates("trait_id")

                    trait_labels = []
                    trait_map = {}
                    for _, row in seg_traits.iterrows():
                        char = str(row["character"]) if pd.notna(row["character"]) else ""
                        states = str(row["state_options"]) if pd.notna(row["state_options"]) else ""
                        label = f"{char}: {states}" if states else char
                        base = label
                        while label in trait_map:
                            label = f"{base} [{row['trait_id']}]"
                        trait_labels.append(label)
                        trait_map[label] = row["trait_id"]

                    sel_trait_label = st.selectbox(
                        "ลักษณะที่จะตรวจสอบ:",
                        ["-- เลือก --"] + trait_labels,
                        key=f"trait_{len(selected_traits)}"
                    )

                    if sel_trait_label != "-- เลือก --":
                        sel_trait_id = trait_map[sel_trait_label]

                        values = sorted(
                            avail[avail["trait_id"] == sel_trait_id]["trait_value"].dropna().unique()
                        )

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

        # ── init session state ──
        if "fam_selected_traits" not in st.session_state:
            st.session_state.fam_selected_traits = {}
        if "fam_step_history" not in st.session_state:
            st.session_state.fam_step_history = []

        fam_selected = st.session_state.fam_selected_traits

        # ── คำนวณ candidates ──
        fam_candidates = filter_family(family_data, fam_selected)

        # ── Header ──
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write(f"ฐานข้อมูล: **{family_data['family'].nunique()} families** | เหลือ: **{len(fam_candidates)} families**")
        with col2:
            if st.button("🔄 เริ่มใหม่", key="fam_reset", use_container_width=True):
                st.session_state.fam_selected_traits = {}
                st.session_state.fam_step_history = []
                st.rerun()

        # ── แสดง traits ที่เลือกไปแล้ว ──
        if st.session_state.fam_step_history:
            st.markdown("**ลักษณะที่เลือกไปแล้ว:**")
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

        # ── ถ้า candidates เหลือ 0 ──
        if len(fam_candidates) == 0:
            st.error("⚠️ ไม่พบ Family ที่ตรงกับเงื่อนไข — กด 'เริ่มใหม่' หรือลบลักษณะที่เลือกผิดออก")

        # ── ถ้า candidates เหลือ 1 ──
        elif len(fam_candidates) == 1:
            st.success(f"✅ ระบุได้ **1 Family: {list(fam_candidates)[0]}**")
            st.info("💡 กลับไปใช้ **Key to Species** เพื่อระบุชนิดต่อ")

        # ── ยังมีหลาย candidates ──
        else:
            avail_fam = family_data[family_data["family"].isin(fam_candidates)]
            used_fam_traits = set(fam_selected.keys())
            avail_fam_traits = avail_fam[~avail_fam["trait_id"].isin(used_fam_traits)]

            # ── จัดกลุ่ม segment ──
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
                    "pereopod 3", "pereopod 3 merus",
                    "pereopod 4", "pereopod 4 merus",
                    "pereopod 5", "pereopod 5 basis", "pereopod 5 merus",
                    "pereopod 6", "pereopod 6 merus",
                    "pereopod 7", "pereopod 7 basis", "pereopod 7 dactyl"
                ],
                "📦 Coxae": [
                    "coxa 1", "coxa 2", "coxa 3", "coxa 4",
                    "coxa 5", "coxa 6", "coxae"
                ],
                "🫁 Body": [
                    "body", "pereonite", "pleonite", "pleon 3"
                ],
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

            # segment ที่ไม่อยู่ในกลุ่มไหน
            all_grouped = {s for segs in seg_groups_fam.values() for s in segs}
            ungrouped = sorted(avail_fam_segs - all_grouped)
            if ungrouped:
                active_fam_groups["📋 อื่นๆ"] = ungrouped

            if not active_fam_groups:
                st.info(f"🔍 ไม่มี trait เพิ่มเติม — พบ **{len(fam_candidates)} families**")
            else:
                st.markdown(f"**เลือกกลุ่ม Segment** (เหลือ {len(fam_candidates)} families):")

                sel_fam_group = st.selectbox(
                    "กลุ่ม:",
                    ["-- เลือก --"] + list(active_fam_groups.keys()),
                    key=f"fam_grp_{len(fam_selected)}"
                )

                if sel_fam_group != "-- เลือก --":
                    fam_group_segs = active_fam_groups[sel_fam_group]

                    sel_fam_seg = st.selectbox(
                        "Segment:",
                        ["-- เลือก --"] + fam_group_segs,
                        key=f"fam_seg_{len(fam_selected)}"
                    )

                    if sel_fam_seg != "-- เลือก --":
                        fam_seg_traits = avail_fam_traits[
                            avail_fam_traits["observation_note"] == sel_fam_seg
                        ][["trait_id", "trait_value"]].drop_duplicates("trait_id")

                        # ใช้ trait_value แรกเป็น label แทน trait_id
                        fam_trait_labels = []
                        fam_trait_map = {}
                        for _, row in fam_seg_traits.iterrows():
                            vals = family_data[
                                family_data["trait_id"] == row["trait_id"]
                            ]["trait_value"].dropna().unique()
                            state_preview = ", ".join(sorted(vals)[:3])
                            label = f"{state_preview}..."  if len(vals) > 3 else state_preview
                            base = label
                            while label in fam_trait_map:
                                label = f"{base} [{row['trait_id']}]"
                            fam_trait_labels.append(label)
                            fam_trait_map[label] = row["trait_id"]

                        sel_fam_trait_label = st.selectbox(
                            "ลักษณะที่จะตรวจสอบ:",
                            ["-- เลือก --"] + fam_trait_labels,
                            key=f"fam_trait_{len(fam_selected)}"
                        )

                        if sel_fam_trait_label != "-- เลือก --":
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

                            sel_fam_val_label = st.selectbox(
                                "ลักษณะที่พบ:",
                                ["-- เลือก --"] + fam_value_labels,
                                key=f"fam_val_{len(fam_selected)}"
                            )

                            if sel_fam_val_label != "-- เลือก --":
                                sel_fam_val = fam_values[fam_value_labels.index(sel_fam_val_label)]
                                if st.button("✅ ยืนยันการเลือก", key="fam_confirm", use_container_width=True):
                                    st.session_state.fam_selected_traits[sel_fam_trait_id] = sel_fam_val
                                    st.session_state.fam_step_history.append(
                                        (sel_fam_trait_id, sel_fam_val, sel_fam_seg, sel_fam_trait_label)
                                    )
                                    st.rerun()

            # ── แสดงผลลัพธ์ปัจจุบัน ──
            if fam_selected and len(fam_candidates) > 1:
                st.divider()
                st.info(f"🔍 ผลลัพธ์ปัจจุบัน: **{len(fam_candidates)} families** — เลือก trait เพิ่มเพื่อแยกให้ชัดขึ้น")
                for fam in sorted(fam_candidates):
                    st.write(f"• {fam}")
                st.info("💡 เมื่อทราบ Family แล้ว กลับไปใช้ **Key to Species** เพื่อระบุชนิดต่อ")

    except Exception as e:
        st.error(f"ไม่สามารถโหลด Key to Family ได้: {e}")
        st.caption("ตรวจสอบว่าไฟล์ keytofamily.csv อยู่ใน folder เดียวกันกับ app.py")