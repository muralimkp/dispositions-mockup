from openai import AzureOpenAI
import streamlit as st
import json
import streamlit.components.v1 as components

def process_transcript(transcript_file):
    # Decode the uploaded file directly (no need to use open)
    content = transcript_file.read().decode("utf-8")
    lines = content.splitlines()
    return lines  # or any processed result


def initialize_llm(config):
    llm = AzureOpenAI(
        azure_deployment=config.get('azure_deployment'),
        azure_endpoint=config.get('azure_endpoint'),
        api_key=config.get('api_key'),
        api_version=config.get('api_version')
    )

    return llm

def visualize_disposition_path(path_json_str):
    if "level_mapping" not in st.session_state:
        st.warning("Level mapping not found in session state.")
        return

    try:
        path_dict = json.loads(path_json_str)
    except json.JSONDecodeError:
        st.error("Invalid JSON string provided.")
        return

    st.markdown("### ✦ AI Dispositions")

    table_html = """
    <style>
    table.disposition-table {
        width: 100%;
        border-collapse: collapse;
        font-family: 'Segoe UI', sans-serif;
        margin-top: 10px;
    }
    table.disposition-table th, table.disposition-table td {
        padding: 12px;
        text-align: left;
        border: 1px solid #ccc;
    }
    table.disposition-table th {
        background-color: #f2f2f2;
    }
    table.disposition-table tr:nth-child(even) {
        background-color: #fafafa;
    }
    </style>
    <table class="disposition-table">
        <thead>
            <tr>
                <th>Level</th>
                <th>Label</th>
                <th>AI Disposition</th>
            </tr>
        </thead>
        <tbody>
    """

    for level_key in sorted(path_dict.keys(), key=lambda x: int(x[1:])):
        label = st.session_state.level_mapping.get(level_key, "(Unknown Label)")
        dispositions = ", ".join(path_dict[level_key])
        table_html += f"""
            <tr>
                <td>{level_key}</td>
                <td>{label}</td>
                <td>{dispositions}</td>
            </tr>
        """

    table_html += """
        </tbody>
    </table>
    """

    components.html(table_html, height=400, scrolling=True)
def generate_disposition_prompt(config: dict) -> str:
    levels = config.get("dispositions", [])
    prompt_parts = ["You will be given a customer service transcript."]

    prompt_parts.append("Your task is to identify disposition values based on the configuration provided.")

    prompt_parts.append("The configuration contains levels of dispositions:")

    for level in levels:
        level_str = f"\nLevel {level['level']} - {level['label']}: {level.get('description', '').strip() or 'No description'}"
        values = level.get("values", [])
        if values:
            level_str += f"\nPossible values: {', '.join(values)}"
        else:
            level_str += "\nYou may generate suitable values if none are listed."
        prompt_parts.append(level_str)

    prompt_parts.append("""
Guidelines:
- You may assign more than one value per level, but keep it concise.
- If the config provides possible values, pick from them. If not, choose sensible values based on the transcript.
- Return the result as a JSON in the format: { "L1": [...], "L2": [...], "L3": [...] }
- Do not explain. Just return the JSON.

""")

    return "\n".join(prompt_parts)

def get_level_label_mapping(config: dict) -> dict:
    mapping = {}
    for item in config.get("dispositions", []):
        level_key = f"L{item['level']}"
        mapping[level_key] = item.get("label", f"Level {item['level']}")
    return mapping

def identify_dispositions(llm,prompt,transcript,model):
 response = llm.chat.completions.create(
    temperature=0.1,
    model=model,
    max_tokens=4096,
    messages=[
        {"role": "system", "content": prompt},
        {"role": "user", "content": f"Perform the above task for this transcript - {transcript}"}
    ]
 )
 print('function called')
 generated_text = response.choices[0].message.content
 print(generated_text)
 return generated_text