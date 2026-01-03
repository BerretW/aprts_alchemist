local VORP_INV = exports.vorp_inventory:vorp_inventoryApi()

RegisterNetEvent('aprts_alchemist:finishCraft')
AddEventHandler('aprts_alchemist:finishCraft', function(data)
    local _source = source
    local beakerIngredients = data.beakerIngredients
    local totalConsumed = data.totalConsumed
    
    -- Data o procesu z klienta
    local finalTemp = data.finalTemp or 0
    local finalTime = data.finalTime or 0

    -- 1. Odebrání surovin (stejné jako předtím)
    local allItemsRemoved = true
    for itemInfo, amountUsed in pairs(totalConsumed) do
        if amountUsed > 0 then
            local check = VORP_INV.subItem(_source, itemInfo, amountUsed)
            if not check then allItemsRemoved = false end
        end
    end

    if not allItemsRemoved then
        TriggerClientEvent('vorp:TipRight', _source, 'Chyba: Nedostatek surovin!', 4000)
        return
    end

    -- 2. Výpočet směsi (stejné jako předtím - barva, pH, množství)
    local currentMix = { r = 0, g = 0, b = 0, ph = 0, amount = 0 }
    local totalAmount = 0
    
    for itemName, count in pairs(beakerIngredients) do
        local configItem = Config.Ingredients[itemName]
        if configItem and count > 0 then
            local itemTotalAmount = configItem.amount * count
            if totalAmount == 0 then
                currentMix.r = configItem.r; currentMix.g = configItem.g; currentMix.b = configItem.b; currentMix.ph = configItem.ph
                totalAmount = itemTotalAmount
            else
                local newTotal = totalAmount + itemTotalAmount
                currentMix.r = ((currentMix.r * totalAmount) + (configItem.r * itemTotalAmount)) / newTotal
                currentMix.g = ((currentMix.g * totalAmount) + (configItem.g * itemTotalAmount)) / newTotal
                currentMix.b = ((currentMix.b * totalAmount) + (configItem.b * itemTotalAmount)) / newTotal
                currentMix.ph = ((currentMix.ph * totalAmount) + (configItem.ph * itemTotalAmount)) / newTotal
                totalAmount = newTotal
            end
        end
    end
    currentMix.amount = totalAmount

    -- 3. Hledání receptu (NOVĚ S KONTROLOU TEPLOTY A ČASU)
    local resultItem = 'item_junk' 
    local resultLabel = 'Alchymistický odpad'
    local resultCount = 1

    if totalAmount > 0 then
        for recipeId, recipe in pairs(Config.Recipes) do
            local match = true
            local cond = recipe.conditions
            local proc = recipe.process -- Načtení požadavků na proces

            -- A) Fyzikální vlastnosti
            if currentMix.ph < cond.phMin or currentMix.ph > cond.phMax then match = false end
            if currentMix.amount < cond.minTotalAmount then match = false end
            
            if cond.colorTarget then
                local rDiff = math.abs(currentMix.r - cond.colorTarget.r)
                local gDiff = math.abs(currentMix.g - cond.colorTarget.g)
                local bDiff = math.abs(currentMix.b - cond.colorTarget.b)
                if rDiff > (cond.colorTolerance or 30) or gDiff > (cond.colorTolerance or 30) or bDiff > (cond.colorTolerance or 30) then match = false end
            end

            -- B) Ingredience
            if match and recipe.requirements then
                for _, req in ipairs(recipe.requirements) do
                    local usedCount = beakerIngredients[req.item] or 0
                    local itemCfg = Config.Ingredients[req.item]
                    local totalMl = usedCount * (itemCfg and itemCfg.amount or 0)
                    if totalMl < req.minAmount then match = false; break end
                end
            end

            -- C) NOVÉ: Proces (Teplota a Čas)
            if match and proc then
                -- Kontrola teploty
                if math.abs(finalTemp - proc.temp) > proc.tempTolerance then
                    match = false
                end
                -- Kontrola času
                if math.abs(finalTime - proc.time) > proc.timeTolerance then
                    match = false
                end
            end

            if match then
                resultItem = recipe.rewardItem or recipeId
                resultLabel = recipe.label
                
                -- Logika množství (kotel)
                local unitSize = cond.minTotalAmount
                if unitSize and unitSize > 0 then
                    local multiplier = math.floor(currentMix.amount / unitSize)
                    if multiplier < 1 then multiplier = 1 end
                    resultCount = (recipe.rewardCount or 1) * multiplier
                else
                    resultCount = recipe.rewardCount or 1
                end
                break
            end
        end
    end

    -- 4. Odměna
    if resultItem == 'item_junk' then
        TriggerClientEvent('vorp:TipRight', _source, 'Pokus se nezdařil. Vznikl jen kal.', 4000)
        exports.vorp_inventory:addItem(_source, 'item_junk', 1)
        exports.westhaven_skill:increaseSkill(_source, 'chemic', 1) 
    else
        exports.vorp_inventory:addItem(_source, resultItem, resultCount)
        exports.westhaven_skill:increaseSkill(_source, 'chemic', 15) -- Větší skill za složitější proces
        TriggerClientEvent('vorp:TipRight', _source, 'Vyrobeno: ' .. resultCount .. 'x ' .. resultLabel, 4000)
    end
end)