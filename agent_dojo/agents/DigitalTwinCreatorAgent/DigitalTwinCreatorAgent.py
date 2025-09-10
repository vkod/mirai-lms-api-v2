import dspy
import os
import pandas as pd
from dspy.teleprompt import BootstrapFewShotWithRandomSearch
from agent_dojo.tools.file_utils import get_optimized_program_file_directory, get_training_set_directory
from agent_dojo.tools.lmtools import log_lm_execution_cost
from typing import Any,Literal

from dotenv import load_dotenv
load_dotenv()

#dspy.settings.configure( track_usage=True )

#import mlflow

#mlflow.set_tracking_uri("http://localhost:5000")
#mlflow.set_experiment("DSPy")

#mlflow.dspy.autolog(
    # Log the optimization progress
#    log_compiles=True,
    # Log the evaluation results
#    log_evals=True,
    # Log traces from module executions
#    log_traces=True
#)

TEST_SET="lead_personas_dataset_v6_10records_detailed_existing.csv"

reflection_model=dspy.LM(model="gpt-4.1", temperature=1.0, max_tokens=32000)
model_for_optimization=dspy.LM('openai/gpt-4.1-mini',temperature=1.0, max_tokens=16000)
model_for_execution=dspy.LM('openai/gpt-4.1-mini',temperature=1.0, max_tokens=16000)


class ExtractDigitalTwinSig(dspy.Signature):
    """Create an imaginary persona based on data provided and update the digital twin with data as much as possible.
    If existing_digital_twin information is provided, update it with new or changed information based on clear signals in data"""
    data: str = dspy.InputField()
    existing_digital_twin:str = dspy.InputField()
    digital_twin: str = dspy.OutputField(desc="markdown-formatted")

class ClassifyLeadSig(dspy.Signature):
    """Classify the lead based on the digital twin information"""
    digital_twin: str = dspy.InputField()
    lead_classification: Literal["hot", "warm", "cold"] = dspy.OutputField()

class DigitalTwinCreatorAgent(dspy.Module):
    def __init__(self):
        super().__init__()
        self.perform_digital_twin_extraction = dspy.ChainOfThought(ExtractDigitalTwinSig)
        self.classify_lead = dspy.ChainOfThought(ClassifyLeadSig)

    def forward(self, data,existing_digital_twin):
        digital_twin = self.perform_digital_twin_extraction(data=data,existing_digital_twin=existing_digital_twin).digital_twin
        lead_classification = self.classify_lead(digital_twin=digital_twin).lead_classification
        return dspy.Prediction(digital_twin=digital_twin, lead_classification=lead_classification)

class AssessDigitalTwinQualitySig(dspy.Signature):
    """Assess the quality of digital twin text created"""
    assessed_text = dspy.InputField()
    assessment_question = dspy.InputField()
    assessment_answer: bool = dspy.OutputField()

class AssessUpdateToDigitalTwinSig(dspy.Signature):
    """Assess if the updates made to the digitial twin are good"""
    existing_digital_twin = dspy.InputField()
    digital_twin = dspy.InputField()
    assessment_question = dspy.InputField()
    assessment_answer: bool = dspy.OutputField()

def _metric(example,pred,trace=None):
    digital_twin = pred.digital_twin
    assessment_question = "Does the assessed text have enough information captured to act as a digital twin of a lead?"
    enough_information = dspy.Predict(AssessDigitalTwinQualitySig)(assessed_text=digital_twin, assessment_question=assessment_question)


    assessment_question = "Is the assessed text in markdown format?"
    is_in_markdown_format = dspy.Predict(AssessDigitalTwinQualitySig)(assessed_text=digital_twin, assessment_question=assessment_question).assessment_answer

    digital_twin_update_good=False

    #For some reason existing_digital_twin is sometimes float
    if isinstance(example.existing_digital_twin, float):
        example.existing_digital_twin = str(example.existing_digital_twin)

    if example.existing_digital_twin!='nan' and example.existing_digital_twin.strip()!="":
        assessment_question = "Are the updates made to the digital twin good and relevant?"
        digital_twin_update_good = dspy.Predict(AssessUpdateToDigitalTwinSig)(existing_digital_twin=example.existing_digital_twin, digital_twin=digital_twin, assessment_question=assessment_question).assessment_answer
    else:
        digital_twin_update_good=True

    #Search digital_twin text to make sure it has "Financial Information", "Occupation", "Annual Income", "Persona Summary"
    contains_key_sections=False
    if "Financial Information" in digital_twin and "Occupation" in digital_twin and "Annual Income" in digital_twin and "Persona Summary" in digital_twin:
        contains_key_sections=True

    #Print all three values
    print(f"enough_information: {enough_information.assessment_answer}, contains_key_sections: {contains_key_sections}, digital_twin_update_good: {digital_twin_update_good}")
    score=enough_information.assessment_answer + contains_key_sections + digital_twin_update_good + is_in_markdown_format

    #if trace is not None: return score>=3
    #return score/4.0
    return dspy.Prediction(
        score=score,
        enough_information=enough_information.assessment_answer,
        contains_key_sections=contains_key_sections,
        digital_twin_update_good=digital_twin_update_good,
        is_in_markdown_format=is_in_markdown_format
    )

