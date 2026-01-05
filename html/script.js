// ============================================================
// FILE: html/script.js
// ============================================================

// --- HLAVNÍ PROMĚNNÉ ---
let currentMix = { r: 255, g: 255, b: 255, ph: 7.0, amount: 0 };

// Sledování surovin
let ingredientsInBeaker = {};   // Co je v kádince (pro recept)
let ingredientsTotalUsed = {};  // Co se odečte z inventáře (včetně vylitých pokusů)

// Data z klienta
let inventoryItems = [];
let availableRecipes = [];
let playerSkill = 0;
let imgBaseUrl = "nui://vorp_inventory/html/img/items/"; // Defaultní cesta

// Stav procesu (Hardcore mechaniky)
let isBusy = false;          // Blokuje interakce během animací
let isBurnerOn = false;      // Stav hořáku
let targetTemp = 0;          // Nastavená teplota
let currentBoilTime = 0;     // Doba varu v sekundách
let boilInterval = null;     // Timer pro var

const MAX_BEAKER_VOLUME = 500;

// ============================================================
// 1. INICIALIZACE A EVENTY
// ============================================================

window.addEventListener('message', function(event) {
    if (event.data.type === "OPEN_GAME") {
        inventoryItems = event.data.inputs || [];
        availableRecipes = event.data.recipes || [];
        playerSkill = event.data.playerSkill || 0;
        
        if (event.data.imgDir) {
            imgBaseUrl = event.data.imgDir;
        }

        document.getElementById('player-skill').innerText = playerSkill;

        setupGame();
        document.getElementById('game-container').style.display = 'flex';
    }
});

document.addEventListener('keydown', function(event) {
    // Zavření ESCapem, ale jen pokud neprobíhá animace
    if (event.key === "Escape" && !isBusy) closeGame();
});

function setupGame() {
    // Reset směsi
    currentMix = { r: 255, g: 255, b: 255, ph: 7.0, amount: 0 };
    ingredientsInBeaker = {};
    ingredientsTotalUsed = {};
    
    // Reset procesu
    isBusy = false;
    isBurnerOn = false;
    targetTemp = 0;
    currentBoilTime = 0;
    if (boilInterval) clearInterval(boilInterval);

    // Reset UI prvků
    document.getElementById('temp-slider').value = 0;
    document.getElementById('temp-val').innerText = "0";
    document.getElementById('boil-time').innerText = "00:00";
    
    const btnBurner = document.getElementById('btn-burner');
    btnBurner.classList.remove('active');
    btnBurner.innerText = "ZAPÁLIT HOŘÁK";
    
    document.getElementById('bubbles').classList.add('hidden');
    document.getElementById('action-overlay').classList.add('hidden');

    // Inicializace inventáře
    inventoryItems.forEach(item => {
        item.currentCount = item.count; 
    });

    renderInventory();
    updateVisuals();
    identifyMixture();
}

// ============================================================
// 2. RENDEROVÁNÍ INVENTÁŘE (S IKONAMI)
// ============================================================

function renderInventory() {
    const container = document.getElementById('inventory-list');
    container.innerHTML = '';
    
    inventoryItems.forEach((item, index) => {
        const div = document.createElement('div');
        
        // Zamezení klikání pokud item došel, nebo pokud "pracujeme" (isBusy / isBurnerOn)
        // (Bezpečnostní prvek: nelze přilévat do vařící směsi, může vybuchnout - zjednodušeno na zákaz)
        const isLocked = item.currentCount <= 0 || isBusy || isBurnerOn;
        const disabledClass = isLocked ? 'disabled' : '';
        
        div.className = `inv-item ${disabledClass}`;
        
        const imgPath = `${imgBaseUrl}${item.id}.png`;
        
        div.innerHTML = `
            <div class="icon-container">
                <!-- Glow efekt podle barvy chemikálie -->
                <div class="icon-glow" style="
                    background: radial-gradient(circle, rgba(${item.r},${item.g},${item.b}, 0.6) 0%, rgba(0,0,0,0) 70%);
                    box-shadow: inset 0 0 10px rgba(${item.r},${item.g},${item.b}, 0.3);
                "></div>
                <img src="${imgPath}" class="inv-img" onerror="this.style.display='none'" alt="${item.label}">
            </div>
            
            <div class="item-info">
                <div class="item-name">${item.label}</div>
                <div class="item-details">
                    Skladem: <span id="count-${index}">${item.currentCount}</span><br>
                    <small style="color: #d7ccc8;">
                        <span style="color: rgb(${item.r},${item.g},${item.b});">●</span> 
                        pH ${item.ph} (+${item.amount}ml)
                    </small>
                </div>
            </div>
        `;
        
        if (!isLocked) {
            div.onclick = () => addToMix(index);
        }
        
        container.appendChild(div);
    });
}

