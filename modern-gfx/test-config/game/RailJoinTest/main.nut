class RailJoinTest extends GSController {
	function Start();
}

function T(x, y) { return GSMap.GetTileIndex(x, y); }

/* Failures show up as signs in the screenshot (the game's log is not kept). */
function Check(what, ok, tile = null)
{
	if (ok) return;
	GSLog.Warning(what + " failed: " + GSError.GetLastErrorString());
	if (tile != null) GSSign.BuildSign(tile, what + ": " + GSError.GetLastErrorString());
}

/* Moves to the neighbour tile across an edge, and the track joining two edges. */
MOVE <- { SW = [1, 0], SE = [0, 1], NE = [-1, 0], NW = [0, -1] };
OPPOSITE <- { SW = "NE", SE = "NW", NE = "SW", NW = "SE" };
function TrackBetween(a, b)
{
	local key = a < b ? a + b : b + a;
	return {
		NESW = GSRail.RAILTRACK_NE_SW, NWSE = GSRail.RAILTRACK_NW_SE, NENW = GSRail.RAILTRACK_NW_NE,
		SESW = GSRail.RAILTRACK_SW_SE, NWSW = GSRail.RAILTRACK_NW_SW, NESE = GSRail.RAILTRACK_NE_SE,
	}[key];
}

/* Lay one track per tile from (x, y) along the moves; returns the tiles with their tracks. */
function LayPath(x, y, moves)
{
	local laid = [];
	for (local i = 0; i <= moves.len(); i++) {
		local entry = OPPOSITE[moves[i > 0 ? i - 1 : 0]];
		local exit = moves[i < moves.len() ? i : moves.len() - 1];
		local track = TrackBetween(entry, exit);
		laid.append([x, y, track]);
		Check("track", GSRail.BuildRailTrack(T(x, y), track), T(x, y));
		if (i < moves.len()) {
			x += MOVE[moves[i]][0];
			y += MOVE[moves[i]][1];
		}
	}
	return laid;
}

function RailJoinTest::Start()
{
	while (GSCompany.ResolveCompanyID(GSCompany.COMPANY_FIRST) == GSCompany.COMPANY_INVALID) this.Sleep(1);
	local company = GSCompany.ResolveCompanyID(GSCompany.COMPANY_FIRST);
	GSCompany.ChangeBankBalance(company, 200000000, GSCompany.EXPENSES_OTHER, GSMap.TILE_INVALID);
	local mode = GSCompanyMode(company);
	GSRail.SetCurrentRailType(0);

	/* The screenshot starts near the map centre and runs to the south. */
	local cx = GSMap.GetMapSizeX() / 2 + 3;
	local cy = GSMap.GetMapSizeY() / 2 + 8;
	Check("level", GSTile.LevelTiles(T(cx - 10, cy - 10), T(cx + 17, cy + 12)), T(cx, cy));

	/* Zigzags: every straight piece meeting every corner piece on both ends, corner pieces in a
	 * row (vertical and horizontal on screen) and corner pieces turning by 90 degrees. */
	local paths = [
		[-9, -8, ["SW", "SW", "SE", "SW", "SE", "SW", "SW"]],             // X - vertical diagonal - X
		[-9, -3, ["SE", "SE", "SW", "SE", "SW", "SE", "SE"]],             // Y - vertical diagonal - Y
		[-2, 1, ["SW", "SW", "NW", "SW", "NW", "SW", "SW"]],              // X - horizontal diagonal - X
		[3, -9, ["SE", "SE", "NE", "SE", "NE", "SE", "SE"]],              // Y - horizontal diagonal - Y
		[4, 0, ["SW", "SW", "SE", "SW", "SE", "SE", "SE"]],               // X - vertical diagonal - Y
		[-5, 7, ["SW", "SE", "SW", "SE", "SW", "NW", "SW", "NW", "SW"]],  // vertical into horizontal diagonal
		[9, -5, ["SE", "SW", "SE", "SW", "SE", "NE", "SE", "NE", "SE"]],  // the same from Y
	];
	foreach (p in paths) LayPath(cx + p[0], cy + p[1], p[2]);

	/* Junctions: a corner piece branching off a straight one, and both corner pieces on one tile. */
	Check("junction X", GSRail.BuildRailTrack(T(cx - 8, cy - 8), GSRail.RAILTRACK_NE_SE), T(cx - 8, cy - 8));
	Check("junction Y", GSRail.BuildRailTrack(T(cx - 9, cy - 2), GSRail.RAILTRACK_NW_SW), T(cx - 9, cy - 2));
	Check("double", GSRail.BuildRailTrack(T(cx + 6, cy + 1), GSRail.RAILTRACK_NE_SE), T(cx + 6, cy + 1));

	/* Sloped: the same zigzags with the far corner of every corner piece raised, so the piece
	 * lies on the lower half of a one-corner slope. */
	foreach (p in [[12, 2, ["SW", "SW", "SE", "SW", "SE", "SW", "SW"]], [10, 10, ["SW", "SW", "NW", "SW", "NW", "SW", "SW"]]]) {
		local x = cx + p[0], y = cy + p[1];
		local corners = { [GSRail.RAILTRACK_NE_SE] = GSTile.SLOPE_W, [GSRail.RAILTRACK_NW_SW] = GSTile.SLOPE_E,
			[GSRail.RAILTRACK_NW_NE] = GSTile.SLOPE_S, [GSRail.RAILTRACK_SW_SE] = GSTile.SLOPE_N };
		/* Walk the path once without building to find the corner pieces. */
		local tx = x, ty = y;
		for (local i = 0; i <= p[2].len(); i++) {
			local entry = OPPOSITE[p[2][i > 0 ? i - 1 : 0]];
			local exit = p[2][i < p[2].len() ? i : p[2].len() - 1];
			local track = TrackBetween(entry, exit);
			if (track in corners) Check("raise", GSTile.RaiseTile(T(tx, ty), corners[track]), T(tx, ty));
			if (i < p[2].len()) {
				tx += MOVE[p[2][i]][0];
				ty += MOVE[p[2][i]][1];
			}
		}
		LayPath(x, y, p[2]);
	}
	GSLog.Info("rail join test built");
	while (true) this.Sleep(1000);
}
