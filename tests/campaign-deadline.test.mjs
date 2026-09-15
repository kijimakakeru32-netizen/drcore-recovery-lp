import test from 'node:test';
import assert from 'node:assert/strict';
import {getCampaignDeadline} from '../dist/assets/campaign-deadline.mjs';

const cases = [
  ['September start', '2026-09-01T00:00:00+09:00', '9/30まで', '2026-09-30'],
  ['just before September cutoff', '2026-09-30T21:59:59.999+09:00', '9/30まで', '2026-09-30'],
  ['September cutoff', '2026-09-30T22:00:00+09:00', '10/31まで', '2026-10-31'],
  ['October start keeps October deadline', '2026-10-01T00:00:00+09:00', '10/31まで', '2026-10-31'],
  ['31-day month cutoff', '2026-10-31T22:00:00+09:00', '11/30まで', '2026-11-30'],
  ['year rollover', '2026-12-31T22:00:00+09:00', '1/31まで', '2027-01-31'],
  ['February in a regular year', '2027-02-28T21:59:59+09:00', '2/28まで', '2027-02-28'],
  ['February cutoff', '2027-02-28T22:00:00+09:00', '3/31まで', '2027-03-31'],
  ['leap February is not over on the 28th', '2028-02-28T22:00:00+09:00', '2/29まで', '2028-02-29'],
  ['leap day cutoff', '2028-02-29T22:00:00+09:00', '3/31まで', '2028-03-31'],
  ['same cutoff from a different time zone', '2026-09-30T06:00:00-07:00', '10/31まで', '2026-10-31'],
];

for (const [name, instant, text, isoDate] of cases) {
  test(name, () => assert.deepEqual(getCampaignDeadline(new Date(instant)), {text, isoDate}));
}
