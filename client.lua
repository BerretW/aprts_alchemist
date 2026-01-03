-- Lokální proměnné, které přepíší Config
local LoadedIngredients = {}
local LoadedRecipes = {}
local isDataLoaded = false

-- Vyžádání dat při startu
CreateThread(function()
    TriggerServerEvent('aprts_alchemist:requestData')
end)

-- Příjem dat ze serveru
RegisterNetEvent('aprts_alchemist:updateConfig')
AddEventHandler('aprts_alchemist:updateConfig', function(servIngredients, servRecipes)
    LoadedIngredients = servIngredients
    LoadedRecipes = servRecipes
    isDataLoaded = true
    print("Alchymistická data synchronizována z DB.")
end)

RegisterCommand('startchem', function()
    if not isDataLoaded then
        print("Chyba: Data z databáze se ještě nenačetla. Zkus to za chvíli.")
        TriggerServerEvent('aprts_alchemist:requestData') -- Zkusíme znovu
        return
    end

    local playerSkill = Config.GetPlayerSkill()
    
    -- Získání inventáře z VORP
    local inventory = exports.vorp_inventory:getInventoryItems()
    
    if not inventory then 
        inventory = {} 
    end

    -- Filtrace a příprava dat pro UI
    local validIngredients = {}

    for _, item in pairs(inventory) do
        -- TADY JE ZMĚNA: Hledáme v LoadedIngredients (z DB) místo Config.Ingredients
        local dbData = LoadedIngredients[item.name]

        if dbData then
            table.insert(validIngredients, {
                id = item.name,
                label = item.label, -- Použijeme label z inventáře (je přesnější než DB)
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

    -- Příprava receptů
    local recipesForUI = {}
    -- TADY JE ZMĚNA: Iterujeme LoadedRecipes (z DB)
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
        imgDir = "nui://vorp_inventory/html/img/items/" 
    })
end)

RegisterNUICallback('finish', function(data, cb)
    SetNuiFocus(false, false)
    -- data obsahuje: { beakerIngredients, totalConsumed }
    TriggerServerEvent('aprts_alchemist:finishCraft', data)
    cb('ok')
end)

RegisterNUICallback('close', function(data, cb)
    SetNuiFocus(false, false)
    cb('ok')
end)
