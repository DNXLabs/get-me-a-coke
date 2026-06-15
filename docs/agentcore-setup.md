# AgentCore Payments Setup

Manual prerequisites for AgentCore Payments. Run these once before first use.

## Prerequisites

1. AWS CLI configured with profile `nonprod-dnxai`
2. AgentCore CLI installed (`pip install bedrock-agentcore-cli`)
3. Coinbase CDP credentials (or Stripe Privy)

## Step 1: Create Coinbase CDP Credentials

1. Go to [Coinbase Developer Platform](https://portal.cdp.coinbase.com/)
2. Create a new API key with wallet permissions
3. Save the API key ID and private key

## Step 2: Store Credentials in AgentCore Identity

```bash
# Store Coinbase CDP credentials
agentcore identity create \
  --name coinbase-cdp \
  --type coinbase-cdp \
  --api-key-id YOUR_CDP_API_KEY_ID \
  --private-key-file path/to/cdp-private-key.pem \
  --region ap-southeast-2 \
  --profile nonprod-dnxai
```

## Step 3: Create Payment Manager + Connector

```bash
# Create payment manager
agentcore payments create-manager \
  --name get-me-a-coke-payments \
  --region ap-southeast-2 \
  --profile nonprod-dnxai

# Create connector (links to Coinbase CDP identity)
agentcore payments create-connector \
  --manager-name get-me-a-coke-payments \
  --identity-name coinbase-cdp \
  --type coinbase-cdp \
  --region ap-southeast-2 \
  --profile nonprod-dnxai
```

## Step 4: Create Payment Instrument (Wallet)

```bash
agentcore payments create-instrument \
  --manager-name get-me-a-coke-payments \
  --type embedded-wallet \
  --network base-sepolia \
  --region ap-southeast-2 \
  --profile nonprod-dnxai
```

Note the `payment_instrument_id` from the output.

## Step 5: Fund the Wallet (Testnet)

1. Get the wallet address from the payment instrument
2. Use a [Base Sepolia faucet](https://www.alchemy.com/faucets/base-sepolia) to get testnet ETH
3. Bridge or mint testnet USDC on Base Sepolia

## Step 6: Update .env

```bash
PAYMENT_MANAGER_ARN=arn:aws:bedrock-agentcore:ap-southeast-2:<AWS_ACCOUNT_ID>:payment-manager/YOUR_MANAGER_ID
PAYMENT_INSTRUMENT_ID=YOUR_INSTRUMENT_ID
PAYMENT_SESSION_ID=YOUR_SESSION_ID
PAYMENT_USER_ID=thiago
```

## Step 7: Configure AgentCore Runtime

```bash
# After CDK deploys the IAM role
agentcore configure \
  --agent-name get-me-a-coke-agent-dev \
  --role-arn arn:aws:iam::<AWS_ACCOUNT_ID>:role/get-me-a-coke-agentcore-runtime-dev \
  --region ap-southeast-2 \
  --profile nonprod-dnxai

agentcore launch
```
