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

	GSLog.Info("InfraTest done");
	while (true) this.Sleep(1000);
}
