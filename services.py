# services.py
import os
import requests # Use the requests library now
from dotenv import load_dotenv
import hashlib
import ast # For safely evaluating string representation of list/dict
import json # For parsing JSON response

load_dotenv()

PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")
if not PERPLEXITY_API_KEY:
    raise ValueError("PERPLEXITY_API_KEY not found in .env file. Please create a .env file with your API key.")

# --- Perplexity API Configuration ---
API_BASE_URL = "https://api.perplexity.ai/chat/completions"
# --- Select your Sonar Model ---
# As per your example, "sonar" might be a general endpoint.
# Perplexity's docs also list specific ones like:
# - sonar-small-chat
# - sonar-medium-chat
# - sonar-small-online
# - sonar-medium-online
# Let's stick to sonar-medium-online as it's good for search-augmented tasks.
# If "sonar" is a generic model name they accept, that's fine too.
# Check their latest API docs for the most accurate model names.
MODEL_NAME = "sonar"
# MODEL_NAME = "sonar" # If this is a valid model identifier per their docs for HTTP API

def get_perplexity_response(prompt_content: str, system_prompt_content: str = None, max_tokens: int = 1500) -> str:
    """
    Gets a response from the Perplexity API using direct HTTP requests.
    """
    if system_prompt_content is None:
        system_prompt_content = (
            "You are an expert medical research assistant. "
            "Provide detailed, accurate, and well-sourced information. "
            "When providing information, if sources are cited by the underlying model, include them directly in the text, "
            "for example: 'According to a study [Study Name](URL), the prevalence is X%.' "
            "If asked for data for charts, try to provide it in a Python-style list of tuples or a simple table format within your text response. "
            "Be factual and concise."
        )

    messages = []
    if system_prompt_content:
        messages.append({"role": "system", "content": system_prompt_content})
    messages.append({"role": "user", "content": prompt_content})

    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "max_tokens": max_tokens,
        # You can add other parameters here like temperature, stream (if supported & handled)
        # "temperature": 0.7,
    }
    headers = {
        "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json" # Good practice
    }

    try:
        print(f"Sending prompt to Perplexity ({MODEL_NAME}) via HTTP: '{prompt_content[:100]}...'")
        response = requests.post(API_BASE_URL, json=payload, headers=headers, timeout=120) # Added timeout
        response.raise_for_status()  # Raises an HTTPError for bad responses (4XX or 5XX)
        
        response_data = response.json()
        
        # Debug: Print the full response structure for the first call to understand it
        # if "printed_once" not in get_perplexity_response.__dict__:
        #     print("Full Perplexity API JSON Response:", json.dumps(response_data, indent=2))
        #     get_perplexity_response.printed_once = True

        # Adjust based on the actual structure of Perplexity's response JSON
        # Common structures for chat completions:
        # response_data['choices'][0]['message']['content']
        # response_data['output'] (sometimes)
        # Let's assume it's similar to OpenAI's structure for now.
        if response_data.get("choices") and \
           isinstance(response_data["choices"], list) and \
           len(response_data["choices"]) > 0 and \
           response_data["choices"][0].get("message") and \
           response_data["choices"][0]["message"].get("content"):
            content = response_data["choices"][0]["message"]["content"]
        else:
            # Fallback or error if structure is different
            print("Unexpected response structure from Perplexity API:")
            print(json.dumps(response_data, indent=2))
            return "Error: Could not parse response from AI due to unexpected format."

        print(f"Received response from Perplexity: '{content[:100]}...'")
        return content.strip()
        
    except requests.exceptions.HTTPError as http_err:
        error_content = "Unknown error"
        try:
            error_details = response.json() # Try to get error details from JSON response
            error_content = error_details.get("error", {}).get("message", response.text)
        except json.JSONDecodeError:
            error_content = response.text # If not JSON, use raw text
        print(f"HTTP error calling Perplexity API: {http_err} - Details: {error_content}")
        return f"Error: AI API request failed (HTTP {response.status_code}). Details: {error_content}"
    except requests.exceptions.RequestException as req_err:
        print(f"Request error calling Perplexity API: {req_err}")
        return f"Error: Could not connect to AI service. Details: {str(req_err)}"
    except Exception as e:
        print(f"Generic error in get_perplexity_response: {e}")
        import traceback
        traceback.print_exc()
        return f"Error: An unexpected error occurred while communicating with the AI. Details: {str(e)}"

def generate_report_id(topic: str) -> str:
    """Generates a simple unique ID for the report based on the topic."""
    return hashlib.md5(topic.lower().encode()).hexdigest()[:12]

