import json
from flask import Flask, render_template, jsonify, request, send_from_directory
import os

from bonus_agent import Agent

def print_cyan(text: str) -> None:
    print(f"\033[96m{text}\033[0m")

def init_agent(agent_folder: str) -> Agent:
    agent_path = os.path.join('cs222_assignment_1_bonus', 'isabella', 'agent.json')
    with open(agent_path, 'r') as f:
        agent_json = json.load(f)

    return Agent(agent_json["name"], agent_json["description"])

app = Flask(__name__, 
            static_folder='cs222_assignment_1_bonus/static',
            template_folder='cs222_assignment_1_bonus/templates')

isabella = init_agent("isabella")
current_step = 0
max_steps = 25

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start_baking', methods=['POST'])
def start_baking():
    global current_step
    current_step = 0
    isabella.env.reset()
    initial_message = "Hi there! I'm Isabella, and I absolutely love baking. I'm so excited to bake a cake today!"
    isabella.message_history = [{"role": "assistant", "content": initial_message}]
    
    return jsonify({
        "message": initial_message,
        "progress": isabella.env.get_progress(),
        "completed": False,
        "feedback": "",
        "executed_actions": []
    })

@app.route('/next_step', methods=['POST'])
def next_step():
    global current_step
    if current_step < max_steps and not isabella.env._all_steps_completed():
        current_step += 1
        
        agent_message, attempted_actions, executed_actions, feedbacks = isabella.baking_step()
        
        feedback = '\n'.join(feedbacks)
        progress = isabella.env.get_progress()
        
        if isabella.env._all_steps_completed():
            final_message = "Wonderful! We've successfully baked the cake. Let's enjoy it!" if isabella.env.check_final_ingredients() else "Hmm... it seems we made some mistakes with the ingredients and the cake tastes... not so good. Let's try again next time!"
            isabella.message_history.append({"role": "assistant", "content": final_message})
            return jsonify({
                "agent_message": agent_message,
                "final_message": final_message,
                "progress": progress,
                "completed": True,
                "feedback": feedback,
                "attempted_actions": attempted_actions,
                "executed_actions": executed_actions
            })
        
        return jsonify({
            "agent_message": agent_message,
            "progress": progress,
            "completed": False,
            "feedback": feedback,
            "attempted_actions": attempted_actions,
            "executed_actions": executed_actions
        })
    else:
        return jsonify({
            "agent_message": "Oh dear, it seems we've taken too long to bake the cake. Let's try again another time!",
            "completed": True,
            "feedback": "",
            "attempted_actions": [],
            "executed_actions": []
        })

@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory(app.static_folder, path)

if __name__ == '__main__':
    app.run(debug=True)