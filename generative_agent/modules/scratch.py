class Scratch: 
  def __init__(self, scratch=None): 
    self.first_name = ""
    self.last_name = ""

    self.age = 0
    self.sex = ""
    self.census_division = ""
    self.political_ideology = ""
    self.political_party = ""
    self.education = ""
    self.race = ""
    self.ethnicity = ""
    self.annual_income = 0.0
    self.address = ""

    self.extraversion = 0.0
    self.agreeableness = 0.0
    self.conscientiousness = 0.0
    self.neuroticism = 0.0
    self.openness = 0.0

    self.fact_sheet = ""
    self.speech_pattern = ""
    self.self_description = ""
    self.private_self_description = ""

    if scratch: 
      self.first_name = scratch["first_name"]
      self.last_name = scratch["last_name"]

      self.age = int(scratch["age"])
      self.sex = scratch["sex"]
      self.census_division = scratch["census_division"]
      self.political_ideology = scratch["political_ideology"]
      self.political_party = scratch["political_party"]
      self.education = scratch["education"]
      self.race = scratch["race"]
      self.ethnicity = scratch["ethnicity"]
      self.annual_income = float(scratch["annual_income"])
      self.address = scratch["address"]

      self.extraversion = float(scratch["extraversion"])
      self.agreeableness = float(scratch["agreeableness"])
      self.conscientiousness = float(scratch["conscientiousness"])
      self.neuroticism = float(scratch["neuroticism"])
      self.openness = float(scratch["openness"])

      self.fact_sheet = scratch["fact_sheet"]
      self.speech_pattern = scratch["speech_pattern"]
      self.self_description = scratch["self_description"]
      self.private_self_description = scratch["private_self_description"]


  def package(self): 
    """
    Packaging the agent's scratch memory for saving. 

    Parameters:
      None
    Returns: 
      packaged dictionary
    """
    curr_package = {}
    curr_package["first_name"] = self.first_name
    curr_package["last_name"] = self.last_name

    curr_package["age"] = self.age
    curr_package["sex"] = self.sex
    curr_package["census_division"] = self.census_division
    curr_package["political_ideology"] = self.political_ideology
    curr_package["political_party"] = self.political_party
    curr_package["education"] = self.education
    curr_package["race"] = self.race
    curr_package["ethnicity"] = self.ethnicity
    curr_package["annual_income"] = self.annual_income
    curr_package["address"] = self.address

    curr_package["extraversion"] = self.extraversion
    curr_package["agreeableness"] = self.agreeableness
    curr_package["conscientiousness"] = self.conscientiousness
    curr_package["neuroticism"] = self.neuroticism
    curr_package["openness"] = self.openness

    curr_package["fact_sheet"] = self.fact_sheet
    curr_package["speech_pattern"] = self.speech_pattern
    curr_package["self_description"] = self.self_description
    curr_package["private_self_description"] = self.private_self_description

    return curr_package


  def get_fullname(self):
    return f"{self.first_name} {self.last_name}" 
