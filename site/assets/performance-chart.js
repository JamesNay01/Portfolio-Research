/**
 * Performance chart — pure math, no DOM.
 * Kept separate from rendering (in performance.html's inline script) so
 * the filtering/rebasing logic can be unit-tested directly, the same
 * pattern as engine/valuation.js.
 */
(function (root, factory) {
  const mod = factory();
  if (typeof module === "object" && module.exports) module.exports = mod;
  if (typeof root !== "undefined") root.PerformanceChart = mod;
})(typeof window !== "undefined" ? window : globalThis, function () {
  "use strict";

  const RANGE_MONTHS = { "3m": 3, "6m": 6, "1y": 12, "2y": 24, "all": Infinity };

  /**
   * Rebases a series of % returns (relative to some earlier baseline) so
   * that the FIRST element of the given slice becomes 0%, preserving the
   * true compounded shape of the line within that window. Converting to
   * a growth factor first (rather than just subtracting) is what makes
   * this correct — percentages don't subtract linearly.
   */
  function rebase(pctReturns) {
    if (!pctReturns.length) return [];
    const baseFactor = 1 + pctReturns[0] / 100;
    return pctReturns.map((p) => {
      const factor = 1 + p / 100;
      return round2((factor / baseFactor - 1) * 100);
    });
  }

  function round2(v) {
    return Math.round(v * 100) / 100;
  }

  /**
   * Slices dates/portfolioReturns/benchmarkReturns to the requested
   * range (counting back from the last point) and rebases both series
   * to 0% at the start of that window.
   */
  function filterRange(dates, portfolioReturns, benchmarkReturns, rangeKey) {
    const months = RANGE_MONTHS[rangeKey] ?? Infinity;
    const n = dates.length;
    const start = months === Infinity ? 0 : Math.max(0, n - months);
    const slicedDates = dates.slice(start);
    return {
      dates: slicedDates,
      portfolio: rebase(portfolioReturns.slice(start)),
      benchmark: rebase(benchmarkReturns.slice(start)),
      resolution: "monthly",
    };
  }

  /** Given a mouse x-position as a 0..1 fraction of the plot width, finds the nearest data index. */
  function nearestIndex(fracX, n) {
    if (n <= 1) return 0;
    return Math.min(n - 1, Math.max(0, Math.round(fracX * (n - 1))));
  }

  return { RANGE_MONTHS, rebase, filterRange, nearestIndex };
});
