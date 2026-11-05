/* Test game script: builds two big airports, a helistation and a heliport and buys every
 * buildable aircraft and helicopter on round trips between them, so tools/aircraft_shot.sh
 * can photograph aircraft parked, taxiing, taking off and in flight. GPL v2. */
class AircraftTestInfo extends GSInfo {
	function GetAuthor()      { return "openttd-modern"; }
	function GetName()        { return "AircraftTest"; }
	function GetShortName()   { return "AIRT"; }
	function GetDescription() { return "Builds airports and heliports and buys every aircraft for screenshots"; }
	function GetVersion()     { return 1; }
	function GetDate()        { return "2026-11-05"; }
	function CreateInstance() { return "AircraftTest"; }
	function GetAPIVersion()  { return "15"; }
}

RegisterGS(AircraftTestInfo());