// ============================================================
// 3. LOGIKA NALÉVÁNÍ (PROGRESS BAR)
// ============================================================

// Upravená funkce addToMix pro animaci lahvičky
function addToMix(index) {
    if (isBusy || isBurnerOn) return; 

    const item = inventoryItems[index];
    if (item.currentCount <= 0) return;
    if (currentMix.amount + item.amount > MAX_BEAKER_VOLUME) return;

    // 1. ZAMKNOUT UI
    isBusy = true;
    renderInventory(); // Itemmy zešednou

    // 2. PŘÍPRAVA SCÉNY
    const scene = document.getElementById('pouring-scene');
    const bottleImg = document.getElementById('pouring-bottle-img');
    const stream = document.getElementById('pouring-stream');

    // Nastavíme obrázek podle toho, co držíme
    bottleImg.src = `${imgBaseUrl}${item.id}.png`;
    
    // Nastavíme barvu proudu podle ingredience
    stream.style.backgroundColor = `rgb(${item.r}, ${item.g}, ${item.b})`;
    // Reset stylů (pro jistotu)
    bottleImg.classList.remove('tilted');
    stream.classList.remove('flowing');
    
    // Zobrazíme scénu
    scene.classList.remove('hidden');

    // === SEKVENCE ANIMACE ===
    
    // KROK A: Naklonění lahve (0ms)
    // Dáme malý delay, aby se stihl načíst display:block
    setTimeout(() => {
        bottleImg.classList.add('tilted');
    }, 50);

    // KROK B: Spuštění proudu (po 400ms - až se lahev nakloní)
    setTimeout(() => {
        stream.classList.add('flowing');
        
        // Zvukový efekt by šel přidat zde: playPourSound();
    }, 400);

    // KROK C: Zastavení proudu (po 1500ms - doba lití)
    setTimeout(() => {
        stream.classList.remove('flowing');
        
        // ZDE PROVEDEME VÝPOČTY (v momentě kdy přestane téct)
        finalizePouring(index);
        
    }, 1800);

    // KROK D: Vrácení lahve zpět (po chvilce co doteče)
    setTimeout(() => {
        bottleImg.classList.remove('tilted');
    }, 2000);

    // KROK E: Skrytí scény a odemčení (až se lahev narovná)
    setTimeout(() => {
        scene.classList.add('hidden');
        isBusy = false;
        renderInventory(); // Odemknout itemy
    }, 2600);
}

// Funkce finalizePouring zůstává stejná jako v předchozí verzi
function finalizePouring(index) {
    const item = inventoryItems[index];
    
    // 1. Odečet z UI
    item.currentCount--;
    document.getElementById(`count-${index}`).innerText = item.currentCount;

    // 2. Data pro server
    if (!ingredientsInBeaker[item.id]) ingredientsInBeaker[item.id] = 0;
    ingredientsInBeaker[item.id]++;

    if (!ingredientsTotalUsed[item.id]) ingredientsTotalUsed[item.id] = 0;
    ingredientsTotalUsed[item.id]++;

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

// ============================================================
// 4. LOGIKA VAŘENÍ (HOŘÁK A TEPLOTA)
// ============================================================

// Voláno při posunu slideru
function updateTempDisplay() {
    targetTemp = parseInt(document.getElementById('temp-slider').value);
    document.getElementById('temp-val').innerText = targetTemp;
    
    // Pokud hoří, aktualizujeme vizuál bublinek hned
    if (isBurnerOn) updateBubbles();
    identifyMixture();
}

function toggleBurner() {
    if (isBusy) return; // Nemůžeme zapalovat, když naléváme

    isBurnerOn = !isBurnerOn;
    const btn = document.getElementById('btn-burner');
    
    if (isBurnerOn) {
        // ZAPNUTÍ
        btn.classList.add('active');
        btn.innerText = "ZHASNOUT HOŘÁK";
        renderInventory(); // Zamknout inventář

        // Start Timeru
        boilInterval = setInterval(() => {
            // Čas běží, jen pokud je teplota > 20°C a je co vařit
            if (currentMix.amount > 0 && targetTemp > 20) {
                currentBoilTime++;
                updateBoilTimeDisplay();
                identifyMixture(); // Kontrola receptu v reálném čase
            }
        }, 1000);
        
        updateBubbles();

    } else {
        // VYPNUTÍ
        btn.classList.remove('active');
        btn.innerText = "ZAPÁLIT HOŘÁK";
        
        clearInterval(boilInterval);
        document.getElementById('bubbles').classList.add('hidden');
        renderInventory(); // Odemknout inventář
    }
}

function updateBoilTimeDisplay() {
    const minutes = Math.floor(currentBoilTime / 60);
    const seconds = currentBoilTime % 60;
    // Formát MM:SS
    const str = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    document.getElementById('boil-time').innerText = str;
}

function updateBubbles() {
    const bubbles = document.getElementById('bubbles');
    // Bublinky se objeví, pokud je hořák zapnutý, je tam tekutina a teplota > 80
    if (isBurnerOn && currentMix.amount > 0 && targetTemp > 80) {
        bubbles.classList.remove('hidden');
        // Rychlost animace by šla měnit podle teploty, ale stačí toggle
    } else {
        bubbles.classList.add('hidden');
    }
}

// ============================================================
// 5. VIZUALIZACE A RESET
// ============================================================

function updateVisuals() {
    document.getElementById('current-amt').innerText = Math.round(currentMix.amount);
    document.getElementById('current-ph').innerText = currentMix.ph.toFixed(1);
    
    const liquid = document.getElementById('liquid');
    liquid.style.backgroundColor = `rgb(${Math.round(currentMix.r)}, ${Math.round(currentMix.g)}, ${Math.round(currentMix.b)})`;
    
    let heightPerc = (currentMix.amount / MAX_BEAKER_VOLUME) * 100;
    if (heightPerc > 100) heightPerc = 100;
    liquid.style.height = heightPerc + '%';
}

function resetMix() {
    if (isBusy) return;
    
    // Bezpečnost: vypnout hořák
    if (isBurnerOn) toggleBurner();

    // Reset dat
    currentMix = { r: 255, g: 255, b: 255, ph: 7.0, amount: 0 };
    ingredientsInBeaker = {};
    currentBoilTime = 0;

    // Aktualizace UI
    updateBoilTimeDisplay();
    updateVisuals();
    identifyMixture();
    
    // Poznámka: Itemmy se NEVRACÍ (ingredientsTotalUsed zůstává).
}

// ============================================================
// 6. IDENTIFIKACE RECEPTU (VČETNĚ PROCESU)
// ============================================================

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
            predBox.innerText = "Neznámá směs";
            predBox.classList.add("prediction-vague");
        }
    } else {
        predBox.innerText = "Kal (Špatný postup)";
        predBox.classList.add("prediction-trash");
    }
}

