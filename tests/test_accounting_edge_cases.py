from brownie import Contract, Wei
import pytest


def test_accounting_edge_cases_token_1(
    chain,
    token_1,
    token_1_vault,
    token_1_strategy,
    user,
    token_1_amount,
    RELATIVE_APPROX,
    utils,
    token_1_whale,
    gov,
):
    accounting_edge_cases(
        chain,
        token_1,
        token_1_vault,
        token_1_strategy,
        user,
        token_1_amount,
        RELATIVE_APPROX,
        utils,
        token_1_whale,
        gov,
    )


def test_accounting_edge_cases_token_2(
    chain,
    token_2,
    token_2_vault,
    token_2_strategy,
    user,
    token_2_amount,
    RELATIVE_APPROX,
    utils,
    token_2_whale,
    gov,
):
    accounting_edge_cases(
        chain,
        token_2,
        token_2_vault,
        token_2_strategy,
        user,
        token_2_amount,
        RELATIVE_APPROX,
        utils,
        token_2_whale,
        gov,
    )


def accounting_edge_cases(
    chain,
    token,
    vault,
    strategy,
    user,
    amount,
    RELATIVE_APPROX,
    utils,
    token_whale,
    gov,
):
    user_balance_before = token.balanceOf(user)
    utils.move_user_funds_to_vault(user, vault, token, amount)

    # harvest
    chain.sleep(1)
    strategy.harvest()
    assert pytest.approx(strategy.estimatedTotalAssets(), rel=RELATIVE_APPROX) == amount

    token.transfer(
        strategy, amount, {"from": token_whale}
    )  # Simulate as if ySwap has already happened
    vault.updateStrategyDebtRatio(
        strategy, 9_900, {"from": gov}
    )  # Should be 100% profit and 1% debtOustanding
    assert (
        pytest.approx(vault.debtOutstanding(strategy), rel=RELATIVE_APPROX)
        == amount * 0.01
    )
    chain.sleep(1)
    strategy.harvest()
    assert (
        pytest.approx(strategy.estimatedTotalAssets(), rel=RELATIVE_APPROX) == amount
    )  # Wasn't able to pull out that 1%, and during the vault's report() it hadn't yet updated its total assets

    chain.sleep(1)
    strategy.harvest()  # Should move all of the debt limit into the strategy, since profit has been moved to vault and thus vault.totalAssets() has been updated
    assert (
        pytest.approx(strategy.estimatedTotalAssets(), rel=RELATIVE_APPROX)
        == amount * 2 * 0.99
    )

    vault.updateStrategyDebtRatio(strategy, 5_000, {"from": gov})  # 50%
    chain.sleep(1)
    strategy.harvest()
    assert (
        pytest.approx(strategy.estimatedTotalAssets(), rel=RELATIVE_APPROX)
        == amount * 2 * 0.99
    )  # Can't get it out of Tokemak yet
    assert (
        pytest.approx(vault.debtOutstanding(strategy), rel=RELATIVE_APPROX)
        == amount * 0.98
    )

    utils.make_funds_withdrawable_from_tokemak(strategy, amount * 0.98)
    chain.sleep(1)
    strategy.harvest()
    assert pytest.approx(strategy.estimatedTotalAssets(), rel=RELATIVE_APPROX) == amount
    assert vault.debtOutstanding(strategy) == 0

    token.transfer(
        strategy, amount * 0.01, {"from": token_whale}
    )  # Simulate as if ySwap has already happened
    vault.updateStrategyDebtRatio(strategy, 0, {"from": gov})
    chain.sleep(1)
    strategy.harvest()
    # Harvest should trigger an initiation of withdrawal for full amount
    utils.mock_one_cycle_passed()
    chain.sleep(1)
    strategy.harvest()

    chain.sleep(3600 * 10)
    chain.mine(1)

    # withdrawal
    vault.withdraw({"from": user})
    assert pytest.approx(
        token.balanceOf(user), rel=RELATIVE_APPROX
    ) == user_balance_before + amount + (amount * 0.01)
    assert vault.balanceOf(user) == 0
