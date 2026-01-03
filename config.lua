Config = {}
Config.GetPlayerSkill = function()
    return exports['westhaven_skill']:getSkillLevel('chemic')
end
Config = {}

-- Funkce pro získání skillu (uprav dle svého skill systému)
Config.GetPlayerSkill = function()
    return exports['westhaven_skill']:getSkillLevel('chemic') or 0
end

-- Suroviny
-- type: určuje ikonu v případě fallbacku, ale hlavně logickou skupinu
-- amount: kolik ml se přilije na jedno kliknutí
Config.Ingredients = {
    -- ROZPOUŠTĚDLA (Velký objem)
    ['tool_water_bottle'] = { label = "Destilovaná Voda", r=200, g=220, b=255, ph=7.0, amount=50, type='bottle' },
    ['product_agave_juice'] = { label = "Šťáva z Agáve", r=255, g=255, b=100, ph=6.5, amount=25, type='bottle' },
    ['product_oil'] = { label = "Rostlinný Olej", r=200, g=150, b=50, ph=7.2, amount=30, type='bottle' },
    ['product_kerosene'] = { label = "Kerosin", r=180, g=180, b=180, ph=6.8, amount=40, type='bottle' },

    -- KYSELINY A ZÁSADY (Střední objem, výrazné pH)
    ['product_acid_base'] = { label = "Základní Kyselina", r=200, g=20, b=20, ph=3.0, amount=15, type='flask' },
    ['product_chlorine'] = { label = "Chlór", r=50, g=255, b=50, ph=10.5, amount=15, type='flask' },
    ['ampoule_of_vitriol'] = { label = "Ampule Vitriolu", r=0, g=255, b=255, ph=1.0, amount=10, type='vial' }, -- Silná kyselina
    ['ammonia_ampoule'] = { label = "Ampule Amoniaku", r=255, g=255, b=0, ph=12.0, amount=10, type='vial' }, -- Silná zásada

    -- EXTRAKTY A DROGY (Malý objem, silná barva)
    ['medic_levandule_tinctur'] = { label = "Levandulová Tinktura", r=150, g=100, b=255, ph=7.5, amount=10, type='vial' },
    ['product_aroma_oil'] = { label = "Aromatický Olej", r=255, g=100, b=200, ph=7.0, amount=10, type='vial' },
    ['morphine_ampoules'] = { label = "Ampule Morfinu", r=240, g=240, b=255, ph=6.5, amount=5, type='vial' },
    ['opium_ampoules'] = { label = "Ampule Opia", r=80, g=40, b=10, ph=6.0, amount=5, type='vial' },
    ['product_broth_peyote'] = { label = "Peyote Vývar", r=50, g=100, b=50, ph=5.5, amount=20, type='jar' },
    
    -- HMOTY (Husté)
    ['product_hash_oil'] = { label = "Hašišový olej", r=60, g=40, b=0, ph=6.5, amount=10, type='jar' },
    ['product_hash_blob'] = { label = "Hašišová hmota", r=40, g=30, b=10, ph=6.0, amount=15, type='jar' },
    
    -- JEDY
    ['drink_poison_watter_bottle'] = { label = "Láhev s otrávenou vodou", r=100, g=100, b=50, ph=4.0, amount=50, type='bottle' },
    ['item_junk'] = { label = "Alchymistický odpad", r=70, g=70, b=70, ph=7.0, amount=10, type='jar' },

    -- PRŮMYSLOVÉ MATERIÁLY
    ['chemic_oil'] = { label = "Olej z rafinérie", r=35, g=30, b=25, ph=6.8, amount=40, type='bottle' }, -- Tmavá, hustá kapalina, neutrální
    ['material_mucilage_synthetic'] = { label = "Klíh chemický", r=240, g=235, b=210, ph=9.5, amount=20, type='jar' }, -- Bělavá/Krémová pasta, mírně zásaditá
    ['chemic_mercury'] = { label = "Ampulka rtuti", r=170, g=170, b=180, ph=6.0, amount=5, type='vial' }, -- Stříbrno-šedá, těžký kov (malé množství)
}

