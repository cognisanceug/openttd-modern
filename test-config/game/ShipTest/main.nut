class ShipTest extends GSController {
	done = false;
	function Start();
	function Save() { return { done = true }; }
	function Load(version, data) { this.done = ("done" in data) && data.done; }
}

function T(x, y) { return GSMap.GetTileIndex(x, y); }

/* On failure, log and leave a sign with the error at the tile. */
function Check(what, ok, tile = null)
{
	if (!ok) {
		local text = what + ": " + GSError.GetLastErrorString();
		GSLog.Warning(text);
		if (tile != null) GSSign.BuildSign(tile, text);
	}
	return ok;
}

/* Bring the north corner of a tile to height h, then level the rectangle to it. */
function LevelTo(x0, y0, x1, y1, h)
{
	local t = T(x0, y0);
	for (local i = 0; i < 8 && GSTile.GetCornerHeight(t, GSTile.CORNER_N) > h; i++) GSTile.LowerTile(t, GSTile.SLOPE_N);
	for (local i = 0; i < 8 && GSTile.GetCornerHeight(t, GSTile.CORNER_N) < h; i++) GSTile.RaiseTile(t, GSTile.SLOPE_N);
	return Check("level " + x0 + "," + y0, GSTile.LevelTiles(t, T(x1, y1)));
}

function ShipTest::Start()
{
	/* After loading the photographed save, do not build again. */
	if (this.done) return;
	while (GSCompany.ResolveCompanyID(GSCompany.COMPANY_FIRST) == GSCompany.COMPANY_INVALID) this.Sleep(1);
	local company = GSCompany.ResolveCompanyID(GSCompany.COMPANY_FIRST);
	GSCompany.ChangeBankBalance(company, 2000000000, GSCompany.EXPENSES_OTHER, GSMap.TILE_INVALID);
	local cx = GSMap.GetMapSizeX() / 2;
	local cy = GSMap.GetMapSizeY() / 2;
	local mode = GSCompanyMode(company);

	/* Canal pond inside the photographed area (see AirportTest): x0..x1, y0..y1 at height 1. */
	local x0 = cx + 2, y0 = cy + 10, x1 = cx + 17, y1 = cy + 29;
	LevelTo(x0 - 1, y0 - 1, x1 + 1, y1 + 1, 1);
	for (local x = x0; x <= x1; x++) {
		for (local y = y0; y <= y1; y++) Check("canal", GSMarine.BuildCanal(T(x, y)));
	}
	local depot = T(x0 + 2, y0 + 1);
	Check("depot", GSMarine.BuildWaterDepot(depot, T(x0 + 1, y0 + 1)), depot);

	/* Buoys at the corners of an inner rectangle and in the middle. */
	local buoys = [T(x0 + 2, y0 + 4), T(x1 - 2, y0 + 4), T(x1 - 2, y1 - 2), T(x0 + 2, y1 - 2), T((x0 + x1) / 2, (y0 + y1) / 2)];
	foreach (b in buoys) Check("buoy", GSMarine.BuildBuoy(b), b);
	/* Round trips: around the rectangle (axis legs) and across it (diagonal legs). */
	local routes = [[0, 1, 2, 3], [2, 3, 0, 1], [0, 2, 1, 3], [1, 3, 4, 0], [4, 1, 4, 3], [3, 1, 0, 2]];

	local engines = GSEngineList(GSVehicle.VT_WATER);
	local n = 0;
	foreach (e, _ in engines) {
		if (!GSEngine.IsBuildable(e)) continue;
		for (local k = 0; k < 2; k++) {
			local v = GSVehicle.BuildVehicle(depot, e);
			if (!Check("ship " + GSEngine.GetName(e), GSVehicle.IsValidVehicle(v), depot)) continue;
			foreach (b in routes[n % routes.len()]) GSOrder.AppendOrder(v, buoys[b], GSOrder.OF_NONE);
			GSVehicle.StartStopVehicle(v);
			GSLog.Info("ship " + GSEngine.GetName(e));
			n++;
			this.Sleep(30);
		}
	}
	GSLog.Info("ShipTest done: " + n + " ships");
}
