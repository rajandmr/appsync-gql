# AppSync GraphQL with Python Lambdas

A minimal Serverless Framework example that provisions two AWS AppSync GraphQL
APIs backed by Python 3.12 Lambda resolvers and DynamoDB. Mirrors the conventions
of the [`sns-sqs-fanout`](https://github.com/rajandmr/sns-sqs-fanout) reference
repo (split `resources/*.yml` + `functions/*.yml`, `uv` for deps, raw
CloudFormation resources orchestrated by `serverless.yml`).

## Architecture

```text
                          ┌─────────────┐        ┌───────────────┐
client (x-api-key) ───────▶│  AppSync    │──────▶│  Lambda       │──▶ DynamoDB
                          │  Todos API  │       │  (Python 3.12)│     TodosTable
                          │  API_KEY    │       └───────────────┘
                          └─────────────┘

                          ┌─────────────┐        ┌───────────────┐
client (Cognito JWT) ─────▶│  AppSync    │──────▶│  Lambda       │──▶ DynamoDB
client (x-api-key, read)──▶│  Orders API │       │  (Python 3.12)│     OrdersTable
                          │  COGNITO +  │       └───────────────┘
                          │  API_KEY    │
                          └─────────────┘
                                │
                                └── Cognito User Pool (OrdersUserPool)
```

- **Todos API** uses `API_KEY` authentication (with `AWS_IAM` as an additional
  provider) and exposes full CRUD over a `Todo` type.
- **Orders API** uses `COGNITO_USER_POOLS` as its primary auth, with `API_KEY`
  as an additional provider so queries can be read by API key while
  `createOrder` requires an authenticated Cognito user. AppSync's built-in
  `@aws_api_key` and `@aws_cognito_user_pools` directives enforce that split.

## Resources

- `resources/dynamodb.yml` — `TodosTable` (PK `id`) and `OrdersTable` (PK `orderId`), both on-demand billing.
- `resources/cognito.yml` — `OrdersUserPool` + `OrdersUserPoolClient` backing the Orders API.
- `resources/iam.yml` — Lambda execution role (DynamoDB CRUD), AppSync service roles (one per API, allowed to invoke the matching Lambdas), and a shared AppSync CloudWatch Logs role.
- `resources/appsync-todos.yml` — GraphQL API, API key, schema, one AWS_LAMBDA data source per resolver function, and one resolver per field.
- `resources/appsync-orders.yml` — same shape as the Todos API, with Cognito auth.
- `resources/outputs.yml` — CloudFormation outputs (API URLs, API keys, Cognito pool/client IDs).
- `functions/index.yml` — Lambda function definitions (one per GraphQL field).
- `schema/todos.graphql`, `schema/orders.graphql` — readable copies of the schemas (the source of truth used in the inline `AWS::AppSync::GraphQLSchema` definitions).

Each AppSync resolver is a *direct Lambda* resolver: the request mapping
template forwards `$context` to the Lambda as the event, and the response
mapping template returns `$context.result` unchanged. Each Lambda inspects
`event["arguments"]` and the DynamoDB table referenced by its environment
variable, then returns a plain Python dict that AppSync serializes back to the
GraphQL client.

## Prerequisites

- AWS credentials with permission to create CloudFormation, AppSync, Lambda,
  IAM, DynamoDB, and Cognito resources.
- Node.js and npm for the Serverless Framework v3.
- Python 3.12 (for local tooling/IDE only — `boto3` is provided by the AWS
  Lambda Python runtime). Optional: [`uv`](https://github.com/astral-sh/uv) to
  sync dev dependencies (`boto3`, `boto3-stubs`).

## Deploy

```bash
uv sync                 # optional: installs boto3 + boto3-stubs for local dev
npx osls deploy         # or: npx serverless deploy
```

Retrieve the outputs:

```bash
npx osls info --verbose
export TODOS_URL="https://YOUR_TODOS_API_ID.appsync-api.us-east-1.amazonaws.com/graphql"
export TODOS_KEY="da2-..."
export ORDERS_URL="https://YOUR_ORDERS_API_ID.appsync-api.us-east-1.amazonaws.com/graphql"
export ORDERS_KEY="da2-..."
export ORDERS_USER_POOL_ID="us-east-1_..."
export ORDERS_USER_POOL_CLIENT_ID="..."
```

## Query the Todos API (API_KEY)

Create a todo:

```bash
curl --request POST "$TODOS_URL" \
  --header "x-api-key: $TODOS_KEY" \
  --header "Content-Type: application/json" \
  --data '{"query":"mutation { createTodo(title:\"buy milk\",completed:false){ id title completed } }"}'
```

List todos:

```bash
curl --request POST "$TODOS_URL" \
  --header "x-api-key: $TODOS_KEY" \
  --header "Content-Type: application/json" \
  --data '{"query":"query { listTodos { id title completed } }"}'
```

## Query the Orders API

Reads are available with an API key (the schema's `@aws_api_key` directives
allow API-key access on the read fields):

```bash
curl --request POST "$ORDERS_URL" \
  --header "x-api-key: $ORDERS_KEY" \
  --header "Content-Type: application/json" \
  --data '{"query":"query { listOrders { orderId customerId total status } }"}'
```

`createOrder` requires a Cognito user. Register and authenticate:

```bash
aws cognito-idp sign-up \
  --client-id "$ORDERS_USER_POOL_CLIENT_ID" \
  --username user@example.com \
  --password 'Password123' \
  --user-attributes Name=email,Value=user@example.com

aws cognito-idp admin-confirm-sign-up \
  --user-pool-id "$ORDERS_USER_POOL_ID" \
  --username user@example.com

aws cognito-idp initiate-auth \
  --auth-flow USER_PASSWORD_AUTH \
  --client-id "$ORDERS_USER_POOL_CLIENT_ID" \
  --auth-parameters USERNAME=user@example.com,PASSWORD='Password123'
# copy AuthenticationResult.IdToken -> $TOKEN

curl --request POST "$ORDERS_URL" \
  --header "Authorization: $TOKEN" \
  --header "Content-Type: application/json" \
  --data '{"query":"mutation { createOrder(total:42.5,status:\"PENDING\"){ orderId customerId total status } }"}'
```

## Inspect logs

```bash
npx osls logs --function createTodo --tail
npx osls logs --function listTodos --tail
npx osls logs --function createOrder --tail
```

AppSync request logs are also written to CloudWatch Logs under the
`/aws/appsync/apis/<api-id>` log group.

## Package and cleanup

```bash
npx osls package     # validate + build the CloudFormation package locally
npx osls remove      # tear the whole stack down
```

## Push changes to GitHub

This repository uses the HTTPS GitHub URL for personal access token (PAT)
authentication. PATs do not authenticate an SSH remote such as
`git@github.com:...`.

Configure the remote once:

```bash
git remote add origin https://github.com/rajandmr/appsync-gql.git
# If origin already exists, use:
# git remote set-url origin https://github.com/rajandmr/appsync-gql.git
```

For a VPS, the safest convenient option is Git's in-memory credential cache.
It keeps the token available to subsequent terminals for eight hours without
writing it to disk:

```bash
git config --global credential.helper 'cache --timeout=28800'
git push -u origin main
```

When prompted, enter your GitHub username and use the PAT as the password.
Do not use your GitHub account password. The token should have the minimum
required repository permissions and a short expiration time.

On macOS, use the system keychain instead:

```bash
git config --global credential.helper osxkeychain
git push -u origin main
```

Never put a PAT in this README, a shell history entry, a Git remote URL, or a
committed file. Revoke a token immediately if it is exposed.

## Notes

- The AppSync GraphQL schemas are inlined as `Definition` strings in
  `AWS::AppSync::GraphQLSchema` resources so no separate S3 upload step is
  needed. The readable copies live under `schema/` for convenience.
- Because an AppSync `AWS::AppSync::DataSource` of type `LAMBDA` points at
  exactly one Lambda function, there is one data source per resolver field
  (5 for Todos, 3 for Orders), all sharing the appropriate AppSync service
  role.
- `createOrder` stores the caller's Cognito `sub` as `customerId` via
  `$context.identity.sub`, which the Lambda reads from `event["identity"]["sub"]`.