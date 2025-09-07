import dspy
import os
import pandas as pd
from dspy.teleprompt import BootstrapFewShotWithRandomSearch
from agent_dojo.tools.file_utils import get_optimized_program_file_directory, get_training_set_directory
from typing import Any

from dotenv import load_dotenv
load_dotenv()

dspy.settings.configure( track_usage=True )

class PersonaDigitalTwinAgent(dspy.Module):
    def __init__(self,  tools=[]):
        super().__init__()
        self.instructions = "Create an imaginary persona based on data provided and update the digital twin with data as much as possible."
        self.tools = tools
        signature = dspy.Signature('data: dict[str,Any] -> digital_twin: str', self.instructions)
        self.react = dspy.ReAct(signature=signature, tools=tools, max_iters=5)

    def forward(self, data):
        return self.react(data=data)


class Assess(dspy.Signature):
    """Assess the quality of digital twin text created"""
    assessed_text = dspy.InputField()
    assessment_question = dspy.InputField()
    assessment_answer: bool = dspy.OutputField()


def _metric(example,pred,trace=None):
    digital_twin = pred.digital_twin
    assessment_question = "Does the assessed text have enough information captured to act as a digital twin of a lead?"
    enough_information = dspy.Predict(Assess)(assessed_text=digital_twin, assessment_question=assessment_question)

    #Search digital_twin text to make sure it has "Financial Information", "Occupation", "Annual Income", "Persona Summary"
    contains_key_sections=False
    if "Financial Information" in digital_twin and "Occupation" in digital_twin and "Annual Income" in digital_twin and "Persona Summary" in digital_twin:
        contains_key_sections=True

    return  enough_information.assessment_answer and contains_key_sections

def optimize():
    optimize_using_miprov2()


def _load_test_set(csv_filename, caller_file):
    csv_path = os.path.join(get_training_set_directory(caller_file), csv_filename)
    df = pd.read_csv(csv_path)
    test_set = [
        dspy.Example(data=row['data'], digital_twin=row['digital_twin']).with_inputs("data")
        for _, row in df.iterrows()
    ]
    return test_set

def _save_optimized_program(optimized_program, caller_file):
    optimized_program_file_dir = get_optimized_program_file_directory(caller_file)
    optimized_program.save(
        os.path.join(optimized_program_file_dir, 'PersonaDigitalTwinAgent_Optimized'),
        save_program=True
    )

def optimize_using_bootstrapfewshot():
    test_set = _load_test_set('lead_personas_dataset_v3_detailed_twins.csv', __file__)
    with dspy.context(lm=dspy.LM('openai/gpt-4.1')):
        program = PersonaDigitalTwinAgent(tools=[])
        config = dict(max_bootstrapped_demos=4, max_labeled_demos=4, num_candidate_programs=5, num_threads=4)
        optimizer = BootstrapFewShotWithRandomSearch(metric=_metric, **config)
        optimized_program = optimizer.compile(program, trainset=test_set)
        _save_optimized_program(optimized_program, __file__)

def optimize_using_miprov2():
    test_set = _load_test_set('lead_personas_dataset_v3_detailed_twins.csv', __file__)
    with dspy.context(lm=dspy.LM('openai/gpt-4o-mini')):
        program = PersonaDigitalTwinAgent(tools=[])
        optimizer = dspy.MIPROv2(metric=_metric, auto="light")
        optimized_program = optimizer.compile(program, trainset=test_set)
        _save_optimized_program(optimized_program, __file__)

def run(data):
    agent = PersonaDigitalTwinAgent()
    optimized_program_file_dir = get_optimized_program_file_directory(__file__)
    optimized_program_file = os.path.join(optimized_program_file_dir, 'PersonaDigitalTwinAgent_Optimized')
    if os.path.exists(optimized_program_file):
        agent = dspy.load(optimized_program_file)
    else:
        #Throw error
        raise FileNotFoundError("Optimized program not found. Please train the agent first.")
        
    with dspy.context(lm=dspy.LM('openai/gpt-4.1-mini')):
        output = agent(data=data)
        print(output.get_lm_usage())

    return output.digital_twin