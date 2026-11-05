/* Test game script: funds farms and clears rows of land around the map centre, so
 * tools/terrain_shot.sh can photograph farm fields, fences and the grass regrowth stages. GPL v2. */
class TerrainTestInfo extends GSInfo {
	function GetAuthor()      { return "openttd-modern"; }
	function GetName()        { return "TerrainTest"; }
	function GetShortName()   { return "TRNT"; }
	function GetDescription() { return "Funds farms and clears land around the map centre for screenshots"; }
	function GetVersion()     { return 1; }
	function GetDate()        { return "2026-11-05"; }
	function CreateInstance() { return "TerrainTest"; }
	function GetAPIVersion()  { return "15"; }
}

RegisterGS(TerrainTestInfo());
