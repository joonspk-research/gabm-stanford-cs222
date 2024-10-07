from simulation_engine.settings import *
from simulation_engine.global_methods import *

from agent_bank.navigator import *
from generative_agent.generative_agent import * 

from cs222_assignment_1.memories.jasmine_carter_memories import *
from cs222_assignment_1.memories.matthew_jacobs_memories import *
from cs222_assignment_1.questions.jasmine_carter_questions import *
from cs222_assignment_1.questions.matthew_jacobs_questions import *


def chat_session(generative_agent, stateless=False): 
  print (f"Start chatting with {generative_agent.scratch.get_fullname()}.")
  print ("Type 'bye' to exit.")
  print ("")

  context = input("First, describe the context of this conversation: ")
  user_name = input("And what is your name: ")
  print ("")

  curr_convo = []

  while True: 
    if stateless: curr_convo = []

    user_input = input("You: ").strip()
    curr_convo += [[user_name, user_input]]

    if user_input.lower() == "bye":
      print(generative_agent.utterance(curr_convo)) 
      break

    response = generative_agent.utterance(curr_convo)  
    curr_convo += [[generative_agent.scratch.get_fullname(), response]]
    print(f"{generative_agent.scratch.get_fullname()}: {response}")


def main(): 
  return 


if __name__ == '__main__':
  main()
  

