def _simple_metric(example,pred,trace=None):
    digital_twin = pred.digital_twin
    
    contains_key_sections=False
    if "Financial Information" in digital_twin and "Occupation" in digital_twin and "Annual Income" in digital_twin and "Persona Summary" in digital_twin:
        contains_key_sections=True

    return contains_key_sections

def optimize():
    optimize_using_gepa()


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
    lm=model_for_optimization
    with dspy.context(lm=lm):
        program = DigitalTwinCreatorAgent()
        config = dict(max_bootstrapped_demos=4, max_labeled_demos=4, num_candidate_programs=2, num_threads=1)
        optimizer = BootstrapFewShotWithRandomSearch(metric=_simple_metric, **config)
        optimized_program = optimizer.compile(program, trainset=test_set)
        _save_optimized_program(optimized_program, __file__)
        log_lm_execution_cost(lm,"optimize_using_bootstrapfewshot")

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

def _compute_score_with_feedback(gold, pred, trace=None, pred_name=None, pred_trace=None):

    metrics= _metric(gold, pred, trace)
    feedback_text = ""
    if metrics.score==4:
        if gold.existing_digital_twin!='nan' and gold.existing_digital_twin.strip()!="":
            feedback_text = "The digital twin created is of high quality based on three criteria: enough information to act as a digital twin, contains key sections, and good updates to existing digital twin."
        else:
            feedback_text = "The digital twin created is of high quality based on two criteria: enough information to act as a digital twin, and contains key sections."
    
    if metrics.enough_information==False:
        feedback_text = f"The digital twin created did not have enough information to act as a digital twin. The score is {metrics.score}/4.0."

    if metrics.is_in_markdown_format==False:
        feedback_text = f"The digital twin created is not in markdown format. The score is {metrics.score}/4.0. The digital twin should be in markdown format."

    if metrics.contains_key_sections==False:
        feedback_text = f"The digital twin created did not contain key sections. The score is {metrics.score}/4.0. Digital twin should contain 'Financial Information', 'Occupation', 'Annual Income' and 'Persona Summary'"

    if metrics.digital_twin_update_good==False:
        feedback_text = f"The updates made to the existing digital twin were not good and relevant. The score is {metrics.score}/4.0."

    return dspy.Prediction(
        score=metrics.score/4.0,
        feedback=feedback_text,
    )

def optimize_using_gepa():
    test_set = _load_test_set(TEST_SET, __file__)
    with dspy.context(lm=model_for_optimization):
        program = DigitalTwinCreatorAgent()
        optimizer = dspy.GEPA(metric=_compute_score_with_feedback,  num_threads=4, track_stats=True, track_best_outputs=True, reflection_lm=reflection_model,max_full_evals=15)
        optimized_program = optimizer.compile(program, trainset=test_set)
        _save_optimized_program(optimized_program, __file__)
        log_lm_execution_cost(model_for_optimization,"optimize_using_gepa_metrics")
        log_lm_execution_cost(reflection_model,"optimize_using_gepa_reflection")

def run(data, existing_digital_twin=None):
    agent = DigitalTwinCreatorAgent()
    optimized_program_file_dir = get_optimized_program_file_directory(__file__)
    optimized_program_file = os.path.join(optimized_program_file_dir, 'DigitalTwinCreatorAgent_Optimized')
    if os.path.exists(optimized_program_file):
        agent = dspy.load(optimized_program_file)
    else:
        #Throw error
        raise FileNotFoundError("Optimized program not found. Please train the agent first.")

    lm=model_for_execution
    with dspy.context(lm=lm):
        output = agent(data=data, existing_digital_twin=existing_digital_twin)
        #print(output.get_lm_usage())
        log_lm_execution_cost(lm,"DigitalTwinCreatorAgent")

    return output.digital_twin