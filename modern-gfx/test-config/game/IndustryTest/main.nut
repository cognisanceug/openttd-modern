class IndustryTest extends GSController {
	done = false;
	function Start();
	function Save() { return { done = true }; }
	function Load(version, data) { this.done = ("done" in data) && data.done; }
}

function T(x, y) { return GSMap.GetTileIndex(x, y); }

/* The 4x "big" screenshot starts at the view's top-left corner, so with the default
 * 10000x5000 shot it covers tiles with -10 <= dy - dx <= 68 and -15 <= dx + dy <= 63
 * relative to the map centre (dx, dy). */
function Visible(dx, dy, w, h)
{
	return dy - (dx + w) >= -8 && (dy + h) - dx <= 66 && dx + dy >= -12 && dx + w + dy + h <= 60;
}

function Note(tile, text)
{
	GSSign.BuildSign(tile, text);
	GSLog.Warning(text);
}

/* Try to build an industry of the given type on rings of growing radius around a tile. */
function PlaceIndustry(type, x, y, radius)
{
	for (local r = 0; r <= radius; r++) {
		for (local dx = -r; dx <= r; dx++) {
			for (local dy = -r; dy <= r; dy++) {
				if (abs(dx) != r && abs(dy) != r) continue;
				if (GSIndustryType.BuildIndustry(type, T(x + dx, y + dy))) return true;
			}
		}
	}
	Note(T(x, y), GSIndustryType.GetName(type) + ": " + GSError.GetLastErrorString());
	return false;
}

function IndustryTest::Start()
{
	/* After loading the photographed save, do not build again. */
	if (this.done) return;
	while (GSCompany.ResolveCompanyID(GSCompany.COMPANY_FIRST) == GSCompany.COMPANY_INVALID) this.Sleep(1);
	local cx = GSMap.GetMapSizeX() / 2;
	local cy = GSMap.GetMapSizeY() / 2;

	/* A large town for the statue and the bank. */
	GSTown.FoundTown(T(cx - 2, cy + 8), GSTown.TOWN_SIZE_LARGE, true, GSTown.ROAD_LAYOUT_2x2, null);
	local town = GSTile.GetClosestTown(T(cx - 2, cy + 8));

	{
		local mode = GSCompanyMode(GSCompany.ResolveCompanyID(GSCompany.COMPANY_FIRST));
		GSCompany.SetLoanAmount(GSCompany.GetMaxLoanAmount());
		if (!GSCompany.BuildCompanyHQ(T(cx - 4, cy - 1))) Note(T(cx - 4, cy - 1), "HQ: " + GSError.GetLastErrorString());
		for (local i = 0; i < 3; i++) GSObjectType.BuildObject(3, 0, T(cx - 1 + i, cy - 3));
		if (!GSTown.PerformTownAction(town, GSTown.TOWN_ACTION_BUILD_STATUE)) {
			Note(T(cx - 2, cy + 8), "statue: " + GSError.GetLastErrorString());
		}
	}

	/* Slot centres 7 tiles apart inside the photographed area, away from the HQ and the town. */
	local slots = [];
	for (local dy = -6; dy <= 60; dy += 7) {
		for (local dx = -10; dx <= 40; dx += 7) {
			if (!Visible(dx - 3, dy - 3, 7, 7)) continue;
			if (dx < 4 && dy < 18) continue; // HQ and town
			slots.append([cx + dx, cy + dy]);
		}
	}
	/* Farms spread fields over their neighbours, so they go to the last slot; banks only into towns. */
	local types = [];
	local farm = null;
	local bank = null;
	foreach (type, _ in GSIndustryTypeList()) {
		if (!GSIndustryType.CanBuildIndustry(type) && !GSIndustryType.CanProspectIndustry(type)) continue;
		local name = GSIndustryType.GetName(type);
		if (name.find("Oil Rig") != null) continue;
		if (name.find("Bank") != null) {
			bank = type;
		} else if (name.find("Farm") != null) {
			farm = type;
		} else {
			types.append(type);
		}
	}
	if (bank != null) PlaceIndustry(bank, cx - 2, cy + 8, 6);
	/* First wave: complete when the shot is taken. */
	local next = 0;
	foreach (type in types) {
		if (next >= slots.len() - 1) break;
		local s = slots[next++];
		PlaceIndustry(type, s[0], s[1], 5);
	}
	if (farm != null) PlaceIndustry(farm, slots.top()[0], slots.top()[1], 3);
	/* Construction stages: the third autosave comes at about day 80; a stage takes 4 tile
	 * loops of 256 ticks. Build the second wave in three groups aged ~36, ~21 and ~9 days. */
	local wave2 = [];
	foreach (type in types) {
		local name = GSIndustryType.GetName(type);
		if (name.find("Forest") == null && name.find("Oil Wells") == null) wave2.append(type);
	}
	foreach (g, day in [44, 59, 71]) {
		this.Sleep(max(1, 74 * day - GSController.GetTick()));
		foreach (i, type in wave2) {
			if (i % 3 != g || next >= slots.len() - 1) continue;
			local s = slots[next++];
			PlaceIndustry(type, s[0], s[1], 5);
		}
	}
}
