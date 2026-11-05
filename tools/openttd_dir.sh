# Sourced by the tool scripts after they cd to the ModernGFX root: sets OPENTTD to the OpenTTD
# (Modern) checkout whose game build (build/) and source tables (src/table) the tools use.
# Default: the parent folder if ModernGFX sits inside the checkout, else ../openttd-modern.
if [ -z "$OPENTTD" ]; then
	if [ -f ../src/openttd.cpp ]; then OPENTTD="$(cd .. && pwd)"; else OPENTTD="$(cd .. && pwd)/openttd-modern"; fi
fi
