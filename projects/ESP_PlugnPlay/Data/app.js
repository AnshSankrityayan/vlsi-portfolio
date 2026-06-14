// ── Sensor catalog ────────────────────────────────────────────────────────────
// Each entry defines everything needed — user only has to confirm the GPIO pin.
const CATALOG = [
  // ── Temperature & Humidity ──────────────────────────────────────────────────
  {
    name: "DHT11", category: "Temp / Humidity",
    label: "DHT11 Temp+Humidity", type: "dht11",
    desc: "Digital sensor — temp °C + humidity %",
    wiring: "VCC→3.3V · GND→GND · DATA→any digital GPIO + 10kΩ pull-up to 3.3V",
    pin: 4, pin2: -1,
    warnHigh: 35, dangerHigh: 42,
  },
  {
    name: "DHT22 / AM2302", category: "Temp / Humidity",
    label: "DHT22 Temp+Humidity", type: "dht22",
    desc: "More accurate than DHT11, same wiring",
    wiring: "VCC→3.3V · GND→GND · DATA→any digital GPIO + 10kΩ pull-up to 3.3V",
    pin: 4, pin2: -1,
    warnHigh: 35, dangerHigh: 42,
  },
  {
    name: "LM35 Temperature", category: "Temp / Humidity",
    label: "LM35 Temperature", type: "temperature",
    desc: "Analog output: 10mV/°C · use ADC pin 32-39",
    wiring: "VCC→5V · GND→GND · OUT→ADC pin 32-39",
    pin: 36,
    warnHigh: 35, dangerHigh: 42,
  },
  {
    name: "NTC Thermistor", category: "Temp / Humidity",
    label: "NTC Thermistor", type: "analog",
    desc: "Resistance drops as temperature rises",
    wiring: "3.3V→10kΩ→GPIO (ADC 32-39)→NTC→GND",
    pin: 34,
  },

  // ── Gas / Air ───────────────────────────────────────────────────────────────
  {
    name: "MQ-2 (LPG / Smoke)", category: "Gas / Air",
    label: "MQ-2 Gas", type: "gas",
    desc: "LPG, propane, methane, smoke · preheat 1 min",
    wiring: "VCC→5V · GND→GND · AO→ADC pin 32-39",
    pin: 34,
    warnHigh: 1500, dangerHigh: 3000,
  },
  {
    name: "MQ-3 (Alcohol)", category: "Gas / Air",
    label: "MQ-3 Alcohol", type: "gas",
    desc: "Ethanol / alcohol vapour detection",
    wiring: "VCC→5V · GND→GND · AO→ADC pin 32-39",
    pin: 34,
    warnHigh: 800, dangerHigh: 2000,
  },
  {
    name: "MQ-4 (Methane)", category: "Gas / Air",
    label: "MQ-4 Methane", type: "gas",
    desc: "Natural gas, methane (CH₄)",
    wiring: "VCC→5V · GND→GND · AO→ADC pin 32-39",
    pin: 34,
    warnHigh: 1000, dangerHigh: 2500,
  },
  {
    name: "MQ-5 (LPG / Natural Gas)", category: "Gas / Air",
    label: "MQ-5 LPG", type: "gas",
    desc: "LPG, natural gas",
    wiring: "VCC→5V · GND→GND · AO→ADC pin 32-39",
    pin: 34,
    warnHigh: 1000, dangerHigh: 2500,
  },
  {
    name: "MQ-7 (Carbon Monoxide)", category: "Gas / Air",
    label: "MQ-7 CO", type: "gas",
    desc: "Carbon monoxide — preheat required",
    wiring: "VCC→5V · GND→GND · AO→ADC pin 32-39",
    pin: 34,
    warnHigh: 800, dangerHigh: 2000,
  },
  {
    name: "MQ-9 (CO + Flammable Gas)", category: "Gas / Air",
    label: "MQ-9 CO/Gas", type: "gas",
    desc: "CO and combustible gas combo sensor",
    wiring: "VCC→5V · GND→GND · AO→ADC pin 32-39",
    pin: 34,
    warnHigh: 900, dangerHigh: 2200,
  },
  {
    name: "MQ-135 (Air Quality)", category: "Gas / Air",
    label: "MQ-135 Air Quality", type: "gas",
    desc: "CO₂, ammonia, benzene, smoke · general air quality",
    wiring: "VCC→5V · GND→GND · AO→ADC pin 32-39",
    pin: 34,
    warnHigh: 1000, dangerHigh: 2500,
  },

  // ── Distance ─────────────────────────────────────────────────────────────────
  {
    name: "HC-SR04 Ultrasonic", category: "Distance",
    label: "Distance", type: "ultrasonic",
    desc: "2–400 cm range · needs TRIG + ECHO pins",
    wiring: "VCC→5V · GND→GND · TRIG→digital GPIO · ECHO→digital GPIO (add 1kΩ+2kΩ divider for 3.3V)",
    pin: 5, pin2: 18,
    warnHigh: 50, dangerHigh: 10,
  },

  // ── Light ────────────────────────────────────────────────────────────────────
  {
    name: "LDR (Light Dependent Resistor)", category: "Light",
    label: "LDR Light", type: "ldr",
    desc: "Analog light level 0-100%",
    wiring: "3.3V→LDR→GPIO (ADC 32-39)→10kΩ→GND",
    pin: 35,
  },
  {
    name: "BH1750 Light Sensor", category: "Light",
    label: "BH1750 Lux", type: "analog",
    desc: "I²C digital lux sensor (SDA=21, SCL=22) — add I²C support separately",
    wiring: "VCC→3.3V · GND→GND · SDA→GPIO 21 · SCL→GPIO 22 · ADDR→GND",
    pin: 21,
  },

  // ── Soil / Water ──────────────────────────────────────────────────────────────
  {
    name: "Capacitive Soil Moisture", category: "Soil / Water",
    label: "Soil Moisture", type: "soil",
    desc: "Capacitive (no corrosion) · 0-100% output",
    wiring: "VCC→3.3V · GND→GND · AOUT→ADC pin 32-39",
    pin: 32,
    warnLow: 30, dangerLow: 15,
  },
  {
    name: "Resistive Soil Moisture", category: "Soil / Water",
    label: "Soil Moisture", type: "soil",
    desc: "Basic resistive probe · corrodes over time",
    wiring: "VCC→3.3V · GND→GND · AO→ADC pin 32-39",
    pin: 32,
    warnLow: 30, dangerLow: 15,
  },
  {
    name: "Water Level Sensor", category: "Soil / Water",
    label: "Water Level", type: "analog",
    desc: "Analog depth/level 0-4095 raw",
    wiring: "VCC→5V · GND→GND · S→ADC pin 32-39",
    pin: 33,
    warnHigh: 3500, dangerHigh: 4000,
  },
  {
    name: "Rain / Raindrops Sensor", category: "Soil / Water",
    label: "Rain Sensor", type: "analog",
    desc: "Analog: high = more rain, DO = threshold output",
    wiring: "VCC→5V · GND→GND · AO→ADC pin 32-39",
    pin: 35,
    warnHigh: 2000, dangerHigh: 3500,
  },

  // ── Motion / Presence ─────────────────────────────────────────────────────────
  {
    name: "PIR HC-SR501 (Motion)", category: "Motion / Presence",
    label: "PIR Motion", type: "pir",
    desc: "Digital HIGH when motion detected",
    wiring: "VCC→5V · GND→GND · OUT→any digital GPIO",
    pin: 13,
  },
  {
    name: "IR Obstacle Sensor", category: "Motion / Presence",
    label: "IR Obstacle", type: "digital",
    desc: "LOW = obstacle detected in front",
    wiring: "VCC→3.3V · GND→GND · OUT→any digital GPIO",
    pin: 14,
  },
  {
    name: "TTP223 Touch Sensor", category: "Motion / Presence",
    label: "Touch", type: "digital",
    desc: "HIGH when touched",
    wiring: "VCC→3.3V · GND→GND · SIG→any digital GPIO",
    pin: 15,
  },

  // ── Sound ─────────────────────────────────────────────────────────────────────
  {
    name: "Sound Sensor KY-037", category: "Sound",
    label: "Sound Level", type: "analog",
    desc: "Analog microphone output — louder = higher raw value",
    wiring: "VCC→5V · GND→GND · AO→ADC pin 32-39",
    pin: 34,
    warnHigh: 2500, dangerHigh: 3800,
  },

  // ── Voltage / Current ─────────────────────────────────────────────────────────
  {
    name: "Voltage Divider Monitor", category: "Electrical",
    label: "Voltage", type: "analog",
    desc: "Use R1/R2 divider to scale down to 3.3V max",
    wiring: "V_in → R1 → GPIO (ADC 32-39) → R2 → GND",
    pin: 39,
  },
  {
    name: "ACS712 Current Sensor", category: "Electrical",
    label: "Current (A)", type: "analog",
    desc: "Analog Hall-effect current sensor · 5A/20A/30A variants",
    wiring: "VCC→5V · GND→GND · OUT→ADC pin 32-39",
    pin: 36,
  },

  // ── Output ────────────────────────────────────────────────────────────────────
  {
    name: "Relay Module", category: "Output",
    label: "Relay", type: "relay",
    desc: "Toggle switch via dashboard · IN is active LOW",
    wiring: "VCC→5V · GND→GND · IN→any digital GPIO",
    pin: 26,
  },
];

