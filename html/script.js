let currentMix = { r: 0, g: 0, b: 0, ph: 7.0, amount: 0 };
let ingredientsUsed = {}; // Co posíláme serveru
let inventoryItems = [];  // Lokální stav inventáře v UI
let availableRecipes = [];
let playerSkill = 0;

const MAX_BEAKER_VOLUME = 250;

window.addEventListener('message', function(event) {
    if (event.data.type === "OPEN_GAME") {
        inventoryItems = event.data.inputs || [];
        availableRecipes = event.data.recipes || [];
        playerSkill = event.data.playerSkill || 0;

        document.getElementById('player-skill').innerText = playerSkill;

        setupGame();
        document.getElementById('game-container').style.display = 'flex';
    }
});

document.addEventListener('keydown', function(event) {
    if (event.key === "Escape") closeGame();
});

function setupGame() {
    currentMix = { r: 255, g: 255, b: 255, ph: 7.0, amount: 0 };
    ingredientsUsed = {};
    
    // Reset počítadla použití
    inventoryItems.forEach(item => {
        ingredientsUsed[item.id] = 0;
        // Přidáme pomocnou vlastnost pro aktuální zobrazený počet (aby se neresetoval inventář při resetu kádinky, jen při zavření)
        if (item.currentCount === undefined) {
             item.currentCount = item.count;
        }
    });

    renderInventory();
    updateVisuals();
    identifyMixture();
}

function renderInventory() {
    const container = document.getElementById('inventory-list');
    container.innerHTML = '';
    
    inventoryItems.forEach((item, index) => {
        const div = document.createElement('div');
        // Pokud dojdou kusy, znepřístupníme tlačítko
        const isDisabled = item.currentCount <= 0 ? 'disabled' : '';
        
        div.className = `inv-item ${isDisabled}`;
        
        // Určení CSS třídy pro tvar (fallback na jar)
        const shapeClass = item.type ? `shape-${item.type}` : 'shape-jar';
        
        div.innerHTML = `
            <div class="icon-container ${shapeClass}">
                <div class="icon-liquid" style="background: rgb(${item.r},${item.g},${item.b});"></div>
            </div>
            <div class="item-info">
                <div class="item-name">${item.label}</div>
                <div class="item-details">
                    Množství: <span id="count-${index}">${item.currentCount}</span> ks<br>
                    <small>+${item.amount}ml | pH ${item.ph}</small>
                </div>
            </div>
        `;
        
        if (!isDisabled) {
            div.onclick = () => addToMix(index);
        }
        
        container.appendChild(div);
    });
}

function addToMix(index) {
    const item = inventoryItems[index];
    
    // Kontrola, zda máme item
    if (item.currentCount <= 0) return;

    // 1. Odečtení z lokálního inventáře
    item.currentCount--;
    document.getElementById(`count-${index}`).innerText = item.currentCount;
    
    // Pokud došly itemy, překreslíme, aby zešedl
    if (item.currentCount === 0) {
        renderInventory();
    }

    // 2. Záznam pro server
    if (!ingredientsUsed[item.id]) ingredientsUsed[item.id] = 0;
    ingredientsUsed[item.id] += 1; // Serveru posíláme počet POUŽITÝCH KUSŮ, ne ml (aby věděl kolik odebrat itemů)

    // 3. Fyzika míchání
    if (currentMix.amount === 0) {
        currentMix.r = item.r;
        currentMix.g = item.g;
        currentMix.b = item.b;
        currentMix.ph = item.ph;
        currentMix.amount = item.amount;
    } else {
        const totalAmount = currentMix.amount + item.amount;
        
        currentMix.r = ((currentMix.r * currentMix.amount) + (item.r * item.amount)) / totalAmount;
        currentMix.g = ((currentMix.g * currentMix.amount) + (item.g * item.amount)) / totalAmount;
        currentMix.b = ((currentMix.b * currentMix.amount) + (item.b * item.amount)) / totalAmount;
        
        currentMix.ph = ((currentMix.ph * currentMix.amount) + (item.ph * item.amount)) / totalAmount;
        currentMix.amount = totalAmount;
    }
    
    updateVisuals();
    identifyMixture();
}

function resetMix() {
    // POZOR: Tlačítko "Vylít" nevrací itemy do inventáře! (Hardcore verze)
    // Pokud chceš vracet itemy, musel bys tady iterovat ingredientsUsed a přičíst je zpět k item.currentCount.
    
    /* 
    // Verze s vracením itemů (odkomentuj pokud chceš):
    inventoryItems.forEach(item => {
        if (ingredientsUsed[item.id]) {
            item.currentCount += ingredientsUsed[item.id];
        }
    });
    */

    currentMix = { r: 255, g: 255, b: 255, ph: 7.0, amount: 0 };
    // Resetujeme tracking pro aktuální směs, ale itemy jsou už "pryč" (vylité do výlevky)
    // Pokud použiješ verzi s vracením, resetuj ingredientsUsed na 0 tady.
    // V této verzi ingredientsUsed necháme být? Ne, musíme resetovat counter pro NOVOU várku, 
    // ale itemy v 'inventoryItems' už jsou odečtené.
    // Abychom neposlali serveru, že má odečíst 2x tolik, musíme logiku serveru upravit, 
    // nebo zde ingredientsUsed vynulovat a smířit se s tím, že itemy zmizely.
    
    // Správná logika pro "Vylití do kanálu": Itemy jsou pryč.
    // Ale my ingredientsUsed musíme vynulovat, protože začínáme novou směs.
    // A serveru pošleme finální ingredientsUsed až při kliknutí na "Hotovo".
    // ALE: Co když naleju 5 věcí, vyleju to, a pak zavřu okno? Měly by se odečíst?
    // Řešení: Server by měl odečíst itemy na základě toho, co se "spotřebovalo".
    // V této jednoduché verzi: Reset smaže jen vizuál v kádince. 
    // Ale ingredientsUsed se musí vyčistit, aby se nepřičítaly k nové směsi.
    // ALE itemy v levém menu se nevrátí (už jsou "currentCount" nižší).
    
    ingredientsUsed = {}; // Začínáme novou směs, stará je v kanálu.
    
    updateVisuals();
    identifyMixture();
    renderInventory(); // Refresh tlačítek
}

