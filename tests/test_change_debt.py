import brownie
from brownie import Contract
import pytest


def test_change_debt_token_1(
    chain,
    gov,
    token_1,
    token_1_vault,
    token_1_strategy,
    user,
    token_1_amount,
    RELATIVE_APPROX,
    utils,
):
    change_debt(
        chain,
        gov,
        token_1,
        token_1_vault,
        token_1_strategy,
        user,
        token_1_amount,
        RELATIVE_APPROX,
        utils,
    )


def test_change_debt_token_2(
    chain,
    gov,
    token_2,
    token_2_vault,
    token_2_strategy,
    user,
    token_2_amount,
    RELATIVE_APPROX,
    utils,
):
    change_debt(
        chain,
        gov,
        token_2,
        token_2_vault,
        token_2_strategy,
        user,
        token_2_amount,
        RELATIVE_APPROX,
        utils,
    )


def change_debt(
    chain, gov, token, vault, strategy, user, amount, RELATIVE_APPROX, utils
):
    # Deposit to the vault and harvest
    token.approve(vault.address, amount, {"from": user})
    vault.deposit(amount, {"from": user})
    vault.updateStrategyDebtRatio(strategy.address, 5_000, {"from": gov})
    chain.sleep(1)
    strategy.harvest()
    half = int(amount / 2)
    sixty_percent = int(amount * 0.6)
    fourty_percent = int(amount * 0.4)

    assert pytest.approx(strategy.estimatedTotalAssets(), rel=RELATIVE_APPROX) == half

    vault.updateStrategyDebtRatio(strategy.address, 10_000, {"from": gov})
    chain.sleep(1)
    strategy.harvest()
    assert pytest.approx(strategy.estimatedTotalAssets(), rel=RELATIVE_APPROX) == amount

    # In order to pass this tests, you will need to implement prepareReturn.
    # TODO: uncomment the following lines.
    vault.updateStrategyDebtRatio(strategy.address, 6_000, {"from": gov})

    utils.make_funds_withdrawable_from_tokemak(strategy, gov, fourty_percent)

    strategy.harvest()
    assert (
        pytest.approx(strategy.estimatedTotalAssets(), rel=RELATIVE_APPROX)
        == sixty_percent
    )
