import { HardhatUserConfig } from "hardhat/config";
import "@nomicfoundation/hardhat-toolbox";
import "@openzeppelin/hardhat-upgrades";
import "@matterlabs/hardhat-zksync";
import "@nomiclabs/hardhat-solhint";
import "hardhat-deploy";
import "dotenv/config";
import "hardhat-contract-sizer";

let localTestMnemonic =
  "test test test test test test test test test test test junk";
const config: HardhatUserConfig = {
  defaultNetwork: "arbitrum_mainnet",
  solidity: {
    compilers: [
      {
        version: "0.8.22",
        settings: {
          optimizer: { enabled: true, runs: 2000000 },
          viaIR: true,
          evmVersion: "paris",
        },
      },
      {
        version: "0.8.19",
        settings: {
          optimizer: { enabled: true, runs: 2000000 },
          viaIR: true,
          evmVersion: "paris",
        },
      },
      {
        version: "0.8.20",
        settings: {
          optimizer: { enabled: true, runs: 2000000 },
          viaIR: true,
          evmVersion: "paris",
        },
      },
    ],
  },
  networks: {
    hardhat: {
      accounts: {
        mnemonic: localTestMnemonic,
        accountsBalance: "10000000000000000000000000",
      },
      gas: 100_000_000,
      allowUnlimitedContractSize: true,
      blockGasLimit: 1_000_000_000_000,
    },
    arbitrum_mainnet: {
      url:
        "https://arbitrum-mainnet.infura.io/v3/" +
        process.env.ARBITRUM_MAINNET_INFURA_API_KEY,
      chainId: 42161,
      accounts: [
        process.env.ARBITRUM_MAINNET_PRIVATE_KEY,
        process.env.ARBITRUM_MAINNET_PRIVATE_KEY_WORKER_1,
        process.env.ARBITRUM_MAINNET_PRIVATE_KEY_WORKER_2,
        process.env.ARBITRUM_MAINNET_PRIVATE_KEY_WORKER_3,
      ],
      l2OwnerAddress: process.env.ARBITRUM_MAINNET_L2_OWNER_ADDRESS,
      treasuryAddress: process.env.ARBITRUM_MAINNET_TREASURY_ADDRESS,
      collectionAddress: process.env.ARBITRUM_MAINNET_COLLECTION_ADDRESS,
      workerHubAddress: process.env.ARBITRUM_MAINNET_WORKER_HUB_ADDRESS,
      stakingHubAddress: process.env.ARBITRUM_MAINNET_STAKING_HUB_ADDRESS,
      daoTokenAddress: process.env.ARBITRUM_MAINNET_DAO_TOKEN_ADDRESS,
      workerHubScoringAddress:
        process.env.ARBITRUM_MAINNET_WORKER_HUB_SCORING_ADDRESS,
      hybridModelAddress: process.env.ARBITRUM_MAINNET_HYBRID_MODEL_ADDRESS,
      hybridModelScoringAddress:
        process.env.ARBITRUM_MAINNET_HYBRID_MODEL_SCORING_ADDRESS,
      systemPromptManagerAddress:
        process.env.ARBITRUM_MAINNET_SYSTEM_PROMPT_MANAGER_ADDRESS,
      squadManagerAddress: process.env.ARBITRUM_MAINNET_SQUAD_MANAGER_ADDRESS,
      wEAIAddress: process.env.ARBITRUM_MAINNET_WEAI,
      allowUnlimitedContractSize: true,
      ethNetwork: "https://testnet.runechain.com/rpc", // The Ethereum Web3 RPC URL.
      zksync: false,
      gasPrice: "auto",
    } as any,
    base_mainnet: {
      url:
        "https://base-mainnet.infura.io/v3/" +
        process.env.BASE_MAINNET_INFURA_API_KEY,
      chainId: 8453,
      accounts: [
        process.env.BASE_MAINNET_PRIVATE_KEY,
        process.env.BASE_MAINNET_PRIVATE_KEY_WORKER_1,
        process.env.BASE_MAINNET_PRIVATE_KEY_WORKER_2,
        process.env.BASE_MAINNET_PRIVATE_KEY_WORKER_3,
      ],
      l2OwnerAddress: process.env.BASE_MAINNET_L2_OWNER_ADDRESS,
      treasuryAddress: process.env.BASE_MAINNET_TREASURY_ADDRESS,
      collectionAddress: process.env.BASE_MAINNET_COLLECTION_ADDRESS,
      workerHubAddress: process.env.BASE_MAINNET_WORKER_HUB_ADDRESS,
      stakingHubAddress: process.env.BASE_MAINNET_STAKING_HUB_ADDRESS,
      daoTokenAddress: process.env.BASE_MAINNET_DAO_TOKEN_ADDRESS,
      workerHubScoringAddress:
        process.env.BASE_MAINNET_WORKER_HUB_SCORING_ADDRESS,
      hybridModelAddress: process.env.BASE_MAINNET_HYBRID_MODEL_ADDRESS,
      hybridModelScoringAddress:
        process.env.BASE_MAINNET_HYBRID_MODEL_SCORING_ADDRESS,
      systemPromptManagerAddress:
        process.env.BASE_MAINNET_SYSTEM_PROMPT_MANAGER_ADDRESS,
      squadManagerAddress: process.env.BASE_MAINNET_SQUAD_MANAGER_ADDRESS,
      wEAIAddress: process.env.BASE_MAINNET_WEAI,
      allowUnlimitedContractSize: true,
      ethNetwork: "https://testnet.runechain.com/rpc", // The Ethereum Web3 RPC URL.
      zksync: false,
      gasPrice: "auto",
    } as any,
  },
  namedAccounts: {
    deployer: 0,
  },
  paths: {
    sources: "./contracts",
    tests: "./tests",
    cache: "./cache",
    artifacts: "./artifacts",
  },
  etherscan: {
    apiKey: {
      regtest3: "abc123",
      arbitrumOne: "def456",
    },
  },
  mocha: {
    timeout: 2000000,
    color: true,
    reporter: "mocha-multi-reporters",
    reporterOptions: {
      configFile: "./mocha-report.json",
    },
  },
};

export default config;
