import re
from typing import List, Tuple, Dict, Any

from simulation_engine.gpt_structure import gpt_request

class BakingEnvironment:
    def __init__(self, agent):
        self.agent = agent
        self.feedbacks = []
        self.reset()

    def reset(self) -> None:
        self.state = "initial"
        self.ingredients = {
            i: {"required": r, "current": 0} for i, r in zip(
                ["flour", "baking_powder", "salt", "butter", "sugar", "eggs", "vanilla_extract", "milk"],
                [250, 2, 1, 230, 300, 4, 2, 240]
            )
        }
        self.tools = {t: {"used": False, "preheated" if t == "oven" else "prepared" if t == "pans" else None: False} for t in ["oven", "mixing_bowl", "large_bowl", "whisk", "mixer", "pans"]}
        self.steps_completed = set()
        self.oven_temperature = None
        self.dry_mixed = self.wet_mixed = self.cream_done = False

    def _send_feedback(self, message: str) -> None:
        self.feedbacks.append(message)
        self.agent.message_history.append({"role": "user", "content": message})

    def process_action(self, action: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[str]]:
        processed_actions = self.extract_action(action)
        
        detected_actions = []
        for processed_action in processed_actions.split(','):
            processed_action = processed_action.strip().lower()
            
            if 'bake cake' in processed_action:
                detected_actions.append((self.bake_cake, ()))
            elif 'pour batter' in processed_action:
                detected_actions.append((self.pour_batter, ()))
            elif 'preheat oven' in processed_action:
                match = re.search(r'(\d+)', processed_action)
                if match:
                    temperature = int(match.group(1))
                    detected_actions.append((self.preheat_oven, (temperature,)))
            elif 'cream' in processed_action:
                detected_actions.append((self.mix_ingredients, ("cream",)))
            elif 'combine all ingredients' in processed_action:
                detected_actions.append((self.combine_all_ingredients, ()))
            elif 'mix dry ingredients' in processed_action:
                detected_actions.append((self.mix_ingredients, ("dry",)))
            elif 'mix wet ingredients' in processed_action:
                detected_actions.append((self.mix_ingredients, ("wet",)))
            elif 'add' in processed_action:
                match = re.search(r'(\d+)\s*(\w+)', processed_action)
                if match:
                    amount = int(match.group(1))
                    ingredient = match.group(2)
                    detected_actions.append((self.add_ingredient, (ingredient, amount)))
            elif 'get' in processed_action or 'use' in processed_action:
                match = re.search(r'(mixing[_ ]bowl|large[_ ]bowl|whisk|mixer|pans|oven)', processed_action)
                if match:
                    tool = match.group(1)
                    detected_actions.append((self.use_tool, (tool,)))
            elif 'cool' in processed_action:
                detected_actions.append((self.cool_cake, ()))

        if any(func.__name__ == 'mix_ingredients' and args[0] == 'dry' for func, args in detected_actions) and \
           any(func.__name__ == 'mix_ingredients' and args[0] == 'wet' for func, args in detected_actions):
            detected_actions.append((self.combine_all_ingredients, ()))

        sorted_actions = self._sort_actions(detected_actions)
        attempted_actions = []
        executed_actions = []
        self.feedbacks = []

        for action_func, args in sorted_actions:
            attempted_action = {"name": action_func.__name__, "args": args}
            attempted_actions.append(attempted_action)
            try:
                action_func(*args)
                executed_actions.append(attempted_action)
            except Exception as e:
                self._send_feedback(f"Failed to execute {action_func.__name__}: {str(e)}")

        if self._all_steps_completed():
            self.check_final_ingredients()

        return attempted_actions, executed_actions, self.feedbacks

    def extract_action(self, action: str) -> str:
        prompt = f"""
        Given a description of a baker's action, extract the action and arguments.
        Provide a comma-separated list of simple actions. ONLY the following actions are allowed:
        - For adding ingredients: "add [quantity in number only, no units] [ingredient name]"
        Valid ingredients are: {', '.join(ingredient.replace(' ', '_') for ingredient in self.ingredients.keys())}
        - For getting or using tools: "get / use [tool name]"
        Valid tools are: {', '.join(tool.replace(' ', '_') for tool in self.tools.keys() if tool != 'oven')}
        - For mixing: "mix dry ingredients", "mix wet ingredients", "cream butter and sugar", "combine all ingredients"
        - For oven actions: "preheat oven to X degrees", "bake cake"
        - For other actions: "pour batter", "cool cake"

        Example:
        Input: "I'm going to grab the whisk and mix the dry ingredients"
        Your response: "use whisk, mix dry ingredients"

        Input: "Now I'll add 4 eggs, one at a time, then mix it all together with the mixer"
        Your response: "add 4 eggs, use mixer, mix wet ingredients"

        Input: {action}
        """
        response = gpt_request(prompt, model="gpt-4o", max_tokens=100)
        return response

    def _sort_actions(self, actions: List[Tuple[callable, Tuple]]) -> List[Tuple[callable, Tuple]]:
        dependencies = {
            self.mix_ingredients: [self.use_tool],
            self.combine_all_ingredients: [lambda: self.mix_ingredients("dry"), lambda: self.mix_ingredients("wet")],
            self.pour_batter: [self.combine_all_ingredients],
            self.bake_cake: [self.pour_batter, self.preheat_oven]
        }

        def dependencies_satisfied(action, completed_actions):
            return action not in dependencies or all(any(isinstance(dep, type(ca)) for ca in completed_actions) for dep in dependencies[action])

        sorted_actions = []
        completed_actions = set()

        while actions:
            for action in actions:
                if dependencies_satisfied(action[0], completed_actions):
                    sorted_actions.append(action)
                    completed_actions.add(action[0])
                    actions.remove(action)
                    break
            else:
                sorted_actions.extend(actions)
                break

        return sorted_actions

    def get_progress(self) -> Dict[str, Any]:
        progress = {
            "steps": [],
            "dry_ingredients": [],
            "wet_ingredients": []
        }
        
        step_tool_map = {
            "mix_dry_ingredients": [("mixing_bowl", "Mixing Bowl"), ("whisk", "Whisk")],
            "cream": [("large_bowl", "Large Bowl"), ("mixer", "Mixer")],
            "mix_wet_ingredients": [("large_bowl", "Large Bowl"), ("mixer", "Mixer")],
        }
        
        all_steps = ["preheat_oven", "prepare_pans", "mix_dry_ingredients", "cream", "mix_wet_ingredients", "combine_all_ingredients", "pour_batter", "bake_cake", "cool_cake"]
        
        for step in all_steps:
            status = "completed" if step in self.steps_completed else "incomplete"
            step_name = step.replace('_', ' ').capitalize()
            if step in step_tool_map:
                tool_statuses = [{"name": name, "used": self.tools[t]["used"]} for t, name in step_tool_map[step]]
                progress["steps"].append({"name": step_name, "status": status, "tools": tool_statuses})
            else:
                progress["steps"].append({"name": step_name, "status": status})
        
        dry_ingredients = ["flour", "baking_powder", "salt"]
        wet_ingredients = ["butter", "sugar", "eggs", "vanilla_extract", "milk"]
        
        for ingredient in dry_ingredients:
            data = self.ingredients[ingredient]
            progress["dry_ingredients"].append({
                "name": ingredient.capitalize(),
                "current": data["current"],
                "required": data["required"]
            })
        
        for ingredient in wet_ingredients:
            data = self.ingredients[ingredient]
            progress["wet_ingredients"].append({
                "name": ingredient.capitalize(),
                "current": data["current"],
                "required": data["required"]
            })
        
        return progress

    def _all_steps_completed(self) -> bool:
        all_steps = {"preheat_oven", "prepare_pans", "mix_dry_ingredients", "cream", "mix_wet_ingredients", "combine_all_ingredients", "pour_batter", "bake_cake", "cool_cake"}
        return self.steps_completed == all_steps

    def check_final_ingredients(self) -> bool:
        errors = [f"{i}: expected {d['required']}, got {d['current']}" for i, d in self.ingredients.items() if d["current"] != d["required"]]
        if errors:
            self._send_feedback("Your cake didn't turn out quite right... Here are the issues with the ingredients:")
            for e in errors:
                self._send_feedback(e)
            return False
        else:
            self._send_feedback("You successfully baked a delicious cake!")
            return True

    # Add these methods if they're not already present
    def add_ingredient(self, ingredient: str, amount: int) -> None:
        if ingredient in self.ingredients:
            self.ingredients[ingredient]["current"] += amount
            self._send_feedback(f"Added {amount} {ingredient}")
        else:
            self._send_feedback(f"You tried to add {amount} {ingredient}, but {ingredient} is not a valid ingredient")

    def use_tool(self, tool: str) -> None:
        if tool in self.tools:
            self.tools[tool]["used"] = True
            if tool == "pans":
                self.tools[tool]["prepared"] = True
                self.steps_completed.add("prepare_pans")
                self._send_feedback(f"You prepared the cake pans.")
            elif tool == "oven":
                if self.oven_temperature is not None:
                    self.tools[tool]["preheated"] = True
                    self.steps_completed.add("preheat_oven")
                    self._send_feedback(f"You used the oven, which is preheated to {self.oven_temperature}°F")
                else:
                    self._send_feedback("You tried to use the oven, but it's not preheated yet.")
            else:
                self._send_feedback(f"Using {tool}")
        else:
            self._send_feedback(f"You tried to use {tool}, but {tool} is not a valid tool")

    def preheat_oven(self, temperature: int) -> None:
        self.oven_temperature = temperature
        self.tools["oven"]["preheated"] = True
        self.steps_completed.add("preheat_oven")
        self._send_feedback(f"You preheated the oven to {self.oven_temperature}°F")

    def mix_ingredients(self, type: str) -> None:
        if type == "cream":
            required_tools = ["large_bowl", "mixer"]
            ingredients = ["butter", "sugar"]
        elif type == "dry":
            required_tools = ["mixing_bowl", "whisk"]
            ingredients = ["flour", "baking_powder", "salt"]
        else:  # wet
            required_tools = ["large_bowl", "mixer"]
            ingredients = ["eggs", "vanilla_extract", "milk"]

        if all(self.ingredients[ing]["current"] > 0 for ing in ingredients):
            if all(self.tools[tool]["used"] for tool in required_tools):
                if type == "cream":
                    self.cream_done = True
                    self.steps_completed.add("cream")
                    self._send_feedback("You creamed the butter and sugar until light and fluffy")
                else:
                    setattr(self, f"{type}_mixed", True)
                    self.steps_completed.add(f"mix_{type}_ingredients")
                    self._send_feedback(f"You mixed the {type} ingredients in the {'mixing' if type == 'dry' else 'large'} bowl with the {'whisk' if type == 'dry' else 'mixer'}")
            else:
                missing_tools = [tool for tool in required_tools if not self.tools[tool]['used']]
                self._send_feedback(f"You need to use {', '.join(required_tools)} to {'cream the butter and sugar, and are missing' if type == 'cream' else f'mix the {type} ingredients, and are missing'}: {', '.join(missing_tools)}")
        else:
            missing = [ing for ing in ingredients if self.ingredients[ing]["current"] == 0]
            self._send_feedback(f"You are missing the following ingredients for {'creaming' if type == 'cream' else f'{type} mixture'}: {', '.join(missing)}")

    def combine_all_ingredients(self) -> None:
        if self.dry_mixed and self.wet_mixed:
            self.steps_completed.add("combine_all_ingredients")
            self._send_feedback("You combined all the ingredients together")
        else:
            if not self.dry_mixed:
                self._send_feedback("You need to mix the dry ingredients before combining all ingredients")
            if not self.wet_mixed:
                self._send_feedback("You need to mix the wet ingredients before combining all ingredients")

    def pour_batter(self) -> None:
        if "combine_all_ingredients" in self.steps_completed and self.tools["pans"]["prepared"]:
            self.steps_completed.add("pour_batter")
            self._send_feedback("You poured the batter evenly into the prepared cake pans")
        else:
            self._send_feedback("You need to combine all ingredients and prepare cake pans first")

    def bake_cake(self) -> None:
        if "pour_batter" in self.steps_completed and self.tools["oven"]["preheated"]:
            if self.oven_temperature == 350:
                self.steps_completed.add("bake_cake")
                self._send_feedback("You baked the cake for 30-35 minutes")
            else:
                self._send_feedback(f"The oven temperature should be 350°F, but it's currently set to {self.oven_temperature}°F")
        elif "pour_batter" not in self.steps_completed:
            self._send_feedback("Please pour the batter into the pans first")
        elif not self.tools["oven"]["preheated"]:
            self._send_feedback("Please preheat the oven to 350°F first")
        else:
            self._send_feedback("Please pour the batter and preheat the oven to 350°F first")

    def cool_cake(self) -> None:
        if "bake_cake" in self.steps_completed:
            self.steps_completed.add("cool_cake")
            self._send_feedback("You let the pans sit for 10 minutes, then cooled the cake on a wire rack")
        else:
            self._send_feedback("Please bake the cake first")