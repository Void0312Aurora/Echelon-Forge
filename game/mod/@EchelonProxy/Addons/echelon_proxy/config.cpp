class CfgPatches
{
    class echelon_proxy
    {
        name = "Echelon Proxy";
        author = "OpenAI Codex";
        requiredVersion = 2.12;
        requiredAddons[] = {"A3_Functions_F"};
        units[] = {};
        weapons[] = {};
    };
};

class CfgFunctions
{
    class EPX
    {
        tag = "EPX";

        class Core
        {
            file = "echelon_proxy\\functions";
            class postInit
            {
                postInit = 1;
            };
            class tick {};
            class startSession {};
            class stopSession {};
            class buildHostState {};
            class applyProxyState {};
            class spawnProxyAircraft {};
            class extensionCall {};
        };
    };
};
