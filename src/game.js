(() => {
  const canvas = document.querySelector('#game');
  const ctx = canvas.getContext('2d');
  const scoreEl = document.querySelector('#score');
  const livesEl = document.querySelector('#lives');
  const timeEl = document.querySelector('#time');
  const bestEl = document.querySelector('#best');
  const startButton = document.querySelector('#startButton');
  const restartButton = document.querySelector('#restartButton');

  const W = canvas.width;
  const H = canvas.height;
  const clamp = (value, min, max) => Math.max(min, Math.min(max, value));
  const rand = (min, max) => Math.random() * (max - min) + min;
  const distance = (a, b) => Math.hypot(a.x - b.x, a.y - b.y);

  const keys = new Set();
  const stars = Array.from({ length: 90 }, () => ({ x: rand(0, W), y: rand(0, H), r: rand(0.7, 2.1), s: rand(10, 42) }));
  const state = {
    running: false,
    paused: false,
    over: false,
    score: 0,
    lives: 3,
    timeLeft: 60,
    lastTime: 0,
    spawnStar: 0,
    spawnRock: 0,
    flash: 0,
    best: Number(localStorage.getItem('minigme-best') || 0),
    player: { x: W / 2, y: H / 2, r: 18, speed: 330 },
    pickups: [],
    rocks: [],
  };

  bestEl.textContent = state.best;

  function reset() {
    state.running = true;
    state.paused = false;
    state.over = false;
    state.score = 0;
    state.lives = 3;
    state.timeLeft = 60;
    state.spawnStar = 0;
    state.spawnRock = 0;
    state.flash = 0;
    state.player.x = W / 2;
    state.player.y = H / 2;
    state.pickups = [];
    state.rocks = [];
    for (let i = 0; i < 7; i += 1) spawnPickup();
    updateHud();
  }

  function updateHud() {
    scoreEl.textContent = state.score;
    livesEl.textContent = state.lives;
    timeEl.textContent = Math.max(0, Math.ceil(state.timeLeft));
    bestEl.textContent = state.best;
  }

  function spawnPickup() {
    state.pickups.push({
      x: rand(36, W - 36),
      y: rand(36, H - 36),
      r: rand(9, 14),
      pulse: rand(0, Math.PI * 2),
    });
  }

  function spawnRock() {
    const side = Math.floor(rand(0, 4));
    const rock = { x: 0, y: 0, vx: 0, vy: 0, r: rand(15, 28), spin: rand(-4, 4), angle: rand(0, 7) };
    if (side === 0) { rock.x = -30; rock.y = rand(0, H); rock.vx = rand(130, 230); rock.vy = rand(-90, 90); }
    if (side === 1) { rock.x = W + 30; rock.y = rand(0, H); rock.vx = rand(-230, -130); rock.vy = rand(-90, 90); }
    if (side === 2) { rock.x = rand(0, W); rock.y = -30; rock.vx = rand(-90, 90); rock.vy = rand(130, 230); }
    if (side === 3) { rock.x = rand(0, W); rock.y = H + 30; rock.vx = rand(-90, 90); rock.vy = rand(-230, -130); }
    state.rocks.push(rock);
  }

  function update(dt) {
    if (!state.running || state.paused || state.over) return;

    state.timeLeft -= dt;
    state.spawnStar -= dt;
    state.spawnRock -= dt;
    state.flash = Math.max(0, state.flash - dt);

    if (state.spawnStar <= 0) {
      spawnPickup();
      state.spawnStar = rand(0.7, 1.25);
    }
    if (state.spawnRock <= 0) {
      spawnRock();
      state.spawnRock = rand(0.55, 1.05);
    }

    const p = state.player;
    let dx = 0;
    let dy = 0;
    if (keys.has('arrowleft') || keys.has('a')) dx -= 1;
    if (keys.has('arrowright') || keys.has('d')) dx += 1;
    if (keys.has('arrowup') || keys.has('w')) dy -= 1;
    if (keys.has('arrowdown') || keys.has('s')) dy += 1;
    if (dx || dy) {
      const len = Math.hypot(dx, dy);
      p.x = clamp(p.x + (dx / len) * p.speed * dt, p.r, W - p.r);
      p.y = clamp(p.y + (dy / len) * p.speed * dt, p.r, H - p.r);
    }

    for (const rock of state.rocks) {
      rock.x += rock.vx * dt;
      rock.y += rock.vy * dt;
      rock.angle += rock.spin * dt;
    }
    state.rocks = state.rocks.filter((r) => r.x > -80 && r.x < W + 80 && r.y > -80 && r.y < H + 80);

    for (let i = state.pickups.length - 1; i >= 0; i -= 1) {
      const star = state.pickups[i];
      star.pulse += dt * 5;
      if (distance(p, star) < p.r + star.r) {
        state.pickups.splice(i, 1);
        state.score += 10;
      }
    }

    for (let i = state.rocks.length - 1; i >= 0; i -= 1) {
      const rock = state.rocks[i];
      if (distance(p, rock) < p.r + rock.r * 0.82) {
        state.rocks.splice(i, 1);
        state.lives -= 1;
        state.flash = 0.18;
        if (state.lives <= 0) endGame();
      }
    }

    if (state.timeLeft <= 0) endGame();
    updateHud();
  }

  function endGame() {
    state.over = true;
    state.running = false;
    if (state.score > state.best) {
      state.best = state.score;
      localStorage.setItem('minigme-best', String(state.best));
    }
    updateHud();
  }

  function drawBackground(dt) {
    ctx.fillStyle = '#050814';
    ctx.fillRect(0, 0, W, H);
    ctx.save();
    ctx.globalAlpha = 0.9;
    for (const s of stars) {
      s.y += s.s * dt;
      if (s.y > H) { s.y = 0; s.x = rand(0, W); }
      ctx.fillStyle = s.r > 1.6 ? '#9cecff' : '#d8f7ff';
      ctx.beginPath();
      ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2);
      ctx.fill();
    }
    ctx.restore();
  }

  function drawShip() {
    const p = state.player;
    ctx.save();
    ctx.translate(p.x, p.y);
    ctx.shadowColor = '#54d9ff';
    ctx.shadowBlur = 22;
    ctx.fillStyle = '#54d9ff';
    ctx.beginPath();
    ctx.moveTo(0, -23);
    ctx.lineTo(18, 18);
    ctx.lineTo(0, 10);
    ctx.lineTo(-18, 18);
    ctx.closePath();
    ctx.fill();
    ctx.shadowBlur = 0;
    ctx.fillStyle = '#06101d';
    ctx.beginPath();
    ctx.arc(0, -3, 6, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();
  }

  function drawPickup(star) {
    const glow = 1 + Math.sin(star.pulse) * 0.2;
    ctx.save();
    ctx.translate(star.x, star.y);
    ctx.rotate(star.pulse * 0.35);
    ctx.shadowColor = '#ffd166';
    ctx.shadowBlur = 18;
    ctx.fillStyle = '#ffd166';
    ctx.beginPath();
    for (let i = 0; i < 10; i += 1) {
      const r = (i % 2 === 0 ? star.r : star.r * 0.45) * glow;
      const a = -Math.PI / 2 + (i * Math.PI) / 5;
      ctx.lineTo(Math.cos(a) * r, Math.sin(a) * r);
    }
    ctx.closePath();
    ctx.fill();
    ctx.restore();
  }

  function drawRock(rock) {
    ctx.save();
    ctx.translate(rock.x, rock.y);
    ctx.rotate(rock.angle);
    ctx.fillStyle = '#6f7890';
    ctx.strokeStyle = '#aab4cc';
    ctx.lineWidth = 2;
    ctx.beginPath();
    for (let i = 0; i < 9; i += 1) {
      const a = (i / 9) * Math.PI * 2;
      const r = rock.r * rand(0.72, 1.05);
      ctx.lineTo(Math.cos(a) * r, Math.sin(a) * r);
    }
    ctx.closePath();
    ctx.fill();
    ctx.stroke();
    ctx.restore();
  }

  function drawOverlay(text, subtext) {
    ctx.save();
    ctx.fillStyle = 'rgba(5, 8, 20, 0.62)';
    ctx.fillRect(0, 0, W, H);
    ctx.textAlign = 'center';
    ctx.fillStyle = '#eaf4ff';
    ctx.font = '800 52px Microsoft YaHei, sans-serif';
    ctx.fillText(text, W / 2, H / 2 - 18);
    ctx.fillStyle = '#93a8c5';
    ctx.font = '22px Microsoft YaHei, sans-serif';
    ctx.fillText(subtext, W / 2, H / 2 + 30);
    ctx.restore();
  }

  function render(dt = 0) {
    drawBackground(dt);
    for (const pickup of state.pickups) drawPickup(pickup);
    for (const rock of state.rocks) drawRock(rock);
    drawShip();

    if (state.flash > 0) {
      ctx.fillStyle = `rgba(255, 107, 107, ${state.flash * 2.8})`;
      ctx.fillRect(0, 0, W, H);
    }

    if (!state.running && !state.over) drawOverlay('星尘收集者', '点击“开始游戏”起飞');
    if (state.paused) drawOverlay('已暂停', '按空格继续');
    if (state.over) drawOverlay('游戏结束', `最终分数 ${state.score} · 按 R 或点击重新开始`);
  }

  function loop(now) {
    const dt = Math.min(0.033, (now - state.lastTime) / 1000 || 0);
    state.lastTime = now;
    update(dt);
    render(dt);
    requestAnimationFrame(loop);
  }

  function canvasPoint(event) {
    const rect = canvas.getBoundingClientRect();
    const point = event.touches ? event.touches[0] : event;
    return {
      x: ((point.clientX - rect.left) / rect.width) * W,
      y: ((point.clientY - rect.top) / rect.height) * H,
    };
  }

  let dragging = false;
  function movePlayerTo(event) {
    if (!state.running || state.paused || state.over) return;
    const p = canvasPoint(event);
    state.player.x = clamp(p.x, state.player.r, W - state.player.r);
    state.player.y = clamp(p.y, state.player.r, H - state.player.r);
  }

  canvas.addEventListener('pointerdown', (event) => { dragging = true; movePlayerTo(event); });
  canvas.addEventListener('pointermove', (event) => { if (dragging) movePlayerTo(event); });
  window.addEventListener('pointerup', () => { dragging = false; });
  canvas.addEventListener('touchmove', (event) => { event.preventDefault(); movePlayerTo(event); }, { passive: false });

  window.addEventListener('keydown', (event) => {
    const key = event.key.toLowerCase();
    keys.add(key);
    if (key === ' ') {
      event.preventDefault();
      if (state.running) state.paused = !state.paused;
    }
    if (key === 'r') reset();
  });
  window.addEventListener('keyup', (event) => keys.delete(event.key.toLowerCase()));

  startButton.addEventListener('click', reset);
  restartButton.addEventListener('click', reset);

  reset();
  state.running = false;
  requestAnimationFrame(loop);
})();
