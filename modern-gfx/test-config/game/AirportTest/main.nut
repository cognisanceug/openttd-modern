class AirportTest extends GSController {
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

/* A canal pond at height 0 inside a ring of land at height 1, so the ring tiles become the
 * inclined slopes docks need. */
function Pond(x0, y0, w, h)
{
	LevelTo(x0 - 2, y0 - 2, x0 + w + 1, y0 + h + 1, 1);
	LevelTo(x0, y0, x0 + w, y0 + h, 0);
	for (local x = x0; x < x0 + w; x++) {
		for (local y = y0; y < y0 + h; y++) Check("canal", GSMarine.BuildCanal(T(x, y)));
	}
}

function AirportTest::Start()
{
	/* After loading the photographed save, do not build again. */
	if (this.done) return;
	while (GSCompany.ResolveCompanyID(GSCompany.COMPANY_FIRST) == GSCompany.COMPANY_INVALID) this.Sleep(1);
	local company = GSCompany.ResolveCompanyID(GSCompany.COMPANY_FIRST);
	GSCompany.ChangeBankBalance(company, 2000000000, GSCompany.EXPENSES_OTHER, GSMap.TILE_INVALID);
	local cx = GSMap.GetMapSizeX() / 2;
	local cy = GSMap.GetMapSizeY() / 2;

	/* Airports need a local authority. */
	GSTown.FoundTown(T(cx - 30, cy - 12), GSTown.TOWN_SIZE_SMALL, false, GSTown.ROAD_LAYOUT_ORIGINAL, null);

	/* Places (top-left offset from the centre) inside the photographed area, see
	 * IndustryTest's Visible(): the 4x shot covers -12 <= dx + dy <= 60, -8 <= dy - dx <= 66. */
	local airports = [
		[GSAirport.AT_INTERCON, -7, -3], [GSAirport.AT_INTERNATIONAL, -16, 6], [GSAirport.AT_METROPOLITAN, -24, 14],
		[GSAirport.AT_LARGE, -32, 22], [GSAirport.AT_COMMUTER, -24, 22], [GSAirport.AT_SMALL, -16, 15],
		[GSAirport.AT_HELISTATION, -7, 10], [GSAirport.AT_HELIDEPOT, -3, -7], [GSAirport.AT_HELIPORT, -10, 0],
	];
	{
		local mode = GSCompanyMode(company);
		foreach (a in airports) {
			local x = cx + a[1], y = cy + a[2];
			local w = GSAirport.GetAirportWidth(a[0]), h = GSAirport.GetAirportHeight(a[0]);
			local t = T(x, y);
			LevelTo(x, y, x + w, y + h, max(1, GSTile.GetCornerHeight(t, GSTile.CORNER_N)));
			Check("airport " + a[0], GSAirport.BuildAirport(t, a[0], GSStation.STATION_NEW), t);
		}

		/* Dock pond: a dock in the middle of every side, flat part in the water. */
		local dx = cx - 29, dy = cy + 30;
		Pond(dx, dy, 5, 5);
		foreach (d in [[-1, 2], [5, 2], [2, -1], [2, 5]]) {
			local t = T(dx + d[0], dy + d[1]);
			Check("dock", GSMarine.BuildDock(t, GSStation.STATION_NEW), t);
		}

		/* Oil rig pond at sea level: the rig checks water from (-4, -4) to (5, 6) around its tile. */
		Pond(cx + 18, cy + 21, 10, 11);
		/* Funded by the company, which may clear its own canals for the rig's tiles. */
		foreach (type, _ in GSIndustryTypeList()) {
			if (GSIndustryType.GetName(type).find("Oil Rig") != null) {
				Check("oil rig", GSIndustryType.BuildIndustry(type, T(cx + 22, cy + 25)), T(cx + 22, cy + 25));
			}
		}
		foreach (b in [[19, 22], [26, 22], [19, 30], [26, 30]]) Check("buoy", GSMarine.BuildBuoy(T(cx + b[0], cy + b[1])));
	}
	GSLog.Info("AirportTest done");
}
