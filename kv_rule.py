import os
import json
import sys
from dotenv import load_dotenv
from openai import OpenAI


# Load .env from the parent directory (adjust path if needed)
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '../../.env'))
#api_key = os.getenv("OPENAI_API_KEY")


def select_dictionary_range(input_dict, start_key, end_key):
    """
    Selects items from a dictionary where the keys are within a specified range.

    Args:
        input_dict (dict): The input dictionary.
        start_key (int): The starting key of the range (inclusive).
        end_key (int): The ending key of the range (inclusive).

    Returns:
        dict: A dictionary containing only the items within the specified range.
    """
    # Filter dictionary items within the range using dictionary comprehension
    selected_items = {key: value for key, value in input_dict.items() if start_key <= int(key) <= end_key}
    print(f"Selected {len(selected_items)} items from page {start_key} to {end_key}.")

    return selected_items


def update_json_if_different(json_file, new_data):
    """
    Updates a JSON file with new data only if it's not already present 
    or if the new data is different from the existing data.

    Args:
        json_file (str): Path to the JSON file.
        new_data (dict): The new dictionary to add or update.

    Returns:
        None
    """
    # Check if the JSON file exists; if not, initialize it as an empty list
    if not os.path.exists(json_file):
        with open(json_file, "w", encoding="utf-8") as file:
            json.dump([], file)  # Start with an empty list

    # Load existing data from the JSON file
    with open(json_file, "r", encoding="utf-8") as file:
        try:
            existing_data = json.load(file)
        except json.JSONDecodeError:
            existing_data = {}  # In case the file is empty or corrupted
        # Check if `new_data` matches any dictionary in `existing_data`
    
    for key, value in new_data.items():
        #print(f"Checking if key '{key}' with value '{value}' exists in the existing data...")
        # Check if the key exists and the value matches in the existing dictionary
        if key in existing_data and existing_data[key] == value:
            #print(f"Key '{key}' with value '{value}' already exists. Skipping...")
            pass
        else:
            # Add or update the key-value pair in the existing dictionary
            #print(f"Key '{key}' with value '{value}' does not exist or is different. Adding/updating...")
            existing_data[key] = value
            #print(f"Key '{key}' with value '{value}' added to the dictionary.")
    with open(json_file, "w", encoding="utf-8") as file:
        json.dump(dict(sorted(existing_data.items())), file, indent=4)
        print("The new data has been added to the JSON file.")
    
    return existing_data



def extract_rules_gpt(page_content_dict, output_json, prompt=None, start_page=1, end_page=2):
    """
    Extract technical terms using OpenAI GPT and their definitions.

    Args:
        page_content_dict (dict): Dictionary containing page content.
        output_json (str): Path to save extracted terms and definitions as JSON.
        prompt (str, optional): Custom prompt for GPT model.
    """

    context = select_dictionary_range(page_content_dict, start_page, end_page)
    #print(context)

    # Initialize the OpenAI client (API key is automatically picked up from OPENAI_API_KEY environment variable)
    client = OpenAI()
    results = {}
    
    for page_number, page_content in context.items():

        # Load text from file
        text = f"\nPage {page_number}\n\n{page_content}" 
        print(f"Processing page {page_number} with content length: {len(text)} characters, and context is {text[:100]}...")  # Print first 100 characters for context
        # Define default prompt if none is provided
        if prompt is None:
            prompt = """You are a knowledgeable assistant specializing in technical terms and definitions. 
                Your task is to extract key terms from the provided text. Here are some examples of key terms: 
                "Aerodynamic, Tractive System, Shutdown System, Accelerator Pedal Position Sensor, Brake Pedal,
                Material properties, material, External Item, Impact Attenuator, Accumulator, Firewall, Powertrain, 
                Catch Cans, Thermal Protection, Scatter Shields, Coolant, Butt Joints/Butt Joint, Inertia Switch, Transponder,
                Brake Over Travel Switch, Wiring, Grounded Low Voltage, Grounding, Lighting, Light". After extracting the key terms,
                write them in json format. {terms}: key terms separated by comma in a list
                """

        # Create a chat completion
        try:
            response = client.responses.create(
                model="gpt-5-nano",  # Specify the model to use
                input=prompt + "\n\n" + text,  # Combine prompt and context
            )

            # Access and print the model's response
            results[page_number] = response.output_text
            print(f"Extracted technical terms for page {page_number}: {results[page_number]}")

        except Exception as e:
            print(f"An error occurred: {e}")

    # Save the results to the output JSON file
    # Call the function to check and update the JSON file
    update_json_if_different(output_json, results)
    # with open(output_json, "w", encoding="utf-8") as json_file:
    #     json.dump(results, json_file, indent=4)
    print(f"Technical terms and definitions extracted using GPT saved to {output_json}")    

