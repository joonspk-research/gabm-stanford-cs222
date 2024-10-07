import json
import re


def extract_first_json_dict(input_str):
  try:
    # Replace curly quotes with standard double quotes
    input_str = (input_str.replace("“", "\"")
                          .replace("”", "\"")
                          .replace("‘", "'")
                          .replace("’", "'"))
    
    # Find the first occurrence of '{' in the input_str
    start_index = input_str.index('{')
    
    # Initialize a count to keep track of open and close braces
    count = 1
    end_index = start_index + 1
    
    # Loop to find the closing '}' for the first JSON dictionary
    while count > 0 and end_index < len(input_str):
        if input_str[end_index] == '{':
            count += 1
        elif input_str[end_index] == '}':
            count -= 1
        end_index += 1
    
    # Extract the JSON substring
    json_str = input_str[start_index:end_index]
    
    # Parse the JSON string into a Python dictionary
    json_dict = json.loads(json_str)
    
    return json_dict
  except ValueError:
    # Handle the case where the JSON parsing fails
    return None



def extract_first_json_dict_categorical(input_str): 
  reasoning_pattern = r'"Reasoning":\s*"([^"]+)"'
  response_pattern = r'"Response":\s*"([^"]+)"'

  reasonings = re.findall(reasoning_pattern, input_str)
  responses = re.findall(response_pattern, input_str)

  return responses, reasonings


def extract_first_json_dict_numerical(input_str): 
  reasoning_pattern = re.compile(r'"Reasoning":\s*"([^"]+)"')
  response_pattern = re.compile(r'"Response":\s*(\d+\.?\d*)')

  reasonings = reasoning_pattern.findall(input_str)
  responses = response_pattern.findall(input_str)
  return responses, reasonings
  

if __name__ == '__main__':
  input_str = """```json
{
  "1": {
    "Q": "What is your age",
    "Range Interpretation": {
      "0-20": "This range might be chosen by a younger individual, perhaps still in school or at the beginning of their adult life, with limited life experiences.",
      "21-40": "This range could represent a young adult who is likely to be navigating early career choices, relationships, and personal growth, perhaps reflecting a balance of youthful energy and emerging responsibility.",
      "41-60": "Individuals in this range might be more established in their careers and personal lives, with a focus on family, stability, and long-term goals.",
      "61-89": "This range typically represents older adults who may be reflecting on their life achievements, perhaps transitioning into retirement or seeking legacy opportunities."
    },
    "Reasoning": "Given that Adam was born on August 17, 1981, he is currently 42 years old. This fits him into the 41-60 age range as he is navigating adulthood with various responsibilities and aspirations.",
    "Response": 42.2
  },
  "2": {
    "Q": "What is your favorite number",
    "Range Interpretation": {
      "0-20": "A person who chooses a number in this range may value simplicity or childhood nostalgia, often connecting with numbers that have personal significance or represent fun memories.",
      "21-40": "Individuals selecting numbers in this range might be more reflective or strategic, possibly linking the number to achievements, milestones, or personal preferences that resonate with their current life stage.",
      "41-60": "Choosing a number in this range could signify a deeper connection to life experiences, representing significant moments or values that have been shaped over time.",
      "61-89": "This range may reflect a person's wisdom or experience, often selecting numbers that represent longevity, stability, or historical significance."
    },
    "Reasoning": "Adam did not explicitly mention a favorite number in the interview, but given his age and background, he may choose a number that reflects a significant moment in his life or resonates with him personally. However, since he did not express a strong inclination toward any specific number, a middle-ground number might be a reasonable prediction.",
    "Response": 33
  }
}
```
  """
  extract_first_json_dict_numerical(input_str)

