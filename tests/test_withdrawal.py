import pytest

# test some of the possible scenarios involving withdrawals from the strategy


def test_withdraw_without_strategist_intervention_token_1(
    chain,
    token_1,
    token_1_vault,
    token_1_strategy,
    user,
    token_1_amount,
    RELATIVE_APPROX,
    tokemak_manager,
    token_1_tokemak_liquidity_pool,
    utils,
):
    withdraw_without_strategist_intervention(
        chain,
        token_1,
        token_1_vault,
        token_1_strategy,
        user,
        token_1_amount,
        RELATIVE_APPROX,
        tokemak_manager,
        token_1_tokemak_liquidity_pool,
        utils,
    )


def test_withdraw_without_strategist_intervention_token_2(
    chain,
    token_2,
    token_2_vault,
    token_2_strategy,
    user,
    token_2_amount,
    RELATIVE_APPROX,
    tokemak_manager,
    token_2_tokemak_liquidity_pool,
    utils,
):
    withdraw_without_strategist_intervention(
        chain,
        token_2,
        token_2_vault,
        token_2_strategy,
        user,
        token_2_amount,
        RELATIVE_APPROX,
        tokemak_manager,
        token_2_tokemak_liquidity_pool,
        utils,
    )


# withdraw the full amount out of the strategy without any external calls to strategy.requestWithdrawal()
def withdraw_without_strategist_intervention(
    chain,
    token,
    vault,
    strategy,
    user,
    amount,
    RELATIVE_APPROX,
    tokemak_manager,
    tokemak_liquidity_pool,
    utils,
):
    # Deposit to the vault
    user_balance_before = token.balanceOf(user)
    utils.move_user_funds_to_vault(user, vault, token, amount)

    # Harvest & tend
    chain.sleep(1)
    strategy.harvest()
    assert pytest.approx(strategy.estimatedTotalAssets(), rel=RELATIVE_APPROX) == amount
    strategy.tend()

    # Strategy shouldn't have requested any withdrawal yet
    (
        cycleIndexWhenWithdrawable,
        amountRequested,
    ) = tokemak_liquidity_pool.requestedWithdrawals(strategy.address)
    assert pytest.approx(amountRequested, rel=RELATIVE_APPROX) == 0

    vault.withdraw({"from": user})

    # Strategy should have initiated withdrawal, but not completed yet
    (
        cycleIndexWhenWithdrawable,
        amountRequested,
    ) = tokemak_liquidity_pool.requestedWithdrawals(strategy.address)
    assert pytest.approx(amountRequested, rel=RELATIVE_APPROX) == amount
    assert (
        pytest.approx(token.balanceOf(user), rel=RELATIVE_APPROX)
        == user_balance_before - amount
    )
    assert cycleIndexWhenWithdrawable == tokemak_manager.getCurrentCycleIndex() + 1

    utils.mock_one_day_passed()
    vault.withdraw({"from": user})

    # Strategy should have completed withdrawal
    assert (
        pytest.approx(token.balanceOf(user), rel=RELATIVE_APPROX) == user_balance_before
    )


def test_partial_withdraw_token_1(
    chain,
    token_1,
    token_1_vault,
    token_1_strategy,
    user,
    token_1_amount,
    RELATIVE_APPROX,
    utils,
):
    partial_withdraw(
        chain,
        token_1,
        token_1_vault,
        token_1_strategy,
        user,
        token_1_amount,
        RELATIVE_APPROX,
        utils,
    )


def test_partial_withdraw_token_2(
    chain,
    token_2,
    token_2_vault,
    token_2_strategy,
    user,
    token_2_amount,
    RELATIVE_APPROX,
    utils,
):
    partial_withdraw(
        chain,
        token_2,
        token_2_vault,
        token_2_strategy,
        user,
        token_2_amount,
        RELATIVE_APPROX,
        utils,
    )


# test that the strategy can execute a partial withdrawal, while initiating a withdrawal for the remaining amount needed
def partial_withdraw(
    chain, token, vault, strategy, user, amount, RELATIVE_APPROX, utils
):
    # Deposit to the vault
    user_balance_before = token.balanceOf(user)
    utils.move_user_funds_to_vault(user, vault, token, amount)
    user_balance_after_deposit = token.balanceOf(user)

    # Harvest & tend
    chain.sleep(1)
    strategy.harvest()
    assert pytest.approx(strategy.estimatedTotalAssets(), rel=RELATIVE_APPROX) == amount
    strategy.tend()

    # Allow first for a partial withdraw out of tokemak
    partial_withdraw_amount = amount / 4
    utils.make_funds_withdrawable_from_tokemak(strategy, partial_withdraw_amount)

    vault.withdraw({"from": user})
    assert (
        pytest.approx(token.balanceOf(user), rel=RELATIVE_APPROX)
        == user_balance_after_deposit + partial_withdraw_amount
    )

    # Strategy should have triggered a request withdraw for the rest of the amount,
    # so that once a day passes it should be available
    utils.mock_one_day_passed()

    vault.withdraw({"from": user})
    assert (
        pytest.approx(token.balanceOf(user), rel=RELATIVE_APPROX) == user_balance_before
    )
