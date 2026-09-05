import { useEffect, useMemo, useState } from "react";
import {
  getAttention,
  getLastSeen,
  getQuotes,
  getScenarios,
  markChecked,
  selectScenario,
  type AttentionResponse,
  type DemoScenario,
  type MarketQuote,
} from "./api/client";
import {
  addItem,
  createWatchlist,
  getWatchlist,
  listWatchlists,
  removeItem,
  reorderItems,
  searchInstruments,
  type Instrument,
  type Watchlist,
} from "./api/watchlists";
import "./styles.css";

const WATCHLIST = [
  "RELIANCE",
  "TCS",
  "INFY",
  "HDFCBANK",
  "ICICIBANK",
  "SBIN",
  "ITC",
  "LT",
  "WIPRO",
  "HCLTECH",
];

const COMPANY_NAMES: Record<string, string> = {
  RELIANCE: "Reliance Industries",
  TCS: "Tata Consultancy Services",
  INFY: "Infosys",
  HDFCBANK: "HDFC Bank",
  ICICIBANK: "ICICI Bank",
  SBIN: "State Bank of India",
  ITC: "ITC Limited",
  LT: "Larsen & Toubro",
  WIPRO: "Wipro",
  HCLTECH: "HCL Technologies",
};

function formatPrice(value: number) {
  return `₹${value.toLocaleString("en-IN", {
    maximumFractionDigits: 2,
  })}`;
}

function formatPercent(value: number) {
  return `${value >= 0 ? "+" : ""}${value.toFixed(2)}%`;
}

function attentionLabel(level: AttentionResponse["level"]) {
  switch (level) {
    case "high":
      return "High attention";
    case "moderate":
      return "Worth a look";
    case "low":
      return "Small change";
    default:
      return "No major change";
  }
}

function attentionClass(level: AttentionResponse["level"]) {
  return `attention-${level}`;
}

function dataStatusLabel(status: string) {
  return status.charAt(0).toUpperCase() + status.slice(1).toLowerCase();
}

