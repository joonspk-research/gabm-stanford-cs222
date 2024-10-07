let game;
let gameStates = [];
let currentStep = 0;
let char;
let items = {};

const TILE_SIZE = 16;
const MAP_WIDTH = 8;
const MAP_HEIGHT = 8;
const SCALE = 4;
const WIDTH = MAP_WIDTH * TILE_SIZE * SCALE;
const HEIGHT = MAP_HEIGHT * TILE_SIZE * SCALE;

const WALKABLE_TILES = [0, 98, 101, 100, 99];
const WALKABLE_BEHIND_TILES = [110, 111, 112, 136, 137, 138];
const FRIDGE_ITEMS = ['butter', 'milk', 'eggs'];

const config = {
  type: Phaser.AUTO,
  width: WIDTH,
  height: HEIGHT,
  parent: 'game-container',
  backgroundColor: '#eef3ef',
  antialias: false,
  pixelArt: true,
  physics: {
    default: 'arcade',
    arcade: { gravity: { y: 0 }, debug: false }
  },
  scene: { preload, create, update }
};

game = new Phaser.Game(config);

let currentTypewriterTimeout;

function typeWriter(text, elementId, speed = 10) {
  const element = document.getElementById(elementId);
  clearTimeout(currentTypewriterTimeout);
  element.innerHTML = '';
  let i = 0;
  function type() {
    if (i < text.length) {
      element.innerHTML += text.charAt(i);
      i++;
      currentTypewriterTimeout = setTimeout(type, speed);
    }
  }
  type();
}

function preload() {
  this.load.image('tiles', 'static/assets/kitchen_tileset.png');
  this.load.tilemapCSV('kitchen-map', 'static/assets/kitchen_tilemap.csv');
  this.load.spritesheet('char', 'static/assets/char_spritesheet.png', { frameWidth: 32, frameHeight: 32 });
  
  ['flour', 'baking_powder', 'salt', 'butter', 'sugar', 'eggs', 
   'vanilla_extract', 'milk', 'mixing_bowl', 'large_bowl', 
   'whisk', 'mixer', 'pans'].forEach(item => 
    this.load.image(item, `static/assets/${item}.png`)
  );
  this.load.tilemapCSV('item-positions', 'static/assets/item_positions.csv');
  this.load.image('success_cake', 'static/assets/success_cake.png');
  this.load.image('timeout_cake', 'static/assets/timeout_cake.png');
  this.load.image('bad_cake', 'static/assets/bad_cake.png');
}

function create() {
  const map = this.make.tilemap({ key: 'kitchen-map', tileWidth: TILE_SIZE, tileHeight: TILE_SIZE });
  const tileset = map.addTilesetImage('tiles', 'tiles', TILE_SIZE, TILE_SIZE);
  const layer = map.createLayer(0, tileset, 0, 0).setScale(SCALE);

  [layer.texture, this.textures.get('tiles')].forEach(texture => {
    if (texture) texture.setFilter(Phaser.Textures.NEAREST);
  });
  window.gameLayer = layer.setDepth(100);
  char = this.physics.add.sprite(4 * TILE_SIZE * SCALE + (TILE_SIZE * SCALE / 2), 5 * TILE_SIZE * SCALE + (TILE_SIZE * SCALE / 2), 'char', 0)
    .setScale(SCALE / 2);
  if (char.texture) char.texture.setFilter(Phaser.Textures.NEAREST);

  createAnimations.call(this);
  char.play('idle_front');
  const itemPositionsMap = this.make.tilemap({ key: 'item-positions', tileWidth: TILE_SIZE, tileHeight: TILE_SIZE });
  updateCharacterDepth();
  createItems.call(this, itemPositionsMap);
  createDebugGrid.call(this);
}

function createAnimations() {
  const animConfig = { frameRate: 10, repeat: -1 };
  ['front', 'left', 'right', 'back'].forEach((direction, index) => {
    this.anims.create({
      key: `idle_${direction}`,
      frames: [{ key: 'char', frame: index * 3 }],
      frameRate: 1,
      repeat: -1
    });
    this.anims.create({
      key: `walk_${direction}`,
      frames: this.anims.generateFrameNumbers('char', { start: index * 3, end: index * 3 + 2 }),
      ...animConfig
    });
  });
}

