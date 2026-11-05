class FxTest extends GSController {
	done = false;
	function Start();
	function Save() { return { done = true }; }
	function Load(version, data) { this.done = ("done" in data) && data.done; }
}

function T(x, y) { return GSMap.GetTileIndex(x, y); }

function Check(what, ok, tile = null)
{
	if (!ok) {
		local text = what + ": " + GSError.GetLastErrorString();
		GSLog.Warning(text);
		if (tile != null) GSSign.BuildSign(tile, text);
	}
	return ok;
}

function LevelTo(x0, y0, x1, y1, h)
{
	local t = T(x0, y0);
	for (local i = 0; i < 8 && GSTile.GetCornerHeight(t, GSTile.CORNER_N) > h; i++) GSTile.LowerTile(t, GSTile.SLOPE_N);
	for (local i = 0; i < 8 && GSTile.GetCornerHeight(t, GSTile.CORNER_N) < h; i++) GSTile.RaiseTile(t, GSTile.SLOPE_N);
	return Check("level " + x0 + "," + y0, GSTile.LevelTiles(t, T(x1, y1)));
}

/* Rectangular loop x0-x1 x y0-y1 with a station on the y0 side, a depot on the x0 side and one-way signals. */
function BuildLoop(rt, x0, y0, x1, y1)
{
	GSRail.SetCurrentRailType(rt);
	local path = [];
	for (local x = x0; x < x1; x++) path.append(T(x, y0));
	for (local y = y0; y < y1; y++) path.append(T(x1, y));
	for (local x = x1; x > x0; x--) path.append(T(x, y1));
	for (local y = y1; y > y0; y--) path.append(T(x0, y));
	local xa = (x0 + x1) / 2 - 2;
	Check("station", GSRail.BuildRailStation(T(xa, y0), GSRail.RAILTRACK_NE_SW, 1, 4, GSStation.STATION_NEW), T(xa, y0));
	Check("station", GSRail.BuildRailStation(T(xa, y1), GSRail.RAILTRACK_NE_SW, 1, 4, GSStation.STATION_NEW), T(xa, y1));
	local n = path.len();
	for (local i = 0; i < n; i++) {
		if (GSRail.IsRailStationTile(path[i])) continue;
		Check("rail", GSRail.BuildRail(path[(i + n - 1) % n], path[i], path[(i + 1) % n]), path[i]);
	}
	local ym = (y0 + y1) / 2;
	local depot = T(x0 - 1, ym), front = T(x0, ym);
	Check("depot", GSRail.BuildRailDepot(depot, front), depot);
	Check("depot track", GSRail.BuildRailTrack(front, GSRail.RAILTRACK_NW_NE), front);
	Check("depot track", GSRail.BuildRailTrack(front, GSRail.RAILTRACK_NE_SE), front);
	for (local i = 1; i < n; i += 3) {
		local t = path[i];
		if (GSRail.IsRailStationTile(t) || GSRail.IsRailStationTile(path[(i + 1) % n]) || t == front) continue;
		GSRail.BuildSignal(t, path[(i + 1) % n], GSRail.SIGNALTYPE_NORMAL);
	}
	return [depot, T(xa, y0), T(xa, y1)];
}

/* Buildable engines of rail type rt whose name contains one of the words (all of them if words is empty). */
function Engines(rt, words)
{
	local out = [];
	foreach (e, _ in GSEngineList(GSVehicle.VT_RAIL)) {
		if (!GSEngine.IsBuildable(e) || GSEngine.IsWagon(e) || GSEngine.GetRailType(e) != rt) continue;
		local name = GSEngine.GetName(e);
		local ok = words.len() == 0;
		foreach (w in words) if (name.find(w) != null) ok = true;
		if (ok) out.append(e);
	}
	return out;
}

function Wagon()
{
	foreach (e, _ in GSEngineList(GSVehicle.VT_RAIL)) {
		if (GSEngine.IsBuildable(e) && GSEngine.IsWagon(e) && GSEngine.GetRailType(e) == 0) return e;
	}
	return null;
}

