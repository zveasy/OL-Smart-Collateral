// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/* ──────────────────────────────────────────────────────────
   Imports
   ────────────────────────────────────────────────────────── */
import "@openzeppelin/contracts/token/ERC1155/ERC1155.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/Strings.sol";

/// @title O&L Carbon Credit (ERC-1155)
/// @notice Each tokenId represents 1 tonne of CO₂e for a given vintage/project.
///         Semi-fungible: balance = tonnes.  Burn == retirement.
contract OLCarbonCredit is ERC1155, AccessControl {
    using Strings for uint256;

    /* ──────────────────────────────────────────────────────
       Roles
       ────────────────────────────────────────────────────── */
    bytes32 public constant ADMIN_ROLE  = keccak256("ADMIN_ROLE");
    bytes32 public constant MINTER_ROLE = keccak256("MINTER_ROLE");
    bytes32 public constant BURNER_ROLE = keccak256("BURNER_ROLE");

    /* ──────────────────────────────────────────────────────
       Metadata struct
       ────────────────────────────────────────────────────── */
    struct CarbonMeta {
        uint16  vintageYear;   // 2023
        bytes32 projectId;     // "VCS-12345" hashed
        bytes32 registry;      // "VERRA", "GOLDSTD", etc.
        uint16  esgScore;      // 0-1000
        bool    retired;       // true if burned/retired
    }

    // tokenId => metadata
    mapping(uint256 => CarbonMeta) private _meta;

    /* ──────────────────────────────────────────────────────
       Events
       ────────────────────────────────────────────────────── */
    event CarbonMinted(
        uint256 indexed tokenId,
        address indexed to,
        uint256 amount,
        CarbonMeta meta
    );

    event CarbonRetired(
        uint256 indexed tokenId,
        address indexed account,
        uint256 amount
    );

    /* ──────────────────────────────────────────────────────
       Constructor
       ────────────────────────────────────────────────────── */
    constructor(string memory baseURI) ERC1155(baseURI) {
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(ADMIN_ROLE,           msg.sender);
        _grantRole(MINTER_ROLE,          msg.sender);
        _grantRole(BURNER_ROLE,          msg.sender);
    }

    // ───── *** REQUIRED OVERRIDE *** ─────
    function supportsInterface(bytes4 interfaceId)
        public
        view
        override(ERC1155, AccessControl)
        returns (bool)
    {
        return super.supportsInterface(interfaceId);
    }
    
    /* ──────────────────────────────────────────────────────
       Admin — set base URI
       ────────────────────────────────────────────────────── */
    function setURI(string calldata newuri) external onlyRole(ADMIN_ROLE) {
        _setURI(newuri);
    }

    /* ──────────────────────────────────────────────────────
       Mint (issue credits)
       ────────────────────────────────────────────────────── */
    function mint(
        address to,
        uint256 tokenId,
        uint256 amount,
        CarbonMeta calldata meta,
        bytes calldata data
    ) external onlyRole(MINTER_ROLE) {
        require(amount > 0, "Amount must be > 0");
        require(!_meta[tokenId].retired, "TokenId already retired");
        _meta[tokenId] = meta;
        _mint(to, tokenId, amount, data);
        emit CarbonMinted(tokenId, to, amount, meta);
    }

    /* ──────────────────────────────────────────────────────
       Burn (retire credits)
       ────────────────────────────────────────────────────── */
    function retire(
        address account,
        uint256 tokenId,
        uint256 amount
    ) external onlyRole(BURNER_ROLE) {
        _burn(account, tokenId, amount);
        _meta[tokenId].retired = true;
        emit CarbonRetired(tokenId, account, amount);
    }

    /* ──────────────────────────────────────────────────────
       View helpers
       ────────────────────────────────────────────────────── */
    function carbonMeta(uint256 tokenId) external view returns (CarbonMeta memory) {
        return _meta[tokenId];
    }

    function uri(uint256 tokenId) public view override returns (string memory) {
        // If using a baseURI like "ipfs://CID/{id}.json"
        return string(abi.encodePacked(super.uri(tokenId), tokenId.toString(), ".json"));
    }
}
