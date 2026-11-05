class WaterTest extends GSController {
	function Start();
}

function T(x, y) { return GSMap.GetTileIndex(x, y); }

function Check(what, ok)
{
	if (!ok) GSLog.Warning(what + " failed: " + GSError.GetLastErrorString());
	return ok;
}

function WaterTest::Start()
{
	/* The player's company is created after the script starts. */
	while (GSCompany.ResolveCompanyID(GSCompany.COMPANY_FIRST) == GSCompany.COMPANY_INVALID) this.Sleep(1);
	local mode = GSCompanyMode(GSCompany.ResolveCompanyID(GSCompany.COMPANY_FIRST));
	GSCompany.SetLoanAmount(GSCompany.GetMaxLoanAmount());

	local cx = GSMap.GetMapSizeX() / 2;
	local cy = GSMap.GetMapSizeY() / 2;

	/* A level field at the centre's height; everything below is built or shaped on it. */
	local c = T(cx, cy);
	Check("level", GSTile.LevelTiles(c, T(cx - 7, cy - 6)));
	Check("level", GSTile.LevelTiles(c, T(cx + 5, cy - 6)));
	Check("level", GSTile.LevelTiles(c, T(cx - 7, cy + 5)));
	Check("level", GSTile.LevelTiles(c, T(cx + 5, cy + 5)));

	/* A canal ring (sides, outer and inner corners), a two-wide bay, a dead end and two ship depots. */
	for (local x = cx - 5; x <= cx + 1; x++) {
		Check("canal", GSMarine.BuildCanal(T(x, cy - 3)));
		Check("canal", GSMarine.BuildCanal(T(x, cy + 1)));
	}
	for (local y = cy - 2; y <= cy; y++) {
		Check("canal", GSMarine.BuildCanal(T(cx - 5, y)));
		Check("canal", GSMarine.BuildCanal(T(cx + 1, y)));
	}
	Check("canal", GSMarine.BuildCanal(T(cx - 4, cy - 2)));
	Check("canal", GSMarine.BuildCanal(T(cx - 3, cy - 2)));
	Check("canal", GSMarine.BuildCanal(T(cx + 1, cy + 2)));
	Check("depot X", GSMarine.BuildWaterDepot(T(cx - 2, cy + 1), T(cx - 3, cy + 1)));
	Check("depot Y", GSMarine.BuildWaterDepot(T(cx + 1, cy - 2), T(cx + 1, cy - 3)));

	/* Locks in all four directions: raising a plateau tile next to a flat tile makes the
	 * inclined slope a lock needs. X axis: plateau (cx..cx+2, cy-5), locks lowering to SW and NE. */
	for (local x = cx; x <= cx + 2; x++) Check("raise", GSTile.RaiseTile(T(x, cy - 5), GSTile.SLOPE_ELEVATED));
	Check("lock SW", GSMarine.BuildLock(T(cx - 1, cy - 5)));
	Check("lock NE", GSMarine.BuildLock(T(cx + 3, cy - 5)));
	/* Y axis: plateau (cx+4, cy-1..cy+1), locks lowering to NW and SE. */
	for (local y = cy - 1; y <= cy + 1; y++) Check("raise", GSTile.RaiseTile(T(cx + 4, y), GSTile.SLOPE_ELEVATED));
	Check("lock SE", GSMarine.BuildLock(T(cx + 4, cy - 2)));
	Check("lock NW", GSMarine.BuildLock(T(cx + 4, cy + 2)));

	/* An aqueduct over a one-level valley: plateau tiles at both ends make the heads' slopes. */
	Check("raise", GSTile.RaiseTile(T(cx - 7, cy + 4), GSTile.SLOPE_ELEVATED));
	Check("raise", GSTile.RaiseTile(T(cx - 1, cy + 4), GSTile.SLOPE_ELEVATED));
	Check("aqueduct", GSBridge.BuildBridge(GSVehicle.VT_WATER, 0, T(cx - 6, cy + 4), T(cx - 2, cy + 4)));
	Check("canal", GSMarine.BuildCanal(T(cx - 7, cy + 4)));
	Check("canal", GSMarine.BuildCanal(T(cx - 1, cy + 4)));

	GSLog.Info("WaterTest done");
	while (true) this.Sleep(1000);
}
