FROM public.ecr.aws/lambda/python:3.11-arm64

# Install system build tools needed for packages with native extensions
RUN (command -v dnf && dnf -y install gcc gcc-c++ make && dnf clean all) || \
    (yum -y install gcc gcc-c++ make && yum clean all)

COPY *.py /var/task
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

CMD ["stock_retrieval_lambda.lambda_handler"]