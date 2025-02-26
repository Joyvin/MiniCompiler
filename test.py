def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n-1)

def main(): 
    num = 5
    print("Fibonnaci:", fibonacci(num))
    print("Factorial:", factorial(num))
