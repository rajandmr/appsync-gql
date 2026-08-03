# Testing

This document describes how to deploy and exercise both AppSync APIs. The
commands below use the AWS credentials stored in `.env`.

## Prerequisites

- Node.js and `npx`
- Python 3.12
- `curl`
- AWS credentials with permissions to deploy and invoke the stack
- AWS CLI and `jq` for the Cognito test flow

The project uses the Serverless Framework-compatible `osls` CLI through `npx`.

## Load AWS credentials

Do not commit `.env` or print its contents. Load it only into the current shell:

```bash
set -a
. ./.env
set +a
```

Confirm that the required variables are present without displaying their values:

```bash
for variable in AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_REGION; do
  test -n "${!variable:-}" && echo "$variable is set" || echo "$variable is missing"
done
```

## Package and deploy

Validate the Python sources and CloudFormation package:

```bash
python -m compileall -q functions utils
npx osls package
```

Deploy the `dev` stage:

```bash
npx osls deploy --stage dev
```

Inspect the deployed stack and retrieve its outputs:

```bash
npx osls info --stage dev --verbose
```

Copy these values from the `Stack Outputs` section into shell variables. Do not
commit them to the repository:

```bash
export TODOS_URL="https://YOUR_TODOS_API_ID.appsync-api.us-east-1.amazonaws.com/graphql"
export TODOS_KEY="YOUR_TODOS_API_KEY"
export ORDERS_URL="https://YOUR_ORDERS_API_ID.appsync-api.us-east-1.amazonaws.com/graphql"
export ORDERS_KEY="YOUR_ORDERS_API_KEY"
export ORDERS_USER_POOL_ID="us-east-1_..."
export ORDERS_USER_POOL_CLIENT_ID="..."
```

## Todos API: API-key CRUD test

The Todos API uses an API key. Create a temporary todo and save its ID:

```bash
create_response=$(curl --fail-with-body -sS "$TODOS_URL" \
  --header "x-api-key: $TODOS_KEY" \
  --header 'Content-Type: application/json' \
  --data '{"query":"mutation { createTodo(title:\"testing\",completed:false){ id title completed } } }')

echo "$create_response"
TODO_ID=$(printf '%s' "$create_response" | \
  python -c 'import json,sys; d=json.load(sys.stdin); assert not d.get("errors"), d; print(d["data"]["createTodo"]["id"])')
```

Read, update, list, and delete the todo:

```bash
curl --fail-with-body -sS "$TODOS_URL" \
  --header "x-api-key: $TODOS_KEY" \
  --header 'Content-Type: application/json' \
  --data "{\"query\":\"query { getTodo(id:\\\"$TODO_ID\\\"){ id title completed } }\"}"

curl --fail-with-body -sS "$TODOS_URL" \
  --header "x-api-key: $TODOS_KEY" \
  --header 'Content-Type: application/json' \
  --data "{\"query\":\"mutation { updateTodo(id:\\\"$TODO_ID\\\",title:\\\"updated\\\",completed:true){ id title completed } }\"}"

curl --fail-with-body -sS "$TODOS_URL" \
  --header "x-api-key: $TODOS_KEY" \
  --header 'Content-Type: application/json' \
  --data '{"query":"query { listTodos { id title completed } }"}'

curl --fail-with-body -sS "$TODOS_URL" \
  --header "x-api-key: $TODOS_KEY" \
  --header 'Content-Type: application/json' \
  --data "{\"query\":\"mutation { deleteTodo(id:\\\"$TODO_ID\\\"){ id } }\"}"
```

Each successful response should contain a `data` object and no `errors` array.
After deletion, `getTodo` should return `"data":{"getTodo":null}`.

The optional `title` and `completed` arguments may both be omitted from
`updateTodo`; this should return the existing todo rather than fail.

## Orders API: API-key read authorization

The Orders API permits API-key reads but requires Cognito authentication for
`createOrder`.

Test a read with the API key:

