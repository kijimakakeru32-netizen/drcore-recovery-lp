const JST_OFFSET = 9 * 60 * 60 * 1000;
const CURRENT_CAMPAIGN_DEADLINE = {
  text: '10/31まで',
  isoDate: '2026-10-31',
  rollover: Date.UTC(2026, 9, 31, 22) - JST_OFFSET,
};

// Advance the displayed deadline at 22:00 JST on the last day of each month.
export function getCampaignDeadline(now = new Date()) {
  if (now.getTime() < CURRENT_CAMPAIGN_DEADLINE.rollover) {
    return {
      text: CURRENT_CAMPAIGN_DEADLINE.text,
      isoDate: CURRENT_CAMPAIGN_DEADLINE.isoDate,
    };
  }
  const japan = new Date(now.getTime() + JST_OFFSET);
  const year = japan.getUTCFullYear();
  const month = japan.getUTCMonth();
  const lastDay = new Date(Date.UTC(year, month + 1, 0)).getUTCDate();
  const rollover = Date.UTC(year, month, lastDay, 22) - JST_OFFSET;
  const deadline = new Date(Date.UTC(year, month + (now.getTime() >= rollover ? 2 : 1), 0));
  return {
    text: `${deadline.getUTCMonth() + 1}/${deadline.getUTCDate()}まで`,
    isoDate: deadline.toISOString().slice(0, 10),
  };
}

if (typeof document !== 'undefined') {
  const elements = document.querySelectorAll('[data-campaign-deadline]');
  if (elements.length) {
    const update = () => {
      const deadline = getCampaignDeadline();
      elements.forEach(element => {
        element.textContent = deadline.text;
        element.dateTime = deadline.isoDate;
      });
    };
    update();
    setInterval(update, 60_000);
    window.addEventListener('pageshow', update);
    document.addEventListener('visibilitychange', () => {
      if (!document.hidden) update();
    });
  }
}
