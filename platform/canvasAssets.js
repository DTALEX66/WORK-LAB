const CCTV_STATE_IDS = Object.freeze([
  '00_idle_closed', '01_door_open', '02_door_opening', '03_door_closing',
  '04_moving_up', '05_moving_down', '06_power_low', '07_power_outage',
  '08_emergency_stop', '09_door_jammed', '10_signal_lost', '11_camera_glitch',
  '12_scan_active', '13_entity_near', '14_shadow_inside', '15_anomaly_wandering',
  '16_wrong_floor', '17_loop_corridor', '18_locked', '19_stabilized',
  '20_threat_high', '21_maintenance_mode', '22_system_reboot', '23_cooldown_safe',
]);

const BUTTON_ASSETS = Object.freeze({
  default: 'visual/buttons/btn_close_default.png',
  recommended: 'visual/buttons/btn_up_recommended.png',
  danger: 'visual/buttons/btn_stop_danger.png',
  disabled: 'visual/buttons/btn_disabled.png',
  inspectLog: 'visual/buttons/btn_log_secondary.png',
  unlockHiddenLog: 'visual/buttons/btn_scan_default.png',
  pressed: 'visual/buttons/btn_pressed.png',
  more: 'visual/buttons/btn_more_secondary.png',
});

const OVERLAY_ASSETS = Object.freeze({
  frame: 'visual/overlays/overlay_cctv_frame.png',
  scanlines: 'visual/overlays/overlay_scanlines.png',
  vignette: 'visual/overlays/overlay_vignette.png',
  redAlert: 'visual/overlays/overlay_red_alert_frame.png',
  glitch: 'visual/overlays/overlay_glitch_blocks.png',
  sweep: 'visual/overlays/overlay_scan_sweep.png',
});

export function getCanvasVisualAssetManifest() {
  return {
    cctv: Object.fromEntries(CCTV_STATE_IDS.map(id => [id, `visual/cctv/${id}_mobile.png`])),
    buttons: { ...BUTTON_ASSETS },
    overlays: { ...OVERLAY_ASSETS },
  };
}

export function createCanvasAssetStore(imageFactory) {
  const manifest = getCanvasVisualAssetManifest();
  const records = new Map();

  function load(path) {
    if (!path || records.has(path) || typeof imageFactory !== 'function') return;
    const record = { image: null, loaded: false, failed: false };
    records.set(path, record);
    try {
      const image = imageFactory();
      if (!image) {
        record.failed = true;
        return;
      }
      record.image = image;
      image.onload = () => { record.loaded = true; };
      image.onerror = () => { record.failed = true; };
      image.src = path;
    } catch {
      record.failed = true;
    }
  }

  function preload() {
    for (const path of Object.values(manifest.cctv)) load(path);
    for (const path of Object.values(manifest.buttons)) load(path);
    for (const path of Object.values(manifest.overlays)) load(path);
  }

  function get(path) {
    const record = records.get(path);
    return record?.loaded ? record.image : null;
  }

  return {
    manifest,
    preload,
    getCctv: stateId => get(manifest.cctv[stateId] || manifest.cctv['00_idle_closed']),
    getButton: kind => get(manifest.buttons[kind] || manifest.buttons.default),
    getOverlay: kind => get(manifest.overlays[kind]),
    getStatus: () => ({
      total: records.size,
      loaded: [...records.values()].filter(record => record.loaded).length,
      failed: [...records.values()].filter(record => record.failed).length,
    }),
  };
}