def extract_technical_terms_gpt(input_file, output_file, prompt=None,start_page=1,end_page=2):
    """
    Extract technical terms using OpenAI GPT and their definitions.

    Args:
        input_folder (str): Path to the folder containing input JSON files.
        output_folder (str): Path to the folder where output JSON files will be saved.
        prompt (str, optional): Custom prompt for GPT model.
        start_page (int, optional): Starting page number for extraction.
        end_page (int, optional): Ending page number for extraction.
    """
    # Ensure the output file exists
    if not os.path.exists(os.path.dirname(output_file)):
        os.makedirs(os.path.dirname(output_file))

    context = select_dictionary_range(page_content_dict, start_page, end_page)
    #print(context)

    # Initialize the OpenAI client (API key is automatically picked up from OPENAI_API_KEY environment variable)
    client = OpenAI()
    results = {}

    for page_number, page_content in context.items():

        # Load text from file
        text = f"\nPage {page_number}\n\n{page_content}"
        print(f"Processing page {page_number} with content length: {len(text)} characters, and context is {text[:100]}...")  # Print first 100 characters for context
        # Define default prompt if none is provided
        if prompt is None:
            prompt = """You are a knowledgeable assistant specializing in technical terms and definitions.
                Your task is to extract key terms from the provided text. Here are some examples of key terms:
                "Aerodynamic, Tractive System, Shutdown System, Accelerator Pedal Position Sensor, Brake Pedal,
                Material properties, material, External Item, Impact Attenuator, Accumulator, Firewall, Powertrain,
                Catch Cans, Thermal Protection, Scatter Shields, Coolant, Butt Joints/Butt Joint, Inertia Switch, Transponder,
                Brake Over Travel Switch, Wiring, Grounded Low Voltage, Grounding, Lighting, Light". After extracting the key terms,
                write them in json format. {terms}: key terms separated by comma in a list
                """

        # Create a chat completion
        try:
            response = client.responses.create(
                model="gpt-5-nano",  # Specify the model to use
                input=prompt + "\n\n" + text,  # Combine prompt and context
            )

            # Access and print the model's response
            results[page_number] = response.output_text
            print(f"Extracted technical terms for page {page_number}: {results[page_number]}")

        except Exception as e:
            print(f"An error occurred: {e}")

    # Save the results to the output JSON file
    # Call the function to check and update the JSON file
    update_json_if_different(output_json, results)
    # with open(output_json, "w", encoding="utf-8") as json_file:
    #     json.dump(results, json_file, indent=4)
    print(f"Technical terms and definitions extracted using GPT saved to {output_json}")


prompt_rule_extraction = """
"You are tasked with processing a technically formatted document to build a structured lookup table in JSON format. 
The goal is to precisely capture rules, while ensuring accuracy in page numbers and rule numbers for all entries in the lookup table. 
Follow these precise instructions:

Requirements
1. Lookup Table structure
Each rule number in the document serves as a key in the lookup table. 
The corresponding value for each key is a JSON object that captures the following attributes:

Page number: The page number where the information appears. 
Rule number: The rule number itself (extracted directly).
Definition: A verbatim quote of the rule’s description as provided in the document.

2. Requirements for Rule number extraction
Identify and extract the rule number from the start of each line, including the full hierarchical structure (e.g., V.1.2).

3. Example context and Extraction Instructions for definition attribute only
Capture the full definition of the rule verbatim, including all text associated with the rule, until a new rule (marked by another rule number) begins.
Do not omit or modify the rule description in any way.

Example Document Context:
V.1.2 Wheelbase
The vehicle must have a minimum wheelbase of 1525 mm
V.1.3 Vehicle Track
The vehicle’s track width must meet certain requirements for safety.
Expected Extraction for definition attribute only.

For rule V.1.2:
Rule Number: V.1.2
Definition: "Wheelbase\nThe vehicle must have a minimum wheelbase of 1525 mm\n"

For rule V.1.3:
Rule Number: V.1.3
Definition: "Vehicle Track\nThe vehicle’s track width must meet certain requirements for safety."


Output Format
The output should be in JSON format, structured as follows:
Lookup Table for Rules:
{
  "rule_number_1": {
    "page_number": "1",
    "rule_number": "D.2.2.1",
    "definition": "The exact description quoted from the document.",
  },
  "rule_number_2": {
    "page_number": "2",
    "rule_number": "EV.2",
    "definition": "Another quoted description from the document."
  }
}

"""
text_file = '../files/cln_rules.txt'  # Path to the text file containing extracted content
text_json = '../files/cln_rules.json'
output_json = '../files/extracted_rules.json'

