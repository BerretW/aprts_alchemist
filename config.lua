Config = {}
Config.GetPlayerSkill = function()
    return exports['westhaven_skill']:getSkillLevel('chemic')
end

Config.Ingredients = {
    ['tool_water_bottle'] = { label = "Voda", r=200, g=200, b=255, ph=7.0, amount=20 },
    ['medic_levandule_tinctur'] = { label = "Levandulová Tinktuira", r=255, g=200, b=0, ph=8.0, amount=10 },
    ['drink_poison_watter_bottle'] = { label = "Láhev s otávenou vodou", r=220, g=210, b=150, ph=7.5, amount=10 },
    ['product_hash_oil'] = { label = "Hašišový olej", r=50, g=30, b=20, ph=6.5, amount=5 },
    ['product_hash_blob'] = { label = "Hašišová hmota", r=30, g=20, b=10, ph=6.0, amount=15 },
    ['product_acid_base'] = { label = "Základní Kyselina", r=255, g=0, b=0, ph=2.0, amount=5 },
    ['product_broth_peyote'] = { label = "Peyote Vývar", r=0, g=255, b=0, ph=5.5, amount=10 },
    ['product_chlorine'] = { label = "Chlór", r=0, g=0, b=255, ph=11.0, amount=5 },
    ['product_agave_juice'] = { label = "Šťáva z Agáve", r=255, g=255, b=0, ph=6.8, amount=15 },
    ['product_aroma_oil'] = { label = "Aromatický Olej", r=255, g=0, b=255, ph=7.2, amount=10 },
    ['product_kerosene'] = { label = "Kerosin", r=100, g=100, b=100, ph=7.0, amount=10 },
    ['product_oil'] = { label = "Rostlinný Olej", r=150, g=75, b=0, ph=7.5, amount=15 },
}

Config.Recipes = {
    ['drink_poison_watter_bottle'] = {
        id = 'drink_poison_watter_bottle', -- ID je potřeba pro JS
        label = "Otrávená voda",
        
        -- Hráč musí mít skill alespoň 10, aby viděl název. Jinak vidí "Neznámá směs".
        minSkillToIdentify = 10,

        conditions = {
            phMin = 7.2, phMax = 7.8,
            colorTarget = {r=220, g=210, b=150},
            colorTolerance = 40,
            minTotalAmount = 60,
        },
        requirements = {
            { item = 'medic_levandule_tinctur', minAmount = 20 },
            { item = 'tool_water_bottle', minAmount = 20 }
        },
        AmountPer100mill = 1,  -- Kolik itemů se spotřebuje při výrobě (pro ukázku)
        rewardItem = 'drink_poison_watter_bottle',
        -- rewardItem a rewardCount v NUI nepotřebujeme posílat (bezpečnost)
    },
    
    ['item_junk'] = {
        id = 'item_junk',
        label = "Alchymistický odpad",
        minSkillToIdentify = 0, -- Pozná každý
        conditions = {
            -- Příklad pro odpad - velmi široký rozsah nebo specifická chyba
             phMin = 0, phMax = 14,
             minTotalAmount = 100, 
             -- odpad nemá specifickou barvu, nebo requirements
        }
    }
}