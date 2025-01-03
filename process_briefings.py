import re
import json
import subprocess
import requests
import logging
import sys
import html2text
from dotenv import load_dotenv
import requests
import re
import os

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Put your API key in a .env file in the same directory as this script
load_dotenv()
API_KEY = os.getenv("NEBIUS_API_KEY")
if not API_KEY:
    raise ValueError("NEBIUS_API_KEY environment variable not set")

# API configuration
BASE_URL = "https://api.studio.nebius.com/v1/chat/completions" # v1 instead of api for nebius
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}

# function to call a large language model with the OpenAI API
def call_llm(prompt, model="Qwen/Qwen2.5-72B-Instruct", raw_response=False):
    logging.debug(f"Calling LLM with prompt: {prompt}")
    payload = {
        "model": model,
        "messages":[{"role": "user", "content": prompt}, {"role": "system","content": "You are a helpful AI assistant, expert-level at generating summaries and data extraction. You always return JSON data in response to user prompts. You never add any additional content besides JSON."}],
    }
    #logging.debug(f"Payload sent to LLM API: {json.dumps(payload, indent=2)}")

    try:
        response = requests.post(BASE_URL, headers=HEADERS, json=payload, verify=False)
        response.raise_for_status()
        
        response_data = json.loads(response.text)
        logging.debug(f"Raw LLM response: {json.dumps(response_data, indent=2)}")

        choices = response_data.get("choices", [])
        if choices and "message" in choices[0]:
            content = choices[0]["message"]["content"]
            logging.debug(f"Extracted content from response: {content}")

            match = re.search(r"```json\s*(.*?)\s*```", content, re.DOTALL)
            if match:
                content = match.group(1).strip()
                logging.debug(f"Cleaned JSON content: {content}")

            if raw_response:
                return content

            parsed_content = None
            try:
                parsed_content = json.loads(content)
            except json.JSONDecodeError:
                logging.error(f"Failed to parse JSON content: {content}")
            return parsed_content if parsed_content else {}

    except requests.exceptions.RequestException as e:
        logging.error(f"Error calling LLM API: {e}")
        if response is not None:
            logging.error(f"Response Content: {response.text}")
       
        # sometimes these things are flakey, so we'll retry a few times
        call_llm.error_count = getattr(call_llm, 'error_count', 0) + 1
        if call_llm.error_count >= 3:
            raise RuntimeError("Three consecutive errors occurred while calling the LLM API.")
    else:
        call_llm.error_count = 0

def chunk_text(text, max_chunk_size=512):
    """Chunk text into manageable sections."""
    sentences = text.split('. ')
    chunks = []
    current_chunk = []
    current_length = 0

    for sentence in sentences:
        if current_length + len(sentence) <= max_chunk_size:
            current_chunk.append(sentence)
            current_length += len(sentence)
        else:
            chunks.append('. '.join(current_chunk))
            current_chunk = [sentence]
            current_length = len(sentence)
    if current_chunk:
        chunks.append('. '.join(current_chunk))
    return chunks

def extract_topic_metadata(chunk):
    """Run topic-specific queries for a text chunk."""
    queries = {
    "policies_and_priorities_keywords": f"Extract an array of keywords or phrases related to policies, strategic priorities, and high-level goals in this text. If there are no keywords, return an empty array.\n Text: {chunk}",
    "organizational_structure_keywords": f"Extract an array of keywords or phrases related to organizational roles, responsibilities, and hierarchy in this text. If there are no keywords, return an empty array.\n Text: {chunk}",
    "program_and_operations_keywords": f"Extract an array of keywords or phrases related to programs, initiatives, and operational processes in this text. If there are no keywords, return an empty array.\n Text: {chunk}",
    "key_partners_keywords": f"Extract an array of keywords or phrases identifying key partners, stakeholders, or collaborators mentioned in this text. If there are no keywords, return an empty array.\n Text: {chunk}",
    "challenges_keywords": f"Extract an array of keywords or phrases describing challenges, risks, or obstacles mentioned in this text. If there are no keywords, return an empty array.\n Text: {chunk}",
    "history_and_legislation_keywords": f"Extract an array of keywords or phrases describing legislative frameworks, historical context, or the evolution of policies mentioned in this text. If there are no keywords, return an empty array.\n Text: {chunk}"
}
    
    topic_metadata = {}
    for topic, query in queries.items():
        logging.debug(f"Extracting metadata for topic: {topic}")
        topic_metadata[topic] = call_llm(prompt=query)
    return topic_metadata

def extract_metadata(chunk, chunk_id, section_title):
    """Extract metadata for a given text chunk."""
    metadata = {
        "chunk_id": chunk_id,
        "section_title": section_title,
        "summary": call_llm(prompt=f"Summarize the following text: {chunk}"),
        "chunk_text": chunk
    }
    metadata.update(extract_topic_metadata(chunk))
    return metadata

def process_document(document_path, output_path):
    """Process a document and generate metadata for RAG."""
    with open(document_path, 'r', encoding='utf-8') as file:
        document = file.read()
    
    # Convert HTML to Markdown
    markdown_text = html2text.html2text(document)
    
    sections = re.split(r"\n#+\s", markdown_text)  # Split by headings
    
    with open(output_path, 'w', encoding='utf-8') as outfile:
        outfile.write("[\n")  # Start JSON array

        for section_id, section in enumerate(sections):
            section_title = section.split("\n")[0]  # Assume first line is the title
            chunks = chunk_text(section)
            
            for chunk_id, chunk in enumerate(chunks):
                metadata = extract_metadata(chunk, f"{section_id}-{chunk_id}", section_title)
                json.dump(metadata, outfile, ensure_ascii=False, indent=4)
                if section_id < len(sections) - 1 or chunk_id < len(chunks) - 1:
                    outfile.write(",\n")  # Add comma between JSON objects

        outfile.write("\n]")  # End JSON array
    print(f"Metadata saved to {output_path}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python process_briefings.py <document_path> <output_path>")
        sys.exit(1)

    document_path = sys.argv[1]
    output_path = sys.argv[2]

    process_document(document_path, output_path)