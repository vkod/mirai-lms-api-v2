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