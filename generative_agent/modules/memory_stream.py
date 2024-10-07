from typing import List, Dict, Any, Tuple, Union, Optional
import random
import string

from numpy import dot
from numpy.linalg import norm

from simulation_engine.settings import * 
from simulation_engine.global_methods import *
from simulation_engine.gpt_structure import *
from simulation_engine.llm_json_parser import *


def cos_sim(a: List[float], b: List[float]) -> float:
  """
  This function calculates the cosine similarity between two input vectors 
  'a' and 'b'. Cosine similarity is a measure of similarity between two 
  non-zero vectors of an inner product space that measures the cosine 
  of the angle between them.

  Parameters: 
    a: 1-D array object 
    b: 1-D array object 
  Returns: 
    A scalar value representing the cosine similarity between the input 
    vectors 'a' and 'b'.
  
  Example: 
    >>> a = [0.3, 0.2, 0.5]
    >>> b = [0.2, 0.2, 0.5]
    >>> cos_sim(a, b)
  """
  return dot(a, b)/(norm(a)*norm(b))


def normalize_dict_floats(d: Dict[Any, float], 
                          target_min: float, 
                          target_max: float) -> Dict[Any, float]:
  """
  This function normalizes the float values of a given dictionary 'd' between 
  a target minimum and maximum value. The normalization is done by scaling the
  values to the target range while maintaining the same relative proportions 
  between the original values.

  Parameters: 
    d: Dictionary. The input dictionary whose float values need to be 
       normalized.
    target_min: Integer or float. The minimum value to which the original 
                values should be scaled.
    target_max: Integer or float. The maximum value to which the original 
                values should be scaled.
  Returns: 
    d: A new dictionary with the same keys as the input but with the float
       values normalized between the target_min and target_max.

  Example: 
    >>> d = {'a':1.2,'b':3.4,'c':5.6,'d':7.8}
    >>> target_min = -5
    >>> target_max = 5
    >>> normalize_dict_floats(d, target_min, target_max)
  """
  min_val = min(val for val in d.values())
  max_val = max(val for val in d.values())
  range_val = max_val - min_val

  if range_val == 0: 
    for key, val in d.items(): 
      d[key] = (target_max - target_min)/2
  else: 
    for key, val in d.items():
      d[key] = ((val - min_val) * (target_max - target_min) 
                / range_val + target_min)
  return d


def top_highest_x_values(d: Dict[Any, float], x: int) -> Dict[Any, float]:
  """
  This function takes a dictionary 'd' and an integer 'x' as input, and 
  returns a new dictionary containing the top 'x' key-value pairs from the 
  input dictionary 'd' with the highest values.

  Parameters: 
    d: Dictionary. The input dictionary from which the top 'x' key-value pairs 
       with the highest values are to be extracted.
    x: Integer. The number of top key-value pairs with the highest values to
       be extracted from the input dictionary.
  Returns: 
    A new dictionary containing the top 'x' key-value pairs from the input 
    dictionary 'd' with the highest values.
  
  Example: 
    >>> d = {'a':1.2,'b':3.4,'c':5.6,'d':7.8}
    >>> x = 3
    >>> top_highest_x_values(d, x)
  """
  top_v = dict(sorted(d.items(), 
                      key=lambda item: item[1], 
                      reverse=True)[:x])
  return top_v


# ##############################################################################
# ###                              CONCEPT NODE                              ###
# ##############################################################################

class ConceptNode: 
  def __init__(self, node_dict: Dict[str, Any]): 
    # Loading the content of a memory node in the memory stream. 
    self.node_id = node_dict["node_id"]
    self.node_type = node_dict["node_type"]
    self.content = node_dict["content"]
    self.importance = node_dict["importance"]
    self.created = node_dict["created"]
    self.last_retrieved = node_dict["last_retrieved"]
    self.pointer_id = node_dict["pointer_id"]


  def package(self) -> Dict[str, Any]:
    """
    Packaging the agent's scratch memory for saving. 

    Parameters:
      None
    Returns: 
      packaged dictionary
    """
    curr_package = {}
    curr_package["node_id"] = self.node_id
    curr_package["node_type"] = self.node_type
    curr_package["content"] = self.content
    curr_package["importance"] = self.importance
    curr_package["created"] = self.created
    curr_package["last_retrieved"] = self.last_retrieved
    curr_package["pointer_id"] = self.pointer_id

    return curr_package


# ##############################################################################
# ###                             MEMORY STREAM                              ###
# ##############################################################################

