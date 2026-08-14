# Keep ARM64 base image to match Lambda arm64 architecture
FROM public.ecr.aws/lambda/python:3.11-arm64

# Copy function code
COPY *.py /var/task

# Copy requirements
COPY requirements.txt .

# Install dependencies
RUN pip install -r requirements.txt --no-cache-dir

# ✅ filename = stock_retrieval_lambda.py → function = lambda_handler
CMD ["stock_retrieval_lambda.lambda_handler"]

