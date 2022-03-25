import pytest
from brownie import config
from brownie import Contract


@pytest.fixture
def gov(accounts):
    yield accounts.at("0xFEB4acf3df3cDEA7399794D0869ef76A6EfAff52", force=True)


@pytest.fixture
def user(accounts):
    yield accounts[0]


@pytest.fixture
def rewards(accounts):
    yield accounts[1]


@pytest.fixture
def guardian(accounts):
    yield accounts[2]


@pytest.fixture
def management(accounts):
    yield accounts[3]


@pytest.fixture
def strategist(accounts):
    yield accounts[4]


@pytest.fixture
def keeper(accounts):
    yield accounts[5]


@pytest.fixture
def account_with_tokemak_rollover_role(accounts):
    # this account should have the role to allow them to call the Tokemak rollover contract
    yield accounts.at("0x9e0bcE7ec474B481492610eB9dd5D69EB03718D5", force=True)


@pytest.fixture
def tokemak_multisig(accounts):
    # this account should be the owner of the eth pool
    yield accounts.at("0x90b6c61b102ea260131ab48377e143d6eb3a9d4b", force=True)


@pytest.fixture
def token_1():
    # DAI
    token_address = "0x6b175474e89094c44da98b954eedeac495271d0f"
    yield Contract(token_address)


@pytest.fixture
def token_1_whale(accounts):
    # Curve Tripool
    yield accounts.at("0xbebc44782c7db0a1a60cb6fe97d0b483032ff1c7", force=True)


@pytest.fixture
def token_1_tokemak_liquidity_pool():
    address = "0x0CE34F4c26bA69158BC2eB8Bf513221e44FDfB75"
    yield Contract(address)


@pytest.fixture
def token_1_amount(token_1, user, token_1_whale):
    amount = 10_000 * 10 ** token_1.decimals()
    # In order to get some funds for the token you are about to use,
    # it impersonate the whale to use its funds.
    token_1.transfer(user, amount, {"from": token_1_whale, "gas_price": "0"})
    yield amount


@pytest.fixture
def token_1_vault(pm, gov, rewards, guardian, management, token_1, utils):
    yield utils.construct_vault(pm, gov, rewards, guardian, management, token_1)


@pytest.fixture
def token_1_strategy(
    strategist,
    keeper,
    token_1_vault,
    trade_factory,
    Strategy,
    gov,
    ymechs_safe,
    utils,
    token_1_tokemak_liquidity_pool,
):
    strategy = utils.construct_strategy(
        strategist,
        keeper,
        token_1_vault,
        trade_factory,
        Strategy,
        gov,
        ymechs_safe,
        token_1_tokemak_liquidity_pool,
    )
    token_1_vault.addStrategy(strategy, 10_000, 0, 2 ** 256 - 1, 0, {"from": gov})

    yield strategy


@pytest.fixture
def token_2():
    # SUSHI
    token_address = "0x6B3595068778DD592e39A122f4f5a5cF09C90fE2"
    yield Contract(token_address)


@pytest.fixture
def token_2_whale(accounts):
    # Binance
    yield accounts.at("0xF977814e90dA44bFA03b6295A0616a897441aceC", force=True)


@pytest.fixture
def token_2_amount(token_2, user, token_2_whale):
    amount = 10_000 * 10 ** token_2.decimals()
    # In order to get some funds for the token you are about to use,
    # it impersonate the whale to use its funds.
    token_2.transfer(user, amount, {"from": token_2_whale, "gas_price": "0"})
    yield amount


@pytest.fixture
def token_2_tokemak_liquidity_pool():
    address = "0xf49764c9C5d644ece6aE2d18Ffd9F1E902629777"
    yield Contract(address)


@pytest.fixture
def token_2_vault(pm, gov, rewards, guardian, management, token_2, utils):
    yield utils.construct_vault(pm, gov, rewards, guardian, management, token_2)


@pytest.fixture
def token_2_strategy(
    strategist,
    keeper,
    token_2_vault,
    trade_factory,
    Strategy,
    gov,
    ymechs_safe,
    utils,
    token_2_tokemak_liquidity_pool,
):
    strategy = utils.construct_strategy(
        strategist,
        keeper,
        token_2_vault,
        trade_factory,
        Strategy,
        gov,
        ymechs_safe,
        token_2_tokemak_liquidity_pool,
    )
    token_2_vault.addStrategy(strategy, 10_000, 0, 2 ** 256 - 1, 0, {"from": gov})

    yield strategy


