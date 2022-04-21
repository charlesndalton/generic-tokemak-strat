import brownie
from brownie import Contract
import pytest


def test_operation_token_1(
    chain,
    token_1,
    token_1_vault,
    token_1_strategy,
    user,
    token_1_amount,
    RELATIVE_APPROX,
    gov,
    utils,
):
    operation(
        chain,
        token_1,
        token_1_vault,
        token_1_strategy,
        user,
        token_1_amount,
        RELATIVE_APPROX,
        gov,
        utils,
    )


def test_operation_token_2(
    chain,
    token_2,
    token_2_vault,
    token_2_strategy,
    user,
    token_2_amount,
    RELATIVE_APPROX,
    gov,
    utils,
):
    operation(
        chain,
        token_2,
        token_2_vault,
        token_2_strategy,
        user,
        token_2_amount,
        RELATIVE_APPROX,
        gov,
        utils,
    )


def operation(chain, token, vault, strategy, user, amount, RELATIVE_APPROX, gov, utils):
    # Deposit to the vault
    user_balance_before = token.balanceOf(user)
    utils.move_user_funds_to_vault(user, vault, token, amount)

    # harvest
    chain.sleep(1)
    strategy.harvest()
    assert pytest.approx(strategy.estimatedTotalAssets(), rel=RELATIVE_APPROX) == amount

    # tend()
    strategy.tend()

    utils.make_funds_withdrawable_from_tokemak(strategy, gov, amount)

    # withdrawal
    vault.withdraw({"from": user})
    assert (
        pytest.approx(token.balanceOf(user), rel=RELATIVE_APPROX) == user_balance_before
    )


def test_operation_when_tokemak_pool_paused_token_1(
    chain,
    token_1,
    token_1_vault,
    token_1_strategy,
    user,
    token_1_amount,
    RELATIVE_APPROX,
    token_1_tokemak_liquidity_pool,
    tokemak_multisig,
    utils,
):
    operation_when_tokemak_pool_paused(
        chain,
        token_1,
        token_1_vault,
        token_1_strategy,
        user,
        token_1_amount,
        RELATIVE_APPROX,
        token_1_tokemak_liquidity_pool,
        tokemak_multisig,
        utils,
    )


def test_operation_when_tokemak_pool_paused_token_2(
    chain,
    token_2,
    token_2_vault,
    token_2_strategy,
    user,
    token_2_amount,
    RELATIVE_APPROX,
    token_2_tokemak_liquidity_pool,
    tokemak_multisig,
    utils,
):
    operation_when_tokemak_pool_paused(
        chain,
        token_2,
        token_2_vault,
        token_2_strategy,
        user,
        token_2_amount,
        RELATIVE_APPROX,
        token_2_tokemak_liquidity_pool,
        tokemak_multisig,
        utils,
    )


def operation_when_tokemak_pool_paused(
    chain,
    token,
    vault,
    strategy,
    user,
    amount,
    RELATIVE_APPROX,
    tokemak_liquidity_pool,
    tokemak_multisig,
    utils,
):
    tokemak_liquidity_pool.pause({"from": tokemak_multisig})

    # Deposit to the vault
    user_balance_before = token.balanceOf(user)
    utils.move_user_funds_to_vault(user, vault, token, amount)

    # harvest & tend
    chain.sleep(1)
    strategy.harvest()
    strategy.tend()

    # since paused, strategy shouldn't have been able to do anything with the WETH
    assert (
        pytest.approx(token.balanceOf(strategy.address), rel=RELATIVE_APPROX) == amount
    )

    # withdrawal
    vault.withdraw({"from": user})
    assert (
        pytest.approx(token.balanceOf(user), rel=RELATIVE_APPROX) == user_balance_before
    )

    tokemak_liquidity_pool.unpause({"from": tokemak_multisig})