// ── State ─────────────────────────────────────────────────────────────────────
const state = {
  ws: null,
  reconnectTimer: null,
  config: { sensors: [] },
  latest: new Map(),
  history: new Map(),
  dark: localStorage.getItem("theme") === "dark",
};

// ── DOM refs ──────────────────────────────────────────────────────────────────
const el = {
  connBadge:   document.querySelector("#connBadge"),
  dashboard:   document.querySelector("#dashboard"),
  emptyPanel:  document.querySelector("#emptyPanel"),
  setupPanel:  document.querySelector("#setupPanel"),
  pinMapPanel: document.querySelector("#pinMapPanel"),
  pinMapGrid:  document.querySelector("#pinMapGrid"),
  configList:  document.querySelector("#configList"),
  rowTpl:      document.querySelector("#sensorRowTpl"),
  statIp:      document.querySelector("#statIp"),
  statUptime:  document.querySelector("#statUptime"),
  statHeap:    document.querySelector("#statHeap"),
  statClients: document.querySelector("#statClients"),
  i2cHint:     document.querySelector("#i2cHint"),
  themeBtn:    document.querySelector("#themeBtn"),
};

// ── Init theme ────────────────────────────────────────────────────────────────
applyTheme(state.dark);

function applyTheme(dark) {
  document.body.classList.toggle("dark", dark);
  el.themeBtn.textContent = dark ? "Light mode" : "Dark mode";
}

