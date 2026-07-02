export const ANALYTICS_EVENTS = Object.freeze([
  'game_start',
  'game_over',
  'revive_ad_start',
  'revive_ad_reward',
  'hidden_log_ad_start',
  'hidden_log_unlock',
  'fake_ending_trigger',
  'action_click',
  'anomaly_trigger',
]);

const EVENT_SET = new Set(ANALYTICS_EVENTS);

export function createConsoleAnalyticsSink(logger = console) {
  return (event) => {
    logger.log('[analytics]', event.name, event);
  };
}

let analyticsSink = createConsoleAnalyticsSink();

export function setAnalyticsSink(sink) {
  if (typeof sink !== 'function') {
    throw new TypeError('analytics sink must be a function');
  }
  analyticsSink = sink;
}

export function resetAnalyticsSink() {
  analyticsSink = createConsoleAnalyticsSink();
}

export function trackEvent(name, payload = {}, options = {}) {
  if (!EVENT_SET.has(name)) {
    throw new Error(`Unknown analytics event: ${name}`);
  }

  const now = options.now || Date.now;
  const event = {
    name,
    ts: now(),
    ...payload,
  };

  analyticsSink(event);
  return event;
}
