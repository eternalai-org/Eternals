// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.0;

import {ISquad} from "../interfaces/ISquad.sol";
import {Set} from "../lib/Set.sol";

abstract contract SquadStorage is ISquad {
    address systemPromptManager;

    uint256 public currentSquadId;
    mapping(uint256 squadId => address) public squadOwner;
    mapping(uint256 squadId => Set.Uint256Set) internal squadToAgentIds;
    mapping(address squadOwner => uint256) public squadBalance;
    mapping(address squadOwner => mapping(uint256 index => uint256 squadId))
        internal ownedSquads;
    mapping(uint256 squadId => uint256) internal ownedSquadsIndex;
    uint256[] internal _allSquads;
    mapping(uint256 => uint256) internal _allSquadsIndex;
    mapping(uint256 agentId => uint256) public agentToSquadId;

    uint256[50] private __gap;
}
