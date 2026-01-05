local LoadedIngredients = {}
local LoadedRecipes = {}
local isDataLoaded = false
local Prompt = nil
local promptGroup = GetRandomIntInRange(0, 0xffffff)
Target = nil
local effect = nil
local menuOpen = false
CreateThread(function()
    TriggerServerEvent('aprts_alchemist:requestData')
end)
local function waitForCharacter()
    while not LocalPlayer do
        Citizen.Wait(100)
    end
    while not LocalPlayer.state do
        Citizen.Wait(100)
    end
    while not LocalPlayer.state.Character do
        Citizen.Wait(100)
    end
end

local function prompt()
    Citizen.CreateThread(function()
        local str = "Otevřít Laboratoř"
        local wait = 0
        Prompt = Citizen.InvokeNative(0x04F97DE45A519419)
        PromptSetControlAction(Prompt, 0x760A9C6F)
        str = CreateVarString(10, 'LITERAL_STRING', str)
        PromptSetText(Prompt, str)
        PromptSetEnabled(Prompt, true)
        PromptSetVisible(Prompt, true)
        PromptSetHoldMode(Prompt, true)
        PromptSetGroup(Prompt, promptGroup)
        PromptRegisterEnd(Prompt)
    end)
end

RegisterNetEvent('aprts_alchemist:updateConfig')
AddEventHandler('aprts_alchemist:updateConfig', function(servIngredients, servRecipes)
    LoadedIngredients = servIngredients
    LoadedRecipes = servRecipes
    isDataLoaded = true
end)

RegisterNetEvent("westhaven_cores:hitObject")
AddEventHandler("westhaven_cores:hitObject", function(entity, hash, endCoords)

    if entity then
        if hash == GetHashKey(Config.CraftingProp) then
            Target = entity
        else
            Target = nil
        end

    end
end)

local function OpenChemMenu()
    if not isDataLoaded then
        print("Data se načítají, zkus to za chvíli...")
        TriggerServerEvent('aprts_alchemist:requestData')
        return
    end

    local playerSkill = Config.GetPlayerSkill()
    local inventory = exports.vorp_inventory:getInventoryItems()

    if not inventory then
        inventory = {}
    end

    local validIngredients = {}

    for _, item in pairs(inventory) do
        -- VORP vrací 'name' jako ID itemu
        local dbData = LoadedIngredients[item.name]

        if dbData then
            table.insert(validIngredients, {
                id = item.name,
                label = item.label,
                count = item.count,

                type = dbData.type,
                r = dbData.r,
                g = dbData.g,
                b = dbData.b,
                ph = dbData.ph,
                amount = dbData.amount
            })
        end
    end

    local recipesForUI = {}
    for k, v in pairs(LoadedRecipes) do
        table.insert(recipesForUI, {
            id = v.id,
            label = v.label,
            minSkill = v.minSkillToIdentify,
            conditions = v.conditions,
            requirements = v.requirements,
            process = v.process
        })
    end
    menuOpen = true
    SetNuiFocus(true, true)
    SendNUIMessage({
        type = "OPEN_GAME",
        inputs = validIngredients,
        recipes = recipesForUI,
        playerSkill = playerSkill,
        -- Uprav cestu k obrázkům, pokud máš jinou strukturu
        imgDir = "nui://vorp_inventory/html/img/items/"
    })
end

RegisterCommand('startchem', function()
    OpenChemMenu()
end)

RegisterNUICallback('finish', function(data, cb)
    SetNuiFocus(false, false)
    TriggerServerEvent('aprts_alchemist:finishCraft', data)
    cb('ok')
end)

RegisterNUICallback('close', function(data, cb)
    SetNuiFocus(false, false)
    menuOpen = false
    cb('ok')
end)

Citizen.CreateThread(function()
    waitForCharacter()
    while true do
        local pause = 1000
        local playerPed = PlayerPedId()
        local playerCoords = GetEntityCoords(playerPed)
        if menuOpen and not effect and Target then
            local targetCoords = GetEntityCoords(Target)
            UseParticleFxAsset("core")
            effect = StartParticleFxLoopedAtCoord("ent_amb_smoke_chimney_long", targetCoords.x, targetCoords.y,
                targetCoords.z, 0.0, 0.0, 0.0, 1.0, false, false, false, false)
        elseif not menuOpen and effect then
            StopParticleFxLooped(effect, 0)
            effect = nil
        end
        Citizen.Wait(pause)
    end
end)
Citizen.CreateThread(function()
    waitForCharacter()
    prompt()
    while true do
        local pause = 1000
        local playerPed = PlayerPedId()
        local playerCoords = GetEntityCoords(playerPed)
        if Target and DoesEntityExist(Target) then

            local targetCoords = GetEntityCoords(Target)
            local dist = #(playerCoords - targetCoords)
            if dist < 3.0 then
                pause = 5
                local name = CreateVarString(10, 'LITERAL_STRING', "Otevřít")
                PromptSetActiveGroupThisFrame(promptGroup, name)
                if PromptHasHoldModeCompleted(Prompt) then
                    OpenChemMenu()
                    Wait(1000)
                end
            end
        end
        Citizen.Wait(pause)
    end
end)