@pytest.fixture
def toke_token():
    token_address = "0x2e9d63788249371f1DFC918a52f8d799F4a38C94"
    yield Contract(token_address)


@pytest.fixture
def toke_whale(accounts):
    # tokemak treasury
    yield accounts.at("0x8b4334d4812c530574bd4f2763fcd22de94a969b", force=True)


@pytest.fixture
def tokemak_manager():
    address = "0xA86e412109f77c45a3BC1c5870b880492Fb86A14"
    yield Contract(address)


@pytest.fixture
def trade_factory():
    yield Contract("0x99d8679bE15011dEAD893EB4F5df474a4e6a8b29")


@pytest.fixture
def ymechs_safe():
    yield Contract("0x2C01B4AD51a67E2d8F02208F54dF9aC4c0B778B6")


@pytest.fixture(scope="module")
def sushiswap_router(Contract):
    yield Contract("0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F")


@pytest.fixture(scope="module")
def multicall_swapper(interface):
    yield interface.MultiCallOptimizedSwapper(
        # "0xceB202F25B50e8fAF212dE3CA6C53512C37a01D2"
        "0xB2F65F254Ab636C96fb785cc9B4485cbeD39CDAA"
    )


@pytest.fixture
def weth():
    token_address = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
    yield Contract(token_address)


@pytest.fixture(scope="session")
def RELATIVE_APPROX():
    yield 1e-5


@pytest.fixture
def utils(chain, tokemak_manager, account_with_tokemak_rollover_role):
    return Utils(chain, tokemak_manager, account_with_tokemak_rollover_role)


class Utils:
    def __init__(self, chain, tokemak_manager, account_with_tokemak_rollover_role):
        self.chain = chain
        self.tokemak_manager = tokemak_manager
        self.account_with_tokemak_rollover_role = account_with_tokemak_rollover_role

    def mock_one_cycle_passed(self):
        self.chain.sleep(3600 * 24 * 7)
        cycle_duration = self.tokemak_manager.getCycleDuration()
        # self.chain.mine(cycle_duration + 1000)
        self.tokemak_manager.completeRollover(
            "DmTzdi7eC9SM5FaZCzaMpfwpuTt2gXZircVsZUA3DPXWqv",
            {"from": self.account_with_tokemak_rollover_role},
        )

    def make_funds_withdrawable_from_tokemak(self, strategy, amount):
        strategy.requestWithdrawal(amount)

        # Tokemak has 1 week timelock for withdrawals
        self.mock_one_cycle_passed()

    def move_user_funds_to_vault(self, user, vault, token, amount):
        token.approve(vault.address, amount, {"from": user})
        vault.deposit(amount, {"from": user})
        assert token.balanceOf(vault.address) == amount

    def prepare_trade_factory(self, strategy, trade_factory, ymechs_safe, gov):
        trade_factory.grantRole(
            trade_factory.STRATEGY(),
            strategy.address,
            {"from": ymechs_safe, "gas_price": "0 gwei"},
        )
        strategy.setTradeFactory(trade_factory.address, {"from": gov})

    def construct_vault(self, pm, gov, rewards, guardian, management, token):
        Vault = pm(config["dependencies"][0]).Vault
        vault = guardian.deploy(Vault)
        vault.initialize(
            token, gov, rewards, "", "", guardian, management, {"from": gov}
        )
        vault.setDepositLimit(2 ** 256 - 1, {"from": gov})
        vault.setManagement(management, {"from": gov})
        vault.setManagementFee(0, {"from": gov})
        vault.setPerformanceFee(0, {"from": gov})
        return vault

    def construct_strategy(
        self,
        strategist,
        keeper,
        vault,
        trade_factory,
        Strategy,
        gov,
        ymechs_safe,
        tokemak_liquidity_pool,
    ):
        strategy = strategist.deploy(
            Strategy, vault, tokemak_liquidity_pool, "DummyStrategyName"
        )
        strategy.setKeeper(keeper, {"from": gov})
        self.prepare_trade_factory(strategy, trade_factory, ymechs_safe, gov)
        return strategy