class MemoryStream: 
  def __init__(self, 
               nodes: List[Dict[str, Any]], 
               embeddings: Dict[str, List[float]]):
    # Loading the memory stream for the agent. 
    self.seq_nodes = []
    self.id_to_node = dict()
    for node in nodes: 
      new_node = ConceptNode(node)
      self.seq_nodes += [new_node]
      self.id_to_node[new_node.node_id] = new_node

    self.embeddings = embeddings


  def count_observations(self) -> int:
    """
    Counting the number of observations (basically, the number of all nodes in 
    memory stream except for the reflections)

    Parameters:
      None
    Returns: 
      Count
    """
    count = 0
    for i in self.seq_nodes: 
      if i.node_type == "observation": 
        count += 1
    return count


  def retrieve(self, focal_points: List[str], time_step: int, 
       n_count: int = 10,  curr_filter: str = "all", 
       hp: List[float] = [0.5, 3, 0.5], stateless: bool = True, 
       verbose: bool = False, 
       record_json: Optional[str] = None) -> Dict[str, List[ConceptNode]]:
    """
    Retrieve relevant nodes from the memory stream based on given focal points.

    This function is the core of the memory retrieval system. It filters 
    nodes, calculates their relevance to given focal points, and returns the 
    most relevant nodes.

    High-level steps:
    1. Filter nodes based on the curr_filter parameter
    2. For each focal point:
       a. Calculate recency, importance, and relevance scores for each node
       b. Combine these scores to get a master score for each node
       c. Select the top n_count nodes based on their master scores
    3. Optionally record the results to a JSON file
    4. Return the retrieved nodes for each focal point

    :param focal_points: List of strings to focus the memory retrieval on
    :param time_step: Current time step in the simulation
    :param n_count: Number of nodes to retrieve for each focal point
    :param curr_filter: Filter for node types ('all', 'reflection', or 
      'observation')
    :param hp: Hyperparameters [recency_weight, relevance_weight, 
      importance_weight]
    :param stateless: If False, update the last_retrieved time of returned 
      nodes
    :param verbose: If True, print detailed scoring information
    :param record_json: Optional file path to record retrieval results
    :return: Dictionary mapping each focal point to a list of retrieved 
      ConceptNodes
    """
    curr_nodes = []

    # Filtering for the desired node type. curr_filter can be one of the three
    # elements: 'all', 'reflection', 'observation' 
    if curr_filter == "all": 
      curr_nodes = self.seq_nodes
    else: 
      for curr_node in self.seq_nodes: 
        if curr_node.node_type == curr_filter: 
          curr_nodes += [curr_node]

    # <retrieved> is the main dictionary that we are returning
    retrieved = dict() 
    for focal_pt in focal_points: 
      # Calculating the component dictionaries and normalizing them.
      x = extract_recency(curr_nodes)
      recency_out = normalize_dict_floats(x, 0, 1)
      x = extract_importance(curr_nodes)
      importance_out = normalize_dict_floats(x, 0, 1)  
      x = extract_relevance(curr_nodes, self.embeddings, focal_pt)
      relevance_out = normalize_dict_floats(x, 0, 1)
      
      # Computing the final scores that combines the component values. 
      master_out = dict()
      for key in recency_out.keys(): 
        recency_w = hp[0]
        relevance_w = hp[1]
        importance_w = hp[2]
        master_out[key] = (recency_w * recency_out[key]
                         + relevance_w * relevance_out[key] 
                         + importance_w * importance_out[key])

      if verbose: 
        master_out = top_highest_x_values(master_out, len(master_out.keys()))
        for key, val in master_out.items(): 
          print (self.id_to_node[key].content, val)
          print (recency_w*recency_out[key]*1, 
                 relevance_w*relevance_out[key]*1, 
                 importance_w*importance_out[key]*1)

      # Extracting the highest x values.
      # <master_out> has the key of node.id and value of float. Once we get  
      # the highest x values, we want to translate the node.id into nodes 
      # and return the list of nodes.
      master_out = top_highest_x_values(master_out, n_count)
      master_nodes = [self.id_to_node[key] for key in list(master_out.keys())]

      # We do not want to update the last retrieved time_step for these nodes
      # if we are in a stateless mode. 
      if not stateless: 
        for n in master_nodes: 
          n.retrieved_time_step = time_step
        
      retrieved[focal_pt] = master_nodes
    
    if record_json: 
      new_ret = dict()
      for key, val in retrieved.items(): 
        new_ret[key] = [i.content for i in val]
      append_to_json(record_json, new_ret)

    return retrieved 


  def _add_node(self, 
                time_step: int, 
                node_type: str, 
                content: str, 
                importance: float, 
                pointer_id: Optional[int]):
    """
    Adding a new node to the memory stream. 

    Parameters:
      time_step: Current time_step 
      node_type: type of node -- it's either reflection, observation
      content: the str content of the memory record
      importance: int score of the importance score
      pointer_id: the str of the parent node 
    Returns: 
      retrieved: A dictionary whose keys are a focal_pt query str, and whose
        values are a list of nodes that are retrieved for that query str. 
    """
    node_dict = dict()
    node_dict["node_id"] = len(self.seq_nodes)
    node_dict["node_type"] = node_type
    node_dict["content"] = content
    node_dict["importance"] = importance
    node_dict["created"] = time_step
    node_dict["last_retrieved"] = time_step
    node_dict["pointer_id"] = pointer_id
    new_node = ConceptNode(node_dict)

    self.seq_nodes += [new_node]
    self.id_to_node[new_node.node_id] = new_node
    self.embeddings[content] = get_text_embedding(content)


  def remember(self, content: str, time_step: int = 0):
    score = generate_importance_score([content])[0]
    self._add_node(time_step, "observation", content, score, None)


  def reflect(self, 
              anchor: str, 
              reflection_count: int = 5, 
              retrieval_count: int = 10, 
              time_step: int = 0):
    records = self.retrieve([anchor], 
                            time_step, 
                            retrieval_count, 
                            verbose=DEBUG)[anchor]
    record_ids = [i.node_id for i in records]
    reflections = generate_reflection(records, anchor, reflection_count)
    scores = generate_importance_score(reflections)

    for count, reflection in enumerate(reflections): 
      self._add_node(time_step, "reflection", reflections[count], 
                     scores[count], record_ids)