function checkRecipeMatch(recipe) {
    const cond = recipe.conditions;
    
    // 1. Fyzikální vlastnosti (pH, Množství)
    if (currentMix.ph < cond.phMin || currentMix.ph > cond.phMax) return false;
    if (currentMix.amount < cond.minTotalAmount) return false;
    
    // 2. Barva (Tolerance)
    if (cond.colorTarget) {
        const tol = cond.colorTolerance || 30;
        if (Math.abs(currentMix.r - cond.colorTarget.r) > tol) return false;
        if (Math.abs(currentMix.g - cond.colorTarget.g) > tol) return false;
        if (Math.abs(currentMix.b - cond.colorTarget.b) > tol) return false;
    }

    // 3. Ingredience (Requirements)
    if (recipe.requirements) {
        for (let req of recipe.requirements) {
            const usedCount = ingredientsInBeaker[req.item] || 0;
            const itemDef = inventoryItems.find(i => i.id === req.item);
            if (!itemDef) return false; // Nemáme info o itemu
            
            // Kontrola ml
            if ((usedCount * itemDef.amount) < req.minAmount) return false;
        }
    }

    // 4. PROCES (Teplota a Čas)
    // Pokud recept vyžaduje specifický proces
    if (recipe.process) {
        const proc = recipe.process;
        
        // Kontrola Teploty
        // targetTemp je to, co hráč nastavil na slideru
        if (Math.abs(targetTemp - proc.temp) > (proc.tempTolerance || 15)) {
            return false;
        }

        // Kontrola Času
        // currentBoilTime je jak dlouho to hráč nechal bublat
        if (Math.abs(currentBoilTime - proc.time) > (proc.timeTolerance || 5)) {
            return false;
        }
    }
    
    return true;
}

// ============================================================
// 7. KOMUNIKACE SE SERVEREM
// ============================================================

function finishGame() {
    if (isBusy) return;
    if (isBurnerOn) toggleBurner(); // Vypneme hořák před dokončením

    // Odesíláme všechna data pro finální validaci na serveru
    fetch(`https://${GetParentResourceName()}/finish`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            beakerIngredients: ingredientsInBeaker, // Pro recept
            totalConsumed: ingredientsTotalUsed,    // Pro odečet itemů
            finalTemp: targetTemp,                  // Pro validaci procesu
            finalTime: currentBoilTime              // Pro validaci procesu
        })
    });
    
    document.getElementById('game-container').style.display = 'none';
}

function closeGame() {
    if (isBusy) return; // Nemůžeme zavřít uprostřed nalévání
    if (isBurnerOn) toggleBurner();

    document.getElementById('game-container').style.display = 'none';
    fetch(`https://${GetParentResourceName()}/close`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({})
    });
}