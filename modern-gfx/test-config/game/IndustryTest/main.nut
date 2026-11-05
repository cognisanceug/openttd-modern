class IndustryTest extends GSController {
	function Start();
}

function T(x, y) { return GSMap.GetTileIndex(x, y); }

/* The 4x "big" screenshot starts at the view's top-left corner, so with the default
 * 8000x4000 shot it covers tiles with -9 <= dy - dx <= 52 and -14 <= dx + dy <= 45
 * relative to the map centre (dx, dy). */
function Visible(dx, dy, w, h)
{
	return dy - (dx + w) >= -8 && (dy + h) - dx <= 50 && dx + dy >= -12 && dx + w + dy + h <= 42;
}

function Note(tile, text)
{
	GSSign.BuildSign(tile, text);
	GSLog.Warning(text);
}

/* Try to build an industry of the given type in a box, row by row. */
function PlaceIndustry(type, x0, y0, x1, y1)
{
	for (local y = y0; y <= y1; y++) {
		for (local x = x0; x <= x1; x++) {
			if (GSIndustryType.BuildIndustry(type, T(x, y))) return true;
		}
	}
	Note(T(x0, y0), GSIndustryType.GetName(type) + ": " + GSError.GetLastErrorString());
	return false;
}

function IndustryTest::Start()
{
	while (GSCompany.ResolveCompanyID(GSCompany.COMPANY_FIRST) == GSCompany.COMPANY_INVALID) this.Sleep(1);
	local cx = GSMap.GetMapSizeX() / 2;
	local cy = GSMap.GetMapSizeY() / 2;

	/* A large town for the statue and the bank. */
	local town = null;
	if (GSTown.FoundTown(T(cx - 2, cy + 8), GSTown.TOWN_SIZE_LARGE, true, GSTown.ROAD_LAYOUT_2x2, null)) {
		town = GSTile.GetClosestTown(T(cx - 2, cy + 8));
	} else {
		Note(T(cx - 2, cy + 8), "town: " + GSError.GetLastErrorString());
	}

	{
		local mode = GSCompanyMode(GSCompany.ResolveCompanyID(GSCompany.COMPANY_FIRST));
		GSCompany.SetLoanAmount(GSCompany.GetMaxLoanAmount());
		if (!GSCompany.BuildCompanyHQ(T(cx - 4, cy - 1))) Note(T(cx - 4, cy - 1), "HQ: " + GSError.GetLastErrorString());
		for (local i = 0; i < 3; i++) {
			if (!GSObjectType.BuildObject(3, 0, T(cx - 4, cy + 2 + i))) Note(T(cx - 4, cy + 2 + i), "land: " + GSError.GetLastErrorString());
		}
		if (town != null && !GSTown.PerformTownAction(town, GSTown.TOWN_ACTION_BUILD_STATUE)) {
			Note(T(cx - 2, cy + 8), "statue: " + GSError.GetLastErrorString());
		}
	}

	/* Slots of 7x7 tiles inside the photographed area, away from the HQ and the town. */
	local slots = [];
	for (local dy = -8; dy <= 40; dy += 7) {
		for (local dx = -12; dx <= 30; dx += 7) {
			if (!Visible(dx, dy, 6, 6)) continue;
			if (dx < 2 && dy < 16) continue; // HQ and town
			slots.append([cx + dx, cy + dy]);
		}
	}
	local types = [];
	foreach (type, _ in GSIndustryTypeList()) {
		if (GSIndustryType.CanBuildIndustry(type) || GSIndustryType.CanProspectIndustry(type)) types.append(type);
	}
	/* First wave: complete when the shot is taken. */
	local next = 0;
	foreach (type in types) {
		if (next >= slots.len()) break;
		local s = slots[next++];
		PlaceIndustry(type, s[0], s[1], s[0] + 2, s[1] + 2);
	}
	/* Second wave shortly before the third autosave: construction stages. */
	this.Sleep(74 * 70);
	foreach (type in types) {
		if (next >= slots.len()) break;
		local s = slots[next++];
		PlaceIndustry(type, s[0], s[1], s[0] + 2, s[1] + 2);
	}
}