function createItems(itemPositionsMap) {
  for (let y = 0; y < MAP_HEIGHT; y++) {
    for (let x = 0; x < MAP_WIDTH; x++) {
      const tile = itemPositionsMap.getTileAt(x, y);
      if (tile) {
        const itemName = getItemName(tile.index);
        if (itemName) {
          const itemX = x * TILE_SIZE * SCALE + (TILE_SIZE * SCALE / 2);
          const itemY = y * TILE_SIZE * SCALE + (TILE_SIZE * SCALE / 2);
          
          if (itemName === 'oven' || itemName === 'fridge') {
            items[itemName] = { x: itemX, y: itemY };
          } else {
            items[itemName] = this.add.image(itemX, itemY, itemName)
              .setScale(SCALE)
              .setVisible(false);
            
            if (items[itemName].texture) {
              items[itemName].texture.setFilter(Phaser.Textures.NEAREST);
            }
            
            const mapTile = window.gameLayer.getTileAt(x, y);
            items[itemName].setDepth(mapTile && WALKABLE_BEHIND_TILES.includes(mapTile.index) ? 150 : 200);
          }
        }
      }
    }
  }
}

function getItemName(index) {
  const itemMap = {
    1: 'flour', 2: 'baking_powder', 3: 'salt', 4: 'butter', 5: 'sugar',
    6: 'eggs', 7: 'vanilla_extract', 8: 'milk', 9: 'oven', 10: 'mixing_bowl',
    11: 'large_bowl', 12: 'whisk', 13: 'mixer', 14: 'pans', 15: 'fridge'
  };
  return itemMap[index];
}

function createDebugGrid() {
  const graphics = this.add.graphics().lineStyle(2, 0xff0000, 0.0);
  for (let x = 0; x <= MAP_WIDTH; x++) {
    for (let y = 0; y <= MAP_HEIGHT; y++) {
      graphics.strokeRect(x * TILE_SIZE * SCALE, y * TILE_SIZE * SCALE, TILE_SIZE * SCALE, TILE_SIZE * SCALE);
    }
  }
  graphics.setDepth(1000);
}

function update() {}

let isAutoProgressEnabled = false;
let autoProgressInterval;

function autoProgress() {
  if (currentStep < gameStates.length - 1) {
    currentStep++;
    displayGameState(gameStates[currentStep]);
  } else {
    $.post('/next_step', function(data) {
      updateGameState(data);
      if (data.completed) {
        stopAutoProgress();
      }
    });
  }
  updateNavigationButtons();
  updateCurrentStepDisplay();
}

function startAutoProgress() {
  isAutoProgressEnabled = true;
  $('#auto-progress').text('Pause Simulation').addClass('active');
  autoProgressInterval = setInterval(autoProgress, 8000);
}

function stopAutoProgress() {
  isAutoProgressEnabled = false;
  $('#auto-progress').text('Play Simulation').removeClass('active');
  clearInterval(autoProgressInterval);
}

function updateGameState(data) {
  if (gameStates.length === 0) {
    gameStates.push(data);
    currentStep = 0;
  } else {
    gameStates.push(data);
    currentStep = gameStates.length - 1;
  }
  
  displayGameState(data);
  updateNavigationButtons();
  
  if (data.completed) {
    const endGameStatus = data.final_message.includes("successfully baked") ? 'success' :
                          data.final_message.includes("mistakes with the ingredients") ? 'bad' : 'neutral';
    endGame(data.final_message || "Oh dear, it seems we've taken too long to bake the cake. Let's try again another time!", endGameStatus);
  }
}

function displayGameState(state) {
  typeWriter(state.agent_message || state.message, 'speech-box');
  
  let feedbackHtml = '';
  
  if (state.attempted_actions && state.attempted_actions.length > 0) {
    feedbackHtml += '<h3>Attempted Actions:</h3><ul>';
    state.attempted_actions.forEach(action => {
      feedbackHtml += `<li>${formatAction(action)}${state.executed_actions.some(ea => ea.name === action.name) ? '' : ' (Failed)'}</li>`;
    });
    feedbackHtml += '</ul>';
  }
  
  if (state.feedback) {
    feedbackHtml += '<h3>Environment Feedback:</h3>';
    feedbackHtml += state.feedback.split('\n').map(line => 
      $('<div>').text(line).prop('outerHTML')
    ).join('');
  }
  
  $('#feedback').html(feedbackHtml);
  
  if (state.executed_actions && state.executed_actions.length > 0) {
    processExecutedActions(state.executed_actions);
  }
  
  updateProgress(state.progress);
}