function BuyTrains(stops, engines, wagons)
{
	local wagon = Wagon();
	foreach (e in engines) {
		local v = GSVehicle.BuildVehicle(stops[0], e);
		if (!Check("engine " + GSEngine.GetName(e), GSVehicle.IsValidVehicle(v), stops[0])) continue;
		for (local j = 0; j < wagons && wagon != null; j++) {
			local w = GSVehicle.BuildVehicle(stops[0], wagon);
			if (GSVehicle.IsValidVehicle(w)) GSVehicle.MoveWagon(w, 0, v, GSVehicle.GetNumWagons(v) - 1);
		}
		GSOrder.AppendOrder(v, stops[1], GSOrder.OF_NONE);
		GSOrder.AppendOrder(v, stops[2], GSOrder.OF_NONE);
		GSVehicle.StartStopVehicle(v);
		GSLog.Info("train " + GSEngine.GetName(e));
		GSController.Sleep(60);
	}
}

/* A dead-end line x0-x1 at y with a depot at both ends; returns the engines waiting in the depots. */
function CrashLine(x0, x1, y, engine)
{
	GSRail.SetCurrentRailType(0);
	for (local x = x0; x <= x1; x++) Check("crash line", GSRail.BuildRailTrack(T(x, y), GSRail.RAILTRACK_NE_SW), T(x, y));
	local a = T(x0 - 1, y), b = T(x1 + 1, y);
	/* A block signal near b, for trains towards b: the engine from b may leave its depot while the line
	 * is occupied and passes the signal from behind. */
	Check("crash signal", GSRail.BuildSignal(T(x1 - 1, y), T(x1 - 2, y), GSRail.SIGNALTYPE_NORMAL), T(x1 - 1, y));
	Check("crash depot", GSRail.BuildRailDepot(a, T(x0, y)), a);
	Check("crash depot", GSRail.BuildRailDepot(b, T(x1, y)), b);
	local out = [];
	foreach (d in [a, b]) {
		local v = GSVehicle.BuildVehicle(d, engine);
		if (!Check("crash engine", GSVehicle.IsValidVehicle(v), d)) continue;
		Check("crash order", GSOrder.AppendOrder(v, d == a ? b : a, GSOrder.OF_NONE), d);  // to the other end
		out.append(v);
	}
	return out;
}

function BuildBuses(x0, x1, y)
{
	GSRoad.SetCurrentRoadType(GSRoad.ROADTYPE_ROAD);
	Check("road", GSRoad.BuildRoad(T(x0, y), T(x1, y)), T(x0, y));
	Check("stop", GSRoad.BuildDriveThroughRoadStation(T(x0 + 1, y), T(x0 + 2, y), GSRoad.ROADVEHTYPE_BUS, GSStation.STATION_NEW), T(x0 + 1, y));
	Check("stop", GSRoad.BuildDriveThroughRoadStation(T(x1 - 1, y), T(x1 - 2, y), GSRoad.ROADVEHTYPE_BUS, GSStation.STATION_NEW), T(x1 - 1, y));
	local depot = T((x0 + x1) / 2, y + 1);
	Check("road depot", GSRoad.BuildRoadDepot(depot, T((x0 + x1) / 2, y)), depot);
	GSRoad.BuildRoad(depot, T((x0 + x1) / 2, y));
	local passengers = null;
	foreach (c, _ in GSCargoList()) if (GSCargo.HasCargoClass(c, GSCargo.CC_PASSENGERS)) passengers = c;
	local n = 0;
	foreach (e, _ in GSEngineList(GSVehicle.VT_ROAD)) {
		if (n >= 6 || !GSEngine.IsBuildable(e) || GSEngine.GetCargoType(e) != passengers) continue;
		local v = GSVehicle.BuildVehicle(depot, e);
		if (!Check("bus", GSVehicle.IsValidVehicle(v), depot)) continue;
		GSOrder.AppendOrder(v, T(x0 + 1, y), GSOrder.OF_NONE);
		GSOrder.AppendOrder(v, T(x1 - 1, y), GSOrder.OF_NONE);
		GSVehicle.StartStopVehicle(v);
		GSController.Sleep(40);
		n++;
	}
}

