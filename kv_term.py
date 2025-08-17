import os
import json
import sys
from dotenv import load_dotenv
from openai import OpenAI
from collections import defaultdict


# Load .env from the parent directory (adjust path if needed)
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '../../.env'))
#api_key = os.getenv("OPENAI_API_KEY")    


def add_rule_numbers_to_terms(terms_dict, rule_number):
    """
    Adds the rule number as a sub-dictionary for each term in the 'technical_terms' list.

    Args:
        terms_dict (dict): Dictionary containing a list of technical terms under the key 'technical_terms'.
                           Example: {"technical_terms": ["track", "center of gravity", "rollover stability"]}
        rule_number (str): The rule number to associate with each term.
                           Example: "V.1.3"

    Returns:
        dict: Transformed dictionary where each term maps to the rule number as a sub-dictionary.
              Example: {"technical_terms": {"track": "V.1.3", "center of gravity": "V.1.3", "rollover stability": "V.1.3"}}
    """
    print(f"Adding rule number {rule_number} to terms: {terms_dict}")
    technical_terms = terms_dict.get("technical_terms", [])
    # Ensure technical_terms is a list
    if not isinstance(technical_terms, list):
        print(f"Warning: technical_terms is not a list. Value: {technical_terms}")
        technical_terms = [] if technical_terms == "NONE" else [technical_terms]
    print(f"Adding rule number {rule_number} to terms: {technical_terms}")

    # Transform the terms list into a dictionary with rule_number
    transformed_terms = dict((term, rule_number) for term in technical_terms)

    return {"technical_terms": transformed_terms}


def add_rule_number_to_measurements(data_dict, rule_number):
    """
    Adds a 'rule#' field to each parameter dictionary in the provided data dictionary.

    Args:
        data_dict (dict): The input dictionary containing parameter data.
                          Example Format:
                          {
                              "parameter1": { "type": "power", "component": "motor", ... },
                              "parameter2": { "type": "voltage", "component": "motor", ... }
                          }
        rule_number (str): The rule number to add to each parameter.
                           Example: "V.1.2"

    Returns:
        dict: Updated dictionary with 'rule#' added to each parameter.
    """
    # Iterate through each key-value pair in the input dictionary
    for key, value in data_dict.items():
        # Add 'rule#' field to the inner dictionary
        value["rule#"] = rule_number

    return data_dict


def extract_details(input_file, output_file, prompt_term_extraction, prompt_measurement_extraction, start_page=1, end_page=2):
    """
    Reads a JSON file structured as:
    {
        "page#": {
            "rule#": {
                "page_number": "",
                "rule_number": "",
                "definition": ""
            }
        }
    }
    Extracts the definitions for each rule on each page.
    Args:
        json_file (str): The path to the JSON file.
    Returns:
        dict: A dictionary containing page-wise extracted rule definitions as:
        {
            "page#": {
                "rule#": "definition"
            }
        }
    """
    # Load the JSON file
    with open(input_file, 'r') as file:
        data = json.load(file)

    # Prepare a dictionary to hold extracted definitions
    extracted_definitions = {}

    # Iterate through pages and rules
    for page, rules in data.items():
        # Extract page number from the key
        page_number = int(page)

        # Process only pages within the specified range
        if start_page <= page_number <= end_page:
            # If rules is a string, try to parse it as JSON
            if isinstance(rules, str):
                try:
                    rules = json.loads(rules)
                except json.JSONDecodeError:
                    print(f"Warning: Could not decode rules for page {page}")
                    continue
            print(f'Processing page: {page_number}, and rules: {type(rules)}')

            for rule, details in rules.items():
                print(f'Processing rule: {rule} on page: {page_number}, with details: {details}')
                # Extract the rule definition
                definition = details.get("definition", "")
                # Find technical terms and measurements in the definition
                terms = invoke_llm(definition, prompt=prompt_term_extraction)
                measurements = invoke_llm(definition, prompt=prompt_measurement_extraction)
                # If terms is a string, convert it to a dictionary
                if isinstance(terms, str):
                    try:
                        terms = json.loads(terms)
                        measurements = json.loads(measurements)
                    except json.JSONDecodeError:
                        print(f"Warning: Could not decode terms for rule {rule}")
                        continue
                # Add the rule number to the terms dictionary
                terms = add_rule_numbers_to_terms(terms, rule)
                measurements = add_rule_number_to_measurements(measurements, rule)
                #print(f"Updated terms for rule {rule}: {terms}")
                print(f"Updated measurements for rule {rule}: {measurements}")
                # Store the extracted definition and terms in the output dictionary
                details["terms"] = terms["technical_terms"]
                details["measurements"] = measurements
                
                if isinstance(data[page], str):
                    try:
                        data[page] = json.loads(data[page])
                    except json.JSONDecodeError:
                        print(f"Warning: Could not decode rules for page {page}")
                data[page][rule] = details
                #measurements = find_measurements(definition)
                #details["measurements"] = measurements
        #print(f"the updated JSON structure is: {data}")
    # Save the updated JSON with terms added
    with open(output_file, 'w') as file:
        json.dump(data, file, indent=4)
        print(f"Updated JSON file with technical terms saved as {output_file}")

    return data


