import pandas as pd

def load_data():
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
    return species, traits, species_traits, merged


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

    result = merged[merged["species_id"].isin(candidates)][
        ["species_id", "scientific_name", "Family", "trait_id", "trait_value"]
    ].drop_duplicates(subset=["species_id"]).reset_index(drop=True)

    return result


def list_trait_options(merged, trait_id):
    return sorted(merged[merged["trait_id"] == trait_id]["trait_value"].dropna().unique())


def smart_trait_order(merged, candidates):
    """เรียง trait ที่แยก species ได้ดีสุดมาก่อน"""
    trait_ids = merged[merged["species_id"].isin(candidates)]["trait_id"].unique()
    scores = []
    for tid in trait_ids:
        n_values = merged[
            (merged["trait_id"] == tid) &
            (merged["species_id"].isin(candidates))
        ]["trait_value"].nunique()
        scores.append((tid, n_values))
    scores.sort(key=lambda x: x[1], reverse=True)
    return [t[0] for t in scores]


def run_interactive_key(merged):
    candidates = set(merged["species_id"].unique())
    selected = {}

    print(f"\nเริ่มต้น: {len(candidates)} species")
    print("พิมพ์ 0 เพื่อกลับ/ข้าม, r เพื่อเริ่มใหม่\n")

    while True:
        # แสดง segment ที่มีอยู่ใน candidates ปัจจุบัน
        available = merged[merged["species_id"].isin(candidates)]
        allowed_segments = [
            "accessory_flagellum", "antenna_1", "antenna_2",
            "compound_eye", "gnathopod_1", "gnathopod_2",
            "pleon_2", "rostrum", "uropod_2"
        ]
        segments = sorted([s for s in available["segment"].dropna().unique()
                            if s in allowed_segments])

        print(f"--- เหลือ {len(candidates)} species ---")
        print("เลือก segment:")
        for i, seg in enumerate(segments, 1):
            print(f"  {i}. {seg}")
        print("  0. สิ้นสุด → ดูผลลัพธ์")

        seg_choice = input("เลือก: ").strip().lower()

        if seg_choice == "0":
            break
        if seg_choice == "r":
            return run_interactive_key(merged)
        if not seg_choice.isdigit() or not (1 <= int(seg_choice) <= len(segments)):
            print("  ⚠️  กรุณาเลือกตัวเลขที่มีในรายการ\n")
            continue

        selected_segment = segments[int(seg_choice) - 1]

        # แสดง character ภายใน segment ที่เลือก
        while True:
            seg_traits = available[
                available["segment"] == selected_segment
            ][["trait_id", "character", "description"]].drop_duplicates("trait_id")

            trait_list = seg_traits.values.tolist()

            print(f"\n[{selected_segment}] เลือก character:")
            for i, (tid, char, desc) in enumerate(trait_list, 1):
                marker = "✓" if tid in selected else " "
                print(f"  {i}. [{marker}] {char} ({tid})")
                if desc and str(desc) != "nan":
                    print(f"         → {desc}")
            print("  0. กลับเลือก segment")

            char_choice = input("เลือก: ").strip().lower()

            if char_choice == "0":
                break
            if char_choice == "r":
                return run_interactive_key(merged)
            if not char_choice.isdigit() or not (1 <= int(char_choice) <= len(trait_list)):
                print("  ⚠️  กรุณาเลือกตัวเลขที่มีในรายการ\n")
                continue

            selected_trait_id = trait_list[int(char_choice) - 1][0]
            selected_character = trait_list[int(char_choice) - 1][1]

            # แสดง state options ของ character นั้น
            while True:
                options = list_trait_options(merged, selected_trait_id)

                print(f"\n  [{selected_character}] เลือกลักษณะ:")
                for i, opt in enumerate(options, 1):
                    marker = "✓" if selected.get(selected_trait_id) == opt else " "
                    print(f"    {i}. [{marker}] {opt}")
                print("    0. กลับเลือก character")

                val_choice = input("  เลือก: ").strip().lower()

                if val_choice == "0":
                    break
                if val_choice == "r":
                    return run_interactive_key(merged)
                if not val_choice.isdigit() or not (1 <= int(val_choice) <= len(options)):
                    print("  ⚠️  กรุณาเลือกตัวเลขที่มีในรายการ\n")
                    continue

                chosen_value = options[int(val_choice) - 1]

                # ทดสอบ filter ก่อนยืนยัน
                test_selected = {**selected, selected_trait_id: chosen_value}
                test_result = filter_species(merged, test_selected)
                test_candidates = set(test_result["species_id"])

                if len(test_candidates) == 0:
                    print(f"\n  ⚠️  ถ้าเลือก '{chosen_value}' จะไม่มี species เหลือเลย")
                    print("  อาจเป็นเพราะข้อมูลไม่ครบ หรือลักษณะนี้ไม่ตรงกับที่บันทึกไว้")
                    confirm = input("  ยืนยันเลือกต่อ? (y/n): ").strip().lower()
                    if confirm != "y":
                        continue

                selected[selected_trait_id] = chosen_value
                candidates = test_candidates if test_candidates else candidates
                print(f"\n  → เหลือ {len(candidates)} species\n")
                break  # กลับไปเลือก character ใหม่

    # แสดงผลลัพธ์สุดท้าย
    final = merged[merged["species_id"].isin(candidates)][
        ["Genus", "scientific_name", "Author", "Family", "Order"]
    ].drop_duplicates().reset_index(drop=True)

    print("\n" + "="*40)
    print("ผลการระบุชนิด")
    print("="*40)
    if len(final) == 1:
        print("✓ ระบุได้ชนิดเดียว:")
    else:
        print(f"พบ {len(final)} species ที่ตรงเงื่อนไข (ดูรูปประกอบเพิ่มเติม):")
    print(final.to_string(index=False))
    print("="*40)
    print(f"\nลักษณะที่เลือกไปทั้งหมด: {len(selected)} trait")
    for tid, val in selected.items():
        print(f"  {tid}: {val}")

if __name__ == "__main__":
    species, traits, species_traits, merged = load_data()
    run_interactive_key(merged)