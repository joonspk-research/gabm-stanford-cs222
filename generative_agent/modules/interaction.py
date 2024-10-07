from typing import List, Tuple, Dict, Any
from simulation_engine.settings import * 
from simulation_engine.global_methods import *
from simulation_engine.gpt_structure import *
from simulation_engine.llm_json_parser import *


def _utterance_agent_desc(agent: 'GenerativeAgent', anchor: str) -> str: 
  """
  Generate a description of the agent based on its attributes and relevant 
  memories.

  This function creates a string description of the agent, including its 
  self-description, speech pattern, and relevant memories retrieved based on 
  the given anchor.

  Steps:
  1. Initialize the agent description string
  2. Add the agent's self-description
  3. Add the agent's speech pattern
  4. Retrieve relevant memories using the anchor
  5. Add the content of retrieved memories to the description

  :param agent: The GenerativeAgent instance
  :param anchor: A string used to retrieve relevant memories
  :return: A string containing the agent's description and relevant memories
  """
  # Step 1: Initialize the agent description string
  agent_desc = ""

  # [TODO]

  # Step 2: Add the agent's self-description
  # TODO: Add the self-description to agent_desc
  # Hint: Use agent.scratch.self_description

  # Step 3: Add the agent's speech pattern
  # TODO: Add the speech pattern to agent_desc
  # Hint: Use agent.scratch.speech_pattern

  # Step 4: Retrieve relevant memories using the anchor
  # TODO: Use agent.memory_stream.retrieve to get relevant memories
  # Hint: Set n_count=10 and verbose=DEBUG

  # Step 5: Add the content of retrieved memories to the description
  # TODO: Iterate through the retrieved nodes and add their content to agent_desc

  return agent_desc


def run_gpt_generate_utterance(
    agent_desc: str, 
    str_dialogue: str,
    context: str,
    prompt_version: str = "1",
    gpt_version: str = "GPT4o",  
    verbose: bool = False) -> Tuple[str, List[Any]]:
  """
  Generate an utterance using GPT based on the agent description, dialogue, and context.

  This function prepares the input for the GPT model, sends the request, and processes the response.

  :param agent_desc: Description of the agent
  :param str_dialogue: The current dialogue string
  :param context: Additional context for the conversation
  :param prompt_version: Version of the prompt to use
  :param gpt_version: Version of GPT to use
  :param verbose: Whether to print verbose output
  :return: A tuple containing the generated utterance and additional information
  """
  def create_prompt_input(
    agent_desc: str, 
    str_dialogue: str, 
    context: str) -> List[str]:
    return [agent_desc, context, str_dialogue]

  def _func_clean_up(gpt_response: str, prompt: str = "") -> str:
    return extract_first_json_dict(gpt_response)["utterance"]

  def _get_fail_safe() -> None:
    return None

  # Set up the prompt file path
  prompt_lib_file = f"{LLM_PROMPT_DIR}/generative_agent/interaction/utternace/utterance_v1.txt" 
 

  # Create the prompt input
  prompt_input = create_prompt_input(agent_desc, str_dialogue, context) 

  # Get the fail-safe response
  fail_safe = _get_fail_safe() 

  # Generate the utterance using the chat_safe_generate function
  output, prompt, prompt_input, fail_safe = chat_safe_generate(
    prompt_input, prompt_lib_file, gpt_version, 1, fail_safe, 
    _func_clean_up, verbose)

  return output, [output, prompt, prompt_input, fail_safe]


def utterance(agent: 'GenerativeAgent', 
              curr_dialogue: List[List[str]], 
              context: str) -> str:
  """Generate an utterance for the agent based on the current dialogue and 
     context."""
  str_dialogue = "".join(f"[{row[0]}]: {row[1]}\n" for row in curr_dialogue)
  str_dialogue += f"[{agent.scratch.get_fullname()}]: [Fill in]\n"

  anchor = str_dialogue
  agent_desc = _utterance_agent_desc(agent, anchor)
  return run_gpt_generate_utterance(
           agent_desc, str_dialogue, context, "1", LLM_VERS)[0]



  





  





  




  





  





