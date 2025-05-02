# Databricks notebook source
# notebooks/job_notebook.py

# COMMAND ----------

print("Starting notebook execution...")

# COMMAND ----------

# Import functions from the library installed as a wheel
# The package name 'src' comes from pyproject.toml
try:
    from src.main import get_greeting, add_numbers
    print("Successfully imported from mylibrary")
except ImportError as e:
    print(f"Error importing from mylibrary: {e}")
    # Optional: You might want to list installed packages to debug
    # %pip list
    raise e # Re-raise the error to fail the job if import fails

# COMMAND ----------

name_to_greet = "Databricks Bundle User"
greeting = get_greeting(name_to_greet)
print(greeting)

# COMMAND ----------

num1 = 15
num2 = 30
sum_result = add_numbers(num1, num2)
print(f"The sum of {num1} and {num2} is: {sum_result}")

# COMMAND ----------

print("Notebook finished successfully.")