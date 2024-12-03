// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.0;

import {ISystemPromptManager} from "../interfaces/ISystemPromptManager.sol";

abstract contract SystemPromptManagerStorage is ISystemPromptManager {
    mapping(uint256 nftId => TokenMetaData) internal datas;
    uint256 public nextTokenId;
    uint256 internal mintPrice;
    address public royaltyReceiver;
    uint16 public royaltyPortion;

    mapping(address => bool) public isManager;
    address public workerHub;
    address public hybridModel;

    mapping(address nftOwner => uint256) internal earnedFees;
    mapping(uint256 nftId => uint256) public poolBalance;
    mapping(address nftOwner => mapping(bytes signature => bool))
        public signaturesUsed;

    mapping(uint256 agentId => bytes[]) internal missionsOf;
    address squadManager;

    uint256[46] private __gap;
}
