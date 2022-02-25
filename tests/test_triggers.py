import brownie
from brownie import Contract
import pytest


def test_triggers_token_1(
    chain, gov, token_1_vault, token_1_strategy, token_1, token_1_amount, user
):
    triggers(chain, gov, token_1_vault, token_1_strategy, token_1, token_1_amount, user)


def test_triggers_token_2(
    chain, gov, token_2_vault, token_2_strategy, token_2, token_2_amount, user
):
    triggers(chain, gov, token_2_vault, token_2_strategy, token_2, token_2_amount, user)


def triggers(chain, gov, vault, strategy, token, amount, user):
    # Deposit to the vault and harvest
    token.approve(vault.address, amount, {"from": user})
    vault.deposit(amount, {"from": user})
    vault.updateStrategyDebtRatio(strategy.address, 5_000, {"from": gov})
    chain.sleep(1)
    strategy.harvest()

    strategy.harvestTrigger(0)
    strategy.tendTrigger(0)
