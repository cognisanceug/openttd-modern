/* Test game script: builds every original airport type, a pond with docks in all four
 * directions, buoys and an oil rig around the map centre so tools/airport_shot.sh can
 * photograph them. GPL v2. */
class AirportTestInfo extends GSInfo {
	function GetAuthor()      { return "openttd-modern"; }
	function GetName()        { return "AirportTest"; }
	function GetShortName()   { return "APTT"; }
	function GetDescription() { return "Builds airports, docks, buoys and an oil rig around the map centre for screenshots"; }
	function GetVersion()     { return 1; }
	function GetDate()        { return "2026-11-05"; }
	function CreateInstance() { return "AirportTest"; }
	function GetAPIVersion()  { return "15"; }
}

RegisterGS(AirportTestInfo());
