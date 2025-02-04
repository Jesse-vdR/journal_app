def greet(name):
    """A simple greeting function"""
    return f"Hello, {name}! Welcome to the AI Website."

def calculate_sum(numbers):
    """Calculate the sum of a list of numbers"""
    return sum(numbers)

if __name__ == "__main__":
    # Example usage
    print(greet("User"))
    numbers = [1, 2, 3, 4, 5]
    print(f"Sum of {numbers} is {calculate_sum(numbers)}")
