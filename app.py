import streamlit as st
import json
from streamlit_sortables import sort_items

st.set_page_config(page_title="Disposition Mockup v2", layout="centered")
st.title("Disposition Mockup v2")

# Initialize session state
if "dispositions" not in st.session_state:
    st.session_state.dispositions = []

if "val_lists" not in st.session_state:
    st.session_state.val_lists = []

if "save_attempted" not in st.session_state:
    st.session_state.save_attempted = False

# Add new disposition
if st.button("➕ Add Disposition"):
    st.session_state.dispositions.append({
        "label": "",
        "description": "",
        "values": []
    })
    st.session_state.val_lists.append([])

# Extract live labels before showing organizer
live_labels = [
    disp["label"].strip() or f"(No Label #{i+1})"
    for i, disp in enumerate(st.session_state.dispositions)
]

# Drag-and-drop UI with inline Level and Label columns
if st.session_state.dispositions:
    st.markdown("### 🧩 Organize Dispositions")

    levels = [f"Level {i+1}" for i in range(len(st.session_state.dispositions))]
    label_to_index = {label: i for i, label in enumerate(live_labels)}

    # Display levels and labels side-by-side
    col1, col2 = st.columns([1, 4])
    with col1:
        for lvl in levels:
            st.markdown(f"<div style='padding: 8px;'>{lvl}</div>", unsafe_allow_html=True)

    with col2:
        sorted_labels = sort_items(live_labels, direction="vertical")
        sorted_indices = [label_to_index[label] for label in sorted_labels]

    # Reorder session state
    st.session_state.dispositions = [st.session_state.dispositions[i] for i in sorted_indices]
    st.session_state.val_lists = [st.session_state.val_lists[i] for i in sorted_indices]

# Disposition editors
for i, disp in enumerate(st.session_state.dispositions):
    with st.expander(f"Level {i + 1}: {disp['label'] or 'Disposition'}", expanded=True):
        label = st.text_input("Label", value=disp["label"], max_chars=30, key=f"label_{i}")
        description = st.text_input("Description (Optional)", value=disp["description"], max_chars=100, key=f"desc_{i}")

        if st.session_state.save_attempted and not label.strip():
            st.error("Label cannot be empty")

        new_val_key = f"new_val_{i}"
        new_val = st.text_input("Add a Value (Optional)", key=new_val_key, max_chars=20, placeholder="Type and press 'Add'")
        if st.button("Add", key=f"add_btn_{i}"):
            new_val_clean = new_val.strip()
            if new_val_clean and new_val_clean not in st.session_state.val_lists[i]:
                st.session_state.val_lists[i].append(new_val_clean)
                st.query_params[new_val_key] = ""

        if st.session_state.val_lists[i]:
            st.markdown("**Values:**")
            tag_cols = st.columns(len(st.session_state.val_lists[i]))
            for j, val in enumerate(st.session_state.val_lists[i]):
                with tag_cols[j]:
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.markdown(
                            f"<div style='padding: 6px 12px; background-color: #f0f2f6; border-radius: 16px; display: inline-block;'>{val}</div>",
                            unsafe_allow_html=True
                        )
                    with col2:
                        if st.button("❌", key=f"del_{i}_{j}"):
                            st.session_state.val_lists[i].pop(j)
                            st.rerun()

        # Update session state
        st.session_state.dispositions[i]["label"] = label.strip()
        st.session_state.dispositions[i]["description"] = description.strip()
        st.session_state.dispositions[i]["values"] = st.session_state.val_lists[i]

# Save config
if st.button("💾 Save Config"):
    st.session_state.save_attempted = True
    errors = [d["label"].strip() == "" for d in st.session_state.dispositions]

    if any(errors):
        st.error("Please fill in all disposition labels before saving.")
    else:
        final_config = {"dispositions": []}
        for idx, disp in enumerate(st.session_state.dispositions):
            if not disp["values"]:
                st.warning(f"Disposition '{disp['label']}' has no values. AI will auto-classify.")
            final_config["dispositions"].append({
                "level": idx + 1,
                "label": disp["label"],
                "description": disp["description"],
                "values": disp["values"]
            })

        st.json(final_config)
        with open("dispositions_config.json", "w") as f:
            json.dump(final_config, f, indent=2)
        st.success("Configuration saved to `dispositions_config.json`!")