// ── Button wiring ──────────────────────────────────────────────────────────────
el.themeBtn.addEventListener("click", () => {
  state.dark = !state.dark;
  localStorage.setItem("theme", state.dark ? "dark" : "light");
  applyTheme(state.dark);
  redrawCharts();
});

document.querySelector("#setupBtn").addEventListener("click", openSetup);
document.querySelector("#emptySetupBtn").addEventListener("click", openSetup);

document.querySelector("#addBtn").addEventListener("click", () => {
  state.config.sensors.push(blankSensor());
  renderConfig();
});

document.querySelector("#saveBtn").addEventListener("click", saveConfig);

document.querySelector("#libraryBtn").addEventListener("click", () => {
  const panel = document.querySelector("#libraryPanel");
  panel.classList.toggle("hidden");
  if (!panel.classList.contains("hidden")) renderLibrary(CATALOG);
});

document.querySelector("#libraryClose").addEventListener("click", () =>
  document.querySelector("#libraryPanel").classList.add("hidden")
);

document.querySelector("#librarySearch").addEventListener("input", (e) => {
  const q = e.target.value.toLowerCase();
  renderLibrary(CATALOG.filter(s =>
    s.name.toLowerCase().includes(q) ||
    s.category.toLowerCase().includes(q) ||
    s.desc.toLowerCase().includes(q)
  ));
});