function formatAction(action) {
  let formattedAction = action.name.replace(/_/g, ' ');
  
  if (action.args && action.args.length > 0) {
    formattedAction += ': ' + action.args.join(', ');
  }
  
  return formattedAction.charAt(0).toUpperCase() + formattedAction.slice(1);
}

function processExecutedActions(executedActions) {
  let actionQueue = [...executedActions];
  
  function processNextAction() {
    if (actionQueue.length > 0) {
      const action = actionQueue.shift();
      const actionMap = {
        'add_ingredient': (args) => {
          const ingredient = args[0];
          const bowl = isWetIngredient(ingredient) ? 'large_bowl' : 'mixing_bowl';
          moveCharTo(ingredient, () => moveCharTo(bowl, processNextAction));
        },
        'use_tool': (args) => moveCharTo(args[0], processNextAction),
        'preheat_oven': () => moveCharTo('oven', processNextAction),
        'mix_ingredients': (args) => {
          const type = args[0];
          if (type === "dry") {
            moveCharTo('mixing_bowl', () => moveCharTo('whisk', processNextAction));
          } else if (type === "wet" || type === "cream") {
            moveCharTo('large_bowl', () => moveCharTo('mixer', processNextAction));
          } else {
            processNextAction();
          }
        },
        'combine_all_ingredients': () => moveCharTo('mixing_bowl', () => moveCharTo('large_bowl', processNextAction)),
        'pour_batter': () => moveCharTo('large_bowl', () => moveCharTo('pans', processNextAction)),
        'bake_cake': () => moveCharTo('pans', () => moveCharTo('oven', processNextAction)),
        'cool_cake': () => moveCharTo('oven', () => moveCharTo('pans', processNextAction))
      };
      
      if (actionMap[action.name]) {
        actionMap[action.name](action.args);
      } else {
        console.log(`Unknown action: ${action.name}`);
        processNextAction();
      }
    }
  }
  
  processNextAction();
}

function isWetIngredient(ingredient) {
  return ['butter', 'sugar', 'eggs', 'vanilla_extract', 'milk'].includes(ingredient.toLowerCase());
}

function findPath(startX, startY, endX, endY) {
  const queue = [[startX, startY]];
  const visited = new Set();
  const parent = new Map();

  while (queue.length > 0) {
    const [x, y] = queue.shift();
    const key = `${x},${y}`;

    if (x === endX && y === endY) {
      return reconstructPath(parent, startX, startY, endX, endY);
    }

    if (!visited.has(key)) {
      visited.add(key);
      [[x + 1, y], [x - 1, y], [x, y + 1], [x, y - 1]].forEach(([nx, ny]) => {
        if (isWalkable(nx, ny) && !visited.has(`${nx},${ny}`)) {
          queue.push([nx, ny]);
          parent.set(`${nx},${ny}`, [x, y]);
        }
      });
    }
  }

  return null;
}

function isWalkable(x, y) {
  if (x < 0 || x >= MAP_WIDTH || y < 0 || y >= MAP_HEIGHT) return false;
  const tile = window.gameLayer.getTileAt(x, y);
  return tile && (WALKABLE_TILES.includes(tile.index) || WALKABLE_BEHIND_TILES.includes(tile.index));
}

