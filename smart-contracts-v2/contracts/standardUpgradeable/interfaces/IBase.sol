// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

interface IStakingHub {
    function getMinFeeToUse(uint32 modelId) external view returns (uint256);
}

interface IInferable {
    function infer(
        uint32 modelId,
        bytes calldata data,
        address creator
    ) external returns (uint64 inferenceId);

    function infer(
        uint32 modelId,
        bytes calldata data,
        address creator,
        bool flag
    ) external returns (uint64 inferenceId);
}
