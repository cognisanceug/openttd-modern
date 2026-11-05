/* Test game script for the effect and disaster sprites: steam, diesel and electric trains on two
 * loops, trains driven into each other, buses, a small airport and the industries the disasters
 * target, so tools/fx_shot.sh can photograph smoke, sparks, explosions and disasters. GPL v2. */
class FxTestInfo extends GSInfo {
	function GetAuthor()      { return "openttd-modern"; }
	function GetName()        { return "FxTest"; }
	function GetShortName()   { return "FXTS"; }
	function GetDescription() { return "Builds trains, buses, an airport and industries for effect screenshots"; }
	function GetVersion()     { return 1; }
	function GetDate()        { return "2026-11-05"; }
	function CreateInstance() { return "FxTest"; }
	function GetAPIVersion()  { return "15"; }
}

RegisterGS(FxTestInfo());
