/* Test game script: builds canals, locks, a ship depot and an aqueduct around the map centre
 * so tools/water_shot.sh can photograph the canal sprites. GPL v2. */
class WaterTestInfo extends GSInfo {
	function GetAuthor()      { return "openttd-modern"; }
	function GetName()        { return "WaterTest"; }
	function GetShortName()   { return "WATT"; }
	function GetDescription() { return "Builds canals, locks, a ship depot and an aqueduct around the map centre for screenshots"; }
	function GetVersion()     { return 1; }
	function GetDate()        { return "2026-11-05"; }
	function CreateInstance() { return "WaterTest"; }
	function GetAPIVersion()  { return "15"; }
}

RegisterGS(WaterTestInfo());