function moveCharTo(itemName, callback) {
  let targetX, targetY;

  function moveToTarget(nextCallback) {
    if (targetX !== undefined && targetY !== undefined) {
      const startX = Math.floor(char.x / (TILE_SIZE * SCALE));
      const startY = Math.floor(char.y / (TILE_SIZE * SCALE));
      const targetTile = window.gameLayer.getTileAt(targetX, targetY);
      const isBehindTile = targetTile && WALKABLE_BEHIND_TILES.includes(targetTile.index);

      let path = isBehindTile ? 
        findPath(startX, startY, targetX, targetY) : 
        findAdjacentPath(startX, startY, targetX, targetY);

      if (path) {
        moveAlongPath(path, () => {
          const dx = targetX - Math.floor(char.x / (TILE_SIZE * SCALE));
          const dy = targetY - Math.floor(char.y / (TILE_SIZE * SCALE));
          
          const direction = isBehindTile ? 'front' :
            Math.abs(dx) > Math.abs(dy) ? (dx > 0 ? 'right' : 'left') :
            (dy > 0 ? 'front' : 'back');
          
          char.play(`idle_${direction}`);

          if (itemName !== 'oven' && itemName !== 'fridge' && items[itemName] && !items[itemName].visible) {
            items[itemName].setVisible(true);
          }

          updateCharacterDepth();
          if (nextCallback) nextCallback();
        });
      } else if (nextCallback) nextCallback();
    } else if (nextCallback) nextCallback();
  }

  if (FRIDGE_ITEMS.includes(itemName)) {
    if (items['fridge']) {
      targetX = Math.floor(items['fridge'].x / (TILE_SIZE * SCALE));
      targetY = Math.floor(items['fridge'].y / (TILE_SIZE * SCALE));
      moveToTarget(() => {
        if (items[itemName]) {
          targetX = Math.floor(items[itemName].x / (TILE_SIZE * SCALE));
          targetY = Math.floor(items[itemName].y / (TILE_SIZE * SCALE));
          moveToTarget(callback);
        } else if (callback) callback();
      });
    } else if (callback) callback();
  } else {
    const item = items[itemName];
    if (item) {
      targetX = Math.floor(item.x / (TILE_SIZE * SCALE));
      targetY = Math.floor(item.y / (TILE_SIZE * SCALE));
      moveToTarget(callback);
    } else if (callback) callback();
  }
}

function findAdjacentPath(startX, startY, targetX, targetY) {
  for (const [adjX, adjY] of [[targetX - 1, targetY], [targetX + 1, targetY], [targetX, targetY - 1], [targetX, targetY + 1]]) {
    if (isWalkable(adjX, adjY)) {
      const tempPath = findPath(startX, startY, adjX, adjY);
      if (tempPath) return tempPath;
    }
  }
  return null;
}

function reconstructPath(parent, startX, startY, endX, endY) {
  const path = [];
  let current = [endX, endY];
  while (current[0] !== startX || current[1] !== startY) {
    path.unshift(current);
    current = parent.get(`${current[0]},${current[1]}`);
  }
  return path;
}

function moveAlongPath(path, callback) {
  if (path.length === 0) {
    updateCharacterDepth();
    if (callback) callback();
    return;
  }

  const [nextX, nextY] = path.shift();
  const targetX = nextX * TILE_SIZE * SCALE + (TILE_SIZE * SCALE / 2);
  const targetY = nextY * TILE_SIZE * SCALE + (TILE_SIZE * SCALE / 2);

  const dx = targetX - char.x;
  const dy = targetY - char.y;

  const direction = Math.abs(dx) > Math.abs(dy) ? (dx > 0 ? 'right' : 'left') : (dy > 0 ? 'front' : 'back');

  char.play(`walk_${direction}`);

  game.scene.scenes[0].tweens.add({
    targets: char,
    x: targetX,
    y: targetY,
    duration: 200,
    ease: 'Linear',
    onComplete: () => {
      updateCharacterDepth();
      moveAlongPath(path, callback);
    }
  });
}

function updateCharacterDepth() {
  const tileX = Math.floor(char.x / (TILE_SIZE * SCALE));
  const tileY = Math.floor(char.y / (TILE_SIZE * SCALE));
  const tile = window.gameLayer.getTileAt(tileX, tileY);
  
  if (tile) {
    char.setDepth(WALKABLE_BEHIND_TILES.includes(tile.index) ? 90 : 150);
  }
}

function updateNavigationButtons() {
  $('#prev-step').prop('disabled', currentStep === 0);
  $('#next-step').prop('disabled', currentStep === gameStates.length - 1 && gameStates[currentStep].completed);
}

