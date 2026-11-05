/* Test game script: builds rail zigzags (straight and corner pieces, flat and sloped)
 * so tools/ingame_shot.sh can photograph the infrastructure sprites. GPL v2. */
class RailJoinTestInfo extends GSInfo {
	function GetAuthor()      { return "openttd-modern"; }
	function GetName()        { return "RailJoinTest"; }
	function GetShortName()   { return "RJNT"; }
	function GetDescription() { return "Builds rail zigzags around the map centre for screenshots"; }
	function GetVersion()     { return 1; }
	function GetDate()        { return "2026-11-05"; }
	function CreateInstance() { return "RailJoinTest"; }
	function GetAPIVersion()  { return "15"; }
}

RegisterGS(RailJoinTestInfo());