document.querySelector("#clearLogBtn").addEventListener("click", () =>
  send({ type: "clear_log" })
);

document.querySelector("#i2cBtn").addEventListener("click", () => {
  el.i2cHint.textContent = "Scanning I²C bus (SDA=GPIO 21, SCL=GPIO 22)…";
  send({ type: "i2c_scan" });
});

document.querySelector("#probeBtn").addEventListener("click", () => {
  document.querySelector("#probePanel").classList.remove("hidden");
  document.querySelector("#probeGrid").innerHTML =
    '<span style="font-size:0.8rem;color:var(--muted)">Reading all pins…</span>';
  send({ type: "pin_probe" });
});

function openSetup() {
  el.setupPanel.classList.remove("hidden");
  el.setupPanel.scrollIntoView({ behavior: "smooth", block: "start" });
}

// ── WebSocket ─────────────────────────────────────────────────────────────────
function connect() {
  const proto = location.protocol === "https:" ? "wss" : "ws";
  state.ws = new WebSocket(`${proto}://${location.host}/ws`);

  state.ws.onopen = () => {
    el.connBadge.textContent = "Live";
    el.connBadge.className = "badge badge-online";
    send({ type: "get_config" });
  };

  state.ws.onmessage = ({ data }) => {
    try {
      handleMessage(JSON.parse(data));
    } catch {}
  };

  state.ws.onclose = () => {
    el.connBadge.textContent = "Offline";
    el.connBadge.className = "badge badge-offline";
    clearTimeout(state.reconnectTimer);
    state.reconnectTimer = setTimeout(connect, 1500);
  };

  state.ws.onerror = () => state.ws.close();
}

function send(payload) {
  if (state.ws?.readyState === WebSocket.OPEN)
    state.ws.send(JSON.stringify(payload));
}

function handleMessage(msg) {
  if (msg.type === "config") {
    state.config = msg.config || { sensors: [] };
    renderConfig();
    renderDashboard();
  } else if (msg.type === "sensor_update") {
    updateReadings(msg.sensors || []);
  } else if (msg.type === "device") {
    updateDevice(msg);
  } else if (msg.type === "i2c_scan") {
    renderI2cResults(msg.devices || []);
  } else if (msg.type === "pin_probe") {
    renderProbeResults(msg.pins || []);
  }
}

// ── Sensor library ────────────────────────────────────────────────────────────
function renderLibrary(entries) {
  const catalog = document.querySelector("#libraryCatalog");

  if (!entries.length) {
    catalog.innerHTML = '<p style="font-size:0.82rem;color:var(--muted)">No sensors match that search.</p>';
    return;
  }

  // Group by category
  const groups = {};
  entries.forEach(s => {
    if (!groups[s.category]) groups[s.category] = [];
    groups[s.category].push(s);
  });

  catalog.innerHTML = Object.entries(groups).map(([cat, sensors]) => `
    <div>
      <div class="lib-category-title">${esc(cat)}</div>
      <div class="lib-category-grid">
        ${sensors.map((s, i) => `
          <div class="lib-card" data-catalog-name="${esc(s.name)}">
            <span class="lib-card-name">${esc(s.name)}</span>
            <span class="lib-card-desc">${esc(s.desc)}</span>
            <span class="lib-card-type">${esc(s.type)}${s.pin2 >= 0 ? ` · trig+echo` : ''}</span>
          </div>
        `).join("")}
      </div>
    </div>
  `).join("");

  catalog.querySelectorAll(".lib-card").forEach(card => {
    card.addEventListener("click", () => {
      const entry = CATALOG.find(s => s.name === card.dataset.catalogName);
      if (entry) addFromCatalog(entry);
    });
  });
}

