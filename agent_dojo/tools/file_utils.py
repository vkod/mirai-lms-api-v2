import os
import inspect


#Return the file name parameter from the training_set folder relative to the calling functions folder.
def get_training_set_directory(caller_file):
    caller_dir = os.path.dirname(os.path.abspath(caller_file))
    training_set_dir = os.path.join(caller_dir, 'training_set')
    if not os.path.exists(training_set_dir):
        os.makedirs(training_set_dir)
    return training_set_dir


def get_optimized_program_file_directory(caller_file):
    caller_dir = os.path.dirname(os.path.abspath(caller_file))
    optimized_program_dir = os.path.join(caller_dir, 'optimized_program')
    if not os.path.exists(optimized_program_dir):
        os.makedirs(optimized_program_dir)
    return optimized_program_dir

def get_persona_photographs_directory():
    # Start from the directory of this file
    current_dir = os.path.dirname(os.path.abspath(__file__))
    while True:
        if os.path.exists(os.path.join(current_dir, 'main.py')) or os.path.exists(os.path.join(current_dir, '.git')):
            break
        parent_dir = os.path.dirname(current_dir)
        if parent_dir == current_dir:
            raise FileNotFoundError("Project root not found.")
        current_dir = parent_dir
    persona_photographs_dir = os.path.join(current_dir, 'agent_dojo', 'persona_photographs')
    if not os.path.exists(persona_photographs_dir):
        os.makedirs(persona_photographs_dir)
    return persona_photographs_dir