Config.Recipes = {
    -- 1. OTRÁVENÁ VODA (Jednoduchý recept na start)
    -- Kombinace vody a levandule (nebo vitriolu pro hardcore verzi).
    ['drink_poison_watter_bottle'] = {
        id = 'drink_poison_watter_bottle',
        label = "Otrávená voda",
        minSkillToIdentify = 0, -- Pozná každý
        
        process = {
            temp = 80,          -- Lehce zahřát
            time = 10,          -- 10 sekund
            tempTolerance = 20, -- Velká tolerance
            timeTolerance = 5   
        },

        conditions = {
            phMin = 6.0, phMax = 8.0,
            minTotalAmount = 100,
            -- Barva by měla být kalně fialová (Voda 200/220/255 + Levandule 150/100/255)
            colorTarget = {r=180, g=170, b=255}, 
            colorTolerance = 60,
        },
        requirements = {
            { item = 'tool_water_bottle', minAmount = 50 },
            { item = 'medic_levandule_tinctur', minAmount = 20 }
        },
        rewardItem = 'drink_poison_watter_bottle',
        rewardCount = 1
    },

    -- 2. LAUDANUM (Lék/Droga)
    -- Opium rozpuštěné v alkoholu (zde Agáve) a vodě.
    ['consumable_laudanum'] = {
        id = 'consumable_laudanum',
        label = "Laudanum",
        minSkillToIdentify = 15,

        process = {
            temp = 60,          -- Pomalé rozpouštění, nesmí se vařit zprudka
            time = 20,          -- Delší čas
            tempTolerance = 10, -- Přísnější na teplotu
            timeTolerance = 5
        },

        conditions = {
            phMin = 6.0, phMax = 7.0, -- Mírně kyselé díky opiu a agáve
            minTotalAmount = 50,
            -- Opium (Hnědá) + Agáve (Žlutá) -> Zlatohnědá
            colorTarget = {r=160, g=140, b=50},
            colorTolerance = 40,
        },
        requirements = {
            { item = 'opium_ampoules', minAmount = 10 },
            { item = 'product_agave_juice', minAmount = 25 }
        },
        rewardItem = 'consumable_laudanum', -- Ujisti se, že tento item existuje v DB
        rewardCount = 1
    },

    -- 3. HEROIN (Těžká droga)
    -- Morfium vařené s kyselinou (náhrada za acetanhydrid). Nebezpečné!
    ['drug_heroin'] = {
        id = 'drug_heroin',
        label = "Syntetický Heroin",
        minSkillToIdentify = 30,

        process = {
            temp = 95,          -- Téměř var
            time = 30,          -- Dlouhé vaření
            tempTolerance = 5,  -- Velmi malá tolerance (Hardcore)
            timeTolerance = 3
        },

        conditions = {
            phMin = 2.0, phMax = 4.5, -- Musí to být kyselé
            minTotalAmount = 30,
            -- Morfin (Bílá/Modrá) + Kyselina (Červená) -> Fialová/Růžová
            colorTarget = {r=220, g=130, b=130},
            colorTolerance = 30,
        },
        requirements = {
            { item = 'morphine_ampoules', minAmount = 15 },
            { item = 'product_acid_base', minAmount = 15 }
        },
        rewardItem = 'drug_heroin',
        rewardCount = 1
    },

    -- 4. VÝBUŠNÉ PALIVO (Crafting material)
    -- Kerosin "vyčištěný" amoniakem.
    ['refined_fuel'] = {
        id = 'refined_fuel',
        label = "Vysoce hořlavé palivo",
        minSkillToIdentify = 1,

        process = {
            temp = 120,         -- Vysoká teplota (destilace)
            time = 15,
            tempTolerance = 15,
            timeTolerance = 5
        },

        conditions = {
            phMin = 7.5, phMax = 9.0, -- Mírně zásadité po amoniaku
            minTotalAmount = 80,
            -- Kerosin (Šedá) + Amoniak (Žlutá) -> Světle žlutá/šedá
            colorTarget = {r=200, g=200, b=150},
            colorTolerance = 50,
        },
        requirements = {
            { item = 'product_kerosene', minAmount = 40 },
            { item = 'ammonia_ampoule', minAmount = 10 }
        },
        rewardItem = 'ammo_explosive_fuel',
        rewardCount = 2 -- Dává víc kusů
    },

    -- 5. CHLOROVÝ PLYN (Tekutá forma - Jed)
    -- Chlór + Vitriol. Extrémně nebezpečné (v RP).
    ['poison_chlorine_gas'] = {
        id = 'poison_chlorine_gas',
        label = "Koncentrovaný Chlór",
        minSkillToIdentify = 40,

        process = {
            temp = 40,          -- Nízká teplota (těkavé!)
            time = 10,
            tempTolerance = 5,  -- Nesmí se přehřát!
            timeTolerance = 2
        },

        conditions = {
            phMin = 1.0, phMax = 5.0, -- Vitriol to srazí dolů
            minTotalAmount = 40,
            -- Chlór (Zelená) + Vitriol (Azurová) -> Jedovatá tyrkysová
            colorTarget = {r=25, g=255, b=150},
            colorTolerance = 25,
        },
        requirements = {
            { item = 'product_chlorine', minAmount = 15 },
            { item = 'ampoule_of_vitriol', minAmount = 10 }
        },
        rewardItem = 'poison_bottle_chlorine',
        rewardCount = 1
    },
-- 6. ZBROJNÍ VAZELÍNA (Údržba zbraní)
    -- Olej z rafinérie + Chemický klíh.
    -- Vytvoří hustou, mastnou hmotu pro čištění zbraní.
    ['item_weapon_grease'] = {
        id = 'item_weapon_grease',
        label = "Zbrojní vazelína",
        minSkillToIdentify = 5,

        process = {
            temp = 50,          -- Jen mírný ohřev, aby se to spojilo
            time = 15,          -- Míchat chvíli
            tempTolerance = 20, -- Není to náročné
            timeTolerance = 5
        },

        conditions = {
            phMin = 7.0, phMax = 9.0, -- Mírně zásadité díky klihu
            minTotalAmount = 60,
            -- Olej (Hnědo-černá) + Klíh (Krémová) -> Tmavě béžová/šedá
            colorTarget = {r=100, g=90, b=80},
            colorTolerance = 40,
        },
        requirements = {
            { item = 'chemic_oil', minAmount = 40 },
            { item = 'material_mucilage_synthetic', minAmount = 20 }
        },
        rewardItem = 'item_weapon_grease', -- Ujisti se, že item existuje v DB
        rewardCount = 1
    },

    -- 7. TŘASKAVÁ RTUŤ (Výbušnina/Rozbuška)
    -- Rtuť + Kyselina (reakce) + Etanol (zde Agáve jako katalyzátor).
    -- Velmi citlivé na teplotu!
    ['explosive_fulminate'] = {
        id = 'explosive_fulminate',
        label = "Třaskavá rtuť",
        minSkillToIdentify = 45, -- Pokročilá chemie

        process = {
            temp = 70,          -- Přesná teplota reakce
            time = 12,          -- Krátká, bouřlivá reakce
            tempTolerance = 5,  -- HARDCORE: Pokud to přeženeš, "vybouchne" to (vznikne odpad)
            timeTolerance = 2
        },

        conditions = {
            phMin = 2.0, phMax = 5.0, -- Kyselé prostředí
            minTotalAmount = 25,      -- Stačí málo (je to koncentrát)
            -- Rtuť (Šedá) + Kyselina (Červená) -> Tmavě rudá/šedá
            colorTarget = {r=140, g=80, b=80},
            colorTolerance = 35,
        },
        requirements = {
            { item = 'chemic_mercury', minAmount = 5 },       -- Drahá surovina
            { item = 'product_acid_base', minAmount = 15 },   -- Reagent
            { item = 'product_agave_juice', minAmount = 5 }   -- Alkoholová báze
        },
        rewardItem = 'ammo_dynamite_component', -- Např. komponenta pro dynamit
        rewardCount = 1
    },
    -- ODPAD (Fallback)
    ['item_junk'] = {
        id = 'item_junk',
        label = "Alchymistický odpad",
        minSkillToIdentify = 0,
        -- Odpad vznikne vždy, když se netrefíš do jiného receptu
        process = { temp = 0, time = 0, tempTolerance = 999, timeTolerance = 999 }, 
        conditions = { phMin = 0, phMax = 14, minTotalAmount = 10 }
    }
}