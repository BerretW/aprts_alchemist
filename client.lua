local LoadedIngredients = {}
local LoadedRecipes = {}
local isDataLoaded = false

CreateThread(function()
    TriggerServerEvent('aprts_alchemist:requestData')
end)

RegisterNetEvent('aprts_alchemist:updateConfig')
AddEventHandler('aprts_alchemist:updateConfig', function(servIngredients, servRecipes)
    LoadedIngredients = servIngredients
    LoadedRecipes = servRecipes
    isDataLoaded = true
end)

RegisterCommand('startchem', function()
    if not isDataLoaded then
        print("Data se načítají, zkus to za chvíli...")
        TriggerServerEvent('aprts_alchemist:requestData')
        return
    end

    local playerSkill = Config.GetPlayerSkill()
    local inventory = exports.vorp_inventory:getInventoryItems()
    
    if not inventory then inventory = {} end

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

    SetNuiFocus(true, true)
    SendNUIMessage({
        type = "OPEN_GAME",
        inputs = validIngredients,
        recipes = recipesForUI,
        playerSkill = playerSkill,
        -- Uprav cestu k obrázkům, pokud máš jinou strukturu
        imgDir = "nui://vorp_inventory/html/img/items/" 
    })
end)

RegisterNUICallback('finish', function(data, cb)
    SetNuiFocus(false, false)
    TriggerServerEvent('aprts_alchemist:finishCraft', data)
    cb('ok')
end)

RegisterNUICallback('close', function(data, cb)
    SetNuiFocus(false, false)
    cb('ok')
end)