// ... updateVisuals, identifyMixture, checkRecipeMatch, finishGame, closeGame ...
// (Jsou stejné jako minule, jen finishGame posílá ingredientsUsed)

function updateVisuals() {
    document.getElementById('current-amt').innerText = Math.round(currentMix.amount);
    document.getElementById('current-ph').innerText = currentMix.ph.toFixed(1);
    
    const liquid = document.getElementById('liquid');
    liquid.style.backgroundColor = `rgb(${Math.round(currentMix.r)}, ${Math.round(currentMix.g)}, ${Math.round(currentMix.b)})`;
    
    let heightPerc = (currentMix.amount / MAX_BEAKER_VOLUME) * 100;
    if (heightPerc > 100) heightPerc = 100;
    liquid.style.height = heightPerc + '%';
}

function identifyMixture() {
    const predBox = document.getElementById('prediction-result');
    if (currentMix.amount <= 0) {
        predBox.innerText = "Prázdno";
        predBox.className = "prediction-unknown";
        return;
    }

    let foundRecipe = null;
    for (let recipe of availableRecipes) {
        if (checkRecipeMatch(recipe)) {
            foundRecipe = recipe;
            break;
        }
    }

    predBox.className = "";
    if (foundRecipe) {
        if (playerSkill >= foundRecipe.minSkill) {
            predBox.innerText = foundRecipe.label;
            predBox.classList.add("prediction-known");
        } else {
            predBox.innerText = "Stabilní směs (?)";
            predBox.classList.add("prediction-vague");
        }
    } else {
        predBox.innerText = "Neznámý kal";
        predBox.classList.add("prediction-trash");
    }
}

function checkRecipeMatch(recipe) {
    const cond = recipe.conditions;
    if (currentMix.ph < cond.phMin || currentMix.ph > cond.phMax) return false;
    if (currentMix.amount < cond.minTotalAmount) return false;
    
    // U requirements musíme počítat celkové množství v ML (počet itemů * množství za item)
    // Protože ingredientsUsed v JS teď ukládá počty kusů (clicks), musíme to převést,
    // nebo v JS ukládat i ml.
    // Jednodušší: V configu recipe requirements definovat "minAmount" jako ML.
    // V JS musíme zjistit kolik ml má jeden item. To musíme najít v 'inventoryItems'.
    
    if (recipe.requirements) {
        for (let req of recipe.requirements) {
            const usedCount = ingredientsUsed[req.item] || 0;
            // Najdeme item v inputu abychom věděli kolik má ml
            const itemInfo = inventoryItems.find(i => i.id === req.item);
            if (!itemInfo) return false; // Nemáme item
            
            const totalMlUsed = usedCount * itemInfo.amount;
            
            if (totalMlUsed < req.minAmount) return false;
        }
    }
    return true;
}

function finishGame() {
    // Musíme poslat i seznam toho, co jsme vylili do kanálu?
    // V této logice: Hráč dostane výsledek jen z toho, co je AKTUÁLNĚ v kádince.
    // Ale z inventáře mu zmizí vše, co proklikal (i ty vylité pokusy).
    // K tomu bychom potřebovali sledovat 'totalConsumedItems' zvlášť od 'currentBatchIngredients'.
    
    // Pro jednoduchost teď posíláme jen to, co tvoří aktuální směs.
    // Což znamená malý exploit: Hráč může vylít nepovedený pokus a itemy se mu neodečtou (pokud zavře okno).
    // Oprava: finishGame by měla poslat rozdíl mezi 'initialCount' a 'currentCount'.
    
    let consumed = {};
    inventoryItems.forEach(item => {
        let diff = (item.initialCount || item.count) - item.currentCount; // item.count je z Lua, item.currentCount se mění
        if (diff > 0) {
            consumed[item.id] = diff;
        }
    });

    fetch(`https://${GetParentResourceName()}/finish`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            r: currentMix.r, g: currentMix.g, b: currentMix.b, ph: currentMix.ph, amount: currentMix.amount,
            ingredientsUsed: consumed // Posíláme reálně spotřebované kusy
        })
    });
    document.getElementById('game-container').style.display = 'none';
}

function closeGame() {
    document.getElementById('game-container').style.display = 'none';
    fetch(`https://${GetParentResourceName()}/close`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({})
    });
}