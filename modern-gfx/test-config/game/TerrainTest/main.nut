class TerrainTest extends GSController {
	function Start();
}

function T(x, y) { return GSMap.GetTileIndex(x, y); }

function TerrainTest::Start()
{
	local cx = GSMap.GetMapSizeX() / 2;
	local cy = GSMap.GetMapSizeY() / 2;

	/* Farms north and west of the centre (deity mode); they plant fields with fences around them. */
	local farm = null;
	foreach (it, _ in GSIndustryTypeList()) {
		if (GSIndustryType.GetName(it) == "Farm") farm = it;
	}
	local spots = [[cx - 4, cy - 9], [cx + 6, cy - 8], [cx - 12, cy - 1]];
	foreach (s in spots) {
		local done = false;
		for (local r = 0; r < 6 && !done; r++) {
			for (local d = -r; d <= r && !done; d++) {
				done = GSIndustryType.BuildIndustry(farm, T(s[0] + d, s[1] + r));
			}
		}
		if (!done) GSLog.Warning("farm not built near " + s[0] + "," + s[1] + ": " + GSError.GetLastErrorString());
	}

	/* The player's company is created after the script starts; clearing land needs one. */
	while (GSCompany.ResolveCompanyID(GSCompany.COMPANY_FIRST) == GSCompany.COMPANY_INVALID) this.Sleep(1);
	local mode = GSCompanyMode(GSCompany.ResolveCompanyID(GSCompany.COMPANY_FIRST));
	GSCompany.SetLoanAmount(GSCompany.GetMaxLoanAmount());

	/* Clear one row south of the centre every few days: cleared land is bare soil and
	 * grows back through 1/3 and 2/3 grass, so the rows show every stage side by side. */
	for (local row = 0; row < 12; row++) {
		for (local x = cx - 7; x <= cx + 7; x++) {
			local t = T(x, cy + 2 + row);
			if (GSTile.IsBuildable(t) && !GSTile.IsFarmTile(t)) GSTile.DemolishTile(t);
		}
		this.Sleep(74 * 8);
	}

	GSLog.Info("TerrainTest done");
	while (true) this.Sleep(1000);
}
