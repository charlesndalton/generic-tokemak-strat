import pytest


def test_revoke_strategy_from_vault_token_1(
    chain,
    token_1,
    token_1_vault,
    token_1_strategy,
    token_1_amount,
    user,
    gov,
    RELATIVE_APPROX,
    utils,
):
    revoke_strategy_from_vault(
        chain,
        token_1,
        token_1_vault,
        token_1_strategy,
        token_1_amount,
        user,
        gov,
        RELATIVE_APPROX,
        utils,
    )


def test_revoke_strategy_from_vault_token_2(
    chain,
    token_2,
    token_2_vault,
    token_2_strategy,
    token_2_amount,
    user,
    gov,
    RELATIVE_APPROX,
    utils,
):
    revoke_strategy_from_vault(
        chain,
        token_2,
        token_2_vault,
        token_2_strategy,
        token_2_amount,
        user,
        gov,
        RELATIVE_APPROX,
        utils,
    )


def revoke_strategy_from_vault(
    chain, token, vault, strategy, amount, user, gov, RELATIVE_APPROX, utils
):
    # Deposit to the vault and harvest
    token.approve(vault.address, amount, {"from": user})
    vault.deposit(amount, {"from": user})
    chain.sleep(1)
    strategy.harvest()
    assert pytest.approx(strategy.estimatedTotalAssets(), rel=RELATIVE_APPROX) == amount

    vault.revokeStrategy(strategy.address, {"from": gov})
    utils.make_funds_withdrawable_from_tokemak(strategy, gov, amount)
    strategy.harvest()
    assert pytest.approx(token.balanceOf(vault.address), rel=RELATIVE_APPROX) == amount


def test_revoke_strategy_from_strategy_token_1(
    chain,
    token_1,
    token_1_vault,
    token_1_strategy,
    token_1_amount,
    user,
    RELATIVE_APPROX,
    gov,
    utils,
):
    revoke_strategy_from_strategy(
        chain,
        token_1,
        token_1_vault,
        token_1_strategy,
        token_1_amount,
        user,
        RELATIVE_APPROX,
        gov,
        utils,
    )


def test_revoke_strategy_from_strategy_token_2(
    chain,
    token_2,
    token_2_vault,
    token_2_strategy,
    token_2_amount,
    user,
    RELATIVE_APPROX,
    gov,
    utils,
):
    revoke_strategy_from_strategy(
        chain,
        token_2,
        token_2_vault,
        token_2_strategy,
        token_2_amount,
        user,
        RELATIVE_APPROX,
        gov,
        utils,
    )


def revoke_strategy_from_strategy(
    chain, token, vault, strategy, amount, user, RELATIVE_APPROX, gov, utils
):
    # Deposit to the vault and harvest
    token.approve(vault.address, amount, {"from": user})
    vault.deposit(amount, {"from": user})
    chain.sleep(1)
    strategy.harvest()
    assert pytest.approx(strategy.estimatedTotalAssets(), rel=RELATIVE_APPROX) == amount

    strategy.setEmergencyExit()
    utils.make_funds_withdrawable_from_tokemak(strategy, gov, amount)
    strategy.harvest()
    assert pytest.approx(token.balanceOf(vault.address), rel=RELATIVE_APPROX) == amount
