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


def build_agent(): 
  curr_agent = GenerativeAgent("SyntheticCS222_Base", "matthew_jacobs")
  for m in matthew_memories: 
    curr_agent.remember(m)
  curr_agent.save("SyntheticCS222", "matthew_jacobs")


def interview_agent(): 
  curr_agent = GenerativeAgent("SyntheticCS222", "matthew_jacobs")
  chat_session(curr_agent, True)


def chat_with_agent(): 
  curr_agent = GenerativeAgent("SyntheticCS222", "matthew_jacobs")
  chat_session(curr_agent, False)


def ask_agent_to_reflect(): 
  curr_agent = GenerativeAgent("SyntheticCS222", "matthew_jacobs")
  curr_agent.reflect("Reflect on your goal in life")


def main(): 
  build_agent()
  interview_agent()
  chat_with_agent()
  ask_agent_to_reflect()


if __name__ == '__main__':
  main()
  

































