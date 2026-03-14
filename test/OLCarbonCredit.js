const { loadFixture } = require("@nomicfoundation/hardhat-toolbox/network-helpers");
const { expect } = require("chai");

describe("OLCarbonCredit", function () {
  async function deployFixture() {
    const [admin, minter, burner, holder] = await ethers.getSigners();
    const Factory = await ethers.getContractFactory("contracts/carbon_contract.sol:OLCarbonCredit");
    const carbon = await Factory.deploy("ipfs://carbon/");

    await carbon.grantRole(await carbon.MINTER_ROLE(), minter.address);
    await carbon.grantRole(await carbon.BURNER_ROLE(), burner.address);

    return { carbon, admin, minter, burner, holder };
  }

  function sampleMeta() {
    return [
      2024,
      ethers.keccak256(ethers.toUtf8Bytes("VCS-12345")),
      ethers.keccak256(ethers.toUtf8Bytes("VERRA")),
      850,
      false,
    ];
  }

  it("mints carbon credits and stores metadata", async function () {
    const { carbon, minter, holder } = await loadFixture(deployFixture);
    const tokenId = 11n;
    const amount = 100n;
    const meta = sampleMeta();

    await expect(
      carbon.connect(minter).mint(holder.address, tokenId, amount, meta, "0x")
    ).to.emit(carbon, "CarbonMinted");

    expect(await carbon.balanceOf(holder.address, tokenId)).to.equal(amount);
    const saved = await carbon.carbonMeta(tokenId);
    expect(saved.vintageYear).to.equal(2024);
    expect(saved.esgScore).to.equal(850);
    expect(saved.retired).to.equal(false);
  });

  it("rejects mint from non-minter", async function () {
    const { carbon, holder } = await loadFixture(deployFixture);

    await expect(
      carbon.connect(holder).mint(holder.address, 12, 1, sampleMeta(), "0x")
    ).to.be.revertedWithCustomError(carbon, "AccessControlUnauthorizedAccount");
  });

  it("retires credits and marks token as retired", async function () {
    const { carbon, minter, burner, holder } = await loadFixture(deployFixture);
    const tokenId = 13n;
    await carbon.connect(minter).mint(holder.address, tokenId, 10, sampleMeta(), "0x");

    await expect(
      carbon.connect(burner).retire(holder.address, tokenId, 5)
    ).to.emit(carbon, "CarbonRetired");

    const saved = await carbon.carbonMeta(tokenId);
    expect(saved.retired).to.equal(true);
    expect(await carbon.balanceOf(holder.address, tokenId)).to.equal(5);
  });

  it("prevents reminting after retirement", async function () {
    const { carbon, minter, burner, holder } = await loadFixture(deployFixture);
    const tokenId = 14n;
    await carbon.connect(minter).mint(holder.address, tokenId, 2, sampleMeta(), "0x");
    await carbon.connect(burner).retire(holder.address, tokenId, 1);

    await expect(
      carbon.connect(minter).mint(holder.address, tokenId, 1, sampleMeta(), "0x")
    ).to.be.revertedWith("TokenId already retired");
  });
});
