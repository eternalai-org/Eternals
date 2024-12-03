// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.0;

import {OwnableUpgradeable} from "@openzeppelin/contracts-upgradeable/access/OwnableUpgradeable.sol";

import {ISystemPromptManager} from "./interfaces/ISystemPromptManager.sol";
import {SquadStorage, Set} from "./storages/SquadStorage.sol";

contract SquadManager is OwnableUpgradeable, SquadStorage {
    using Set for Set.Uint256Set;

    receive() external payable {}

    function initialize(address _systemPromptManager) public initializer {
        __Ownable_init();

        if (_systemPromptManager == address(0)) revert InvalidData();

        systemPromptManager = _systemPromptManager;
    }

    modifier onlySystemPromptManager() {
        _checkSystemPromptManager();
        _;
    }

    function _checkSystemPromptManager() internal view {
        if (msg.sender != systemPromptManager) revert Unauthorized();
    }

    function _moveAgentsToSquad(
        uint256[] calldata _agentIds,
        uint256 _toSquad
    ) private {
        _validateSquadOwnership(msg.sender, _toSquad);

        ISystemPromptManager(systemPromptManager)
            .validateAgentsBeforeMoveToSquad(msg.sender, _agentIds);

        uint256 len = _agentIds.length;

        for (uint256 i = 0; i < len; i++) {
            _processMove(_agentIds[i], _toSquad);
        }
    }

    function moveAgentsToSquad(
        uint256[] calldata _agentIds,
        uint256 _toSquad
    ) external {
        _moveAgentsToSquad(_agentIds, _toSquad);
    }

    function _validateSquadOwnership(
        address _caller,
        uint256 _toSquad
    ) internal view {
        if (_caller != squadOwner[_toSquad]) revert Unauthorized();
        if (_toSquad > currentSquadId || _toSquad == 0) revert InvalidSquadId();
    }

    function _moveAgentToSquad(
        address _caller,
        uint256 _agentId,
        uint256 _toSquad
    ) private {
        _validateSquadOwnership(_caller, _toSquad);

        if (msg.sender != systemPromptManager) {
            ISystemPromptManager(systemPromptManager)
                .validateAgentBeforeMoveToSquad(_caller, _agentId);
        }

        _processMove(_agentId, _toSquad);
    }

    function _processMove(uint256 _agentId, uint256 _toSquad) private {
        uint256 fromSquad = agentToSquadId[_agentId];

        if (fromSquad != _toSquad) {
            agentToSquadId[_agentId] = _toSquad;
            if (fromSquad != 0) {
                squadToAgentIds[fromSquad].erase(_agentId);
            }
            squadToAgentIds[_toSquad].insert(_agentId);
        }

        emit MoveAgentToSquad(_toSquad, _agentId);
    }

    function moveAgentToSquad(uint256 _agentId, uint256 _toSquadId) external {
        _moveAgentToSquad(msg.sender, _agentId, _toSquadId);
    }

    function moveAgentToSquad(
        address _caller,
        uint256 _agentId,
        uint256 _toSquadId
    ) external onlySystemPromptManager {
        _moveAgentToSquad(_caller, _agentId, _toSquadId);
    }

    function createSquad(uint256[] calldata _agentIds) external {
        uint256 squadId = ++currentSquadId;
        squadOwner[squadId] = msg.sender;
        squadBalance[msg.sender]++;

        _moveAgentsToSquad(_agentIds, squadId);

        _addSquadToAllSquadsEnumeration(squadId);
        _addSquadToOwnerEnumeration(msg.sender, squadId);

        emit SquadTransferred(address(0), msg.sender, squadId);
    }

    function _addSquadToOwnerEnumeration(address to, uint256 squadId) private {
        uint256 length = squadBalance[to];
        ownedSquads[to][length] = squadId;
        ownedSquadsIndex[squadId] = length;
    }

    function _addSquadToAllSquadsEnumeration(uint256 squadId) private {
        _allSquadsIndex[squadId] = _allSquads.length;
        _allSquads.push(squadId);
    }

    function totalSquad() external view returns (uint256) {
        return _allSquads.length;
    }

    function getAgentIdsBySquadId(
        uint256 _squadId
    ) external view returns (uint256[] memory) {
        return squadToAgentIds[_squadId].values;
    }
}
