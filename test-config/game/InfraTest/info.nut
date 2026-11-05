/* Test game script: builds rails, roads and level crossings around the map centre
 * so tools/ingame_shot.sh can photograph the infrastructure sprites. GPL v2. */
class InfraTestInfo extends GSInfo {
	function GetAuthor()      { return "openttd-modern"; }
	function GetName()        { return "InfraTest"; }
	function GetShortName()   { return "INFT"; }
	function GetDescription() { return "Builds rails, roads and level crossings around the map centre for screenshots"; }
	function GetVersion()     { return 1; }
	function GetDate()        { return "2026-11-05"; }
	function CreateInstance() { return "InfraTest"; }
	function GetAPIVersion()  { return "15"; }
}

RegisterGS(InfraTestInfo());
