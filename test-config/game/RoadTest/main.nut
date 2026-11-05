class RoadTest extends GSController {
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

/* Build an industry of the type on rings of growing radius around a tile; its id or null. */
function PlaceIndustry(type, x, y, radius, quiet = false)
{
	for (local r = 0; r <= radius; r++) {
		for (local dx = -r; dx <= r; dx++) {
			for (local dy = -r; dy <= r; dy++) {
				if (abs(dx) != r && abs(dy) != r) continue;
				if (!GSIndustryType.BuildIndustry(type, T(x + dx, y + dy))) continue;
				local list = GSIndustryList();
				list.Valuate(GSIndustry.GetIndustryType);
				list.KeepValue(type);
				list.Valuate(GSIndustry.GetDistanceManhattanToTile, T(x + dx, y + dy));
				list.Sort(GSList.SORT_BY_VALUE, true);
				return list.Begin();
			}
		}
	}
	if (!quiet) Check(GSIndustryType.GetName(type), false, T(x, y));
	return null;
}

/* Cargo labels of the lorries with a loaded sprite: raw cargo gets a line of its own, the
 * secondary cargo comes from the industry at the far end of a line. */
RAW <- ["COAL", "GRAI", "WHEA", "MAIZ", "WOOD", "IORE", "CORE", "FRUT", "RUBR",
        "SUGR", "COLA", "CTCD", "TOFF", "BATT", "PLST", "BUBL"];

/* Road along x or y, tile by tile; houses and trees in the way are demolished, industries not. */
function Road(x0, y0, x1, y1)
{
	local dx = x1 > x0 ? 1 : x1 < x0 ? -1 : 0, dy = y1 > y0 ? 1 : y1 < y0 ? -1 : 0;
	local x = x0, y = y0;
	while (x != x1 || y != y1) {
		local t = T(x + dx, y + dy);
		if (!GSRoad.BuildRoad(T(x, y), t)) {
			if (GSIndustry.IsValidIndustry(GSIndustry.GetIndustryID(t)) || GSTile.IsStationTile(t)) return Check("road", false, t);
			GSTile.DemolishTile(t);
			if (!Check("road", GSRoad.BuildRoad(T(x, y), t), t)) return false;
		}
		x += dx; y += dy;
	}
	return true;
}

function Has(list, item) { foreach (i in list) if (i == item) return true; return false; }

/* Rows of the main road taken by depots and bus and truck stops (set in Start). */
BUSY <- [];

/* Station tile for a line end: within catchment of the industry (tiles from the list), on the
 * given side of the main road x = mx, within tol rows of row and off the busy rows; the west
 * end also needs a free tile beyond for turning. */
function StopTile(tiles, mx, east, row, tol = 2)
{
	local best = null, score = 0;
	foreach (t, _ in tiles) {
		local x = GSMap.GetTileX(t), y = GSMap.GetTileY(t);
		if (abs(y - row) > tol || Has(BUSY, y) || !GSTile.IsBuildable(t) || GSTile.GetSlope(t) != GSTile.SLOPE_FLAT) continue;
		if (east ? x < mx + 3 : x > mx - 3) continue;
		if (!east && !GSTile.IsBuildable(T(x - 1, y))) continue;
		local s = (east ? x - mx : mx - x) * 4 + abs(y - row);
		if (best == null || s < score) { best = t; score = s; }
	}
	return best;
}

function RoadTest::Start()
{
	/* After loading the photographed save, do not build again. */
	if (this.done) return;
	while (GSCompany.ResolveCompanyID(GSCompany.COMPANY_FIRST) == GSCompany.COMPANY_INVALID) this.Sleep(1);
	local company = GSCompany.ResolveCompanyID(GSCompany.COMPANY_FIRST);
	GSCompany.ChangeBankBalance(company, 2000000000, GSCompany.EXPENSES_OTHER, GSMap.TILE_INVALID);
	local cx = GSMap.GetMapSizeX() / 2;
	local cy = GSMap.GetMapSizeY() / 2;

	/* A town at the north end of the main road for the buses and as a size reference. */
	GSTown.FoundTown(T(cx - 4, cy - 6), GSTown.TOWN_SIZE_MEDIUM, false, GSTown.ROAD_LAYOUT_ORIGINAL, null);

	local mode = GSCompanyMode(company);
	GSRoad.SetCurrentRoadType(GSRoad.ROADTYPE_ROAD);

	/* Main road along y inside the photographed area (see IndustryTest), depots on both
	 * sides, bus stops: drive-through on the main road, a bay at the south end. Lines join it
	 * within 2 tiles of rows cy + 6 + 7i, so all of these sit between the rows. */
	local mx = cx + 5, y0 = cy - 2, y1 = cy + 54;
	Road(mx, y0, mx, y1);
	local depots = [T(mx + 1, cy + 3), T(mx - 1, cy + 16), T(mx + 1, cy + 30)];
	/* Depots and bays need the road piece on their front tile pointing at them. */
	foreach (d in depots) {
		Check("depot", GSRoad.BuildRoadDepot(d, T(mx, GSMap.GetTileY(d))), d);
		GSRoad.BuildRoad(T(mx, GSMap.GetTileY(d)), d);
	}
	local bus = [T(mx, cy + 1), T(mx, cy + 24), T(mx + 1, cy + 52)];
	Check("bus stop", GSRoad.BuildDriveThroughRoadStation(bus[0], T(mx, cy), GSRoad.ROADVEHTYPE_BUS, GSStation.STATION_NEW), bus[0]);
	Check("bus stop", GSRoad.BuildDriveThroughRoadStation(bus[1], T(mx, cy + 23), GSRoad.ROADVEHTYPE_BUS, GSStation.STATION_NEW), bus[1]);
	Check("bus bay", GSRoad.BuildRoadStation(bus[2], T(mx, cy + 52), GSRoad.ROADVEHTYPE_BUS, GSStation.STATION_NEW), bus[2]);
	GSRoad.BuildRoad(T(mx, cy + 52), bus[2]);
	/* A spare truck stop for lorries without a line (mail, goods, tankers ...). */
	local spare = T(mx, cy + 38);
	foreach (dy in [1, 3, 16, 24, 30, 38, 52]) BUSY.append(cy + dy);
	Check("truck stop", GSRoad.BuildDriveThroughRoadStation(spare, T(mx, cy + 37), GSRoad.ROADVEHTYPE_TRUCK, GSStation.STATION_NEW), spare);

	/* Buildable road vehicles by cargo. */
	local engines = {};
	local buses = [];
	foreach (e, _ in GSEngineList(GSVehicle.VT_ROAD)) {
		if (!GSEngine.IsBuildable(e) || GSEngine.GetRoadType(e) != GSRoad.ROADTYPE_ROAD) continue;
		local c = GSEngine.GetCargoType(e);
		if (GSCargo.HasCargoClass(c, GSCargo.CC_PASSENGERS)) { buses.append(e); continue; }
		if (!(c in engines)) engines[c] <- [];
		engines[c].append(e);
	}

	/* Lines: a raw industry east of the main road (lorries full load at a bay), an industry
	 * accepting its cargo west of it (drive-through stop, dead end beyond to turn). */
	local lines = [];
	foreach (c, _ in engines) {
		if (!Has(RAW, GSCargo.GetCargoLabel(c))) continue;
		local src = null, dst = null;
		foreach (type, _ in GSIndustryTypeList()) {
			if (!GSIndustryType.CanBuildIndustry(type) && !GSIndustryType.CanProspectIndustry(type)) continue;
			local name = GSIndustryType.GetName(type);
			if (name.find("Oil Rig") != null) continue;
			if (src == null && GSIndustryType.IsRawIndustry(type) && GSIndustryType.GetProducedCargo(type).HasItem(c)) src = type;
			/* Prefer an acceptor that produces cargo of a lorry with a loaded sprite. */
			if (GSIndustryType.GetAcceptedCargo(type).HasItem(c)) {
				local useful = false;
				foreach (p, _ in GSIndustryType.GetProducedCargo(type)) if (p in engines && !Has(RAW, GSCargo.GetCargoLabel(p))) useful = true;
				if (dst == null || useful) dst = type;
			}
		}
		if (src != null) lines.append({ cargo = c, src = src, dst = dst });
	}

	local row = cy + 6;
	foreach (l in lines) {
		l.a <- null; l.b <- null;
		/* Zones (desert, rain forest, snow) may need a wider search; the stop follows. */
		local tol = 2;
		local ia = PlaceIndustry(l.src, mx + 10, row - 1, 3, true);
		if (ia == null) ia = PlaceIndustry(l.src, mx + 12, row, 16, true);
		if (ia == null) {
			/* Sub-arctic forests grow above the snow line: raise a plateau for them. */
			for (local i = 0; i < 4 && ia == null; i++) {
				/* One level up: the north corner of every tile is a grid point of the area. */
				for (local x = mx + 7; x <= mx + 15; x++) {
					for (local y = row - 4; y <= row + 3; y++) GSTile.RaiseTile(T(x, y), GSTile.SLOPE_N);
				}
				ia = PlaceIndustry(l.src, mx + 9, row - 3, 1, i < 3);
			}
		}
		if (ia != null && GSIndustry.GetDistanceManhattanToTile(ia, T(mx + 10, row)) > 6) tol = 16;
		if (ia != null) {
			local t = StopTile(GSTileList_IndustryProducing(ia, 3), mx, true, row, tol);
			if (t != null) {
				local x = GSMap.GetTileX(t), y = GSMap.GetTileY(t);
				if (Road(mx, y, x - 1, y) &&
						Check("truck bay", GSRoad.BuildRoadStation(t, T(x - 1, y), GSRoad.ROADVEHTYPE_TRUCK, GSStation.STATION_NEW), t)) {
					GSRoad.BuildRoad(T(x - 1, y), t);
					l.a = t;
				}
			}
		}
		tol = 2;
		local ib = l.dst == null ? null : PlaceIndustry(l.dst, mx - 11, row - 1, 3, true);
		if (l.dst != null && ib == null) { ib = PlaceIndustry(l.dst, mx - 13, row, 16); tol = 16; }
		if (ib != null) {
			local tiles = GSTileList_IndustryAccepting(ib, 3);
			tiles.KeepList(GSTileList_IndustryProducing(ib, 3));
			if (tiles.Count() == 0) tiles = GSTileList_IndustryAccepting(ib, 3);
			local t = StopTile(tiles, mx, false, row, tol);
			if (t != null) {
				local x = GSMap.GetTileX(t), y = GSMap.GetTileY(t);
				if (Road(mx, y, x - 1, y) &&
						Check("truck stop", GSRoad.BuildDriveThroughRoadStation(t, T(x + 1, y), GSRoad.ROADVEHTYPE_TRUCK, GSStation.STATION_NEW), t)) l.b = t;
			}
		}
		if (l.b == null) l.b = spare;
		GSLog.Info("line " + GSCargo.GetCargoLabel(l.cargo) + " " + GSIndustryType.GetName(l.src) + " -> " +
				(l.dst == null ? "-" : GSIndustryType.GetName(l.dst)));
		row += 7;
	}

	/* Every buildable road vehicle twice, from the depots in turn. Raw cargo: full load at the
	 * line's bay, deliver and leave empty. Secondary cargo of a line's far end: full load there,
	 * unload at the bay. Others shuttle between stops without loading. */
	local n = 0;
	local others = [];
	foreach (l in lines) if (l.a != null) others.append(l.a);
	others.append(spare);
	local plan = [];
	foreach (e in buses) plan.append([e, bus[n++ % 3], bus[n % 3], GSOrder.OF_NONE, GSOrder.OF_NONE]);
	foreach (c, list in engines) {
		local route = null;
		foreach (l in lines) {
			if (l.a == null) continue;
			if (l.cargo == c) route = [l.a, l.b, GSOrder.OF_FULL_LOAD_ANY, GSOrder.OF_NO_LOAD];
			else if (route == null && l.dst != null && l.b != spare && GSIndustryType.GetProducedCargo(l.dst).HasItem(c))
				route = [l.b, l.a, GSOrder.OF_FULL_LOAD_ANY, GSOrder.OF_UNLOAD | GSOrder.OF_NO_LOAD];
		}
		foreach (e in list) {
			if (route != null) {
				plan.append([e, route[0], route[1], route[2], route[3]]);
			} else {
				local a = others[n++ % others.len()];
				plan.append([e, a, spare == a ? others[0] : spare, GSOrder.OF_NO_LOAD, GSOrder.OF_NO_LOAD]);
			}
		}
	}
	local count = 0;
	foreach (k in [0, 1]) {
		foreach (p in plan) {
			local depot = depots[count % depots.len()];
			local v = GSVehicle.BuildVehicle(depot, p[0]);
			if (!Check("vehicle " + GSEngine.GetName(p[0]), GSVehicle.IsValidVehicle(v), depot)) continue;
			GSOrder.AppendOrder(v, p[1], p[3]);
			GSOrder.AppendOrder(v, p[2], p[4]);
			GSVehicle.StartStopVehicle(v);
			count++;
			this.Sleep(15);
		}
	}
	GSLog.Info("RoadTest done: " + count + " road vehicles, " + lines.len() + " lines");
}
