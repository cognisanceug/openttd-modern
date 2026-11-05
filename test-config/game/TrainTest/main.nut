class TrainTest extends GSController {
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

/* Append the tiles from the last tile of path to (x, y): straight, or a staircase (a diagonal track) when both change. */
function Walk(path, x, y)
{
	local p = path.top();
	local px = GSMap.GetTileX(p), py = GSMap.GetTileY(p);
	local step = 0;
	while (px != x || py != y) {
		if (px != x && (py == y || step % 2 == 0)) px += x > px ? 1 : -1;
		else py += y > py ? 1 : -1;
		path.append(T(px, py));
		step++;
	}
}

/* An octagonal loop: x0-x1 x y0-y1 with chamfered (diagonal) corners of c tiles. Returns the closed path of tiles. */
function LoopPath(x0, y0, x1, y1, c)
{
	local path = [T(x0 + c, y0)];
	Walk(path, x1 - c, y0);
	Walk(path, x1, y0 + c);
	Walk(path, x1, y1 - c);
	Walk(path, x1 - c, y1);
	Walk(path, x0 + c, y1);
	Walk(path, x0, y1 - c);
	Walk(path, x0, y0 + c);
	Walk(path, x0 + c, y0);
	path.pop(); // the start again
	return path;
}

/* Primary industry types producing a cargo. */
function Producers(cargo)
{
	local out = [];
	foreach (t, _ in GSIndustryTypeList()) {
		if (GSIndustryType.IsRawIndustry(t) && GSIndustryType.GetProducedCargo(t).HasItem(cargo)) out.append(t);
	}
	return out;
}

function BuildNear(type, sx, sy, r)
{
	for (local d = 2; d <= r; d++) {
		for (local dx = -d; dx <= d; dx++) {
			foreach (dy in [-d, d]) {
				if (GSIndustryType.BuildIndustry(type, T(sx + dx, sy + dy))) return true;
			}
		}
	}
	return false;
}

/* One test loop for rail type rt: x0-x1 x y0-y1. Station A (the loading station, primary industries built round it)
 * on the y0 side, station B on the y1 side, a depot on the x0 side and a hill on the x1 side. Every engine of the rail
 * type gets four wagons, cycling through the wagons of that type; every other freight train waits for a full load at A. */
function TrainTest::BuildLoop(rt, x0, y0, x1, y1, h)
{
	if (!GSRail.IsRailTypeAvailable(rt)) {
		GSLog.Warning("rail type " + rt + " not available");
		return;
	}
	GSRail.SetCurrentRailType(rt);
	local ym = (y0 + y1) / 2;
	LevelTo(x1 - 1, ym - 1, x1 + 2, ym + 1, h + 1); // the hill: track up and down a slope

	local xa = (x0 + x1) / 2 - 2;
	Check("station A", GSRail.BuildRailStation(T(xa, y0), GSRail.RAILTRACK_NE_SW, 1, 4, GSStation.STATION_NEW), T(xa, y0));
	Check("station B", GSRail.BuildRailStation(T(xa, y1), GSRail.RAILTRACK_NE_SW, 1, 4, GSStation.STATION_NEW), T(xa, y1));
	local path = LoopPath(x0, y0, x1, y1, 3);
	local n = path.len();
	for (local i = 0; i < n; i++) {
		local t = path[i];
		if (GSRail.IsRailStationTile(t)) continue;
		Check("rail " + rt, GSRail.BuildRail(path[(i + n - 1) % n], t, path[(i + 1) % n]), t);
	}
	local depot = T(x0 - 1, ym + 1), front = T(x0, ym + 1);
	Check("depot", GSRail.BuildRailDepot(depot, front), depot);
	Check("depot track", GSRail.BuildRailTrack(front, GSRail.RAILTRACK_NW_NE), front);
	Check("depot track", GSRail.BuildRailTrack(front, GSRail.RAILTRACK_NE_SE), front);
	/* One-way block signals every third tile, so the trains run round in one direction. */
	for (local i = 1; i < n; i += 3) {
		local t = path[i];
		if (GSRail.IsRailStationTile(t) || GSRail.IsRailStationTile(path[(i + 1) % n]) || t == front) continue;
		GSRail.BuildSignal(t, path[(i + 1) % n], GSRail.SIGNALTYPE_NORMAL);
	}

	local engines = [], wagons = [];
	foreach (e, _ in GSEngineList(GSVehicle.VT_RAIL)) {
		if (!GSEngine.IsBuildable(e)) continue;
		/* Electric trains pull the plain rail wagons. */
		if (GSEngine.IsWagon(e)) {
			if (GSEngine.GetRailType(e) == (rt == 1 ? 0 : rt)) wagons.append(e);
		} else if (GSEngine.GetRailType(e) == rt) {
			engines.append(e);
		}
	}
	/* Industries for the wagons' cargo round station A (inside the loop and north of it). */
	local built = {};
	foreach (w in wagons) {
		foreach (it in Producers(GSEngine.GetCargoType(w))) {
			if (it in built) break;
			if (BuildNear(it, xa + 1, y0 + 1, 7)) {
				built[it] <- true;
				GSLog.Info("industry " + GSIndustryType.GetName(it));
				break;
			}
		}
	}
	local k = 0;
	foreach (idx, e in engines) {
		local v = GSVehicle.BuildVehicle(depot, e);
		if (!Check("engine " + GSEngine.GetName(e), GSVehicle.IsValidVehicle(v), depot)) continue;
		for (local j = 0; j < 4 && wagons.len() > 0; j++) {
			local w = GSVehicle.BuildVehicle(depot, wagons[k++ % wagons.len()]);
			if (GSVehicle.IsValidVehicle(w)) GSVehicle.MoveWagon(w, 0, v, GSVehicle.GetNumWagons(v) - 1);
		}
		GSOrder.AppendOrder(v, T(xa, y0), idx % 2 == 0 ? GSOrder.OF_FULL_LOAD_ANY : GSOrder.OF_NONE);
		GSOrder.AppendOrder(v, T(xa, y1), GSOrder.OF_NONE);
		GSVehicle.StartStopVehicle(v);
		GSLog.Info("train " + GSEngine.GetName(e));
		this.Sleep(150);
	}
}

function TrainTest::Start()
{
	/* After loading the photographed save, do not build again. */
	if (this.done) return;
	while (GSCompany.ResolveCompanyID(GSCompany.COMPANY_FIRST) == GSCompany.COMPANY_INVALID) this.Sleep(1);
	local company = GSCompany.ResolveCompanyID(GSCompany.COMPANY_FIRST);
	GSCompany.ChangeBankBalance(company, 2000000000, GSCompany.EXPENSES_OTHER, GSMap.TILE_INVALID);
	/* "big" screenshots start at the view's top-left corner, which is the map centre: the middle of the
	 * 10000 x 5000 shot is about 21 tiles further along y (map 128 x 256). */
	local cx = GSMap.GetMapSizeX() / 2 - 1;
	local cy = GSMap.GetMapSizeY() / 2 + 21;
	local mode = GSCompanyMode(company);
	LevelTo(cx - 20, cy - 17, cx + 19, cy + 17, 2);
	/* Four loops round the map centre: rail and electrified rail north, monorail and maglev south. */
	this.BuildLoop(0, cx - 16, cy - 13, cx - 3, cy - 3, 2);
	this.BuildLoop(1, cx + 2, cy - 13, cx + 15, cy - 3, 2);
	this.BuildLoop(2, cx - 16, cy + 3, cx - 3, cy + 13, 2);
	this.BuildLoop(3, cx + 2, cy + 3, cx + 15, cy + 13, 2);
	GSLog.Info("TrainTest done");
}