function BuildNear(type, sx, sy, r)
{
	for (local d = 0; d <= r; d++) {
		for (local dx = -d; dx <= d; dx++) {
			foreach (dy in [-d, d]) {
				if (GSIndustryType.BuildIndustry(type, T(sx + dx, sy + dy))) return true;
			}
		}
	}
	return false;
}

function FxTest::Start()
{
	if (this.done) return;
	while (GSCompany.ResolveCompanyID(GSCompany.COMPANY_FIRST) == GSCompany.COMPANY_INVALID) this.Sleep(1);
	local company = GSCompany.ResolveCompanyID(GSCompany.COMPANY_FIRST);
	GSCompany.ChangeBankBalance(company, 2000000000, GSCompany.EXPENSES_OTHER, GSMap.TILE_INVALID);
	local mode = GSCompanyMode(company);
	/* "big" screenshots start at the view's top-left corner, the map centre: the middle of the
	 * 10000 x 5000 shot is about 21 tiles further along y (map 128 x 256, as in TrainTest). */
	local cx = GSMap.GetMapSizeX() / 2 - 1;
	local cy = GSMap.GetMapSizeY() / 2 + 21;
	LevelTo(cx - 20, cy - 19, cx + 18, cy + 6, 2);

	/* Steam and diesel trains on plain rail (north-west), electric trains on electrified rail (north-east). */
	local stops = BuildLoop(0, cx - 18, cy - 17, cx - 4, cy - 8);
	local estops = GSRail.IsRailTypeAvailable(1) ? BuildLoop(1, cx + 2, cy - 17, cx + 16, cy - 8) : null;
	local steam = Engines(0, ["Steam", "Choo-Choo"]);
	local diesel = Engines(0, ["Diesel"]);
	if (steam.len() + diesel.len() == 0) steam = Engines(0, []);
	local crash_engine = steam.len() > 0 ? steam[0] : diesel[0];
	local pairs = [CrashLine(cx - 16, cx - 5, cy - 5, crash_engine), CrashLine(cx - 16, cx - 5, cy - 2, crash_engine)];
	BuildBuses(cx + 3, cx + 17, cy - 5);

	/* Disaster targets: a small airport and the industries south of the trains. */
	foreach (a in [GSAirport.AT_SMALL, GSAirport.AT_COMMUTER, GSAirport.AT_LARGE]) {
		if (GSAirport.IsValidAirportType(a) && Check("airport", GSAirport.BuildAirport(T(cx + 8, cy + 1), a, GSStation.STATION_NEW), T(cx + 8, cy + 1))) break;
	}
	local wanted = ["Power Station", "Oil Refinery", "Factory", "Coal Mine", "Bubble Generator", "Toy Factory",
		"Sweet Factory", "Toffee Quarry", "Battery Farm"];
	foreach (t, _ in GSIndustryTypeList()) {
		local name = GSIndustryType.GetName(t);
		foreach (w in wanted) {
			if (name == w) {
				if (Check("industry " + name, BuildNear(t, cx - 6, cy + 6, 12))) GSLog.Info("industry " + name);
				break;
			}
		}
	}

	BuyTrains(stops, steam, 3);
	BuyTrains(stops, diesel, 3);
	if (estops != null) BuyTrains(estops, Engines(1, []), 3);

	/* Collisions: on each dead-end line one engine runs out and is stopped half-way, then the engine from the
	 * other end runs into it (a train does not leave its depot into an occupied block). Second pair later. */
	GSLog.Info("FxTest built");
	foreach (i, p in pairs) {
		this.Sleep(i == 0 ? 400 : 2200);
		if (p.len() < 2) continue;
		GSVehicle.StartStopVehicle(p[0]);
		this.Sleep(120);
		GSVehicle.StartStopVehicle(p[0]);
		this.Sleep(120);
		GSVehicle.StartStopVehicle(p[1]);
		GSLog.Info("crash pair " + i + " started");
	}
}
