// SPDX-License-Identifier: MIT

pragma solidity ^0.8.20;

import {OwnableUpgradeable} from "@openzeppelin/contracts-upgradeable/access/OwnableUpgradeable.sol";
import {ERC721PausableUpgradeable} from "@openzeppelin/contracts-upgradeable/token/ERC721/extensions/ERC721PausableUpgradeable.sol";
import {ERC721Upgradeable} from "@openzeppelin/contracts-upgradeable/token/ERC721/ERC721Upgradeable.sol";
import {AI721Upgradeable, IERC20} from "./standardUpgradeable/AI721Upgradeable.sol";

contract Dagent721 is
    ERC721PausableUpgradeable,
    OwnableUpgradeable,
    AI721Upgradeable
{
    function initialize(
        string calldata name_,
        string calldata symbol_,
        uint256 mintPrice_,
        address royaltyReceiver_,
        uint16 royaltyPortion_,
        uint256 nextTokenId_,
        address stakingHub_,
        IERC20 tokenFee_
    ) external initializer {
        __ERC721_init(name_, symbol_);
        __ERC721Pausable_init();
        __Ownable_init();

        _AI721_init(
            mintPrice_,
            royaltyReceiver_,
            royaltyPortion_,
            nextTokenId_,
            stakingHub_,
            tokenFee_
        );
    }

    function pause() external onlyOwner whenNotPaused {
        _pause();
    }

    function unpause() external onlyOwner whenPaused {
        _unpause();
    }

    function updateMintPrice(uint256 mintPrice) external onlyOwner {
        _setMintPrice(mintPrice);
    }

    function updateRoyaltyReceiver(address royaltyReceiver) external onlyOwner {
        _setRoyaltyReceiver(royaltyReceiver);
    }

    function updateRoyaltyPortion(uint16 royaltyPortion) external onlyOwner {
        _setRoyaltyPortion(royaltyPortion);
    }

    function updateStakingHub(address stakingHub) external onlyOwner {
        _setStakingHub(stakingHub);
    }

    function mint(
        address to,
        string calldata uri,
        bytes calldata data,
        uint256 fee,
        string calldata promptKey,
        address promptScheduler,
        uint32 modelId
    ) external returns (uint256) {
        return
            _wrapMint(to, uri, data, fee, promptKey, promptScheduler, modelId);
    }

    //
    function _beforeTokenTransfer(
        address _from,
        address _to,
        uint256 _agentId,
        uint256 _batchSize
    ) internal override(AI721Upgradeable, ERC721PausableUpgradeable) {
        super._beforeTokenTransfer(_from, _to, _agentId, _batchSize);
    }

    function _burn(
        uint256 agentId
    ) internal override(ERC721Upgradeable, AI721Upgradeable) {
        super._burn(agentId);
    }

    function tokenURI(
        uint256 _agentId
    )
        public
        view
        override(ERC721Upgradeable, AI721Upgradeable)
        returns (string memory)
    {
        return super.tokenURI(_agentId);
    }

    function supportsInterface(
        bytes4 interfaceId
    ) public view override(ERC721Upgradeable, AI721Upgradeable) returns (bool) {
        return super.supportsInterface(interfaceId);
    }
}