function App() {
  const [quotes, setQuotes] = useState<MarketQuote[]>([]);
  const [attention, setAttention] = useState<AttentionResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [checkStatus, setCheckStatus] = useState<string | null>(null);
  const [selectedSymbol, setSelectedSymbol] = useState<string | null>(null);
  const [scenarios, setScenarios] = useState<DemoScenario[]>([]);
  const [selectedScenario, setSelectedScenario] = useState("NORMAL_DAY");
  const [watchlist, setWatchlist] = useState<Watchlist | null>(null);
  const [instrumentQuery, setInstrumentQuery] = useState("");
  const [instrumentMatches, setInstrumentMatches] = useState<Instrument[]>([]);
  const [watchlistBusy, setWatchlistBusy] = useState(false);

  async function loadDashboard(symbols = WATCHLIST) {
    const requestedSymbols = symbols.length > 0 ? symbols : WATCHLIST;

    try {
      setLoading(true);
      setError(null);
      setCheckStatus(null);

      const [, quoteData, attentionData] = await Promise.all([
        getLastSeen(),
        getQuotes(requestedSymbols),
        getAttention(requestedSymbols),
      ]);

      setQuotes(quoteData);
      setAttention(attentionData);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to load market information.",
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void loadDashboard();
    }, 0);

    return () => window.clearTimeout(timer);
  }, []);

  useEffect(() => {
    void listWatchlists()
      .then(async (watchlists) => {
        if (watchlists[0]) {
          setWatchlist(await getWatchlist(watchlists[0].id));
        }
      })
      .catch(() =>
        setCheckStatus("Your saved watchlist is unavailable right now."),
      );
  }, []);

  useEffect(() => {
    void getScenarios()
      .then(setScenarios)
      .catch(() =>
        setCheckStatus("Demo scenarios are unavailable right now."),
      );
  }, []);

  async function handleScenarioChange(scenario: string) {
    try {
      setLoading(true);
      setError(null);
      await selectScenario(scenario);
      setSelectedScenario(scenario);

      await loadDashboard(
        watchlist && watchlist.items.length > 0
          ? watchlist.items.map((item) => item.instrument.symbol)
          : WATCHLIST,
      );
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to select the demo scenario.",
      );
      setLoading(false);
    }
  }

  async function createSavedWatchlist() {
    try {
      setWatchlistBusy(true);
      const created = await createWatchlist("My Watchlist");
      setWatchlist(created);
      setCheckStatus("Saved watchlist created. Search to add companies.");
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Unable to create watchlist.",
      );
    } finally {
      setWatchlistBusy(false);
    }
  }

  async function handleInstrumentSearch(query: string) {
    setInstrumentQuery(query);

    if (query.trim().length < 1) {
      setInstrumentMatches([]);
      return;
    }

    try {
      setInstrumentMatches(await searchInstruments(query));
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to search instruments.",
      );
    }
  }

  async function updateWatchlist(operation: () => Promise<unknown>) {
    if (!watchlist) return;

    try {
      setWatchlistBusy(true);
      await operation();

      const refreshed = await getWatchlist(watchlist.id);
      setWatchlist(refreshed);
      setInstrumentMatches([]);
      setInstrumentQuery("");

      await loadDashboard(
        refreshed.items.map((item) => item.instrument.symbol),
      );
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Unable to update watchlist.",
      );
    } finally {
      setWatchlistBusy(false);
    }
  }

  const attentionBySymbol = useMemo(
    () => new Map(attention.map((item) => [item.symbol, item])),
    [attention],
  );

  const quoteBySymbol = useMemo(
    () => new Map(quotes.map((item) => [item.symbol, item])),
    [quotes],
  );

  const displayedSymbols = watchlist
    ? watchlist.items.map((item) => item.instrument.symbol)
    : WATCHLIST;

  const meaningfulChanges = attention
    .filter(
      (item) => item.level === "high" || item.level === "moderate",
    )
    .sort((a, b) => b.score - a.score);

  const newMeaningfulChanges = meaningfulChanges.filter(
    (item) => item.isNew,
  );

  const selectedQuote = selectedSymbol
    ? quoteBySymbol.get(selectedSymbol)
    : undefined;

  const selectedAttention = selectedSymbol
    ? attentionBySymbol.get(selectedSymbol)
    : undefined;

  if (loading) {
    return (
      <main className="app-shell">
        <div className="loading-state">
          <div className="loading-spinner" />
          <h2>Checking your watchlist...</h2>
          <p>Looking for changes that actually matter.</p>
        </div>
      </main>
    );
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <div>
          <div className="brand">
            <span className="brand-mark">◎</span>
            Smart Watchlist
          </div>

          <p className="brand-subtitle">
            Know what changed. Know what matters.
          </p>
        </div>

        <button
          className="refresh-button"
          onClick={() => void loadDashboard()}
        >
          ↻ Refresh
        </button>
      </header>

      {error && (
        <div className="error-banner">
          <strong>Couldn't refresh market data.</strong>
          <span>{error}</span>
          <button onClick={() => void loadDashboard()}>
            Retry
          </button>
        </div>
      )}

      {checkStatus && (
        <div className="check-status">{checkStatus}</div>
      )}

      <section
        className="scenario-control"
        aria-label="Demo scenario"
      >
        <span className="demo-feed-label">Demo market feed</span>

        <label htmlFor="scenario-select">Scenario</label>

        <select
          id="scenario-select"
          value={selectedScenario}
          onChange={(event) =>
            void handleScenarioChange(event.target.value)
          }
          disabled={scenarios.length === 0}
        >
          {scenarios.length === 0 ? (
            <option>Loading scenarios...</option>
          ) : (
            scenarios.map((scenario) => (
              <option
                key={scenario.scenario}
                value={scenario.scenario}
              >
                {scenario.title}
              </option>
            ))
          )}
        </select>
      </section>

      <section className="hero">
        <div>
          <h1>What did I miss?</h1>
        </div>

        <div className="hero-stat">
          <strong>{newMeaningfulChanges.length}</strong>

          <span>
            {newMeaningfulChanges.length === 1
              ? "meaningful change"
              : "meaningful changes"}
          </span>

          <small>since your last check</small>
        </div>
      </section>

      <section className="attention-section">
        <div className="section-heading">
          <div>
            <h2>Worth your attention</h2>
            <p>
              Changes supported by the strongest current evidence.
            </p>
          </div>
        </div>

        {meaningfulChanges.length === 0 ? (
          <div className="empty-card">
            <div className="empty-icon">✓</div>
            <h3>Nothing meaningful changed</h3>
            <p>You&apos;re caught up with your watchlist.</p>
          </div>
        ) : (
          <div className="attention-grid">
            {meaningfulChanges.map((item) => {
              const quote = quoteBySymbol.get(item.symbol);

              if (!quote) return null;

              return (
                <button
                  key={item.symbol}
                  className="attention-card"
                  onClick={() =>
                    setSelectedSymbol(item.symbol)
                  }
                >
                  <div className="card-top">
                    <div>
                      <span className="symbol">
                        {item.symbol}
                      </span>

                      <span className="company-name">
                        {COMPANY_NAMES[item.symbol]}
                      </span>
                    </div>

                    <div className="attention-state">
                      {item.isNew && (
                        <span className="new-badge">
                          New
                        </span>
                      )}

                      <span
                        className={`attention-badge ${attentionClass(
                          item.level,
                        )}`}
                      >
                        {attentionLabel(item.level)}
                      </span>
                    </div>
                  </div>

                  <div className="price-row">
                    <strong>
                      {formatPrice(quote.price)}
                    </strong>

                    <span
                      className={
                        quote.percentageChange >= 0
                          ? "positive"
                          : "negative"
                      }
                    >
                      {formatPercent(
                        quote.percentageChange,
                      )}
                    </span>
                  </div>

                  <div className="why-box">
                    <span className="why-title">
                      WHY THIS CHANGED
                    </span>

                    {item.reasons
                      .slice(0, 4)
                      .map((reason) => (
                        <div
                          className="reason"
                          key={reason}
                        >
                          <span className="reason-dot" />
                          {reason}
                        </div>
                      ))}
                  </div>

                  <div className="card-footer">
                    <span>View evidence</span>
                    <strong aria-hidden="true">
                      &rarr;
                    </strong>
                  </div>
                </button>
              );
            })}
          </div>
        )}
      </section>

      <section className="watchlist-section">
        <div className="section-heading">
          <div>
            <h2>Your watchlist</h2>
            <p>Every company you&apos;re monitoring.</p>
          </div>

          <span className="watch-count">
            {quotes.length} stocks
          </span>
        </div>

        <div className="watchlist-tools">
          {watchlist ? (
            <>
              <span className="saved-watchlist-name">
                {watchlist.name}
              </span>

              <label
                className="instrument-search"
                htmlFor="instrument-search"
              >
                <span className="visually-hidden">
                  Search instruments
                </span>

                <input
                  id="instrument-search"
                  value={instrumentQuery}
                  onChange={(event) =>
                    void handleInstrumentSearch(
                      event.target.value,
                    )
                  }
                  placeholder="Search instruments to add"
                />
              </label>

              {instrumentMatches.length > 0 && (
                <div className="instrument-results">
                  {instrumentMatches.map((instrument) => (
                    <button
                      key={instrument.id}
                      type="button"
                      disabled={watchlistBusy}
                      onClick={() =>
                        void updateWatchlist(() =>
                          addItem(
                            watchlist.id,
                            instrument.symbol,
                          ),
                        )
                      }
                    >
                      <strong>{instrument.symbol}</strong>
                      <span>{instrument.companyName}</span>
                      <em>Add</em>
                    </button>
                  ))}
                </div>
              )}
            </>
          ) : (
            <button
              className="create-watchlist-button"
              type="button"
              disabled={watchlistBusy}
              onClick={() =>
                void createSavedWatchlist()
              }
            >
              Create saved watchlist
            </button>
          )}
        </div>

        <div className="watchlist-card">
          <div
            className="watch-table-header"
            aria-hidden="true"
          >
            <span>Company</span>
            <span>Price</span>
            <span>Change</span>
            <span>Attention</span>
            <span />
            <span />
          </div>

          {quotes
            .filter((quote) =>
              displayedSymbols.includes(quote.symbol),
            )
            .map((quote) => {
              const item = attentionBySymbol.get(
                quote.symbol,
              );

              const position =
                watchlist?.items.findIndex(
                  (watchlistItem) =>
                    watchlistItem.instrument.symbol ===
                    quote.symbol,
                );

              return (
                <div
                  key={quote.symbol}
                  className="watch-row"
                  role="button"
                  tabIndex={0}
                  onClick={() =>
                    setSelectedSymbol(quote.symbol)
                  }
                  onKeyDown={(event) => {
                    if (
                      event.key === "Enter" ||
                      event.key === " "
                    ) {
                      event.preventDefault();
                      setSelectedSymbol(
                        quote.symbol,
                      );
                    }
                  }}
                >
                  <div className="stock-identity">
                    <span className="symbol">
                      {quote.symbol}
                    </span>

                    <span className="company-name">
                      {COMPANY_NAMES[quote.symbol]}
                    </span>
                  </div>

                  <div className="watch-price">
                    <strong>
                      {formatPrice(quote.price)}
                    </strong>
                  </div>

                  <span
                    className={
                      quote.percentageChange >= 0
                        ? "positive"
                        : "negative"
                    }
                  >
                    {formatPercent(
                      quote.percentageChange,
                    )}
                  </span>

                  <div className="watch-attention">
                    {item && (
                      <>
                        <span
                          className={`attention-dot ${attentionClass(
                            item.level,
                          )}`}
                        />

                        <span>
                          {attentionLabel(item.level)}
                          {item.isNew
                            ? " · New"
                            : ""}
                        </span>
                      </>
                    )}
                  </div>

                  {watchlist &&
                    position !== undefined &&
                    position >= 0 && (
                      <span className="watch-row-actions">
                        <button
                          type="button"
                          aria-label={`Move ${quote.symbol} up`}
                          disabled={
                            watchlistBusy ||
                            position === 0
                          }
                          onClick={(event) => {
                            event.stopPropagation();

                            const symbols =
                              watchlist.items.map(
                                (item) =>
                                  item.instrument
                                    .symbol,
                              );

                            [
                              symbols[position - 1],
                              symbols[position],
                            ] = [
                              symbols[position],
                              symbols[position - 1],
                            ];

                            void updateWatchlist(() =>
                              reorderItems(
                                watchlist.id,
                                symbols,
                              ),
                            );
                          }}
                        >
                          Up
                        </button>

                        <button
                          type="button"
                          aria-label={`Move ${quote.symbol} down`}
                          disabled={
                            watchlistBusy ||
                            position ===
                              watchlist.items.length -
                                1
                          }
                          onClick={(event) => {
                            event.stopPropagation();

                            const symbols =
                              watchlist.items.map(
                                (item) =>
                                  item.instrument
                                    .symbol,
                              );

                            [
                              symbols[position],
                              symbols[position + 1],
                            ] = [
                              symbols[position + 1],
                              symbols[position],
                            ];

                            void updateWatchlist(() =>
                              reorderItems(
                                watchlist.id,
                                symbols,
                              ),
                            );
                          }}
                        >
                          Down
                        </button>

                        <button
                          type="button"
                          aria-label={`Remove ${quote.symbol}`}
                          disabled={watchlistBusy}
                          onClick={(event) => {
                            event.stopPropagation();

                            void updateWatchlist(() =>
                              removeItem(
                                watchlist.id,
                                quote.symbol,
                              ),
                            );
                          }}
                        >
                          Remove
                        </button>
                      </span>
                    )}

                  <span className="row-arrow">
                    →
                  </span>
                </div>
              );
            })}
        </div>

        <div className="quiet-summary">
          <span className="quiet-icon">◌</span>

          <span>
            {Math.max(
              quotes.length -
                newMeaningfulChanges.length,
              0,
            )}{" "}
            stocks had no meaningful new change.
          </span>
        </div>
      </section>

      <footer className="data-footer">
        <span>● Demo market feed</span>
        <span>
          Data designed for hackathon demonstration
        </span>
      </footer>

      {selectedSymbol &&
        selectedQuote &&
        selectedAttention && (
          <div
            className="modal-backdrop"
            onClick={() =>
              setSelectedSymbol(null)
            }
          >
            <div
              className="detail-modal"
              role="dialog"
              aria-modal="true"
              aria-labelledby="detail-title"
              onClick={(event) =>
                event.stopPropagation()
              }
            >
              <button
                className="close-button"
                onClick={() =>
                  setSelectedSymbol(null)
                }
                aria-label="Close evidence"
              >
                ×
              </button>

              <div className="detail-header">
                <div>
                  <span className="symbol">
                    {selectedQuote.symbol}
                  </span>

                  <h2 id="detail-title">
                    {
                      COMPANY_NAMES[
                        selectedQuote.symbol
                      ]
                    }
                  </h2>
                </div>

                <span
                  className={`attention-badge ${attentionClass(
                    selectedAttention.level,
                  )}`}
                >
                  {attentionLabel(
                    selectedAttention.level,
                  )}
                </span>

                <span className="seen-status">
                  {selectedAttention.isNew
                    ? "NEW SINCE YOUR LAST CHECK"
                    : "Already seen"}
                </span>
              </div>

              <div className="detail-price">
                <strong>
                  {formatPrice(
                    selectedQuote.price,
                  )}
                </strong>

                <span
                  className={
                    selectedQuote.percentageChange >=
                    0
                      ? "positive"
                      : "negative"
                  }
                >
                  {formatPercent(
                    selectedQuote.percentageChange,
                  )}
                </span>
              </div>

              <section className="detail-section">
                <span className="why-title">
                  WHY THIS CHANGED
                </span>

                <div className="evidence-list">
                  <div>
                    <span>Price movement</span>

                    <strong>
                      {formatPercent(
                        selectedQuote.percentageChange,
                      )}
                    </strong>
                  </div>

                  <div>
                    <span>Volume</span>

                    <strong>
                      {(
                        selectedQuote.volume /
                        selectedQuote.averageVolume
                      ).toFixed(1)}
                      × baseline
                    </strong>
                  </div>

                  <div>
                    <span>Day range</span>

                    <strong>
                      {formatPrice(
                        selectedQuote.dayLow,
                      )}{" "}
                      –{" "}
                      {formatPrice(
                        selectedQuote.dayHigh,
                      )}
                    </strong>
                  </div>

                  <div>
                    <span>Data quality</span>

                    <strong
                      className={`data-status data-${selectedQuote.dataStatus}`}
                    >
                      {dataStatusLabel(
                        selectedQuote.dataStatus,
                      )}
                    </strong>
                  </div>
                </div>
              </section>

              <section className="detail-section">
                <span className="why-title">
                  ATTENTION ENGINE
                </span>

                <div className="score-large">
                  <strong>
                    {Math.round(
                      selectedAttention.score,
                    )}
                  </strong>

                  <span>/100</span>
                </div>

                <div className="score-bars">
                  {Object.entries(
                    selectedAttention.evidence,
                  ).map(([key, value]) => (
                    <div
                      className="score-bar-row"
                      key={key}
                    >
                      <span>
                        {key.replace(
                          "Score",
                          "",
                        )}
                      </span>

                      <div className="score-bar">
                        <div
                          style={{
                            width: `${value}%`,
                          }}
                        />
                      </div>

                      <strong>
                        {Math.round(value)}
                      </strong>
                    </div>
                  ))}
                </div>
              </section>

              <section className="detail-section">
                <span className="why-title">
                  WHAT WE FOUND
                </span>

                {selectedAttention.reasons.map(
                  (reason) => (
                    <div
                      className="detail-reason"
                      key={reason}
                    >
                      <span>✓</span>
                      {reason}
                    </div>
                  ),
                )}
              </section>

              <div className="source-note">
                Source: {selectedQuote.source}
                <br />
                Observed:{" "}
                {new Date(
                  selectedQuote.timestamp,
                ).toLocaleString("en-IN")}
              </div>
            </div>
          </div>
        )}
    </main>
  );
}

export { App };
export default App;
