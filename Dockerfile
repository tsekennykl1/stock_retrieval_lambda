FROM public.ecr.aws/lambda/python:3.12

# Copy your function code
COPY lambda_function.py ${LAMBDA_TASK_ROOT}

# Install dependencies if you have requirements.txt
COPY requirements.txt .
RUN pip install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"

# Set the handler
CMD ["lambda_function.lambda_handler"]
