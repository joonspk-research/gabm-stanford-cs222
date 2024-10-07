import random
import json
import string
import csv
import time
import datetime as dt
import pathlib
import os
import sys
import numpy
import math
import shutil, errno
import base64

from PyPDF2 import PdfReader
from os import listdir


def create_folder_if_not_there(curr_path): 
  """
  Checks if a folder in the curr_path exists. If it does not exist, creates
  the folder. 
  Note that if the curr_path designates a file location, it will operate on 
  the folder that contains the file. But the function also works even if the 
  path designates to just a folder. 
  Args:
    curr_list: list to write. The list comes in the following form:
               [['key1', 'val1-1', 'val1-2'...],
                ['key2', 'val2-1', 'val2-2'...],]
    outfile: name of the csv file to write    
  RETURNS: 
    True: if a new folder is created
    False: if a new folder is not created
  """
  outfolder_name = curr_path.split("/")
  if len(outfolder_name) != 1: 
    # This checks if the curr path is a file or a folder. 
    if "." in outfolder_name[-1]: 
      outfolder_name = outfolder_name[:-1]

    outfolder_name = "/".join(outfolder_name)
    if not os.path.exists(outfolder_name):
      os.makedirs(outfolder_name)
      return True

  return False 


def write_list_of_list_to_csv(curr_list_of_list, outfile):
  """
  Writes a list of list to csv. 
  Unlike write_list_to_csv_line, it writes the entire csv in one shot. 
  ARGS:
    curr_list_of_list: list to write. The list comes in the following form:
               [['key1', 'val1-1', 'val1-2'...],
                ['key2', 'val2-1', 'val2-2'...],]
    outfile: name of the csv file to write    
  RETURNS: 
    None
  """
  create_folder_if_not_there(outfile)
  with open(outfile, "w") as f:
    writer = csv.writer(f)
    writer.writerows(curr_list_of_list)


def write_list_to_csv_line(line_list, outfile): 
  """
  Writes one line to a csv file.
  Unlike write_list_of_list_to_csv, this opens an existing outfile and then 
  appends a line to that file. 
  This also works if the file does not exist already. 
  ARGS:
    curr_list: list to write. The list comes in the following form:
               ['key1', 'val1-1', 'val1-2'...]
               Importantly, this is NOT a list of list. 
    outfile: name of the csv file to write   
  RETURNS: 
    None
  """
  create_folder_if_not_there(outfile)

  # Opening the file first so we can write incrementally as we progress
  curr_file = open(outfile, 'a',)
  csvfile_1 = csv.writer(curr_file)
  csvfile_1.writerow(line_list)
  curr_file.close()


def read_file_to_list(curr_file, header=False, strip_trail=True): 
  """
  Reads in a csv file to a list of list. If header is True, it returns a 
  tuple with (header row, all rows)
  ARGS:
    curr_file: path to the current csv file. 
  RETURNS: 
    List of list where the component lists are the rows of the file. 
  """
  if not header: 
    analysis_list = []
    with open(curr_file) as f_analysis_file: 
      data_reader = csv.reader(f_analysis_file, delimiter=",")
      for count, row in enumerate(data_reader): 
        if strip_trail: 
          row = [i.strip() for i in row]
        analysis_list += [row]
    return analysis_list
  else: 
    analysis_list = []
    with open(curr_file) as f_analysis_file: 
      data_reader = csv.reader(f_analysis_file, delimiter=",")
      for count, row in enumerate(data_reader): 
        if strip_trail: 
          row = [i.strip() for i in row]
        analysis_list += [row]
    return analysis_list[0], analysis_list[1:]


def read_file_to_set(curr_file, col=0): 
  """
  Reads in a "single column" of a csv file to a set. 
  ARGS:
    curr_file: path to the current csv file. 
  RETURNS: 
    Set with all items in a single column of a csv file. 
  """
  analysis_set = set()
  with open(curr_file) as f_analysis_file: 
    data_reader = csv.reader(f_analysis_file, delimiter=",")
    for count, row in enumerate(data_reader): 
      analysis_set.add(row[col])
  return analysis_set


def get_row_len(curr_file): 
  """
  Get the number of rows in a csv file 
  ARGS:
    curr_file: path to the current csv file. 
  RETURNS: 
    The number of rows
    False if the file does not exist
  """
  try: 
    analysis_set = set()
    with open(curr_file) as f_analysis_file: 
      data_reader = csv.reader(f_analysis_file, delimiter=",")
      for count, row in enumerate(data_reader): 
        analysis_set.add(row[0])
    return len(analysis_set)
  except: 
    return False


def check_if_file_exists(curr_file): 
  """
  Checks if a file exists
  ARGS:
    curr_file: path to the current csv file. 
  RETURNS: 
    True if the file exists
    False if the file does not exist
  """
  try: 
    with open(curr_file) as f_analysis_file: pass
    return True
  except: 
    return False