def invoke_llm(text, prompt):
    """
    Find technical terms in the extracted definitions.
    Args:
        extracted_definitions (dict): The extracted definitions dictionary.
    Returns:
        dict: A dictionary containing the found technical terms.
    """
    # If the input is a string, treat it as a single text block
    text = text.strip()
    #print(context)

    # Initialize the OpenAI client (API key is automatically picked up from OPENAI_API_KEY environment variable)
    client = OpenAI()
    results = {}
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
        results = response.output_text
        print(f"Extracted results are {results}")
        try:
            results_dict = json.loads(results)
        except json.JSONDecodeError:
            print("Warning: Could not decode results as JSON.")
            results_dict = {}

    except Exception as e:
        print(f"An error occurred: {e}")

    return results_dict



def extract_term_as_key(input_file, output_file):
    """
    Processes a JSON structure to concatenate rule numbers for each term across all pages,
    and add a summary structure to the JSON file.

    Args:
        input_file (str): Path to the input JSON file.
        output_file (str): Path where the processed JSON will be written.
    """
    # Read the JSON file
    with open(input_file, 'r') as file:
        data = json.load(file)

    # Initialize dictionary to hold term-wise concatenated structure
    concatenated_terms = defaultdict(lambda: {"pages": set(), "rules": set()})
    
    # Iterate through pages and rules to build the concatenated term dictionary
    for page, page_data in data.items():
        if isinstance(page_data, str):
            try:
                page_data = json.loads(page_data)
            except json.JSONDecodeError:
                print(f"Warning: Could not decode page data for page {page}")
                continue
            print(f'Processing page: {page}, and rules: {type(page_data)}')
        for key, rule_data in page_data.items():
            page_number = rule_data.get("page#", page)
            rule_number = rule_data.get("rule#", "")
            definition = rule_data.get("definition", "")
            terms = rule_data.get("terms", {})

            for term, rule in terms.items():
                concatenated_terms[term]["pages"].add(page_number)
                concatenated_terms[term]["rules"].add(rule_number)
                concatenated_terms[term]["definition"] = definition  # Overwrite with latest definition

    # Convert sets to lists for JSON serialization immediately after population
    for term in concatenated_terms:
        concatenated_terms[term]["pages"] = list(concatenated_terms[term]["pages"])
        concatenated_terms[term]["rules"] = list(concatenated_terms[term]["rules"])

    # Add the concatenated term structure back to the original data under a new key
    summary = {
        page: {
            term: {
                "page#": term_data["pages"],
                "rule#": term_data["rules"],
                "definition": term_data["definition"],
                "terms": {term: term_data["rules"]}  # Nested structure
            }
            for term, term_data in concatenated_terms.items()
        }
        for page in data.keys()
    }
    data.update(summary)

    # Write the updated JSON to a new file
    with open(output_file, 'w') as file:
        json.dump(data, file, indent=4)


