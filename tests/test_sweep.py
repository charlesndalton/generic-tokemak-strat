import brownie
from brownie import Contract
import pytest


def test_sweep_token_1(
    gov,
    token_1_vault,
    token_1_strategy,
    token_1,
    user,
    token_1_amount,
    toke_token,
    toke_whale,
):
    sweep(
        gov,
        token_1_vault,
        token_1_strategy,
        token_1,
        user,
        token_1_amount,
        toke_token,
        toke_whale,
    )


def test_sweep_token_2(
    gov,
    token_2_vault,
    token_2_strategy,
    token_2,
    user,
    token_2_amount,
    toke_token,
    toke_whale,
):
    sweep(
        gov,
        token_2_vault,
        token_2_strategy,
        token_2,
        user,
        token_2_amount,
        toke_token,
        toke_whale,
    )


def sweep(gov, vault, strategy, token, user, amount, toke_token, toke_whale):
    # Strategy want token doesn't work
    token.transfer(strategy, amount, {"from": user})
    assert token.address == strategy.want()
    assert token.balanceOf(strategy) > 0
    with brownie.reverts("!want"):
        strategy.sweep(token, {"from": gov})

    # Vault share token doesn't work
    with brownie.reverts("!shares"):
        strategy.sweep(vault.address, {"from": gov})

    toke_amount = 10 * (10 ** 18)

    before_balance = toke_token.balanceOf(gov)
    toke_token.transfer(strategy, toke_amount, {"from": toke_whale})
    assert toke_whale.address != strategy.want()
    assert toke_token.balanceOf(user) == 0
    strategy.sweep(toke_token, {"from": gov})
    assert toke_token.balanceOf(gov) == toke_amount + before_balance