function addFromCatalog(entry) {
  state.config.sensors.push({
    id:          `s_${Date.now().toString(36)}`,
    label:       entry.label,
    type:        entry.type,
    pin:         entry.pin  ?? 34,
    pin2:        entry.pin2 ?? -1,
    enabled:     true,
    warnLow:     entry.warnLow    ?? null,
    warnHigh:    entry.warnHigh   ?? null,
    dangerLow:   entry.dangerLow  ?? null,
    dangerHigh:  entry.dangerHigh ?? null,
  });
  renderConfig();

  // Close library and scroll to the new row with wiring hint
  document.querySelector("#libraryPanel").classList.add("hidden");
  el.i2cHint.innerHTML =
    `<strong>${esc(entry.name)}</strong> added — wiring: ${esc(entry.wiring)}`;
  el.configList.lastElementChild?.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

// ── Config ────────────────────────────────────────────────────────────────────
function blankSensor() {
  return {
    id: `s_${Date.now().toString(36)}`,
    label: "New Sensor",
    type: "soil",
    pin: 34,
    pin2: -1,
    enabled: true,
    warnHigh: 80,
    dangerHigh: 95,
  };
}

function renderConfig() {
  el.configList.innerHTML = "";
  (state.config.sensors || []).forEach((sensor, index) => {
    const row = el.rowTpl.content.firstElementChild.cloneNode(true);

    row.querySelector(".s-label").value      = sensor.label  ?? "";
    row.querySelector(".s-type").value       = sensor.type   ?? "analog";
    row.querySelector(".s-pin").value        = sensor.pin    ?? "";
    row.querySelector(".s-pin2").value       = sensor.pin2 >= 0 ? sensor.pin2 : "";
    row.querySelector(".s-warn-high").value  = sensor.warnHigh   ?? "";
    row.querySelector(".s-danger-high").value= sensor.dangerHigh ?? "";
    row.querySelector(".s-enabled").checked  = sensor.enabled !== false;

    const typeSelect  = row.querySelector(".s-type");
    const echoField   = row.querySelector(".s-echo-field");
    const syncEcho    = () => {
      echoField.style.display = typeSelect.value === "ultrasonic" ? "" : "none";
    };
    syncEcho();
    typeSelect.addEventListener("change", syncEcho);

    row.querySelector(".s-remove").addEventListener("click", () => {
      state.config.sensors.splice(index, 1);
      renderConfig();
      renderDashboard();
    });

    el.configList.append(row);
  });
}

function saveConfig() {
  const rows = [...el.configList.querySelectorAll(".config-row")];
  state.config.sensors = rows.map((row, i) => {
    const old  = state.config.sensors[i] || {};
    const pin2 = parseInt(row.querySelector(".s-pin2").value, 10);
    return {
      id:          old.id || `s_${i}_${Date.now().toString(36)}`,
      label:       row.querySelector(".s-label").value || "Sensor",
      type:        row.querySelector(".s-type").value,
      pin:         toNum(row.querySelector(".s-pin").value, 34),
      pin2:        Number.isFinite(pin2) && pin2 >= 0 ? pin2 : -1,
      warnHigh:    toNumOrNull(row.querySelector(".s-warn-high").value),
      dangerHigh:  toNumOrNull(row.querySelector(".s-danger-high").value),
      enabled:     row.querySelector(".s-enabled").checked,
    };
  });
  send({ type: "save_config", config: state.config });
  renderDashboard();
}

// ── Dashboard ─────────────────────────────────────────────────────────────────
function renderDashboard() {
  el.dashboard.innerHTML = "";
  const sensors = (state.config.sensors || []).filter(s => s.enabled !== false);

  el.emptyPanel.classList.toggle("hidden", sensors.length > 0);
  renderPinMap(sensors);

  sensors.forEach(sensor => {
    const card = document.createElement("article");
    card.className = "sensor-card s-offline";
    card.dataset.id = sensor.id;

    const isDual  = sensor.type === "dht11" || sensor.type === "dht22";
    const isRelay = sensor.type === "relay";
    const pinInfo = sensor.type === "ultrasonic"
      ? `GPIO ${sensor.pin} (trig) / ${sensor.pin2} (echo)`
      : `GPIO ${sensor.pin}`;

    card.innerHTML = `
      <div class="card-header">
        <div>
          <div class="card-title">${esc(sensor.label)}</div>
          <div class="card-subtitle">${esc(sensor.type)} · ${pinInfo}</div>
        </div>
        <span class="status-pill sp-offline">offline</span>
      </div>
      <div class="card-value">
        <span class="val-primary">—</span>
        <span class="val-unit"></span>
      </div>
      ${isDual ? '<div class="val-secondary"></div>' : ''}
      <div class="card-analysis">Waiting for data…</div>
      <canvas class="sparkline" aria-hidden="true"></canvas>
    `;

    if (isRelay) {
      const btn = document.createElement("button");
      btn.className = "btn-ghost relay-btn";
      btn.textContent = "Toggle relay";
      btn.addEventListener("click", () => {
        const on = (state.latest.get(sensor.id)?.value ?? 0) > 0.5;
        send({ type: "relay", id: sensor.id, state: !on });
      });
      card.append(btn);
    }

    el.dashboard.append(card);
  });
}

function renderPinMap(sensors) {
  el.pinMapPanel.classList.toggle("hidden", sensors.length === 0);
  el.pinMapGrid.innerHTML = sensors.map(s => {
    const pin = s.type === "ultrasonic" ? `${s.pin}/${s.pin2}` : `${s.pin}`;
    return `<div class="pin-chip">
      <span class="gpio-tag">GPIO ${esc(pin)}</span>
      <span class="chip-name">${esc(s.label)}</span>
      <span class="chip-type">${esc(s.type)}</span>
    </div>`;
  }).join("");
}

function renderProbeResults(pins) {
  const grid = document.querySelector("#probeGrid");
  if (!pins.length) {
    grid.textContent = "No pins returned.";
    return;
  }

  // Sort: active pins first, then by pin number
  pins.sort((a, b) => (b.active - a.active) || (a.pin - b.pin));

  grid.innerHTML = pins.map(p => {
    const isAnalog = p.mode === "analog";
    const pct      = isAnalog ? Math.round((p.analog / 4095) * 100) : null;
    const barWidth = isAnalog ? pct : (p.digital ? 100 : 0);

    return `<div class="probe-pin${p.active ? " active" : ""}">
      <span class="p-label">GPIO ${p.pin}</span>
      <span class="p-analog">${isAnalog ? `${p.analog} raw (${pct}%)` : (p.digital ? "HIGH" : "LOW")}</span>
      <div style="height:4px;border-radius:2px;background:var(--border);overflow:hidden">
        <div style="height:100%;width:${barWidth}%;background:${p.active ? "var(--ok)" : "var(--muted)"};transition:width 0.3s"></div>
      </div>
      <span class="p-meta">${isAnalog ? `${p.mode} · Δ${p.range}` : p.mode}${p.active ? " · ACTIVE" : ""}</span>
    </div>`;
  }).join("");
}

function renderI2cResults(devices) {
  if (!devices.length) {
    el.i2cHint.textContent = "No I²C devices found on SDA GPIO 21 / SCL GPIO 22.";
    return;
  }
  el.i2cHint.innerHTML = "Found: " + devices.map(d =>
    `<strong>${esc(d.address)}</strong> ${esc(d.hint || "")}`
  ).join(" &nbsp;·&nbsp; ");
}

// ── Live readings ─────────────────────────────────────────────────────────────
function updateReadings(readings) {
  readings.forEach(r => {
    state.latest.set(r.id, r);

    const hist = state.history.get(r.id) || [];
    const v = Number(r.value);
    if (Number.isFinite(v)) {
      hist.push(v);
      if (hist.length > 72) hist.shift();
    }
    state.history.set(r.id, hist);

    const card = el.dashboard.querySelector(`[data-id="${CSS.escape(r.id)}"]`);
    if (!card) return;

    const status = r.status || "offline";
    card.className = `sensor-card s-${status}`;

    const pill = card.querySelector(".status-pill");
    pill.className = `status-pill sp-${status}`;
    pill.textContent = status;

    card.querySelector(".val-primary").textContent = fmtVal(r.value);
    card.querySelector(".val-unit").textContent = r.unit || "";
    card.querySelector(".card-analysis").textContent = r.analysis || "";

    const secondary = card.querySelector(".val-secondary");
    if (secondary) {
      secondary.textContent = r.value2 != null
        ? `${fmtVal(r.value2)} ${r.unit2 || ""}`.trim()
        : "";
    }

    drawSparkline(card.querySelector("canvas.sparkline"), hist, status);
  });
}

function updateDevice(info) {
  el.statIp.textContent      = info.ip || "—";
  el.statUptime.textContent  = fmtUptime(info.uptimeMs || 0);
  el.statHeap.textContent    = `${Math.round((info.freeHeap || 0) / 1024)} KB`;
  el.statClients.textContent = info.clients ?? "—";
}

// ── Sparkline chart ───────────────────────────────────────────────────────────
function drawSparkline(canvas, values, status = "ok") {
  if (!canvas) return;

  const dpr = devicePixelRatio || 1;
  const W   = canvas.clientWidth  * dpr || 300 * dpr;
  const H   = canvas.clientHeight * dpr || 60  * dpr;

  if (canvas.width !== W || canvas.height !== H) {
    canvas.width  = W;
    canvas.height = H;
  }

  const ctx = canvas.getContext("2d");
  ctx.clearRect(0, 0, W, H);

  const style     = getComputedStyle(document.documentElement);
  const gridColor = style.getPropertyValue("--border").trim();

  const colorVar = { ok: "--ok", warning: "--warn", danger: "--danger", offline: "--offline" };
  const lineColor = style.getPropertyValue(colorVar[status] || "--brand").trim();

  // Grid lines
  ctx.strokeStyle = gridColor;
  ctx.lineWidth   = dpr;
  for (let i = 1; i < 3; i++) {
    const y = (H / 3) * i;
    ctx.beginPath();
    ctx.moveTo(0, y);
    ctx.lineTo(W, y);
    ctx.stroke();
  }

  if (values.length < 2) return;

  const min   = Math.min(...values);
  const max   = Math.max(...values);
  const range = Math.max(0.001, max - min);
  const pad   = H * 0.12;

  ctx.strokeStyle = lineColor;
  ctx.lineWidth   = 2 * dpr;
  ctx.lineJoin    = "round";
  ctx.lineCap     = "round";
  ctx.beginPath();
  values.forEach((v, i) => {
    const x = (i / (values.length - 1)) * W;
    const y = H - pad - ((v - min) / range) * (H - pad * 2);
    i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
  });
  ctx.stroke();
}

function redrawCharts() {
  document.querySelectorAll(".sensor-card").forEach(card => {
    const id = card.dataset.id;
    const r  = state.latest.get(id) || {};
    drawSparkline(card.querySelector("canvas.sparkline"), state.history.get(id) || [], r.status);
  });
}

// ── Helpers ───────────────────────────────────────────────────────────────────
function fmtVal(v) {
  const n = Number(v);
  if (!Number.isFinite(n)) return "—";
  return n >= 1000 ? n.toFixed(0) : n >= 100 ? n.toFixed(0) : n.toFixed(1);
}

function fmtUptime(ms) {
  const s   = Math.floor(ms / 1000);
  const h   = Math.floor(s / 3600);
  const m   = Math.floor((s % 3600) / 60);
  const sec = s % 60;
  if (h > 0)  return `${h}h ${m}m`;
  if (m > 0)  return `${m}m ${sec}s`;
  return `${sec}s`;
}

function toNum(v, fallback) {
  const n = Number(v);
  return Number.isFinite(n) ? n : fallback;
}

function toNumOrNull(v) {
  const n = Number(v);
  return Number.isFinite(n) ? n : null;
}

function esc(v) {
  return String(v).replace(/[&<>"']/g, c => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;",
  }[c]));
}

// ── Start ─────────────────────────────────────────────────────────────────────
connect();
