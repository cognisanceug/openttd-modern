/* Test game script: builds a main road with depots and bus stops and one line per cargo from a
 * raw industry to an industry accepting it, and buys every buildable road vehicle (twice), so
 * tools/road_shot.sh can photograph buses and lorries, loaded and empty, in all directions. GPL v2. */
class RoadTestInfo extends GSInfo {
	function GetAuthor()      { return "openttd-modern"; }
	function GetName()        { return "RoadTest"; }
	function GetShortName()   { return "RDVT"; }
	function GetDescription() { return "Builds roads, stops and industries and buys every road vehicle for screenshots"; }
	function GetVersion()     { return 1; }
	function GetDate()        { return "2026-11-05"; }
	function CreateInstance() { return "RoadTest"; }
	function GetAPIVersion()  { return "15"; }
}

RegisterGS(RoadTestInfo());
