def python(command: str) -> list[str]:
    """
    Returns commands that will run the specified command as a Python script.
    """
    return ["python3", "-c", command]


def bash(command: str) -> list[str]:
    """
    Returns commands that will run in a bash script.
    """
    return ["bash", "-c", command]
