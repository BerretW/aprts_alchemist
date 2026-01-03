RegisterCommand('startchem', function()
    local playerSkill = Config.GetPlayerSkill()
    print("Otevírám alchymistickou minihru. Skill level: " .. playerSkill)
    
    -- 1. Získání inventáře (VORP)
    -- Ujisti se, že export funguje, jinak použij TriggerServerEvent callback
    local inventory = exports.vorp_inventory:getInventoryItems()
    
    if not inventory then 
        print("Chyba: Nepodařilo se načíst inventář nebo je prázdný.") 
        -- Pro testování bez itemů můžeš odkomentovat return, 
        -- ale v produkci musíš mít itemy.
        -- return 
        inventory = {} -- Fallback aby script nespadl
    end

    -- 2. Filtrace a příprava dat pro UI
    local validIngredients = {}

    for _, item in pairs(inventory) do
        local configData = Config.Ingredients[item.name]
        if configData then
            table.insert(validIngredients, {
                id = item.name,
                label = item.label,
                count = item.count,
                
                -- Vlastnosti
                type = configData.type,
                r = configData.r, g = configData.g, b = configData.b,
                ph = configData.ph,
                amount = configData.amount
            })
        end
    end

    -- 3. Příprava receptů
    local recipesForUI = {}
    for k, v in pairs(Config.Recipes) do
        table.insert(recipesForUI, {
            id = k, -- ID receptu
            label = v.label,
            minSkill = v.minSkillToIdentify,
            conditions = v.conditions,
            requirements = v.requirements,
            process = v.process
        })
    end

    -- 4. Otevření UI
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