prompt_term_extraction = """
Perform Named Entity Recognition (NER) to extract cleaned technical terms from the provided rule definitions. 
These technical terms include domain-specific words or concepts, but any descriptive terms 
(e.g., "small", "large", "inner", "outer", "front", "rear", "side", "top", "bottom", "four", "three", "two", "left", "right") or measurement-related terms (e.g., "diameter", "stress", 
"temperature", "force") must be removed. The output should list only concise, relevant terms related to systems and components. 
Extract the terms exactly as they appear in the definitions, including abbreviations alongside 
their full names when present. Some examples of technical terms are:

Aerodynamic, Tractive System, Shutdown System, Accelerator Pedal Position Sensor, Brake Pedal, 
Material Properties, Material, External Item, Impact Attenuator, Accumulator, Firewall, Powertrain, 
Catch Cans, Thermal Protection, Scatter Shields, Coolant, Butt Joints/Butt Joint, Inertia Switch, 
Transponder, Brake Over Travel Switch, Wiring, Grounded Low Voltage, Grounding, Lighting, Light. 

If a definition contains technical terms, return the extracted terms. If no technical terms are present,
state NONE explicitly.

Input Format:
"Definition text"

Extract the technical terms directly from the "definition" field.

Examples:
Input:
"Wheelbase\nThe vehicle must have a minimum wheelbase of 1525 mm."

Output:
{"technical_terms": ["Wheelbase"]}

Input:
"The track and center of gravity must combine to provide sufficient rollover stability. See IN.9.2."
Output:
{"technical_terms": ["Rollover Stability"]}

Input:
 "There are no specific technical terms in this rule."
Output:

{"technical_terms": "NONE"}

Workflow:
Evaluate the content of the "definition" field for each rule to identify technical terms.
Use your training or predefined knowledge to match technical terms explicitly mentioned in the definition.
Ensure that terms related to systems, components, material, structural, mechanical or electrical concepts are identified.
If a definition contains no identifiable technical terms, return "technical_terms": "NONE".
Notes for the Model:
Focus on domain-specific language.
Technical terms may be single words (e.g., wheelbase, coolant) or short phrases (e.g., rollover stability, accelerator pedal position sensor).
Ignore general terms unless they are part of technical phrases or concepts.
Ensure capitalization for proper named entities as appropriate.
Advanced Notes:
Order Consistency:
Technical terms in the output list should follow the order in which they appear in the definition.
Singular vs. Plural:
Preserve the exact form (singular or plural) as written in the definition.
Accuracy:
Avoid including general terms unless they are part of recognized technical terms
(e.g., include "Catch Cans", not just "Cans").
Abbreviation Clarity:
If a definition includes both the full name and an abbreviation (e.g., “Grounded Low Voltage (GLV)”), extract both terms together (e.g., Grounded Low Voltage (GLV)).
"""

