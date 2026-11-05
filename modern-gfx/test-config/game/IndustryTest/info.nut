/* Test game script: builds a company HQ, a statue, owned land and every buildable
 * industry around the map centre so tools/industry_shot.sh can photograph them. GPL v2. */
class IndustryTestInfo extends GSInfo {
	function GetAuthor()      { return "openttd-modern"; }
	function GetName()        { return "IndustryTest"; }
	function GetShortName()   { return "INDT"; }
	function GetDescription() { return "Builds objects and industries around the map centre for screenshots"; }
	function GetVersion()     { return 1; }
	function GetDate()        { return "2026-11-05"; }
	function CreateInstance() { return "IndustryTest"; }
	function GetAPIVersion()  { return "15"; }
}

RegisterGS(IndustryTestInfo());
