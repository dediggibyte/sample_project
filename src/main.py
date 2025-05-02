# src/main.py
def get_greeting(name: str) -> str:
    """
    Generates a simple greeting message.

    Args:
        name: The name to greet.

    Returns:
        A greeting string.
    """
    if not name:
        return "Hello there!"
    return f"Hello, {name}!"

def add_numbers(a: int, b: int) -> int:
    """
    Adds two numbers.

    Args:
        a: First number.
        b: Second number.

    Returns:
        The sum of a and b.
    """
    return a + b