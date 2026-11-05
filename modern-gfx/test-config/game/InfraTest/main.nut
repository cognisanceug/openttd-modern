class InfraTest extends GSController {
	function Start();
}

function T(x, y) { return GSMap.GetTileIndex(x, y); }

function Check(what, ok)
{
	if (!ok) GSLog.Warning(what + " failed: " + GSError.GetLastErrorString());
}

function InfraTest::Start()
{
	/* The player's company is created after the script starts. */
	while (GSCompany.ResolveCompanyID(GSCompany.COMPANY_FIRST) == GSCompany.COMPANY_INVALID) this.Sleep(1);
	local mode = GSCompanyMode(GSCompany.ResolveCompanyID(GSCompany.COMPANY_FIRST));
	GSCompany.SetLoanAmount(GSCompany.GetMaxLoanAmount());
	GSRail.SetCurrentRailType(0); // normal rail; the list starts with monorail in later years
	GSRoad.SetCurrentRoadType(GSRoad.ROADTYPE_ROAD);

	local cx = GSMap.GetMapSizeX() / 2;
	local cy = GSMap.GetMapSizeY() / 2;

	/* Straight lines crossing at the centre. */
	Check("GSRail.BuildRail T(cx - 5", GSRail.BuildRail(T(cx - 5, cy), T(cx - 4, cy), T(cx + 4, cy)));
	Check("GSRail.BuildRail T(cx", GSRail.BuildRail(T(cx, cy - 5), T(cx, cy - 4), T(cx, cy + 4)));

	/* Short pieces, double pieces and a junction. */
	Check("GSRail.BuildRailTrack T(cx - 2", GSRail.BuildRailTrack(T(cx - 2, cy - 2), GSRail.RAILTRACK_NW_NE));
	Check("GSRail.BuildRailTrack T(cx - 2", GSRail.BuildRailTrack(T(cx - 2, cy - 2), GSRail.RAILTRACK_SW_SE));
	Check("GSRail.BuildRailTrack T(cx + 2", GSRail.BuildRailTrack(T(cx + 2, cy - 2), GSRail.RAILTRACK_NW_SW));
	Check("GSRail.BuildRailTrack T(cx + 2", GSRail.BuildRailTrack(T(cx + 2, cy - 2), GSRail.RAILTRACK_NE_SE));
	Check("GSRail.BuildRailTrack T(cx - 3", GSRail.BuildRailTrack(T(cx - 3, cy), GSRail.RAILTRACK_NW_NE));
	Check("GSRail.BuildRailTrack T(cx - 2", GSRail.BuildRailTrack(T(cx - 2, cy - 1), GSRail.RAILTRACK_NE_SE));
	Check("GSRail.BuildRailTrack T(cx - 1", GSRail.BuildRailTrack(T(cx - 1, cy - 2), GSRail.RAILTRACK_SW_SE));

	/* Roads: two level crossings and a road junction. */
	Check("GSRoad.BuildRoad T(cx + 1", GSRoad.BuildRoad(T(cx + 1, cy - 3), T(cx + 1, cy + 3)));
	Check("GSRoad.BuildRoad T(cx - 3", GSRoad.BuildRoad(T(cx - 3, cy + 2), T(cx + 3, cy + 2)));
	Check("GSRoad.BuildRoad T(cx - 3", GSRoad.BuildRoad(T(cx - 3, cy + 2), T(cx - 3, cy + 3)));
	Check("GSRoad.BuildRoad T(cx + 3", GSRoad.BuildRoad(T(cx + 3, cy - 2), T(cx + 4, cy - 2)));

	/* Signals of every type along the X line (electric; semaphores depend on the build date). */
	Check("signal normal", GSRail.BuildSignal(T(cx - 4, cy), T(cx - 5, cy), GSRail.SIGNALTYPE_NORMAL));
	Check("signal entry", GSRail.BuildSignal(T(cx - 1, cy), T(cx - 2, cy), GSRail.SIGNALTYPE_ENTRY));
	Check("signal exit", GSRail.BuildSignal(T(cx + 2, cy), T(cx + 1, cy), GSRail.SIGNALTYPE_EXIT));
	Check("signal combo", GSRail.BuildSignal(T(cx + 3, cy), T(cx + 4, cy), GSRail.SIGNALTYPE_COMBO));
	Check("signal pbs", GSRail.BuildSignal(T(cx + 4, cy), T(cx + 3, cy), GSRail.SIGNALTYPE_PBS));
	Check("signal pbs oneway", GSRail.BuildSignal(T(cx - 2, cy), T(cx - 1, cy), GSRail.SIGNALTYPE_PBS_ONEWAY));

	/* Depots with visible doors: rail facing SW, road facing SE and SW. */
	Check("rail depot", GSRail.BuildRailDepot(T(cx - 5, cy), T(cx - 4, cy)));
	Check("road depot SE", GSRoad.BuildRoadDepot(T(cx - 2, cy + 1), T(cx - 2, cy + 2)));
	Check("road depot SW", GSRoad.BuildRoadDepot(T(cx - 4, cy + 2), T(cx - 3, cy + 2)));

	/* Bridges of several types, each in the first free row south of the test layout. */
	local types = [0, 2, 4, 6, 9, 10];
	local row = cy + 5;
	foreach (bt in types) {
		local built = false;
		while (!built && row < cy + 16) {
			built = GSBridge.BuildBridge(GSVehicle.VT_RAIL, bt, T(cx - 3, row), T(cx + 3, row));
			row++;
		}
		if (!built) GSLog.Warning("bridge type " + bt + " not built: " + GSError.GetLastErrorString());
	}

	/* One rail and one road tunnel on the nearest inclined slopes. */
	local kinds = [GSVehicle.VT_RAIL, GSVehicle.VT_ROAD];
	foreach (vt in kinds) {
		local done = false;
		for (local r = 2; r < 14 && !done; r++) {
			for (local dx = -r; dx <= r && !done; dx++) {
				for (local dy = -r; dy <= r && !done; dy++) {
					local t = T(cx + dx, cy + dy);
					local sl = GSTile.GetSlope(t);
					if (sl == GSTile.SLOPE_NE || sl == GSTile.SLOPE_SE || sl == GSTile.SLOPE_SW || sl == GSTile.SLOPE_NW) {
						done = GSTunnel.BuildTunnel(vt, t);
					}
				}
			}
		}
		if (!done) GSLog.Warning("tunnel not built");
	}

	/* A rail station north of the test layout; the game picks platform, building and roof tiles. */
	local built = false;
	for (local y = cy - 12; y < cy - 4 && !built; y++) {
		for (local x = cx - 6; x < cx + 2 && !built; x++) {
			built = GSRail.BuildRailStation(T(x, y), GSRail.RAILTRACK_NE_SW, 3, 5, GSStation.STATION_NEW);
		}
	}
	if (!built) GSLog.Warning("rail station not built: " + GSError.GetLastErrorString());

	/* Road stops along the road at cy + 2: bus and truck bays facing it, drive-through stops on it. */
	Check("bus bay", GSRoad.BuildRoadStation(T(cx + 2, cy + 3), T(cx + 2, cy + 2), GSRoad.ROADVEHTYPE_BUS, GSStation.STATION_NEW));
	Check("truck bay", GSRoad.BuildRoadStation(T(cx + 3, cy + 1), T(cx + 3, cy + 2), GSRoad.ROADVEHTYPE_TRUCK, GSStation.STATION_NEW));
	Check("bus drive-through", GSRoad.BuildDriveThroughRoadStation(T(cx - 1, cy + 2), T(cx, cy + 2), GSRoad.ROADVEHTYPE_BUS, GSStation.STATION_NEW));
	Check("truck drive-through", GSRoad.BuildDriveThroughRoadStation(T(cx + 3, cy + 2), T(cx + 2, cy + 2), GSRoad.ROADVEHTYPE_TRUCK, GSStation.STATION_NEW));
	Check("rail waypoint", GSRail.BuildRailWaypoint(T(cx - 3, cy)));

	/* Electrify the test line and lay tram tracks on the roads plus a tram-only line with a curve. */
	/* Rail type 1 is electrified rail in the base game. */
	if (GSRail.IsRailTypeAvailable(1)) {
		Check("electrify", GSRail.ConvertRailType(T(cx - 5, cy - 3), T(cx + 5, cy + 3), 1));
	} else {
		GSLog.Warning("electrified rail not available");
	}
	local tram = null;
	foreach (rt, _ in GSRoadTypeList(GSRoad.ROADTRAMTYPES_TRAM)) { tram = rt; break; }
	if (tram != null) {
		GSRoad.SetCurrentRoadType(tram);
		Check("tram on road x", GSRoad.BuildRoad(T(cx - 3, cy + 2), T(cx + 3, cy + 2)));
		Check("tram on road y", GSRoad.BuildRoad(T(cx + 1, cy - 3), T(cx + 1, cy + 3)));
		Check("tram line", GSRoad.BuildRoad(T(cx + 6, cy - 4), T(cx + 6, cy + 1)));
		Check("tram curve", GSRoad.BuildRoad(T(cx + 6, cy + 1), T(cx + 9, cy + 1)));
	} else {
		GSLog.Warning("no tram road type");
	}

	GSLog.Info("InfraTest done");
	while (true) this.Sleep(1000);
}
