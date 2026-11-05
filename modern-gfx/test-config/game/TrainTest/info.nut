/* Test game script: builds loops of rail, electrified rail, monorail and maglev with
 * stations, a depot, a slope and primary industries, and buys every engine with wagons so
 * tools/train_shot.sh can photograph trains loaded and empty in all directions. GPL v2. */
class TrainTestInfo extends GSInfo {
	function GetAuthor()      { return "openttd-modern"; }
	function GetName()        { return "TrainTest"; }
	function GetShortName()   { return "TRNT"; }
	function GetDescription() { return "Builds rail loops and buys every train for screenshots"; }
	function GetVersion()     { return 1; }
	function GetDate()        { return "2026-11-05"; }
	function CreateInstance() { return "TrainTest"; }
	function GetAPIVersion()  { return "15"; }
}

RegisterGS(TrainTestInfo());
