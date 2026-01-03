RegisterCommand('startchem', function()
    local playerSkill = Config.GetPlayerSkill()
    print("Otevírám alchymistickou minihru. Skill level: " .. playerSkill)
    -- 1. Získání inventáře z VORP
    -- POZOR: Ujisti se, že máš nejnovější vorp_inventory, kde tento export funguje na klientovi.
    -- Pokud ne, musíš si vyžádat data ze serveru přes callback.
    local inventory = exports.vorp_inventory:getInventoryItems()
    
    if not inventory then 
        print("Chyba: Nepodařilo se načíst inventář.") 
        return 
    end

    -- 2. Filtrace a příprava dat pro UI
    local validIngredients = {}

    for _, item in pairs(inventory) do
        -- 'item.name' je technický název (např. 'product_hemp')
        local configData = Config.Ingredients[item.name]

        if configData then
            -- Pokud je item definován v configu jako chemikálie, přidáme ho
            table.insert(validIngredients, {
                id = item.name,           -- ID pro logiku
                label = item.label,       -- Název z inventáře (např. "Konopí")
                count = item.count,       -- Počet kusů v inventáři
                
                -- Chemické vlastnosti z configu
                type = configData.type,
                r = configData.r, 
                g = configData.g, 
                b = configData.b,
                ph = configData.ph,
                amount = configData.amount
            })
        end
    end

    -- 3. Příprava receptů (skryjeme citlivá data)
    local recipesForUI = {}
    for k, v in pairs(Config.Recipes) do
        table.insert(recipesForUI, {
            id = k,
            label = v.label,
            minSkill = v.minSkillToIdentify,
            conditions = v.conditions,
            requirements = v.requirements
        })
    end

    -- 4. Otevření UI
    SetNuiFocus(true, true)
    SendNUIMessage({
        type = "OPEN_GAME",
        inputs = validIngredients, -- Posíláme jen to, co má hráč u sebe!
        recipes = recipesForUI,
        playerSkill = playerSkill
    })
end)

-- Callbacky zůstávají stejné
RegisterNUICallback('finish', function(data, cb)
    SetNuiFocus(false, false)
    TriggerServerEvent('aprts_alchemist:checkMix', data)
    cb('ok')
end)

RegisterNUICallback('close', function(data, cb)
    SetNuiFocus(false, false)
    cb('ok')
end)