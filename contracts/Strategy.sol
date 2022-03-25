// SPDX-License-Identifier: AGPL-3.0
// Feel free to change the license, but this is what we use

// Feel free to change this version of Solidity. We support >=0.6.0 <0.7.0;
pragma solidity 0.6.12;
pragma experimental ABIEncoderV2;

// These are the core Yearn libraries
import {
    BaseStrategy,
    StrategyParams
} from "@yearnvaults/contracts/BaseStrategy.sol";
import "@openzeppelin/contracts/math/Math.sol";
import {
    SafeERC20,
    SafeMath,
    IERC20,
    Address
} from "@openzeppelin/contracts/token/ERC20/SafeERC20.sol";

import "./ySwap/ITradeFactory.sol";

import "../interfaces/tokemak/ILiquidityPool.sol";
import "../interfaces/tokemak/IManager.sol";
import "../interfaces/tokemak/IRewards.sol";

// NOTE: I recommend anyone wishing to use this generic strategy to first test amend 'token_1'
//       (and all other token_1 fixtures) in the tests for their desired 'want,'
//       and making sure that all tests pass.
contract Strategy is BaseStrategy {
    using SafeERC20 for IERC20;
    using Address for address;
    using SafeMath for uint256;

    event Cloned(address indexed clone);

    bool public isOriginal = true;

    ILiquidityPool public tokemakLiquidityPool;
    IERC20 public tAsset;
    string internal strategyName;

    IManager internal constant tokemakManager =
        IManager(0xA86e412109f77c45a3BC1c5870b880492Fb86A14);

    IERC20 internal constant tokeToken =
        IERC20(0x2e9d63788249371f1DFC918a52f8d799F4a38C94);

    IRewards internal constant tokemakRewards =
        IRewards(0x79dD22579112d8a5F7347c5ED7E609e60da713C5);

    address public tradeFactory = address(0);

    // ********** SETUP & CLONING **********

    constructor(
        address _vault,
        address _tokemakLiquidityPool,
        string memory _strategyName
    ) public BaseStrategy(_vault) {
        _initializeStrategy(_tokemakLiquidityPool, _strategyName);
    }

    function _initializeStrategy(
        address _tokemakLiquidityPool,
        string memory _strategyName
    ) internal {
        ILiquidityPool _liquidityPool = ILiquidityPool(_tokemakLiquidityPool);
        require(_liquidityPool.underlyer() == address(want), "!pool_matches");

        tokemakLiquidityPool = _liquidityPool;
        tAsset = IERC20(_tokemakLiquidityPool);
        strategyName = _strategyName;
    }

    // Cloning & initialization code adapted from https://github.com/yearn/yearn-vaults/blob/43a0673ab89742388369bc0c9d1f321aa7ea73f6/contracts/BaseStrategy.sol#L866

    function initialize(
        address _vault,
        address _strategist,
        address _rewards,
        address _keeper,
        address _tokemakLiquidityPool,
        string memory _strategyName
    ) external virtual {
        _initialize(_vault, _strategist, _rewards, _keeper);
        _initializeStrategy(_tokemakLiquidityPool, _strategyName);
    }

    function clone(
        address _vault,
        address _tokemakLiquidityPool,
        string memory _strategyName
    ) external returns (address) {
        return
            this.clone(
                _vault,
                msg.sender,
                msg.sender,
                msg.sender,
                _tokemakLiquidityPool,
                _strategyName
            );
    }

    function clone(
        address _vault,
        address _strategist,
        address _rewards,
        address _keeper,
        address _tokemakLiquidityPool,
        string memory _strategyName
    ) external returns (address newStrategy) {
        require(isOriginal, "!clone");
        bytes20 addressBytes = bytes20(address(this));

        assembly {
            // EIP-1167 bytecode
            let clone_code := mload(0x40)
            mstore(
                clone_code,
                0x3d602d80600a3d3981f3363d3d373d3d3d363d73000000000000000000000000
            )
            mstore(add(clone_code, 0x14), addressBytes)
            mstore(
                add(clone_code, 0x28),
                0x5af43d82803e903d91602b57fd5bf30000000000000000000000000000000000
            )
            newStrategy := create(0, clone_code, 0x37)
        }

        Strategy(newStrategy).initialize(
            _vault,
            _strategist,
            _rewards,
            _keeper,
            _tokemakLiquidityPool,
            _strategyName
        );

        emit Cloned(newStrategy);
    }

    // ********** CORE **********

    function name() external view override returns (string memory) {
        return strategyName;
    }

    function estimatedTotalAssets() public view override returns (uint256) {
        // 1 tWant = 1 want *guaranteed*
        // Tokemak team confirming that a tAsset will have the same decimals as the underlying asset
        return tAssetBalance().add(wantBalance());
    }

    function prepareReturn(uint256 _debtOutstanding)
        internal
        override
        returns (
            uint256 _profit,
            uint256 _loss,
            uint256 _debtPayment
        )
    {
        require(tradeFactory != address(0), "Trade factory must be set.");
        // How much do we owe to the vault?
        uint256 totalDebt = vault.strategies(address(this)).totalDebt;

        uint256 totalAssets = estimatedTotalAssets();

        if (totalAssets >= totalDebt) {
            _profit = totalAssets.sub(totalDebt);
        } else {
            _loss = totalDebt.sub(totalAssets);
        }

        (uint256 _liquidatedAmount, ) =
            liquidatePosition(_debtOutstanding.add(_profit));

        _debtPayment = Math.min(
            _debtOutstanding,
            _liquidatedAmount.sub(_profit)
        ); // _liquidatedAmount will always be greater or equal to profit, since profit needs to be in ETH, so this will never cause sub overflow
    }

    function adjustPosition(uint256 _debtOutstanding) internal override {
        uint256 wantBalance = wantBalance();

        if (wantBalance > _debtOutstanding) {
            uint256 _amountToInvest = wantBalance.sub(_debtOutstanding);

            _checkAllowance(
                address(tokemakLiquidityPool),
                address(want),
                _amountToInvest
            );

            try tokemakLiquidityPool.deposit(_amountToInvest) {} catch {}
        }
    }

    function liquidatePosition(uint256 _amountNeeded)
        internal
        override
        returns (uint256 _liquidatedAmount, uint256 _loss)
    {
        // NOTE: Maintain invariant `_liquidatedAmount + _loss <= _amountNeeded`

        uint256 _existingLiquidAssets = wantBalance();

        if (_existingLiquidAssets >= _amountNeeded) {
            return (_amountNeeded, 0);
        }

        uint256 _amountToWithdraw = _amountNeeded.sub(_existingLiquidAssets);

        (
            uint256 _cycleIndexWhenWithdrawable,
            uint256 _requestedWithdrawAmount
        ) = tokemakLiquidityPool.requestedWithdrawals(address(this));

        if (
            _requestedWithdrawAmount == 0 ||
            _cycleIndexWhenWithdrawable > tokemakManager.getCurrentCycleIndex()
        ) {
            tokemakLiquidityPool.requestWithdrawal(_amountToWithdraw);

            return (_existingLiquidAssets, 0);
        }

        // Cannot withdraw more than withdrawable
        _amountToWithdraw = Math.min(
            _amountToWithdraw,
            _requestedWithdrawAmount
        );

        try tokemakLiquidityPool.withdraw(_amountToWithdraw) {
            uint256 _newLiquidAssets = wantBalance();

            _liquidatedAmount = Math.min(_newLiquidAssets, _amountNeeded);

            if (_liquidatedAmount < _amountNeeded) {
                // If we couldn't liquidate the full amount needed, start the withdrawal process for the remaining
                tokemakLiquidityPool.requestWithdrawal(
                    _amountNeeded.sub(_liquidatedAmount)
                );
            }
        } catch {
            return (_existingLiquidAssets, 0);
        }
    }

    function liquidateAllPositions()
        internal
        override
        returns (uint256 _amountFreed)
    {
        (_amountFreed, ) = liquidatePosition(estimatedTotalAssets());
    }

    // NOTE: Can override `tendTrigger` and `harvestTrigger` if necessary

    function prepareMigration(address _newStrategy) internal override {
        uint256 _tAssetToTransfer = tAssetBalance();
        uint256 _tokeTokenToTransfer = tokeTokenBalance();

        tAsset.safeTransfer(_newStrategy, _tAssetToTransfer);
        tokeToken.safeTransfer(_newStrategy, _tokeTokenToTransfer);
    }

    // Override this to add all tokens/tokenized positions this contract manages
    // on a *persistent* basis (e.g. not just for swapping back to want ephemerally)
    // NOTE: Do *not* include `want`, already included in `sweep` below
    //
    // Example:
    //
    //    function protectedTokens() internal override view returns (address[] memory) {
    //      address[] memory protected = new address[](3);
    //      protected[0] = tokenA;
    //      protected[1] = tokenB;
    //      protected[2] = tokenC;
    //      return protected;
    //    }
    function protectedTokens()
        internal
        view
        override
        returns (address[] memory)
    {}

    /**
     * @notice
     *  Provide an accurate conversion from `_amtInWei` (denominated in wei)
     *  to `want` (using the native decimal characteristics of `want`).
     * @dev
     *  Care must be taken when working with decimals to assure that the conversion
     *  is compatible. As an example:
     *
     *      given 1e17 wei (0.1 ETH) as input, and want is USDC (6 decimals),
     *      with USDC/ETH = 1800, this should give back 1800000000 (180 USDC)
     *
     * @param _amtInWei The amount (in wei/1e-18 ETH) to convert to `want`
     * @return The amount in `want` of `_amtInEth` converted to `want`
     **/
    function ethToWant(uint256 _amtInWei)
        public
        view
        virtual
        override
        returns (uint256)
    {
        // TODO create an accurate price oracle
        return _amtInWei;
    }

    // ----------------- TOKEMAK OPERATIONS ---------

    function requestWithdrawal(uint256 amount)
        external
        onlyEmergencyAuthorized
    {
        tokemakLiquidityPool.requestWithdrawal(amount);
    }

    function claimRewards(
        IRewards.Recipient calldata _recipient,
        uint8 _v,
        bytes32 _r,
        bytes32 _s // bytes calldata signature
    ) external onlyVaultManagers {
        require(
            _recipient.wallet == address(this),
            "Recipient wallet must be strategy"
        );
        tokemakRewards.claim(_recipient, _v, _r, _s);
    }

    // ----------------- YSWAPS FUNCTIONS ---------------------

    function setTradeFactory(address _tradeFactory) external onlyGovernance {
        if (tradeFactory != address(0)) {
            _removeTradeFactoryPermissions();
        }

        // approve and set up trade factory
        tokeToken.safeApprove(_tradeFactory, type(uint256).max);
        ITradeFactory tf = ITradeFactory(_tradeFactory);
        tf.enable(address(tokeToken), address(want));
        tradeFactory = _tradeFactory;
    }

    function removeTradeFactoryPermissions() external onlyEmergencyAuthorized {
        _removeTradeFactoryPermissions();
    }

    function _removeTradeFactoryPermissions() internal {
        tokeToken.safeApprove(tradeFactory, 0);
        tradeFactory = address(0);
    }

    // ----------------- SUPPORT & UTILITY FUNCTIONS ----------

    function tokeTokenBalance() public view returns (uint256) {
        return tokeToken.balanceOf(address(this));
    }

    function wantBalance() public view returns (uint256) {
        return want.balanceOf(address(this));
    }

    function tAssetBalance() public view returns (uint256) {
        return tAsset.balanceOf(address(this));
    }

    // _checkAllowance adapted from https://github.com/therealmonoloco/liquity-stability-pool-strategy/blob/1fb0b00d24e0f5621f1e57def98c26900d551089/contracts/Strategy.sol#L316

    function _checkAllowance(
        address _contract,
        address _token,
        uint256 _amount
    ) internal {
        if (IERC20(_token).allowance(address(this), _contract) < _amount) {
            IERC20(_token).safeApprove(_contract, 0);
            IERC20(_token).safeApprove(_contract, _amount);
        }
    }
}
