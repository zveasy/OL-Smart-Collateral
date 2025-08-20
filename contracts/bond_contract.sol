// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";

contract OLBondERC721 is ERC721URIStorage, AccessControl {
    // ---- roles ----
    bytes32 public constant ADMIN_ROLE  = keccak256("ADMIN_ROLE");
    bytes32 public constant MINTER_ROLE = keccak256("MINTER_ROLE");
    bytes32 public constant BURNER_ROLE = keccak256("BURNER_ROLE");

    // tokenId => keccak256 hash of full BondMetadata JSON (sorted, canonical)
    mapping(uint256 => bytes32) private _metaHash;

    // ---- events ----
    event BondIssued(uint256 indexed tokenId, bytes32 metaHash);
    event BondRedeemed(uint256 indexed tokenId);

    constructor(string memory name_, string memory symbol_) ERC721(name_, symbol_) {
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(ADMIN_ROLE,           msg.sender);
        _grantRole(MINTER_ROLE,          msg.sender);
        _grantRole(BURNER_ROLE,          msg.sender);
    }

    /**
     * @notice Mint a bond NFT with a metadata URI and its off-chain JSON hash.
     * @param to receiver of the NFT
     * @param tokenId unique id (you may also switch to auto-increment if desired)
     * @param tokenURI_ ipfs://… or https://… pointing to the BondMetadata JSON
     * @param metaHash_ keccak256 hash of the **canonical** metadata JSON
     */
    function mintBond(
        address to,
        uint256 tokenId,
        string calldata tokenURI_,
        bytes32 metaHash_
    ) external onlyRole(MINTER_ROLE) {
        _safeMint(to, tokenId);
        _setTokenURI(tokenId, tokenURI_);
        _metaHash[tokenId] = metaHash_;
        emit BondIssued(tokenId, metaHash_);
    }

    /**
     * @notice Burn (redeem) a bond NFT. Requires BURNER_ROLE.
     */
    function redeemBond(uint256 tokenId) external onlyRole(BURNER_ROLE) {
        _burn(tokenId);
        delete _metaHash[tokenId];
        emit BondRedeemed(tokenId);
    }

    /**
     * @notice Read the stored metadata hash for a token
     */
    function metaHashOf(uint256 tokenId) external view returns (bytes32) {
        // OZ v5: _ownerOf is internal; use it to check existence
        require(_ownerOf(tokenId) != address(0), "ERC721: invalid token ID");
        return _metaHash[tokenId];
    }

    // ---- required override (ERC721 + AccessControl) ----
    function supportsInterface(bytes4 interfaceId)
        public
        view
        override(ERC721, AccessControl)
        returns (bool)
    {
        return super.supportsInterface(interfaceId);
    }
}