function updateProgress(progress) {
  $('#steps').empty();
  progress.steps.forEach(function(step) {
    var li = $('<li>').text(step.name);
    if (step.status === 'completed') {
      li.addClass('completed');
    }
    if (step.tools) {
      var toolList = $('<ul>');
      step.tools.forEach(function(tool) {
        var toolLi = $('<li>').text(tool.name);
        if (tool.used) {
          toolLi.addClass('tool-used');
        }
        toolList.append(toolLi);
      });
      li.append(toolList);
    }
    $('#steps').append(li);
  });

  $('#dry-ingredients').empty().append(
    progress.dry_ingredients.map(ing => 
      `<li>${ing.name}: ${ing.current}/${ing.required}</li>`
    ).join('')
  );

  $('#wet-ingredients').empty().append(
    progress.wet_ingredients.map(ing => 
      `<li>${ing.name}: ${ing.current}/${ing.required}</li>`
    ).join('')
  );
}

function testCharacterMovement() {
  const ingredients = ['flour', 'baking_powder', 'salt', 'butter', 'sugar', 'eggs', 'vanilla_extract', 'milk'];
  let currentIndex = 0;

  function moveToNextIngredient() {
    if (currentIndex < ingredients.length) {
      const ingredient = ingredients[currentIndex];
      moveCharTo(ingredient, () => {
        setTimeout(() => {
          currentIndex++;
          moveToNextIngredient();
        }, 1000);
      });
    }
  }

  moveToNextIngredient();
}

function testToolMovement() {
  const tools = ['mixing_bowl', 'large_bowl', 'whisk', 'mixer', 'pans', 'oven'];
  let currentIndex = 0;

  function moveToNextTool() {
    if (currentIndex < tools.length) {
      const tool = tools[currentIndex];
      moveCharTo(tool, () => {
        setTimeout(() => {
          currentIndex++;
          moveToNextTool();
        }, 1000);
      });
    }
  }

  moveToNextTool();
}

function endGame(message, status = 'neutral') {
  stopAutoProgress();
  $('#next-step').prop('disabled', true);
  $('#prev-step').prop('disabled', true);
  
  let imageName;
  switch(status) {
    case 'success':
      imageName = 'success_cake';
      break;
    case 'timeout':
      imageName = 'timeout_cake';
      break;
    case 'bad':
      imageName = 'bad_cake';
      break;
    default:
      imageName = null;
  }
  
  if (imageName) {
    displayEndImage(imageName);
  }
  
  typeWriter(message, 'speech-box');
}

function displayEndImage(imageName) {
  const scene = game.scene.scenes[0];
  
  scene.children.list.forEach(child => {
    child.setVisible(false);
  });
  scene.cameras.main.setBackgroundColor('#FFFFFF');

  const endImage = scene.add.image(WIDTH / 2, HEIGHT / 2, imageName);
  
  endImage.setScale(Math.min(WIDTH / endImage.width, HEIGHT / endImage.height));
  endImage.setDepth(1000);
  endImage.setVisible(true);
  
  if (endImage.texture) {
    endImage.texture.setFilter(Phaser.Textures.LINEAR);
  }
}

function updateCurrentStepDisplay() {
  $('#current-step').text(`Current Step: ${currentStep}`);
}
$(document).ready(function() {

  $.post('/start_baking', function(data) {
    updateGameState(data);
    $('#next-step').prop('disabled', false);
  });

  $('#next-step').click(function() {
    if (currentStep < gameStates.length - 1) {
      currentStep++;
      displayGameState(gameStates[currentStep]);
    } else {
      $.post('/next_step', function(data) {
        updateGameState(data);
      });
    }
    updateNavigationButtons();
  });

  $('#prev-step').click(function() {
    if (currentStep > 0) {
      currentStep--;
      displayGameState(gameStates[currentStep]);
      updateNavigationButtons();
      updateCurrentStepDisplay();
    }
  });

  $('#test-movement').click(function() {
    testCharacterMovement();
  });

  $('#test-tool-movement').click(function() {
    testToolMovement();
  });

  $('#auto-progress').click(function() {
    if (isAutoProgressEnabled) {
      stopAutoProgress();
    } else {
      startAutoProgress();
    }
  });

});