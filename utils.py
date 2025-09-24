import json

def load_job_profiles(file_path: str = "job_profile.json") -> dict:
    """
    Loads the job profiles from the specified JSON file.
    
    Args:
        file_path (str): The path to the job_profile.json file.
        
    Returns:
        dict: A dictionary containing the job profiles.
    """
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: The file {file_path} was not found.")
        return {}
    except json.JSONDecodeError:
        print(f"Error: The file {file_path} is not a valid JSON file.")
        return {}
