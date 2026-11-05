class AircraftTest extends GSController {
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

/* The biggest airport type of the list that can be built this year (YEAR= start years). */
function Biggest(types)
{
	foreach (t in types) if (GSAirport.IsValidAirportType(t)) return t;
	return types.top();
}

function AircraftTest::Start()
{
	/* After loading the photographed save, do not build again. */
	if (this.done) return;
	while (GSCompany.ResolveCompanyID(GSCompany.COMPANY_FIRST) == GSCompany.COMPANY_INVALID) this.Sleep(1);
	local company = GSCompany.ResolveCompanyID(GSCompany.COMPANY_FIRST);
	GSCompany.ChangeBankBalance(company, 2000000000, GSCompany.EXPENSES_OTHER, GSMap.TILE_INVALID);
	local cx = GSMap.GetMapSizeX() / 2;
	local cy = GSMap.GetMapSizeY() / 2;

	/* Airports need a local authority. */
	GSTown.FoundTown(T(cx - 30, cy - 12), GSTown.TOWN_SIZE_MEDIUM, false, GSTown.ROAD_LAYOUT_ORIGINAL, null);

	/* Inside the photographed area (see AirportTest): two big airports for the planes, a
	 * helistation with hangars and a heliport for the helicopters. */
	local big = [GSAirport.AT_INTERCON, GSAirport.AT_INTERNATIONAL, GSAirport.AT_METROPOLITAN, GSAirport.AT_LARGE];
	local sites = [
		[Biggest(big), -7, -3], [Biggest(big.slice(1)), -16, 8],
		[GSAirport.AT_HELISTATION, 4, 12], [GSAirport.AT_HELIPORT, -3, 18],
	];
	local tiles = [];
	local mode = GSCompanyMode(company);
	foreach (a in sites) {
		local x = cx + a[1], y = cy + a[2];
		local w = GSAirport.GetAirportWidth(a[0]), h = GSAirport.GetAirportHeight(a[0]);
		local t = T(x, y);
		LevelTo(x, y, x + w, y + h, max(1, GSTile.GetCornerHeight(t, GSTile.CORNER_N)));
		Check("airport " + a[0], GSAirport.BuildAirport(t, a[0], GSStation.STATION_NEW), t);
		tiles.append(t);
	}
	local hangar = GSAirport.GetHangarOfAirport(tiles[0]);
	local hangar2 = GSAirport.GetHangarOfAirport(tiles[1]);
	local helidepot = GSAirport.GetHangarOfAirport(tiles[2]);

	/* Every buildable aircraft: planes between the two airports, every third waits for a full
	 * load at the first terminal it reaches (parked); helicopters between the heliports. */
	local engines = GSEngineList(GSVehicle.VT_AIR);
	local n = 0;
	foreach (e, _ in engines) {
		if (!GSEngine.IsBuildable(e)) continue;
		local heli = GSEngine.GetPlaneType(e) == GSAirport.PT_HELICOPTER;
		for (local k = 0; k < (heli ? 2 : 1); k++) {
			local depot = heli ? helidepot : (n % 2 ? hangar2 : hangar);
			local v = GSVehicle.BuildVehicle(depot, e);
			if (!Check("aircraft " + GSEngine.GetName(e), GSVehicle.IsValidVehicle(v), depot)) continue;
			local a = heli ? tiles[2] : tiles[n % 2], b = heli ? tiles[3] : tiles[1 - n % 2];
			GSOrder.AppendOrder(v, a, n % 3 == 0 && !heli ? GSOrder.OF_FULL_LOAD_ANY : GSOrder.OF_NONE);
			GSOrder.AppendOrder(v, b, GSOrder.OF_NONE);
			GSVehicle.StartStopVehicle(v);
			GSLog.Info("aircraft " + GSEngine.GetName(e));
			n++;
			this.Sleep(20);
		}
	}
	GSLog.Info("AircraftTest done: " + n + " aircraft");
}
