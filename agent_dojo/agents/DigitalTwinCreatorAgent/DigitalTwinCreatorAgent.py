import dspy
import os
import pandas as pd
from dspy.teleprompt import BootstrapFewShotWithRandomSearch
from agent_dojo.tools.file_utils import get_optimized_program_file_directory, get_training_set_directory
from typing import Any

from dotenv import load_dotenv
load_dotenv()

#dspy.settings.configure( track_usage=True )

TEST_SET="lead_personas_dataset_v6_10records_detailed_existing.csv"

model_for_optimization=dspy.LM('openai/gpt-4.1',temperature=1.0, max_tokens=16000)
model_for_execution=dspy.LM('openai/gpt-4.1',temperature=1.0, max_tokens=16000)


class ExtractDigitalTwin(dspy.Signature):
    """Create an imaginary persona based on data provided and update the digital twin with data as much as possible.
    If existing_digital_twin information is provided, update it with new or changed information based on clear signals in data"""
    data: str = dspy.InputField()
    existing_digital_twin:str = dspy.InputField()
    digital_twin: str = dspy.OutputField(desc="markdown-formatted")

class DigitalTwinCreatorAgent(dspy.Module):
    def __init__(self):
        super().__init__()
        self.perform_digital_twin_extraction = dspy.ChainOfThought(ExtractDigitalTwin)

    def forward(self, data,existing_digital_twin):
        return self.perform_digital_twin_extraction(data=data,existing_digital_twin=existing_digital_twin)


class AssessDigitalTwinQuality(dspy.Signature):
    """Assess the quality of digital twin text created"""
    assessed_text = dspy.InputField()
    assessment_question = dspy.InputField()
    assessment_answer: bool = dspy.OutputField()

class AssessUpdateToDigitalTwin(dspy.Signature):
    """Assess if the updates made to the digitial twin are good"""
    existing_digital_twin = dspy.InputField()
    digital_twin = dspy.InputField()
    assessment_question = dspy.InputField()
    assessment_answer: bool = dspy.OutputField()

def _metric(example,pred,trace=None):
    digital_twin = pred.digital_twin
    assessment_question = "Does the assessed text have enough information captured to act as a digital twin of a lead?"
    enough_information = dspy.Predict(AssessDigitalTwinQuality)(assessed_text=digital_twin, assessment_question=assessment_question)

    digital_twin_update_good=False

    #For some reason existing_digital_twin is sometimes float
    if isinstance(example.existing_digital_twin, float):
        example.existing_digital_twin = str(example.existing_digital_twin)

    if example.existing_digital_twin!='nan' and example.existing_digital_twin.strip()!="":
        assessment_question = "Are the updates made to the digital twin good and relevant?"
        digital_twin_update_good = dspy.Predict(AssessUpdateToDigitalTwin)(existing_digital_twin=example.existing_digital_twin, digital_twin=digital_twin, assessment_question=assessment_question).assessment_answer
    else:
        digital_twin_update_good=True

    #Search digital_twin text to make sure it has "Financial Information", "Occupation", "Annual Income", "Persona Summary"
    contains_key_sections=False
    if "Financial Information" in digital_twin and "Occupation" in digital_twin and "Annual Income" in digital_twin and "Persona Summary" in digital_twin:
        contains_key_sections=True

    #Print all three values
    print(f"enough_information: {enough_information.assessment_answer}, contains_key_sections: {contains_key_sections}, digital_twin_update_good: {digital_twin_update_good}")
    score=enough_information.assessment_answer + contains_key_sections + digital_twin_update_good

    if trace is not None: return score>=3
    return score/3.0

def _simple_metric(example,pred,trace=None):
    digital_twin = pred.digital_twin
    
    contains_key_sections=False
    if "Financial Information" in digital_twin and "Occupation" in digital_twin and "Annual Income" in digital_twin and "Persona Summary" in digital_twin:
        contains_key_sections=True

    return contains_key_sections

def optimize():
    optimize_using_bootstrapfewshot()


def _load_test_set(csv_filename, caller_file):
    csv_path = os.path.join(get_training_set_directory(caller_file), csv_filename)
    df = pd.read_csv(csv_path)
    test_set = [
        dspy.Example(data=row['data'], existing_digital_twin=row['existing_digital_twin'], digital_twin=row['digital_twin']).with_inputs("data", "existing_digital_twin")
        for _, row in df.iterrows()
    ]
    return test_set

def _save_optimized_program(optimized_program, caller_file):
    optimized_program_file_dir = get_optimized_program_file_directory(caller_file)
    optimized_program.save(
        os.path.join(optimized_program_file_dir, 'DigitalTwinCreatorAgent_Optimized'),
        save_program=True
    )

def optimize_using_bootstrapfewshot():
    test_set = _load_test_set(TEST_SET, __file__)
    with dspy.context(lm=model_for_optimization):
        program = DigitalTwinCreatorAgent()
        config = dict(max_bootstrapped_demos=4, max_labeled_demos=4, num_candidate_programs=2, num_threads=1)
        optimizer = BootstrapFewShotWithRandomSearch(metric=_simple_metric, **config)
        optimized_program = optimizer.compile(program, trainset=test_set)
        _save_optimized_program(optimized_program, __file__)

def optimize_using_miprov2():
    test_set = _load_test_set(TEST_SET, __file__)
    with dspy.context(lm=model_for_optimization):
        program = DigitalTwinCreatorAgent()
        optimizer = dspy.MIPROv2(metric=_simple_metric, auto="light",num_threads=1)
        optimized_program = optimizer.compile(program, trainset=test_set)
        _save_optimized_program(optimized_program, __file__)

def optimize_using_simba():
    test_set = _load_test_set(TEST_SET, __file__)
    with dspy.context(lm=model_for_optimization):
        program = DigitalTwinCreatorAgent()
        config = dict(num_candidate_programs=2, num_threads=1)
        optimizer = dspy.SIMBA(metric=_simple_metric, )
        optimized_program = optimizer.compile(program, trainset=test_set)
        _save_optimized_program(optimized_program, __file__)

def run(data, existing_digital_twin=None):
    agent = DigitalTwinCreatorAgent()
    optimized_program_file_dir = get_optimized_program_file_directory(__file__)
    optimized_program_file = os.path.join(optimized_program_file_dir, 'DigitalTwinCreatorAgent_Optimized')
    if os.path.exists(optimized_program_file):
        agent = dspy.load(optimized_program_file)
    else:
        #Throw error
        raise FileNotFoundError("Optimized program not found. Please train the agent first.")

    with dspy.context(lm=model_for_execution):
        output = agent(data=data, existing_digital_twin=existing_digital_twin)
        #print(output.get_lm_usage())

    return output.digital_twin