```bash
curl --fail-with-body -sS "$ORDERS_URL" \
  --header "x-api-key: $ORDERS_KEY" \
  --header 'Content-Type: application/json' \
  --data '{"query":"query { listOrders { orderId customerId total status } }"}'
```

Verify that API-key writes are rejected:

```bash
curl --fail-with-body -sS "$ORDERS_URL" \
  --header "x-api-key: $ORDERS_KEY" \
  --header 'Content-Type: application/json' \
  --data '{"query":"mutation { createOrder(total:42.5,status:\"PENDING\"){ orderId customerId total status } }"}'
```

The response should contain an `Unauthorized` error for `createOrder`.

## Orders API: Cognito-authenticated write

Create a temporary Cognito user. The password must satisfy the user pool policy
(at least eight characters, including uppercase, lowercase, and a number):

```bash
export TEST_USERNAME="pi-test-$(date +%s)@example.com"
export TEST_PASSWORD='Testing123!'

aws cognito-idp sign-up \
  --client-id "$ORDERS_USER_POOL_CLIENT_ID" \
  --username "$TEST_USERNAME" \
  --password "$TEST_PASSWORD" \
  --user-attributes Name=email,Value="$TEST_USERNAME"

aws cognito-idp admin-confirm-sign-up \
  --user-pool-id "$ORDERS_USER_POOL_ID" \
  --username "$TEST_USERNAME"
```

Authenticate and extract the ID token:

```bash
export TOKEN=$(aws cognito-idp initiate-auth \
  --auth-flow USER_PASSWORD_AUTH \
  --client-id "$ORDERS_USER_POOL_CLIENT_ID" \
  --auth-parameters "USERNAME=$TEST_USERNAME,PASSWORD=$TEST_PASSWORD" \
  | jq -r '.AuthenticationResult.IdToken')
```

Create an order with the Cognito token:

```bash
order_response=$(curl --fail-with-body -sS "$ORDERS_URL" \
  --header "Authorization: $TOKEN" \
  --header 'Content-Type: application/json' \
  --data '{"query":"mutation { createOrder(total:42.5,status:\"PENDING\"){ orderId customerId total status } }"}')

echo "$order_response"
```

The response should contain an order with:

- A generated `orderId`
- A non-empty `customerId` matching the Cognito user's `sub`
- `total` equal to `42.5`
- `status` equal to `PENDING`

Use the returned `orderId` to verify authenticated and API-key reads:

```bash
export ORDER_ID=$(printf '%s' "$order_response" | \
  jq -r '.data.createOrder.orderId')

curl --fail-with-body -sS "$ORDERS_URL" \
  --header "Authorization: $TOKEN" \
  --header 'Content-Type: application/json' \
  --data "{\"query\":\"query { getOrder(orderId:\\\"$ORDER_ID\\\"){ orderId customerId total status } }\"}"

curl --fail-with-body -sS "$ORDERS_URL" \
  --header "x-api-key: $ORDERS_KEY" \
  --header 'Content-Type: application/json' \
  --data "{\"query\":\"query { getOrder(orderId:\\\"$ORDER_ID\\\"){ orderId customerId total status } }\"}"
```

Both reads should succeed. API-key `createOrder` must remain unauthorized.

## Lambda logs

Inspect resolver logs if a GraphQL response contains errors:

```bash
npx osls logs --function createTodo --stage dev --startTime 10m
npx osls logs --function updateTodo --stage dev --startTime 10m
npx osls logs --function createOrder --stage dev --startTime 10m
npx osls logs --function listOrders --stage dev --startTime 10m
```

## Cleanup

Delete temporary Cognito users after testing:

```bash
aws cognito-idp admin-delete-user \
  --user-pool-id "$ORDERS_USER_POOL_ID" \
  --username "$TEST_USERNAME"
unset TOKEN TEST_PASSWORD TEST_USERNAME
```

There is no GraphQL `deleteOrder` mutation. Remove temporary order records
from the `appsync-gql-orders` DynamoDB table using the AWS console or
`aws dynamodb delete-item` if test data should not remain.

To remove the complete development stack instead:

```bash
npx osls remove --stage dev
```
