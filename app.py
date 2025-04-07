import streamlit as st
import json

st.set_page_config(page_title="Disposition Mockup", layout="centered")
st.title("Disposition Mockup")

# Initialize session state
if "dispositions" not in st.session_state:
    st.session_state.dispositions = []

if "val_lists" not in st.session_state:
    st.session_state.val_lists = []

# Add new disposition
if st.button("➕ Add Disposition"):
    index = len(st.session_state.dispositions)
    st.session_state.dispositions.append({
        "label": "",
        "description": "",
        "values": [],
        "allow_other_values": False
    })
    st.session_state.val_lists.append([])

# UI for each disposition
for i, disp in enumerate(st.session_state.dispositions):
    with st.expander(f"Disposition {i+1}", expanded=True):
        label = st.text_input("Label", value=disp["label"], max_chars=30, key=f"label_{i}")
        description = st.text_input("Description", value=disp["description"], max_chars=100, key=f"desc_{i}")

        # Input field to add new values
        new_val = st.text_input("Add a Value", key=f"new_val_{i}", max_chars=20, placeholder="Type and press 'Add'")
        if st.button("Add", key=f"add_btn_{i}") and new_val.strip():
            if new_val.strip() not in st.session_state.val_lists[i]:
                st.session_state.val_lists[i].append(new_val.strip())
            st.rerun()

        # Inline value tags with ❌ buttons
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

        # Allow Other Values
        allow_other = st.selectbox(
            "Allow Other Values", [True, False],
            index=int(not disp["allow_other_values"]), key=f"other_{i}"
        )

        # Update disposition state
        st.session_state.dispositions[i] = {
            "label": label,
            "description": description,
            "values": st.session_state.val_lists[i],
            "allow_other_values": allow_other
        }

# Save Button
if st.button("💾 Save Config"):
    final_config = {"dispositions": st.session_state.dispositions}
    st.json(final_config)
    with open("dispositions_config.json", "w") as f:
        json.dump(final_config, f, indent=2)
    st.success("Configuration saved to `dispositions_config.json`!")