with open(text_json, "r", encoding="utf-8") as file:
    # Load the JSON content into a dictionary
    page_content_dict = json.load(file)
    print(f"Loaded {len(page_content_dict)} pages from {text_json}")

# Define the start and end page numbers for extraction
start_page = 16  # Starting page number
end_page = 18  #len(page_content_dict)   # Ending page number
extract_rules_gpt(
    page_content_dict=page_content_dict,
    output_json=output_json,
    prompt=prompt_rule_extraction,
    start_page=start_page,
    end_page=end_page   
)



"""
context = extract_pages_to_text(text_json, start_page, end_page)

please quote the exact definitions for each term from the context. If definition is not available, state none.
If abbreviation is used, please provide the full term as well. The final output structure is json. term: definition

"""

prompt = """
"You are tasked with processing a technically formatted document to build a structured lookup table in JSON format. 
The goal is to precisely capture technical terms and rules, while ensuring accuracy in page numbers and rule numbers for all entries in the lookup table. 
Follow these precise instructions:

Requirements
1. Lookup Table structure
Rule number or technical terms in the document can serve as a key in the lookup table. 
The corresponding value for each key is a JSON object that captures the following attributes:

Page number: The page number where the information appears.
Rule number: The rule number itself (extracted directly).
Definition: A verbatim quote of the rule’s description as provided in the document.
Structure: Any structural details provided in context. eg. shape, size, configuration, connection to other components etc.
Dimension: Any dimensional details provided in context. eg. degree, mm, position, scale, measurement etc.
Material: Any material composition details provided in context. eg. plastic, metal, etc.
Mechanical: Any mechanical properties or details provided in context. eg. tensile strength, hardness, etc.
Electrical: Any electrical properties, such as conductivity or insulation, provided in context.
Thermal: Any thermal properties, such as heat resistance, provided in context. eg. thermal conductivity, specific heat, temperature, etc.
Safety: Any safety-related details (e.g., compliance with regulations, safety features) provided in the immediate context of the rule.
Performance: Any performance-related details (e.g., efficiency, durability) provided in the immediate context of the rule.
Design: Any design-related details (e.g., aesthetics, user interface) provided in the immediate context of the rule.
Cost: Any cost-related details (e.g., pricing, budget constraints) provided in the immediate context of the rule.
Team: Any team-related details (e.g., roles, responsibilities) provided in the immediate context of the rule.

1. Lookup Table structure
Each rule number in the document serves as a key in the lookup table. The corresponding value for each key is a JSON object that captures the following attributes:


2. Lookup Table for Technical Terms
Track all technical terms mentioned in the document. Ensure the following:

Precise Capture:

Record the exact terms as they appear in the document, without modification. For example, if the term appears as "Open Wheel" in the document, retain that exact format in your output.
Do not transform or modify the technical term in any way. Maintain exact casing, punctuation, and formatting.
Accurate Cross-References:

For each term, capture the exact page numbers and rule numbers where it appears.
If the same term is mentioned multiple times on the same page but in different rules, include all applicable rule numbers for that term under that page number.
If the term appears across multiple pages, consolidate its occurrences across all pages and rules.

Example Context and Extraction Instructions for definition attribute only.
Document Context:
V.1.2 Wheelbase
The vehicle must have a minimum wheelbase of 1525 mm
V.1.3 Vehicle Track
The vehicle’s track width must meet certain requirements for safety.
Expected Extraction for definition attribute only.

For rule V.1.2:
Rule Number: V.1.2
Definition: "Wheelbase\nThe vehicle must have a minimum wheelbase of 1525 mm\n"

For rule V.1.3:
Rule Number: V.1.3
Definition: "Vehicle Track\nThe vehicle’s track width must meet certain requirements for safety."

Specific Instructions

Requirements for Rule Extraction
Extract Rule Number:

Identify and extract the rule number from the start of each rule line, including the full hierarchical structure (e.g., V.1.2). 
Treat each rule number as a unique identifier (key) in the lookup table. Include the {page_number: [rule_numbers]} construct in the page_number attribute to capture where the rule is located.
Extract Definition:

Capture the full definition of the rule verbatim, including all text associated with the rule, until a new rule (marked by another rule number) begins.
Do not omit or modify the rule description in any way.
Record Attributes:

For each rule, extract and record the following attributes if they are explicitly provided in the document:

Quote the rule description verbatim as the definition field. Populate other fields (e.g., structure, dimension, material) 
with details provided in the immediate page context, ensuring no inferred information is added. Leave fields empty if details are not explicitly provided.

Extract and Correlate Technical Terms

Extract the precise technical terms as mentioned in the document, preserving formatting, punctuation, and case (e.g., "Open Wheel" instead of "TERM_OPEN_WHEEL").
Avoid modifications or unnecessary transformations to the original term.
Track Occurrences Across Pages and Rules:

Note the specific page numbers and rule numbers where each term appears.
If a term appears on the same page in multiple rules, include all relevant rule numbers for that page.
Attribute Extraction:

Beyond page and rule references, capture other term-related attributes such as definitions, dimensions, structure, material, or performance only when explicitly provided in the document.
Context-Based Extraction
Process the document contextually one page at a time:

Extract rules and technical terms from the specific page you're working on.
When processing technical terms, consolidate details across all rules and pages where they appear, with precise page and rule references.

Output Format
The output should be in JSON format, structured as follows:
Lookup Table for Rules:
{
  "rule_number_1": {
    "page_numbers": {"1": ["D.2.2.1"]},
    "definition": "The exact description quoted from the document.",
    "structure": "",
    "dimension": "",
    "material": "",
    "mechanical": "",
    "electrical": "",
    "thermal": "",
    "safety": "",
    "performance": "",
    "design": "",
    "cost": "",
    "team": ""
  },
  "rule_number_2": {
    "page_numbers": {"2": ["EV.2"]},
    "definition": "Another quoted description from the document.",
    "structure": "Describes the structure.",
    "dimension": "20x30 cm",
    "material": "Aluminum",
    "mechanical": "",
    "electrical": "",
    "thermal": "Resistant to 1200°C",
    "safety": "Includes reinforced zones for impact protection.",
    "performance": "Ensures stability   ",
    "design": "Aerodynamic shape optimized for airflow.",
    "cost": "Moderate production costs due to advanced materials.",
    "team": "Cross-functional team with expertise in aerodynamics, materials science, and manufacturing."

  }
}
Lookup Table for Technical Terms:
{
  "Open Wheel": {
    "page_numbers": {
      "2": ["rule_number_5", "rule_number_8"],
      "4": ["rule_number_12"]
    },
    "definition": "A vehicle configuration with exposed wheels outside the chassis frame.",
    "structure": "Describes the framework surrounding the exposed wheel assembly.",
    "dimension": "Wheel diameter: 18 inches.",
    "material": "High-strength carbon fiber.",
    "mechanical": "Supports suspension components connected to the wheel.",
    "electrical": "",
    "thermal": "",
    "safety": "Includes reinforced zones for impact protection.",
    "performance": "Optimized for reducing drag at high speeds.",
    "design": "Aerodynamic shape optimized for airflow.",
    "cost": "Moderate production costs due to advanced materials.",
    "team": "Cross-functional team with expertise in aerodynamics, materials science, and manufacturing."
  },
  "Chassis": {
    "definition": "The structural backbone of the vehicle.",
    "page_numbers": {
      "2": ["rule_number_3"],
      "5": ["rule_number_9", "rule_number_11"]
    },
    "structure": "Supports mechanical, electrical, and thermal systems.",
    "dimension": "Width: 1.2 meters; Length: 2.5 meters.",
    "material": "Aluminum alloy.",
    "mechanical": "Ensures structural rigidity during operation.",
    "electrical": "",
    "thermal": "Includes heat-resistant zones for high-temperature components.",
    "safety": "Includes reinforced zones for impact protection.",
    "performance": "Designed for durability under load conditions.",
    "design": "Sleek and modern aesthetic with functional elements.",
    "cost": "Cost-effective manufacturing processes implemented.",
    "team": "Dedicated team focusing on structural integrity and safety."
  }
}
Measurement: the type of measurement where numerical value is provided in definition. {dimension:deg or mm, material: Aluminum, mechanical: MPa or N, electrical: V or Ohm or A, Thermal: C}, 
if numerical value is not present, state NONE for dimension, mechanical, function, and temperature.

4. Special Instructions for deciding the type of measurement based on the content of the definition.

- If the definition describes a general requirement without a specific measurement or numerical value, classify the measurement type as "NONE".
- If the definition includes a specific measurement or property or function or temperature (e.g., "1525 mm", "tensile strength of 300 MPa", "input force of 2000 N", "resistor value of 3kOhm "operating temperature of 100°C"), 
extract the value and its unit. If more than one measurement is available for a single definition, include all relevant measurements in the output.

"""