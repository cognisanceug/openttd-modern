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
	GSRail.SetCurrentRailType(GSRailTypeList().Begin());
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

	GSLog.Info("InfraTest done");
	while (true) this.Sleep(1000);
}