# ##############################################################################
# ###                 HELPER FUNCTIONS FOR GENERATIVE AGENTS                 ###
# ##############################################################################

def extract_recency(seq_nodes: List[ConceptNode]) -> Dict[int, float]:
  """
  Calculate the recency score for each node in the given sequence of 
  ConceptNodes.

  This function assigns a recency score to each node based on how recently it 
  was accessed. The score is calculated using an exponential decay function, 
  where more recently accessed nodes receive higher scores.

  Input:
      seq_nodes: A list of ConceptNode objects, each representing a memory or 
        concept. Each node should have 'node_id' and 'last_retrieved' 
        attributes.

  Output:
      A dictionary where:
      - Keys are node IDs (integers)
      - Values are recency scores (floats between 0 and 1)

  Algorithm:
  1. Find the most recent timestamp among all nodes.
  2. For each node, calculate its recency score as:
     score = recency_decay ^ (max_timestep - node's last retrieval time)
  3. A recency_decay of 0.99 is used, meaning the score halves approximately 
     every 69 time steps.

  Note:
  - More recent nodes (those with last_retrieved closer to max_timestep) will 
    have higher scores.
  - The most recently accessed node(s) will always have a score of 1.
  - Scores decrease exponentially for older memories.
  """
  # Complete the function below. 
  # [TODO]

  return dict()


def extract_importance(seq_nodes: List[ConceptNode]) -> Dict[int, float]:
  """
  Extract the importance score for each node in the given sequence of 
  ConceptNodes.

  This function creates a mapping of node IDs to their importance scores. The 
  importance score is a pre-existing attribute of each node, representing the 
  significance or relevance of the memory or concept.

  Input:
      seq_nodes: A list of ConceptNode objects, each representing a memory or 
        concept. Each node should have 'node_id' and 'importance' attributes.

  Output:
      A dictionary where:
      - Keys are node IDs (integers)
      - Values are importance scores (floats)

  Algorithm:
  1. Iterate through each node in the input list.
  2. Extract the importance score from each node.
  3. Create a dictionary mapping each node's ID to its importance score.

  Note:
  - The function assumes that the importance scores are already calculated and 
    stored in each node. It does not compute or modify these scores.
  - The range and scale of importance scores depend on how they were originally 
    assigned to the nodes.
  """
  # Complete the function below. 
  # [TODO]

  return dict()


