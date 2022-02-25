import pytest


def test_vault_shutdown_can_withdraw_token_1(
    chain,
    token_1,
    token_1_vault,
    token_1_strategy,
    user,
    token_1_amount,
    RELATIVE_APPROX,
    utils,
    token_1_whale,
):
    vault_shutdown_can_withdraw(
        chain,
        token_1,
        token_1_vault,
        token_1_strategy,
        user,
        token_1_amount,
        RELATIVE_APPROX,
        utils,
        token_1_whale,
    )


def test_vault_shutdown_can_withdraw_token_2(
    chain,
    token_2,
    token_2_vault,
    token_2_strategy,
    user,
    token_2_amount,
    RELATIVE_APPROX,
    utils,
    token_2_whale,
):
    vault_shutdown_can_withdraw(
        chain,
        token_2,
        token_2_vault,
        token_2_strategy,
        user,
        token_2_amount,
        RELATIVE_APPROX,
        utils,
        token_2_whale,
    )


def vault_shutdown_can_withdraw(
    chain, token, vault, strategy, user, amount, RELATIVE_APPROX, utils, whale
):
    ## Deposit in Vault
    token.approve(vault.address, amount, {"from": user})
    vault.deposit(amount, {"from": user})
    assert token.balanceOf(vault.address) == amount

    if token.balanceOf(user) > 0:
        # Would transfer to zero address but some ERC20s don't allow
        token.transfer(whale.address, token.balanceOf(user), {"from": user})

    # Harvest 1: Send funds through the strategy
    strategy.harvest()
    chain.sleep(3600 * 7)
    chain.mine(1)
    assert pytest.approx(strategy.estimatedTotalAssets(), rel=RELATIVE_APPROX) == amount

    ## Set Emergency
    vault.setEmergencyShutdown(True)

    utils.make_funds_withdrawable_from_tokemak(strategy, amount)

    ## Withdraw (does it work, do you get what you expect)
    vault.withdraw({"from": user})

    assert pytest.approx(token.balanceOf(user), rel=RELATIVE_APPROX) == amount


def test_basic_shutdown_token_1(
    chain,
    token_1,
    token_1_vault,
    token_1_strategy,
    user,
    strategist,
    token_1_amount,
    RELATIVE_APPROX,
    utils,
):
    basic_shutdown(
        chain,
        token_1,
        token_1_vault,
        token_1_strategy,
        user,
        strategist,
        token_1_amount,
        RELATIVE_APPROX,
        utils,
    )


def test_basic_shutdown_token_2(
    chain,
    token_2,
    token_2_vault,
    token_2_strategy,
    user,
    strategist,
    token_2_amount,
    RELATIVE_APPROX,
    utils,
):
    basic_shutdown(
        chain,
        token_2,
        token_2_vault,
        token_2_strategy,
        user,
        strategist,
        token_2_amount,
        RELATIVE_APPROX,
        utils,
    )


def basic_shutdown(
    chain, token, vault, strategy, user, strategist, amount, RELATIVE_APPROX, utils
):
    # Deposit to the vault
    token.approve(vault.address, amount, {"from": user})
    vault.deposit(amount, {"from": user})
    assert token.balanceOf(vault.address) == amount

    # Harvest 1: Send funds through the strategy
    strategy.harvest()
    chain.mine(100)
    assert pytest.approx(strategy.estimatedTotalAssets(), rel=RELATIVE_APPROX) == amount

    ## Earn interest
    chain.sleep(3600 * 24 * 1)  ## Sleep 1 day
    chain.mine(1)

    # Harvest 2: Realize profit
    strategy.harvest()
    chain.sleep(3600 * 6)  # 6 hrs needed for profits to unlock
    chain.mine(1)

    ## Set emergency
    strategy.setEmergencyExit({"from": strategist})

    utils.make_funds_withdrawable_from_tokemak(strategy, amount)

    strategy.harvest()  ## Remove funds from strategy

    assert token.balanceOf(strategy) == 0
    assert token.balanceOf(vault) >= amount  ## The vault has all funds
    ## NOTE: May want to tweak this based on potential loss during migration
