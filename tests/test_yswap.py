from brownie import Contract, Wei
import brownie
from eth_abi import encode_single, encode_abi
from brownie.convert import to_bytes
from eth_abi.packed import encode_abi_packed
import pytest
import eth_utils


def test_profitable_harvest_token_1(
    chain,
    token_1,
    token_1_vault,
    token_1_strategy,
    user,
    strategist,
    token_1_amount,
    RELATIVE_APPROX,
    utils,
    toke_token,
    toke_whale,
    trade_factory,
    sushiswap_router,
    ymechs_safe,
    multicall_swapper,
    gov,
    weth,
):
    profitable_harvest(
        chain,
        token_1,
        token_1_vault,
        token_1_strategy,
        user,
        strategist,
        token_1_amount,
        RELATIVE_APPROX,
        utils,
        toke_token,
        toke_whale,
        trade_factory,
        sushiswap_router,
        ymechs_safe,
        multicall_swapper,
        gov,
        weth,
    )


def test_profitable_harvest_token_2(
    chain,
    token_2,
    token_2_vault,
    token_2_strategy,
    user,
    strategist,
    token_2_amount,
    RELATIVE_APPROX,
    utils,
    toke_token,
    toke_whale,
    trade_factory,
    sushiswap_router,
    ymechs_safe,
    multicall_swapper,
    gov,
    weth,
):
    profitable_harvest(
        chain,
        token_2,
        token_2_vault,
        token_2_strategy,
        user,
        strategist,
        token_2_amount,
        RELATIVE_APPROX,
        utils,
        toke_token,
        toke_whale,
        trade_factory,
        sushiswap_router,
        ymechs_safe,
        multicall_swapper,
        gov,
        weth,
    )


def profitable_harvest(
    chain,
    token,
    vault,
    strategy,
    user,
    strategist,
    amount,
    RELATIVE_APPROX,
    utils,
    toke_token,
    toke_whale,
    trade_factory,
    sushiswap_router,
    ymechs_safe,
    multicall_swapper,
    gov,
    weth,
):
    # Deposit to the vault
    user_balance_before = token.balanceOf(user)
    token.approve(vault.address, amount, {"from": user})
    vault.deposit(amount, {"from": user})
    assert token.balanceOf(vault.address) == amount

    # harvest
    chain.sleep(1)
    chain.mine(1)
    strategy.harvest({"from": strategist})
    assert pytest.approx(strategy.estimatedTotalAssets(), rel=RELATIVE_APPROX) == amount

    toke_token.transfer(strategy, Wei("200 ether"), {"from": toke_whale})

    token_in = toke_token
    token_out = token

    print(f"Executing trade...")
    receiver = strategy.address
    amount_in = token_in.balanceOf(strategy)

    asyncTradeExecutionDetails = [strategy, token_in, token_out, amount_in, 1]

    # always start with optimizations. 5 is CallOnlyNoValue
    optimizations = [["uint8"], [5]]
    a = optimizations[0]
    b = optimizations[1]

    calldata = token_in.approve.encode_input(sushiswap_router, amount_in)
    t = createTx(token_in, calldata)
    a = a + t[0]
    b = b + t[1]

    path = [token_in.address, weth.address, token_out.address]
    calldata = sushiswap_router.swapExactTokensForTokens.encode_input(
        amount_in, 0, path, multicall_swapper, 2 ** 256 - 1
    )
    t = createTx(sushiswap_router, calldata)
    a = a + t[0]
    b = b + t[1]

    expectedOut = sushiswap_router.getAmountsOut(amount_in, path)[2]

    calldata = token_out.transfer.encode_input(receiver, expectedOut)
    t = createTx(token_out, calldata)
    a = a + t[0]
    b = b + t[1]

    transaction = encode_abi_packed(a, b)

    # min out must be at least 1 to ensure that the tx works correctly
    # trade_factory.execute["uint256, address, uint, bytes"](
    #    multicall_swapper.address, 1, transaction, {"from": ymechs_safe}
    # )
    trade_factory.execute["tuple,address,bytes"](
        asyncTradeExecutionDetails,
        multicall_swapper.address,
        transaction,
        {"from": ymechs_safe},
    )
    print(token_out.balanceOf(strategy))

    tx = strategy.harvest({"from": strategist})
    print(tx.events)
    assert tx.events["Harvested"]["profit"] > 0

    vault.updateStrategyDebtRatio(strategy, 0, {"from": gov})
    chain.sleep(1)
    strategy.harvest({"from": strategist})

    strategy.tend()

    utils.make_funds_withdrawable_from_tokemak(strategy, gov, amount)
    chain.sleep(1)
    strategy.harvest({"from": strategist})

    assert token.balanceOf(vault) > amount
    assert strategy.estimatedTotalAssets() == 0


def createTx(to, data):
    inBytes = eth_utils.to_bytes(hexstr=data)
    return [["address", "uint256", "bytes"], [to.address, len(inBytes), inBytes]]


def test_remove_trade_factory_token_1(token_1_strategy, gov, trade_factory, toke_token):
    remove_trade_factory(token_1_strategy, gov, trade_factory, toke_token)


def test_remove_trade_factory_token_2(token_2_strategy, gov, trade_factory, toke_token):
    remove_trade_factory(token_2_strategy, gov, trade_factory, toke_token)


def remove_trade_factory(strategy, gov, trade_factory, toke_token):
    assert strategy.tradeFactory() == trade_factory.address
    assert toke_token.allowance(strategy.address, trade_factory.address) > 0

    strategy.removeTradeFactoryPermissions({"from": gov})

    assert strategy.tradeFactory() != trade_factory.address
    assert toke_token.allowance(strategy.address, trade_factory.address) == 0


# unable to test updateTradeFactory because there aren't two trade factories deployed


def test_harvest_reverts_without_trade_factory_token_1(
    Strategy,
    token_1_vault,
    strategist,
    keeper,
    gov,
    token_1,
    user,
    utils,
    token_1_amount,
    chain,
    token_1_tokemak_liquidity_pool,
):
    harvest_reverts_without_trade_factory(
        Strategy,
        token_1_vault,
        strategist,
        keeper,
        gov,
        token_1,
        user,
        utils,
        token_1_amount,
        chain,
        token_1_tokemak_liquidity_pool,
    )


def test_harvest_reverts_without_trade_factory_token_2(
    Strategy,
    token_2_vault,
    strategist,
    keeper,
    gov,
    token_2,
    user,
    utils,
    token_2_amount,
    chain,
    token_2_tokemak_liquidity_pool,
):
    harvest_reverts_without_trade_factory(
        Strategy,
        token_2_vault,
        strategist,
        keeper,
        gov,
        token_2,
        user,
        utils,
        token_2_amount,
        chain,
        token_2_tokemak_liquidity_pool,
    )


def harvest_reverts_without_trade_factory(
    Strategy,
    vault,
    strategist,
    keeper,
    gov,
    token,
    user,
    utils,
    amount,
    chain,
    tokemak_liquidity_pool,
):
    strategy = strategist.deploy(
        Strategy, vault, tokemak_liquidity_pool, "DummyStrategyName"
    )
    strategy.setKeeper(keeper, {"from": gov})
    vault.addStrategy(strategy, 10_000, 0, 2 ** 256 - 1, 1_000, {"from": gov})

    # Deposit to the vault
    user_balance_before = token.balanceOf(user)
    utils.move_user_funds_to_vault(user, vault, token, amount)

    # harvest
    chain.sleep(1)

    with brownie.reverts("Trade factory must be set."):
        strategy.harvest()
