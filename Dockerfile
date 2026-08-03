FROM public.ecr.aws/lambda/python:3.12

COPY requirements.txt ${LAMBDA_TASK_ROOT}/
RUN pip install -r ${LAMBDA_TASK_ROOT}/requirements.txt --target "${LAMBDA_TASK_ROOT}" --no-cache-dir

COPY lambda_function.py ${LAMBDA_TASK_ROOT}/

CMD ["lambda_function.handler"]