def extract_relevance(seq_nodes: List[ConceptNode], 
                      embeddings: Dict[str, List[float]], 
                      focal_pt: str) -> Dict[int, float]:
  """
  Calculate the relevance score of each node to a given focal point.

  This function computes how relevant each node (memory or concept) is to a 
  specific focal point (e.g., a current thought or query). It uses cosine 
  similarity between the embedding of the focal point and the embedding of 
  each node's content.

  Inputs:
      seq_nodes: A list of ConceptNode objects, each representing a memory or 
        concept. Each node should have 'node_id' and 'content' attributes.
      embeddings: A dictionary mapping content strings to their vector 
        embeddings.
      focal_pt: A string representing the current focus or query.

  Output:
      A dictionary where:
      - Keys are node IDs (integers)
      - Values are relevance scores (floats between -1 and 1, where 1 is most 
        relevant)

  Algorithm:
  1. Get the embedding for the focal point.
  2. For each node:
     a. Retrieve the embedding for the node's content.
     b. Calculate the cosine similarity between the node's embedding and the 
        focal point's embedding.
  3. Return a dictionary of node IDs mapped to their relevance scores.

  Note:
  - Cosine similarity is used as the relevance metric. It ranges from -1 
    (opposite) to 1 (identical).
  - The function assumes that embeddings exist for both the focal point and 
    all node contents.
  - The quality of relevance scoring depends on the quality of the embedding 
    model used.
  """
  # Complete the function below. 
  # [TODO]

  return dict()


# ##############################################################################
# ###                              GPT FUNCTIONS                             ###
# ##############################################################################

def run_gpt_generate_importance(
  records: List[str], 
  prompt_version: str = "1",
  gpt_version: str = "GPT4o", 
  verbose: bool = False) -> Tuple[List[float], List[Any]]:

  def create_prompt_input(records):
    records_str = ""
    for count, r in enumerate(records): 
      records_str += f"Item {str(count+1)}:\n"
      records_str += f"{r}\n"
    return [records_str]

  def _func_clean_up(gpt_response, prompt=""): 
    gpt_response = extract_first_json_dict(gpt_response)
    return list(gpt_response.values())

  def _get_fail_safe():
    return 25

  if len(records) > 1: 
    prompt_lib_file = f"{LLM_PROMPT_DIR}/generative_agent/memory_stream/importance_score/batch_v1.txt" 
  else: 
    prompt_lib_file = f"{LLM_PROMPT_DIR}/generative_agent/memory_stream/importance_score/singular_v1.txt" 

  prompt_input = create_prompt_input(records) 
  fail_safe = _get_fail_safe() 

  output, prompt, prompt_input, fail_safe = chat_safe_generate(
    prompt_input, prompt_lib_file, gpt_version, 1, fail_safe, 
    _func_clean_up, verbose)

  return output, [output, prompt, prompt_input, fail_safe]


def generate_importance_score(records: List[str]) -> List[float]:
  """Generate importance scores for given records."""
  return run_gpt_generate_importance(records, "1", LLM_VERS)[0]


def run_gpt_generate_reflection(
  records: List[str], 
  anchor: str, 
  reflection_count: int,
  prompt_version: str = "1", 
  gpt_version: str = "GPT4o",
  verbose: bool = False) -> Tuple[List[str], List[Any]]:

  def create_prompt_input(records, anchor, reflection_count):
    records_str = ""
    for count, r in enumerate(records): 
      records_str += f"Item {str(count+1)}:\n"
      records_str += f"{r}\n"
    return [records_str, reflection_count, anchor]

  def _func_clean_up(gpt_response, prompt=""): 
    return extract_first_json_dict(gpt_response)["reflection"]

  def _get_fail_safe():
    return []

  if reflection_count > 1: 
    prompt_lib_file = f"{LLM_PROMPT_DIR}/generative_agent/memory_stream/reflection/batch_v1.txt" 
  else: 
    prompt_lib_file = f"{LLM_PROMPT_DIR}/generative_agent/memory_stream/reflection/singular_v1.txt" 

  prompt_input = create_prompt_input(records, anchor, reflection_count) 
  fail_safe = _get_fail_safe() 

  output, prompt, prompt_input, fail_safe = chat_safe_generate(
    prompt_input, prompt_lib_file, gpt_version, 1, fail_safe, 
    _func_clean_up, verbose)

  return output, [output, prompt, prompt_input, fail_safe]


def generate_reflection(
  records: List[ConceptNode], 
  anchor: str, 
  reflection_count: int) -> List[str]: 
  """Generate reflections based on given records and anchor."""
  records = [i.content for i in records]
  return run_gpt_generate_reflection(records, anchor, reflection_count, "1", 
                                     LLM_VERS)[0]
























































