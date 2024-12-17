// SPDX-License-Identifier: MIT

pragma solidity ^0.8.20;

import {ERC20Upgradeable} from "@openzeppelin/contracts-upgradeable/token/ERC20/ERC20Upgradeable.sol";
import {IAI20Upgradeable, IStakingHub, IInferable} from "./interfaces/IAI20Upgradeable.sol";
import {IERC2981Upgradeable} from "@openzeppelin/contracts-upgradeable/interfaces/IERC2981Upgradeable.sol";
import {SafeERC20Upgradeable, IERC20Upgradeable} from "@openzeppelin/contracts-upgradeable/token/ERC20/utils/SafeERC20Upgradeable.sol";

contract AI20Upgradeable is ERC20Upgradeable, IAI20Upgradeable {
    uint256 private constant PORTION_DENOMINATOR = 10000;

    TokenMetaData private _data;
    address public _stakingHub;
    address public _promptScheduler;
    uint32 public _modelId;
    IERC20Upgradeable private _tokenFee;
    uint256 public _poolBalance;
    mapping(bytes32 signature => bool) public _signaturesUsed;
    bytes[] private _mission;
    uint256 private _totalFee;

    function _AI20_init(
        address promptScheduler_,
        address stakingHub_,
        uint32 modelId_,
        IERC20Upgradeable tokenFee_
    ) external onlyInitializing {
        if (
            promptScheduler_ == address(0) ||
            stakingHub_ == address(0) ||
            address(tokenFee_) == address(0)
        ) revert InvalidData();

        _promptScheduler = promptScheduler_;
        _stakingHub = stakingHub_;
        _modelId = modelId_;
        _tokenFee = tokenFee_;
    }

    function _setModelId(uint32 modelId) internal virtual {
        if (modelId == 0 || modelId == _modelId) revert InvalidData();

        _modelId = modelId;
        emit ModelIdUpdate(modelId);
    }

    function _setPromptScheduler(address promptScheduler) internal virtual {
        if (promptScheduler == address(0)) revert InvalidData();

        _promptScheduler = promptScheduler;
        emit PromptSchedulerUpdate(promptScheduler);
    }

    function _setStakingHub(address stakingHub) internal virtual {
        if (stakingHub == address(0)) revert InvalidData();

        _stakingHub = stakingHub;
        emit StakingHubUpdate(stakingHub);
    }

    function _validateURI(string calldata uri) internal pure virtual {
        if (bytes(uri).length == 0) revert InvalidAgentData();
    }

    function _updateAgentData(
        bytes calldata sysPrompt,
        string calldata promptKey,
        uint256 promptIdx
    ) internal virtual {
        _validateAgentData(sysPrompt, promptIdx, promptKey);
        _data.sysPrompts[promptKey][promptIdx] = sysPrompt;
    }

    function _validateAgentData(
        bytes calldata sysPrompt,
        uint256 promptIdx,
        string calldata promptKey
    ) internal view virtual {
        if (sysPrompt.length == 0) revert InvalidAgentData();
        uint256 len = _data.sysPrompts[promptKey].length;
        if (promptIdx >= len) revert InvalidAgentPromptIndex();
    }

    function _addNewAgentData(
        string calldata promptKey,
        bytes calldata sysPrompt
    ) internal virtual {
        if (sysPrompt.length == 0) revert InvalidAgentData();
        _data.sysPrompts[promptKey].push(sysPrompt);

        emit AgentDataAddNew(_data.sysPrompts[promptKey]);
    }

    function _updateAgentFee(uint fee) internal virtual {
        if (_data.fee != fee) {
            _data.fee = uint128(fee);
        }

        emit AgentFeeUpdate(fee);
    }

    function _withdrawFee(address recipient, uint256 amount) internal virtual {
        uint256 withdrawAmount = _totalFee < amount ? _totalFee : amount;

        if (withdrawAmount > 0) {
            _totalFee -= withdrawAmount;
            SafeERC20Upgradeable.safeTransfer(_tokenFee, recipient, withdrawAmount);
        }
    }

    function topUpPoolBalance(uint256 amount) public virtual override {
        SafeERC20Upgradeable.safeTransferFrom(
            _tokenFee,
            msg.sender,
            address(this),
            amount
        );
        _poolBalance += amount;

        emit TopUpPoolBalance(msg.sender, amount);
    }

    function getAgentSystemPrompt(
        string calldata promptKey
    ) public view virtual returns (bytes[] memory) {
        return _data.sysPrompts[promptKey];
    }

    function infer(
        bytes calldata fwdCalldata,
        string calldata externalData,
        string calldata promptKey,
        bool flag,
        uint feeAmount
    ) public virtual override {
        (, bytes memory fwdData) = _infer(fwdCalldata, promptKey, feeAmount);

        uint256 inferId = IInferable(_promptScheduler).infer(
            _modelId,
            fwdData,
            msg.sender,
            flag
        );

        emit InferencePerformed(
            msg.sender,
            fwdData,
            _data.fee,
            externalData,
            inferId
        );
    }

    function infer(
        bytes calldata fwdCalldata,
        string calldata externalData,
        string calldata promptKey,
        uint256 feeAmount
    ) public virtual override {
        (, bytes memory fwdData) = _infer(fwdCalldata, promptKey, feeAmount);

        uint256 inferId = IInferable(_promptScheduler).infer(
            _modelId,
            fwdData,
            msg.sender
        );

        emit InferencePerformed(
            msg.sender,
            fwdData,
            _data.fee,
            externalData,
            inferId
        );
    }

    function _infer(
        bytes calldata fwdCalldata,
        string calldata promptKey,
        uint256 feeAmount
    ) internal virtual returns (uint256, bytes memory) {
        if (_data.sysPrompts[promptKey].length == 0) revert InvalidAgentData();
        if (feeAmount < _data.fee) revert InvalidAgentFee();
        SafeERC20Upgradeable.safeTransferFrom(
            _tokenFee,
            msg.sender,
            address(this),
            feeAmount
        );

        bytes memory fwdData = abi.encodePacked(
            _concatSystemPrompts(_data.sysPrompts[promptKey]),
            fwdCalldata
        );
        uint256 estFeeWH = IStakingHub(_stakingHub).getMinFeeToUse(_modelId);

        if (feeAmount < estFeeWH && _poolBalance >= estFeeWH) {
            unchecked {
                _poolBalance -= estFeeWH;
            }

            if (feeAmount > 0) {
                _totalFee += feeAmount;
            }
        } else if (feeAmount >= estFeeWH) {
            uint256 remain = feeAmount - estFeeWH;
            if (remain > 0) {
                _totalFee += remain;
            }
        } else {
            revert InsufficientFunds();
        }

        SafeERC20Upgradeable.safeApprove(_tokenFee, _promptScheduler, estFeeWH);

        return (estFeeWH, fwdData);
    }

    function inferData() public view virtual returns (uint256) {
        return _data.fee;
    }

    function _createMission(bytes calldata missionData) internal virtual {
        if (missionData.length == 0) revert InvalidAgentData();
        _mission.push(missionData);

        emit AgentMissionAddNew(_mission);
    }

    function getMission()
        public
        view
        virtual
        override
        returns (bytes[] memory)
    {
        return _mission;
    }

    function _concatSystemPrompts(
        bytes[] memory sysPrompts
    ) internal pure virtual returns (bytes memory) {
        uint256 len = sysPrompts.length;
        bytes memory concatedPrompt;

        for (uint256 i = 0; i < len; i++) {
            concatedPrompt = abi.encodePacked(
                concatedPrompt,
                sysPrompts[i],
                ";"
            );
        }

        return concatedPrompt;
    }

    /**
     * @dev This empty reserved space is put in place to allow future versions to add new
     * variables without shifting down storage in the inheritance chain.
     * See https://docs.openzeppelin.com/contracts/4.x/upgradeable#storage_gaps
     */
    uint256[44] private __gap;
}
