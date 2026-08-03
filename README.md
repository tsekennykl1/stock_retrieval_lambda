# stock_retrieval_lambda

A Python AWS Lambda function that retrieves stock data using [yfinance](https://github.com/ranaroussi/yfinance), packaged as a container image and deployed to AWS ECR.

## Project Structure

```
.
├── .github/
│   └── workflows/
│       └── deploy.yml       # GitHub Actions CI/CD pipeline
├── lambda_function.py       # Lambda handler
├── requirements.txt         # Python dependencies
├── Dockerfile               # Container image definition
└── README.md
```

## Lambda Function

The handler accepts an event with the following shape:

```json
{
  "tickers": ["AAPL", "MSFT"],
  "period": "1d"
}
```

| Field     | Type            | Required | Default | Description                              |
|-----------|-----------------|----------|---------|------------------------------------------|
| `tickers` | `list[str]`     | Yes      | —       | List of ticker symbols to retrieve       |
| `period`  | `str`           | No       | `"1d"`  | yfinance period string (e.g. `1d`, `5d`, `1mo`) |

**Example response:**

```json
{
  "statusCode": 200,
  "body": "{\"AAPL\": {\"open\": 213.5, \"high\": 215.0, \"low\": 212.8, \"close\": 214.24, \"volume\": 55000000, \"date\": \"2024-01-01\"}}"
}
```

## CI/CD — GitHub Actions → AWS ECR

The workflow in `.github/workflows/deploy.yml` triggers on every push to `main` and:

1. Builds the Docker image using the Lambda Python 3.12 base image.
2. Pushes it to the ECR repository (tagged with both the commit SHA and `latest`).
3. Updates the Lambda function to use the new image.

### Required GitHub Secrets

| Secret name             | Description                                      |
|-------------------------|--------------------------------------------------|
| `AWS_ACCESS_KEY_ID`     | IAM access key with ECR + Lambda permissions     |
| `AWS_SECRET_ACCESS_KEY` | Corresponding IAM secret key                     |
| `AWS_REGION`            | AWS region (e.g. `us-east-1`)                    |
| `ECR_REPOSITORY`        | ECR repository name (e.g. `stock-retrieval`)     |
| `LAMBDA_FUNCTION_NAME`  | Name of the Lambda function to update            |

### IAM permissions required

The IAM user / role needs at minimum:

```json
{
  "Effect": "Allow",
  "Action": [
    "ecr:GetAuthorizationToken",
    "ecr:BatchCheckLayerAvailability",
    "ecr:GetDownloadUrlForLayer",
    "ecr:BatchGetImage",
    "ecr:InitiateLayerUpload",
    "ecr:UploadLayerPart",
    "ecr:CompleteLayerUpload",
    "ecr:PutImage",
    "lambda:UpdateFunctionCode"
  ],
  "Resource": "*"
}
```

## Local Development

```bash
# Build the image
docker build -t stock-retrieval-lambda .

# Run locally (requires AWS credentials for yfinance network access)
docker run -p 9000:8080 stock-retrieval-lambda

# Invoke the function
curl -XPOST "http://localhost:9000/2015-03-31/functions/function/invocations" \
  -d '{"tickers": ["AAPL", "TSLA"], "period": "1d"}'
```
