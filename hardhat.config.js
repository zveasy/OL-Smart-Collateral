require("@nomicfoundation/hardhat-toolbox");
require("hardhat-contract-sizer");
require("@openzeppelin/hardhat-upgrades");
  

module.exports = { solidity: 
    {version: '0.8.30', 
        settings:{optimizer:
            {enabled:true,runs:200

            }
        }
    },
    contractSizer: {
    alphaSort: true,
    disambiguatePaths: false,
    runOnCompile: false,   // set true if you want size after every compile
    strict: true           // fail if any contract > 24 KiB
    }
};
