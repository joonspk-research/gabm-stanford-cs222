from simulation_engine.settings import *
from simulation_engine.global_methods import *

def get_list_of_agent_id(population="AB1000", count=None):
  agent_folders = find_filenames(f"{POPULATIONS_DIR}/{population}", suffix="")
  if count: 
    agent_folders = agent_folders[:count]

  return [f'{i.split("/")[-1]}' for i in agent_folders]