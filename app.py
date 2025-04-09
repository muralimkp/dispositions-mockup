import streamlit as st
import json
from streamlit_sortables import sort_items
import os
from disposition_functions import process_transcript, initialize_llm, generate_disposition_prompt, \
    get_level_label_mapping, identify_dispositions, visualize_disposition_path

st.set_page_config(page_title="Disposition Mockup v2", layout="centered")
st.title("Disposition Mockup v2")

tab1, tab2 = st.tabs(["Configure Dispositions", "Test Dispositions"])
if "final_config" not in st.session_state:
    st.session_state.final_config = None
if "final_config" not in st.session_state:
    st.session_state.openai_config = None
if "transcript_file" not in st.session_state:
    st.session_state.transcript_file = None
if "llm" not in st.session_state:
    st.session_state.llm = None
if "model_name" not in st.session_state:
    st.session_state.model_name = None
if "transcript_data" not in st.session_state:
    st.session_state.transcript_data = None
if "level_mapping" not in st.session_state:
    st.session_state.level_mapping = None
if "prompt" not in st.session_state:
    st.session_state.prompt = None

with tab1:
    if "dispositions" not in st.session_state and os.path.exists("dispositions_config.json"):
        with open("dispositions_config.json", "r") as f:
            config_data = json.load(f)
        st.session_state.dispositions = config_data.get("dispositions", [])
        st.session_state.val_lists = [disp.get("values", []) for disp in st.session_state.dispositions]
        st.session_state.save_attempted = False
        st.session_state.final_config = config_data
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
            st.session_state.final_config = final_config
            with open("dispositions_config.json", "w") as f:
                json.dump(final_config, f, indent=2)
            st.success("Configuration saved to `dispositions_config.json`!")

with tab2:
    st.header("Upload OpenAI Config File")

    # Upload JSON config
    config_file = st.file_uploader("Upload your OpenAI config file (.json)", type=["json"])
    st.info("The config json should follow this format:\n\n"
            "```\n"
            "{\n"
            '    "azure_endpoint": "<your_endpoint>",\n'
            '    "azure_deployment": "<your_deployment_name>",\n'
            '    "api_key": "<your_api_key>",\n'
            '    "api_version": "<your_api_version>"\n'
            "}\n"
            "```")

    if config_file is not None:
        try:
            config_data = json.load(config_file)

            # Extract values from config
            # azure_endpoint = config_data.get("azure_endpoint", "")
            # api_key = config_data.get("openai_api_key", "")
            # deployment = config_data.get("azure_deployment", "")
            # api_version = config_data.get("api_version", "")

            st.success("Config file loaded successfully.")
            # st.code(f"Endpoint: {azure_endpoint}\nDeployment: {deployment}\nAPI Version: {api_version}",
            #         language="yaml")

            st.session_state.openai_config = config_data
            if (st.session_state.llm == None):
                st.session_state.llm = initialize_llm(st.session_state.openai_config)
                st.session_state.model_name = st.session_state.openai_config.get("azure_deployment")

            # Show transcript uploader after config is loaded
            st.subheader("Upload Transcript Files")
            transcript_file = st.file_uploader("Upload transcripts", type=["txt"], key="transcript_uploader")



            if transcript_file:
                # Store file in session state
                st.session_state.transcript_file = transcript_file
                st.write(f"Transcript uploaded: {transcript_file.name}")
                print(f'final_config : {st.session_state.final_config}')
                # Call processing function
                st.session_state.transcript_data = process_transcript(st.session_state.transcript_file)
                st.session_state.level_mapping = get_level_label_mapping(st.session_state.final_config)
                st.session_state.prompt = generate_disposition_prompt(config=st.session_state.final_config)
                dispositions_found = identify_dispositions(transcript="\n".join(st.session_state.transcript_data),model=st.session_state.model_name,llm=st.session_state.llm,prompt=st.session_state.prompt)
                visualize_disposition_path(dispositions_found)
        except json.JSONDecodeError:
            st.error("Invalid JSON file. Please upload a valid OpenAI config.")
