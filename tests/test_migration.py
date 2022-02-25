import pytest


def test_migration_token_1(
    chain,
    token_1,
    token_1_vault,
    token_1_strategy,
    token_1_amount,
    Strategy,
    strategist,
    gov,
    user,
    trade_factory,
    ymechs_safe,
    token_1_tokemak_liquidity_pool,
    utils,
    RELATIVE_APPROX,
):
    migration(
        chain,
        token_1,
        token_1_vault,
        token_1_strategy,
        token_1_amount,
        Strategy,
        strategist,
        gov,
        user,
        trade_factory,
        ymechs_safe,
        token_1_tokemak_liquidity_pool,
        utils,
        RELATIVE_APPROX,
    )


def test_migration_token_2(
    chain,
    token_2,
    token_2_vault,
    token_2_strategy,
    token_2_amount,
    Strategy,
    strategist,
    gov,
    user,
    trade_factory,
    ymechs_safe,
    token_2_tokemak_liquidity_pool,
    utils,
    RELATIVE_APPROX,
):
    migration(
        chain,
        token_2,
        token_2_vault,
        token_2_strategy,
        token_2_amount,
        Strategy,
        strategist,
        gov,
        user,
        trade_factory,
        ymechs_safe,
        token_2_tokemak_liquidity_pool,
        utils,
        RELATIVE_APPROX,
    )


def migration(
    chain,
    token,
    vault,
    strategy,
    amount,
    Strategy,
    strategist,
    gov,
    user,
    trade_factory,
    ymechs_safe,
    tokemak_liquidity_pool,
    utils,
    RELATIVE_APPROX,
):
    # Deposit to the vault and harvest
    token.approve(vault.address, amount, {"from": user})
    vault.deposit(amount, {"from": user})
    chain.sleep(1)
    strategy.harvest()
    assert pytest.approx(strategy.estimatedTotalAssets(), rel=RELATIVE_APPROX) == amount

    # migrate to a new strategy

    new_strategy = strategist.deploy(
        Strategy, vault, tokemak_liquidity_pool, "DummyStrategyName"
    )
    utils.prepare_trade_factory(new_strategy, trade_factory, ymechs_safe, gov)
    vault.migrateStrategy(strategy, new_strategy, {"from": gov})
    assert (
        pytest.approx(new_strategy.estimatedTotalAssets(), rel=RELATIVE_APPROX)
        == amount
    )