prompt_measurement_extraction = """
You are given a piece of text describing a technical or engineering definition that potentially 
includes numerical data. Your goal is to analyze the text and extract relevant numerical information.
If numerical values are present without any associated units or clear context, do not include them in the output for dimensional measurements. 
Follow these specific instructions:

Dimensional Measurements:
Includes lengths, angles, diameters, radii, areas, thicknesses, etc. Extract only if numerical values are 
accompanied by recognized units, such as mm, cm, m, °, deg, rad, etc.
If no unit is present, ignore the value for this category.
Output in the following dictionary structure:
{
    "dimension1": {
        "type": "dimension_type",   # Example: "angle", "length", "area", "diameter"
        "component": ["component1", "component2"], # Components the value applies to
        "value": "numerical_value", # Example: "80"
        "unit": "unit"              # Example: "deg"
    }
}
json

Material or Physical Properties:
Includes material properties such as Young's modulus, yield strength, thermal conductivity, etc.
Output in the following dictionary structure:
{
    "property1": {
        "type": "property_type",                 # Example: "Young's modulus", "thermal conductivity"
        "component": "component_name",          # Example: "aluminum tubing"
        "material": "material_used",            # Example: "aluminum alloy 6061-T6"
        "welded": "yes/no",                     # Specify if welded (if applicable)
        "value": "numerical_value",             # Example: "69"
        "unit": "unit"                          # Example: "GPa"
    }
}
json

System Parameters:
Includes force, resistance, temperature, current, voltage, power, etc.
Output in the following dictionary structure:
{
    "parameter1": {
        "type": "parameter_type",               # Example: "force", "voltage"
        "component": "component_name",          # Example: "pedal slates"
        "criteria": "criteria_context",         # Example: "minimum", "maximum", "nominal"
        "value": "numerical_value",             # Example: "500"
        "unit": "unit"                          # Example: "N"
    }
}
json

Output Requirements:

Identify Numerical Values:

Detect all numerical values in the text and their associated context.
Group the values into one of the three categories based on their usage.
Structured Output in JSON Format:

Return all extracted information in the specified JSON format.
Ensure each entry in the output is labeled sequentially (e.g., "dimension1", "property1", "parameter1").
Clarify Missing Information:

If certain details (e.g., material, criteria) are missing in the text, leave their value as an empty string ("").
Examples:
Example 1
Input Text:
"The top 180° of the wheels/tires must be unobstructed when viewed from vertically above the wheel. The structural steel tubing has a yield strength of 250 MPa and a Young's modulus of 210 GPa."

Output:

{
    "dimension1": {
        "type": "angle",
        "component": ["wheels", "tires"],
        "value": "180",
        "unit": "deg"
    },
    "property1": {
        "type": "yield strength",
        "component": "structural steel tubing",
        "material": "structural steel",
        "welded": "",
        "value": "250",
        "unit": "MPa"
    },
    "property2": {
        "type": "Young's modulus",
        "component": "structural steel tubing",
        "material": "structural steel",
        "welded": "",
        "value": "210",
        "unit": "GPa"
    }
}

Example 2
Input Text:
"The accelerator pedal's force must be at least 500 N. The resistance across the battery terminals is 0.05 ohms under normal operating conditions."

Output:

{
    "parameter1": {
        "type": "force",
        "component": "accelerator pedal",
        "criteria": "minimum",
        "value": "500",
        "unit": "N"
    },
    "parameter2": {
        "type": "resistance",
        "component": "battery terminals",
        "criteria": "nominal",
        "value": "0.05",
        "unit": "ohms"
    }
}

Example 3
Input Text:
"The diameter of the aluminum tubing is 25 mm, and its thickness is 1.5 mm. 
It is made of aluminum alloy 6061-T6, which is not welded and has a thermal conductivity of 167 W/m·K."
Output:
{
    "dimension1": {
        "type": "diameter",
        "component": ["aluminum tubing"],
        "value": "25",
        "unit": "mm"
    },
    "dimension2": {
        "type": "thickness",
        "component": ["aluminum tubing"],
        "value": "1.5",
        "unit": "mm"
    },
    "property1": {
        "type": "thermal conductivity",
        "component": "aluminum tubing",
        "material": "aluminum alloy 6061-T6",
        "welded": "no",
        "value": "167",
        "unit": "W/m·K"
    }
}


Workflow:
Text Parsing:

Parse the input text and identify numerical values along with their context.
Classification:

Determine whether the numerical value describes:
Dimensional Measurements: Lengths, angles, diameters, areas, etc.
Physical Properties: Material properties like Young's modulus, yield strength, thermal conductivity, etc.
System Parameters: Values related to forces, currents, voltages, etc.
Context Extraction:

Extract additional details such as type, component, material, criteria, and other relevant fields depending on the category.
Output Construction:

Populate the structured dictionary for each identified numerical value with all extracted details, following the specified format.
Validation:

Ensure units and values are correctly assigned, and missing fields are set to "" where applicable.
Final Notes:

Use exact wording and capitalization for parameter, property, and dimensional names as they appear in the text.
Include all components and contextual details associated with the numerical values.
Ensure the output adheres strictly to the JSON format examples for consistency.

"""
input_file = '../files/extracted_rules.json'
output_file = '../files/processed_rules.json'
output_file_with_terms = '../files/processed_rules_with_terms.json'

# Define the start and end page numbers for extraction
start_page = 16  # Starting page number
end_page = 140  #len(page_content_dict)   # Ending page number
extract_details(
    input_file=input_file,
    output_file=output_file,
    prompt_term_extraction=prompt_term_extraction,
    prompt_measurement_extraction=prompt_measurement_extraction,
    start_page=start_page,
    end_page=end_page   
)

#process_json(output_file, output_file_with_terms)