def find_filenames(path_to_dir, suffix=".csv"):
  """
  Given a directory, find all files that ends with the provided suffix and 
  returns their paths.  
  ARGS:
    path_to_dir: Path to the current directory 
    suffix: The target suffix.
  RETURNS: 
    A list of paths to all files in the directory. 
  """
  filenames = listdir(path_to_dir)
  new_filenames = []
  for i in filenames: 
    if ".DS_Store" not in i: 
      new_filenames += [i]
  filenames = new_filenames
  return [ path_to_dir+"/"+filename 
           for filename in filenames if filename.endswith( suffix ) ]


def average(list_of_val): 
  """
  Finds the average of the numbers in a list.
  ARGS:
    list_of_val: a list of numeric values  
  RETURNS: 
    The average of the values
  """
  try: 
    list_of_val = [float(i) for i in list_of_val if not math.isnan(i)]
    return sum(list_of_val)/float(len(list_of_val))
  except: 
    return float('nan')


def std(list_of_val): 
  """
  Finds the std of the numbers in a list.
  ARGS:
    list_of_val: a list of numeric values  
  RETURNS: 
    The std of the values
  """
  try: 
    list_of_val = [float(i) for i in list_of_val if not math.isnan(i)]
    std = numpy.std(list_of_val)
    return std
  except: 
    return float('nan')


def copyanything(src, dst):
  """
  Copy over everything in the src folder to dst folder. 
  ARGS:
    src: address of the source folder  
    dst: address of the destination folder  
  RETURNS: 
    None
  """
  try:
    shutil.copytree(src, dst)
  except OSError as exc: # python >2.5
    if exc.errno in (errno.ENOTDIR, errno.EINVAL):
      shutil.copy(src, dst)
    else: raise


def generate_alphanumeric_string(length):
  characters = string.ascii_letters + string.digits
  result = ''.join(random.choice(characters) for _ in range(length))
  return result


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


def read_file_to_string(file_path):
  try:
    with open(file_path, 'r', encoding='utf-8') as file:
      content = file.read()
    return content
  except FileNotFoundError:
    return "The file was not found."
  except Exception as e:
    return str(e)


def write_string_to_file(full_path, text_content):
  create_folder_if_not_there(full_path)
  import os
  try:
    with open(full_path, 'w', encoding='utf-8') as file:
        file.write(text_content)
    return f"File successfully written to {full_path}"
  except Exception as e:
    return str(e)


def chunk_list(lst, q_chunk_size):
  """
  Splits the given list into sublists of specified chunk size.

  Parameters:
  lst (list): The list to be split into chunks.
  q_chunk_size (int): The size of each chunk.

  Returns:
  list: A list of sublists where each sublist has a length of q_chunk_size.
  """
  # Initialize the result list
  chunked_list = []
  
  # Loop through the list in steps of q_chunk_size
  for i in range(0, len(lst), q_chunk_size):
    # Append the sublist to the result list
    chunked_list.append(lst[i:i + q_chunk_size])

  return chunked_list


def write_dict_to_json(data, filename):
    """
    Writes a dictionary to a JSON file.

    Parameters:
    data (dict): The dictionary to write to the JSON file.
    filename (str): The name of the file to write the JSON data to.
    """
    create_folder_if_not_there(filename)
    try:
        with open(filename, 'w') as json_file:
            json.dump(data, json_file, indent=4)
        # print(f"Dictionary successfully written to {filename}")
    except Exception as e:
        print(f"An error occurred: {e}")


def read_json_to_dict(file_path):
    """
    Reads a JSON file and converts it to a Python dictionary.

    Parameters:
    file_path (str): The path to the JSON file.

    Returns:
    dict: The content of the JSON file as a dictionary.
    """
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
        return data
    except FileNotFoundError:
        print(f"The file at {file_path} was not found.")
    except json.JSONDecodeError:
        print(f"Error decoding JSON from the file at {file_path}.")
    except Exception as e:
        print(f"An error occurred: {e}")


# Your function to append data to an existing JSON
def append_to_json(record_json, new_ret):
    # Create the folder if it doesn't exist
    create_folder_if_not_there(record_json)
    
    # Check if the JSON file already exists
    if os.path.exists(record_json):
        # Load existing data
        with open(record_json, 'r') as json_file:
            existing_data = json.load(json_file)
        # Merge existing data with the new data
        existing_data.update(new_ret)
    else:
        # No existing data, just use new_ret
        existing_data = new_ret
    
    # Write updated data back to the JSON file
    with open(record_json, 'w') as json_file:
        json.dump(existing_data, json_file, indent=4)

def extract_text_from_pdf(pdf_content):
  pdf_file = io.BytesIO(base64.b64decode(pdf_content))
  pdf_reader = PdfReader(pdf_file)
  text = ""
  for page in pdf_reader.pages:
    text += page.extract_text() + "\n"
  return text


if __name__ == '__main__':
  pass



















































