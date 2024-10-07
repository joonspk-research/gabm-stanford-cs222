import json

from typing import Dict, List, Optional, Union

from generative_agent.modules.memory_stream import MemoryStream
from generative_agent.modules.scratch import Scratch
from generative_agent.modules.interaction import utterance
from simulation_engine.settings import *
from simulation_engine.global_methods import *

# ############################################################################
# ###                        GENERATIVE AGENT CLASS                        ###
# ############################################################################

class GenerativeAgent: 
  def __init__(self, population: str, agent_id: str):
    self.population: str
    self.id: str
    self.forked_population: str
    self.forked_id: str
    self.scratch: Scratch
    self.memory_stream: MemoryStream

    # The location of the population folder for the agent. 
    agent_folder = f"{POPULATIONS_DIR}/{population}/{agent_id}"

    # We stop the process if the agent storage folder already exists. 
    if not check_if_file_exists(f"{agent_folder}/scratch.json"):
      print ("Generative agent does not exist in the current location.")
      return 
    
    # Loading the agent's memories. 
    with open(f"{agent_folder}/meta.json") as json_file:
      meta = json.load(json_file)
    with open(f"{agent_folder}/scratch.json") as json_file:
      scratch = json.load(json_file)
    with open(f"{agent_folder}/memory_stream/embeddings.json") as json_file:
      embeddings = json.load(json_file)
    with open(f"{agent_folder}/memory_stream/nodes.json") as json_file:
      nodes = json.load(json_file)

    self.population = meta["population"] 
    self.id = meta["id"] 
    self.forked_population = meta["population"] 
    self.forked_id = meta["id"]
    self.scratch = Scratch(scratch)
    self.memory_stream = MemoryStream(nodes, embeddings)
    
    print (f"Loaded {agent_id}:{population}")


  def initialize(self, population: str, agent_id: str) -> None: 
    """
    Initializes the agent storage folder and its components files init. The 
    folder that is created contains everything that a generative agent needs
    to contain, from its memory stream to scratch memory.  

    Parameters:
      population: The current population.
      agent_id: The id of the agent.
    Returns: 
      None
    """
    # The location of the population folder for the agent. 
    agent_folder = f"{POPULATIONS_DIR}/{population}/{agent_id}"

    # We stop the process if the agent storage folder already exists. 
    if check_if_file_exists(f"{agent_folder}/meta.json"):
      print ("Init not run as the agent storage folder already exists")

    else: 
      # Creating the agent storage folder.
      print (f"Initializing {agent_id}:{population}'s agent storage.")
      create_folder_if_not_there(agent_folder)
      print (f"-- Created {agent_folder}")
      create_folder_if_not_there(f"{agent_folder}/memory_stream")
      print (f"-- Created {agent_folder}/memory_stream")

      # Initializing meta file
      with open(f"{agent_folder}/meta.json", "w") as file:
        meta = {"population": population, 
                "id": agent_id,
                "forked_population": population,
                "forked_id": agent_id}
        json.dump(meta, file, indent=2)  

      # Initializing scratch
      with open(f"{agent_folder}/scratch.json", "w") as file:
        scratch = Scratch().package()
        json.dump(scratch, file, indent=2)  

      # Initializing embeddings
      with open(f"{agent_folder}/memory_stream/embeddings.json", "w") as file:
        json.dump({}, file, indent=2)  

      # Initializing nodes
      with open(f"{agent_folder}/memory_stream/nodes.json", "w") as file:
        json.dump([], file, indent=2)      

    self.load(population, agent_id)


  def package(self): 
    """
    Packaging the agent's meta info for saving. 

    Parameters:
      None
    Returns: 
      packaged dictionary
    """
    return {"population": self.population,
            "id": self.id,
            "forked_population": self.forked_population,
            "forked_id": self.forked_id}


  def save(self, save_population=None, save_id=None): 
    """
    Given a save_code, save the agents' state in the storage. Right now, the 
    save directory works as follows: 
    'storage/<agent_name>/<save_code>'

    As you grow different versions of the agent, save the new agent state in 
    a different save code location. Remember that 'init' is the originally
    initialized agent directory.

    Parameters:
      save_code: str
    Returns: 
      None
    """
    if not save_population: 
      save_population = self.population
    if not save_id: 
      save_id = self.id

    self.forked_population = self.population
    self.forked_id = self.id
    self.population = save_population
    self.id = save_id

    # Name of the agent and the current save location. 
    storage = f"{POPULATIONS_DIR}/{save_population}/{save_id}"
    create_folder_if_not_there(storage)
    create_folder_if_not_there(f"{storage}/memory_stream")
    
    # Saving the agent's memory stream. This includes saving the embeddings 
    # as well as the nodes. 
    with open(f"{storage}/memory_stream/embeddings.json", "w") as json_file:
      json.dump(self.memory_stream.embeddings, 
                json_file)
    with open(f"{storage}/memory_stream/nodes.json", "w") as json_file:
      json.dump([node.package() for node in self.memory_stream.seq_nodes], 
                json_file, indent=2)

    # Saving the agent's scratch memories. 
    with open(f"{storage}/scratch.json", "w") as json_file:
      agent_scratch_summary = self.scratch.package()
      json.dump(agent_scratch_summary, json_file, indent=2)

    # Saving the agent's meta information. 
    with open(f"{storage}/meta.json", "w") as json_file:
      agent_meta_summary = self.package()
      json.dump(agent_meta_summary, json_file, indent=2)


  def remember(self, content: str, time_step: int = 0) -> None: 
    """
    Add a new observation to the memory stream. 

    Parameters:
      content: The content of the current memory record that we are adding to
        the agent's memory stream. 
    Returns: 
      None
    """
    self.memory_stream.remember(content, time_step)


  def reflect(self, anchor: str, time_step: int = 0) -> None: 
    """
    Add a new reflection to the memory stream. 

    Parameters:
      anchor: str reflection anchor
      time_step: int entering timestep
    Returns: 
      None
    """
    self.memory_stream.reflect(anchor, time_step)


  def utterance(self, 
                curr_dialogue: List[List[str]], 
                context: str = "") -> str:
    """
    Given a dialogue of the form, 
      [["Agent 1": "Content..."],
       ["Agent 2": "Content..."], ... ]
    generate the next agent utterance. 

    Parameters:
      anchor: str reflection anchor
      time_step: int entering timestep
    Returns: 
      None
    """
    ret = utterance(self, curr_dialogue, context)
    return ret 






















