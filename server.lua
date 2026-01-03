RegisterNetEvent('aprts_alchemist:finishCraft')
AddEventHandler('aprts_alchemist:finishCraft', function(recipeId, usedIngredients)
    local _source = source
    local recipe = Config.Recipes[recipeId]
    
    if not recipe then return end

    -- 1. KROK: Ověření, zda hráč má suroviny, které v minihře "použil"
    -- usedIngredients vypadá takto: { ['water'] = 40, ['alcohol'] = 10 }
    
    local canCraft = true
    
    -- Příklad pro VORP (pseudokód):
    -- for item, amountUsed in pairs(usedIngredients) do
    --    if amountUsed > 0 then
    --       local count = VORPInv.getItemCount(_source, item)
    --       -- Pozor: v minihře mícháme po ml (např 50ml), ale itemy jsou po kusech.
    --       -- Musíš si určit převod, např. 1 item 'voda' = 100ml. 
    --       -- Pokud je 1 klik = 1 item, pak je to jednoduché:
    --       local clicksNeeded = amountUsed / Config.Ingredients[item].amount
    --       if count < clicksNeeded then canCraft = false end
    --    end
    -- end

    if canCraft then
        -- 2. KROK: Odebrat suroviny
        -- for item, amountUsed in pairs(usedIngredients) do
             -- RemoveItem(_source, item, calculatedCount)
        -- end

        -- 3. KROK: Dát odměnu
        -- VORPInv.addItem(_source, recipe.rewardItem, recipe.rewardCount)
        
        TriggerClientEvent('vorp:TipRight', _source, 'Vyrobil jsi: ' .. recipe.label, 4000)
    else
        TriggerClientEvent('vorp:TipRight', _source, 'Nemáš dostatek surovin!', 4000)
    end
end)