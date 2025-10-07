import hou #type: ignore

def run_increment_save():
    """
    Increment the save number of the current HIP file.
    """
    old_file_name = hou.hipFile.basename()
    try:
        hou.hipFile.saveAndIncrementFileName()
        new_file_name = hou.hipFile.basename()
        hou.ui.setStatusMessage(f"Saved {old_file_name} >>> {new_file_name}", hou.severityType.Message)
    except hou.OperationFailed as e:
        hou.ui.displayError(f"Error incrementing save: {e}")

if __name__ == "__main__":
    pass