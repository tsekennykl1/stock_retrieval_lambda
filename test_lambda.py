import json
from stock_retrieval_lambda import lambda_handler

# Load the test event
with open("/Users/kwokleungtse/Documents/AWS/yfinance-lambda/test_event.json") as f:
    event = json.load(f)

# Simulate the Lambda context (can be empty for local testing)
context = {}

# Invoke the Lambda function
response = lambda_handler(event, context)

# Print the response
print(json.dumps(response, indent=4))