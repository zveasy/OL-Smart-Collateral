const { loadFixture } = require("@nomicfoundation/hardhat-toolbox/network-helpers");
const { expect } = require("chai");

describe("OLBondERC721", function () {
  async function deployFixture() {
    const [admin, minter, burner, holder] = await ethers.getSigners();
    const Factory = await ethers.getContractFactory("OLBondERC721");
    const bond = await Factory.deploy("O&L Bond", "OLB");

    await bond.grantRole(await bond.MINTER_ROLE(), minter.address);
    await bond.grantRole(await bond.BURNER_ROLE(), burner.address);

    return { bond, admin, minter, burner, holder };
  }

  it("mints bond with URI and metadata hash", async function () {
    const { bond, minter, holder } = await loadFixture(deployFixture);
    const tokenId = 1n;
    const tokenURI = "ipfs://bond/1.json";
    const metaHash = ethers.keccak256(ethers.toUtf8Bytes("canonical-json"));

    await expect(
      bond.connect(minter).mintBond(holder.address, tokenId, tokenURI, metaHash)
    ).to.emit(bond, "BondIssued");

    expect(await bond.ownerOf(tokenId)).to.equal(holder.address);
    expect(await bond.tokenURI(tokenId)).to.equal(tokenURI);
    expect(await bond.metaHashOf(tokenId)).to.equal(metaHash);
  });

  it("rejects mint from non-minter", async function () {
    const { bond, holder } = await loadFixture(deployFixture);
    const tokenId = 2n;
    const tokenURI = "ipfs://bond/2.json";
    const metaHash = ethers.keccak256(ethers.toUtf8Bytes("canonical-json-2"));

    await expect(
      bond.connect(holder).mintBond(holder.address, tokenId, tokenURI, metaHash)
    ).to.be.revertedWithCustomError(bond, "AccessControlUnauthorizedAccount");
  });

  it("redeems bond and clears metadata hash", async function () {
    const { bond, minter, burner, holder } = await loadFixture(deployFixture);
    const tokenId = 3n;
    const tokenURI = "ipfs://bond/3.json";
    const metaHash = ethers.keccak256(ethers.toUtf8Bytes("canonical-json-3"));

    await bond.connect(minter).mintBond(holder.address, tokenId, tokenURI, metaHash);

    await expect(bond.connect(burner).redeemBond(tokenId)).to.emit(bond, "BondRedeemed");
    await expect(bond.ownerOf(tokenId)).to.be.reverted;
    await expect(bond.metaHashOf(tokenId)).to.be.revertedWith("ERC721: invalid token ID");
  });
});