async def conduct_deep_research(topic: str):
    """
    Orchestrates the deep research process by making multiple calls to Perplexity.
    (No changes to the logic here, only `get_perplexity_response` is different)
    """
    print(f"Starting deep research for topic: {topic}")
    report_data = {
        "report_id": generate_report_id(topic),
        "topic": topic,
        "summary": None,
        "medical_data_analysis": None,
        "trends_analysis": None,
        "government_schemes": None,
        "diseases_on_rise": None,
        "charts": [],
        "full_text_for_follow_up": ""
    }
    all_text_content = []

    research_sections = [
        ("summary", "Overall Summary",
         f"Provide a comprehensive medical summary of '{topic}'. Focus on key aspects, definitions, and general impact. Keep it concise yet informative."),
        ("medical_data_analysis", "Medical Data & Records Analysis",
         f"Analyze available medical data and records related to '{topic}'. Discuss prevalence, incidence rates, common diagnostic methods, and treatment outcomes. Mention any significant statistics or studies."),
        ("trends_analysis", "Trends Analysis",
         f"Identify and analyze current and emerging trends related to '{topic}'. Are cases increasing or decreasing? Are there new research directions or treatment modalities? Discuss any demographic shifts or risk factors."),
        ("government_schemes", "Relevant Government Schemes & Initiatives",
         f"List and briefly describe any relevant government schemes or public health initiatives related to managing or researching '{topic}' or related health concerns. Focus on schemes from major relevant geographical areas if the topic implies one, otherwise general."),
        ("diseases_on_rise", "Associated Diseases/Complications on the Rise",
         f"Based on the research for '{topic}', are there any specific related diseases or complications that are observed to be on the rise or are of growing concern? Explain why.")
    ]

    for key, title, prompt in research_sections:
        print(f"Fetching section: {title}")
        content = get_perplexity_response(prompt) # This now uses the requests-based function
        report_data[key] = {"title": title, "content": content}
        all_text_content.append(f"## {title}\n{content}\n\n")

    # Chart Data Attempt
    prompt_chart_data = (
        f"Based on the information gathered for '{topic}', provide data suitable for a simple bar chart or line chart. "
        f"For example, this could be prevalence over a few years (e.g., 3-5 data points), or distribution across 3-5 demographic groups, or risk factor percentages. "
        f"The data should be simple. Present it as a Python-style list of tuples, where each tuple is (label, value). "
        f"Example: Data for chart: [('2020', 1500), ('2021', 1700), ('2022', 1650)]. "
        f"Or: Data for chart: [('Group A', 30), ('Group B', 50), ('Group C', 20)]. "
        f"Make sure the output for this specific request starts with 'Data for chart:' and nothing else before it on that line. "
        f"Provide only one dataset for simplicity."
    )
    print("Fetching chart data...")
    chart_data_raw = get_perplexity_response(prompt_chart_data)

    if "Data for chart:" in chart_data_raw:
        data_str_part = chart_data_raw.split("Data for chart:", 1)[1].strip()
        try:
            start_index = data_str_part.find('[')
            end_index = data_str_part.rfind(']')
            if start_index != -1 and end_index != -1 and end_index > start_index:
                data_list_str = data_str_part[start_index : end_index+1]
                parsed_data = ast.literal_eval(data_list_str)
                
                if isinstance(parsed_data, list) and all(isinstance(item, tuple) and len(item) == 2 for item in parsed_data):
                    labels = [str(item[0]) for item in parsed_data]
                    try:
                        values = [float(item[1]) for item in parsed_data]
                        chart_title = f"Illustrative Data for {topic}"
                        chart_type = 'bar'

                        report_data["charts"].append({
                            "type": chart_type,
                            "title": chart_title,
                            "labels": labels,
                            "datasets": [{"label": topic, "data": values}]
                        })
                        print(f"Successfully parsed chart data for {topic}")
                    except ValueError:
                        print(f"Could not convert all chart values to numbers: {parsed_data}")
                else:
                    print(f"Parsed chart data is not in the expected list of tuples format: {parsed_data}")
            else:
                print(f"Could not extract list structure from chart data string: {data_str_part}")
        except (SyntaxError, ValueError, TypeError) as e:
            print(f"Error parsing chart data using ast.literal_eval: {e}. Raw data part: {data_str_part}")
    else:
        print(f"No 'Data for chart:' block found in response. Raw chart response: {chart_data_raw[:200]}...")

    report_data["full_text_for_follow_up"] = "".join(all_text_content)
    print(f"Finished deep research for topic: {topic}")
    return report_data

async def answer_follow_up_question(question: str, report_context: str) -> str:
    """
    Answers a follow-up question using the report content as context.
    """
    system_prompt_content = (
        "You are an AI assistant. The user has previously received a detailed report. "
        "Now they are asking a follow-up question based on that report. "
        "Use ONLY the provided report context to answer the question accurately and concisely. "
        "If the answer is not in the context, clearly state that the information is not available in the provided report content. "
        "Do not search the web or use external knowledge for this follow-up."
    )
    
    user_prompt_content = (
        f"Here is the context from the report I received:\n\n---\nBEGIN REPORT CONTEXT\n{report_context}\nEND REPORT CONTEXT\n---\n\n"
        f"My follow-up question is: {question}"
    )
    
    print(f"Answering follow-up: '{question[:100]}...'")
    answer = get_perplexity_response(user_prompt_content, system_prompt_content)
    print(f"Follow-up answer: '{answer[:100]}...'")
    return answer