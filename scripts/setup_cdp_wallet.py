"""Setup script: Create a CDP wallet and fund it with testnet ETH on Base Sepolia.

Prerequisites:
1. Get credentials from https://portal.cdp.coinbase.com
2. Add to .env:
   CDP_API_KEY_ID=your-api-key-id
   CDP_API_KEY_SECRET=your-api-key-secret
   CDP_WALLET_SECRET=your-wallet-secret

Usage:
    uv run python scripts/setup_cdp_wallet.py
"""

from __future__ import annotations

import asyncio

from dotenv import load_dotenv

load_dotenv()


async def main() -> None:
    from cdp import CdpClient

    print("🔑 Connecting to CDP...")
    async with CdpClient() as cdp:
        # Create an EVM account on Base Sepolia
        print("📦 Creating EVM account...")
        account = await cdp.evm.create_account(name="get-me-a-coke-agent")
        print(f"✅ Created EVM account: {account.address}")

        # Fund with testnet ETH
        print("💰 Requesting testnet ETH from faucet...")
        faucet_hash = await cdp.evm.request_faucet(
            address=account.address,
            network="base-sepolia",
            token="eth",
        )
        print(f"✅ Faucet tx: https://sepolia.basescan.org/tx/{faucet_hash}")

        # Also request testnet USDC if available
        try:
            print("💰 Requesting testnet USDC from faucet...")
            usdc_hash = await cdp.evm.request_faucet(
                address=account.address,
                network="base-sepolia",
                token="usdc",
            )
            print(f"✅ USDC faucet tx: https://sepolia.basescan.org/tx/{usdc_hash}")
        except Exception as e:
            print(f"⚠️  USDC faucet not available: {e}")
            print("   You may need to bridge USDC manually or use a different faucet.")

        print("\n" + "=" * 60)
        print("SETUP COMPLETE")
        print("=" * 60)
        print(f"\nWallet address: {account.address}")
        print(f"Network: Base Sepolia (testnet)")
        print(f"\nAdd this to your .env for AgentCore Payments:")
        print(f"  CDP_WALLET_ADDRESS={account.address}")
        print("\nNext steps:")
        print("  1. Set up AgentCore Payment Manager (see docs/agentcore-setup.md)")
        print("  2. Link this wallet as a Payment Instrument")
        print("  3. Add PAYMENT_MANAGER_ARN and PAYMENT_INSTRUMENT_ID to .env")


if __name__ == "__main__":
    asyncio.run(main())
