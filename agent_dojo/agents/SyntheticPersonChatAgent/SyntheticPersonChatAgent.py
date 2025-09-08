import dspy
import os
import pandas as pd
from dspy.teleprompt import BootstrapFewShotWithRandomSearch
from agent_dojo.tools.file_utils import get_optimized_program_file_directory, get_training_set_directory
from agent_dojo.tools.lmtools import log_lm_execution_cost
from typing import Any,Literal

from dotenv import load_dotenv
load_dotenv()


TEST_SET="lead_personas_dataset_v6_10records_detailed_existing.csv"

reflection_model=dspy.LM(model="gpt-4.1", temperature=1.0, max_tokens=32000)
model_for_optimization=dspy.LM('openai/gpt-4.1',temperature=1.0, max_tokens=16000)
model_for_execution=dspy.LM('openai/gpt-4.1',temperature=1.0, max_tokens=16000)


class SyntheticPersonaChatSig(dspy.Signature):
    """Assume persona of the 'persona' provided. Answer insurance agent's questions. Answer like human with the same persona would do."""
    persona:str = dspy.InputField()
    history: dspy.History = dspy.InputField()
    question:str = dspy.InputField()
    answer: str = dspy.OutputField(desc="normal response like a human")

class SyntheticPersonChatAgent(dspy.Module):
    def __init__(self):
        super().__init__()
        self.answer_question = dspy.ChainOfThought(SyntheticPersonaChatSig)

    def forward(self, question,history, persona) -> Any:
        answer = self.answer_question(question=question,history=history, persona=persona)
        return dspy.Prediction(answer=answer.answer)


def _metric(example,pred,trace=None):
    answer = pred.answer

    if answer is None or answer.strip()=="":
        score=0
    else:
        score=1

    return dspy.Prediction(
        score=score,
    )
  

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


def _compute_score_with_feedback(gold, pred, trace=None, pred_name=None, pred_trace=None):

    metrics= _metric(gold, pred, trace)
    feedback_text = ""
    if metrics.score == 0:
        feedback_text = f"You did not answer the question. The score is {metrics.score}/1.0."
    elif metrics.score == 1:
        feedback_text = f"You answered the question well. The score is {metrics.score}/1.0."

    return dspy.Prediction(
        score=metrics.score/1.0,
        feedback=feedback_text,
    )

def optimize_using_gepa():
    test_set = _load_test_set(TEST_SET, __file__)
    with dspy.context(lm=model_for_optimization):
        program = SyntheticPersonChatAgent()
        optimizer = dspy.GEPA(metric=_compute_score_with_feedback,  num_threads=4, track_stats=True, track_best_outputs=True, reflection_lm=reflection_model,max_full_evals=5)
        optimized_program = optimizer.compile(program, trainset=test_set)
        _save_optimized_program(optimized_program, __file__)
        log_lm_execution_cost(model_for_optimization,"optimize_using_gepa_metrics")
        log_lm_execution_cost(reflection_model,"optimize_using_gepa_reflection")

def run(question,history, persona=""):
    agent = SyntheticPersonChatAgent()
    #optimized_program_file_dir = get_optimized_program_file_directory(__file__)
    #optimized_program_file = os.path.join(optimized_program_file_dir, 'SyntheticPersonChatAgent_Optimized')
    #if os.path.exists(optimized_program_file):
    #    agent = dspy.load(optimized_program_file)
    #else:
        #Throw error
       # raise FileNotFoundError("Optimized program not found. Please train the agent first.")

    lm=model_for_execution
    with dspy.context(lm=lm):
        output = agent(question=question, history=history, persona=persona)
        #print(output.get_lm_usage())
        log_lm_execution_cost(lm,"SyntheticPersonChatAgent_run")

    return output.answer