FROM public.ecr.aws/lambda/python:3.11-arm64

# Copy function code
COPY stock_retrieval_lambda.py ${LAMBDA_TASK_ROOT}
COPY requirements.txt .

# Install dependencies
RUN pip install -r requirements.txt --no-cache-dir

# ✅ filename = stock_retrieval_lambda.py → function = lambda_handler
CMD ["stock_retrieval_lambda.lambda_handler"]

