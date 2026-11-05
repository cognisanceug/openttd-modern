/* Test game script: digs a canal pond, builds a ship depot and buoys and buys every
 * buildable ship (twice) on round trips between the buoys, so tools/ship_shot.sh can
 * photograph ships sailing in all directions. GPL v2. */
class ShipTestInfo extends GSInfo {
	function GetAuthor()      { return "openttd-modern"; }
	function GetName()        { return "ShipTest"; }
	function GetShortName()   { return "SHPT"; }
	function GetDescription() { return "Builds a pond with a ship depot and buoys and buys every ship for screenshots"; }
	function GetVersion()     { return 1; }
	function GetDate()        { return "2026-11-05"; }
	function CreateInstance() { return "ShipTest"; }
	function GetAPIVersion()  { return "15"; }
}

RegisterGS(ShipTestInfo());
