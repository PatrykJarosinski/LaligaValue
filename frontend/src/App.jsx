import { useEffect, useMemo, useState } from "react";

const PAGE_SIZE = 10;

const STATUS_LABELS = {
  scheduled: "Zaplanowany",
  live: "Na żywo",
  finished: "Zakończony",
  postponed: "Przełożony",
  cancelled: "Odwołany",
};

const MARKET_LABELS = {
  "1x2": "1X2",
  over_under_2_5: "Powyżej / poniżej 2,5",
};

async function fetchApi(path, signal) {
  const response = await fetch(`/api${path}`, { signal });
  if (!response.ok) {
    const error = new Error("Nie udało się pobrać danych z API.");
    error.status = response.status;
    throw error;
  }
  return response.json();
}

function useApi(path) {
  const [state, setState] = useState({ data: null, loading: Boolean(path), error: null });

  useEffect(() => {
    if (!path) {
      setState({ data: null, loading: false, error: null });
      return undefined;
    }

    const controller = new AbortController();
    setState({ data: null, loading: true, error: null });
    fetchApi(path, controller.signal)
      .then((data) => setState({ data, loading: false, error: null }))
      .catch((error) => {
        if (error.name !== "AbortError") setState({ data: null, loading: false, error });
      });

    return () => controller.abort();
  }, [path]);

  return state;
}

function readRoute() {
  const hash = window.location.hash.replace(/^#/, "");
  return hash || "/";
}

function formatDate(value) {
  return new Intl.DateTimeFormat("pl-PL", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

function formatOdds(value) {
  return Number(value).toLocaleString("pl-PL", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 3,
  });
}

function matchScore(match) {
  if (match.home_score === null || match.away_score === null) return "—";
  return `${match.home_score} : ${match.away_score}`;
}

function routeLink(path) {
  return `#${path}`;
}

function ApiState({ state, emptyMessage, children }) {
  if (state.loading) return <div className="state-card">Ładowanie danych…</div>;
  if (state.error) return <div className="state-card state-card--error">{state.error.message}</div>;
  if (!state.data) return null;
  if (Array.isArray(state.data) ? state.data.length === 0 : state.data.results?.length === 0) {
    return <div className="state-card">{emptyMessage}</div>;
  }
  return children;
}

function StatusBadge({ status }) {
  return <span className={`status status--${status}`}>{STATUS_LABELS[status] ?? status}</span>;
}

function MatchName({ match }) {
  return (
    <span className="match-name">
      <span>{match.home_team.name}</span>
      <span className="match-name__divider">—</span>
      <span>{match.away_team.name}</span>
    </span>
  );
}

function App() {
  const [route, setRoute] = useState(readRoute);

  useEffect(() => {
    const onHashChange = () => setRoute(readRoute());
    window.addEventListener("hashchange", onHashChange);
    return () => window.removeEventListener("hashchange", onHashChange);
  }, []);

  const routePath = route.split("?")[0];
  const page = routePath.startsWith("/mecze/")
    ? "match-detail"
    : routePath === "/mecze"
      ? "matches"
      : routePath === "/kursy"
        ? "odds"
        : routePath === "/value"
          ? "value"
          : "dashboard";
  const matchId = routePath.match(/^\/mecze\/(\d+)\/?$/)?.[1];

  return (
    <div className="app-shell">
      <header className="topbar">
        <a className="brand" href={routeLink("/")}>
          <span className="brand__mark">LV</span>
          <span>
            <strong>LaLiga Value</strong>
            <small>panel analityczny</small>
          </span>
        </a>
        <nav className="nav" aria-label="Główna nawigacja">
          <a className={page === "dashboard" ? "is-active" : ""} href={routeLink("/")}>Dashboard</a>
          <a className={page === "matches" || page === "match-detail" ? "is-active" : ""} href={routeLink("/mecze")}>Mecze</a>
          <a className={page === "odds" ? "is-active" : ""} href={routeLink("/kursy")}>Kursy</a>
          <a className={page === "value" ? "is-active" : ""} href={routeLink("/value")}>Potencjalne value</a>
        </nav>
      </header>

      <main className="content">
        <div className="test-data-notice">Dane demonstracyjne — kursy i statystyki oznaczone jako testowe, nie są aktualnymi danymi rynkowymi.</div>
        {page === "dashboard" && <DashboardPage />}
        {page === "matches" && <MatchesPage />}
        {page === "match-detail" && <MatchDetailPage matchId={matchId} />}
        {page === "odds" && <OddsComparisonPage />}
        {page === "value" && <ValuePage />}
      </main>
    </div>
  );
}

function DashboardPage() {
  const matchesState = useApi("/matches/?page_size=100");
  const teamsState = useApi("/teams/?page_size=100");
  const seasonsState = useApi("/seasons/?page_size=100");
  const matches = matchesState.data?.results ?? [];
  const upcoming = matches.filter((match) => match.status === "scheduled").slice(0, 4);
  const finishedCount = matches.filter((match) => match.status === "finished").length;
  const hasError = matchesState.error || teamsState.error || seasonsState.error;

  return (
    <>
      <PageHeading eyebrow="Przegląd" title="Dashboard" description="Szybki podgląd testowych danych zapisanych w Twojej lokalnej bazie." />
      {hasError && <div className="state-card state-card--error">Nie udało się pobrać podsumowania danych.</div>}
      <section className="metric-grid" aria-label="Podsumowanie danych">
        <Metric label="Mecze" value={matchesState.loading ? "…" : matches.length} note="w bazie testowej" />
        <Metric label="Zaplanowane" value={matchesState.loading ? "…" : upcoming.length} note="do obserwacji" />
        <Metric label="Zakończone" value={matchesState.loading ? "…" : finishedCount} note="ze statystykami" />
        <Metric label="Drużyny" value={teamsState.loading ? "…" : teamsState.data?.count ?? 0} note={`${seasonsState.data?.count ?? 0} sezon`} />
      </section>

      <section className="panel">
        <div className="panel__header">
          <div>
            <p className="eyebrow">Terminarz</p>
            <h2>Najbliższe spotkania</h2>
          </div>
          <a className="text-link" href={routeLink("/mecze")}>Zobacz wszystkie →</a>
        </div>
        <ApiState state={matchesState} emptyMessage="Brak zaplanowanych meczów w danych testowych.">
          {upcoming.length ? (
            <div className="fixture-list">
              {upcoming.map((match) => <FixtureCard key={match.id} match={match} />)}
            </div>
          ) : <div className="state-card">Brak zaplanowanych meczów w danych testowych.</div>}
        </ApiState>
      </section>
    </>
  );
}

function MatchesPage() {
  const seasonsState = useApi("/seasons/?page_size=100");
  const teamsState = useApi("/teams/?page_size=100");
  const [filters, setFilters] = useState({ season: "", team: "", date: "" });
  const [page, setPage] = useState(1);
  const query = useMemo(() => {
    const params = new URLSearchParams({ page: String(page), page_size: String(PAGE_SIZE) });
    Object.entries(filters).forEach(([key, value]) => { if (value) params.set(key, value); });
    return params.toString();
  }, [filters, page]);
  const matchesState = useApi(`/matches/?${query}`);
  const matches = matchesState.data?.results ?? [];
  const totalPages = Math.max(1, Math.ceil((matchesState.data?.count ?? 0) / PAGE_SIZE));

  function updateFilter(name, value) {
    setPage(1);
    setFilters((current) => ({ ...current, [name]: value }));
  }

  return (
    <>
      <PageHeading eyebrow="Baza meczów" title="Mecze" description="Filtruj lokalnie zapisane mecze według sezonu, daty lub drużyny." />
      <section className="panel">
        <div className="filters">
          <label>Sezon
            <select value={filters.season} onChange={(event) => updateFilter("season", event.target.value)}>
              <option value="">Wszystkie sezony</option>
              {(seasonsState.data?.results ?? []).map((season) => <option key={season.id} value={season.id}>{season.name}</option>)}
            </select>
          </label>
          <label>Drużyna
            <select value={filters.team} onChange={(event) => updateFilter("team", event.target.value)}>
              <option value="">Wszystkie drużyny</option>
              {(teamsState.data?.results ?? []).map((team) => <option key={team.id} value={team.id}>{team.name}</option>)}
            </select>
          </label>
          <label>Data
            <input type="date" value={filters.date} onChange={(event) => updateFilter("date", event.target.value)} />
          </label>
          <button className="button button--ghost" type="button" onClick={() => { setFilters({ season: "", team: "", date: "" }); setPage(1); }}>Wyczyść filtry</button>
        </div>
      </section>
      <section className="panel panel--table">
        <ApiState state={matchesState} emptyMessage="Nie znaleziono meczów dla wybranych filtrów.">
          <div className="table-wrap">
            <table>
              <thead><tr><th>Data</th><th>Mecz</th><th>Status</th><th>Wynik</th><th /></tr></thead>
              <tbody>{matches.map((match) => (
                <tr key={match.id}>
                  <td>{formatDate(match.kickoff_at)}</td>
                  <td><MatchName match={match} /></td>
                  <td><StatusBadge status={match.status} /></td>
                  <td className="score">{matchScore(match)}</td>
                  <td><a className="text-link" href={routeLink(`/mecze/${match.id}`)}>Szczegóły</a></td>
                </tr>
              ))}</tbody>
            </table>
          </div>
        </ApiState>
        {matchesState.data?.count > PAGE_SIZE && <Pagination page={page} totalPages={totalPages} onChange={setPage} />}
      </section>
    </>
  );
}

function MatchDetailPage({ matchId }) {
  const matchState = useApi(matchId ? `/matches/${matchId}/` : null);
  const statisticsState = useApi(matchId ? `/matches/${matchId}/statistics/` : null);
  const oddsState = useApi(matchId ? `/matches/${matchId}/odds/?page_size=100` : null);
  const match = matchState.data;

  if (matchState.loading) return <div className="state-card">Ładowanie szczegółów meczu…</div>;
  if (matchState.error || !match) return <div className="state-card state-card--error">Nie znaleziono wskazanego meczu.</div>;

  return (
    <>
      <a className="back-link" href={routeLink("/mecze")}>← Wróć do meczów</a>
      <section className="match-hero">
        <p className="eyebrow">{match.season.name} · {formatDate(match.kickoff_at)}</p>
        <div className="match-hero__teams"><span>{match.home_team.name}</span><strong>{matchScore(match)}</strong><span>{match.away_team.name}</span></div>
        <StatusBadge status={match.status} />
      </section>
      <section className="two-column">
        <div className="panel">
          <div className="panel__header"><div><p className="eyebrow">Parametry meczu</p><h2>Statystyki</h2></div></div>
          {statisticsState.loading && <div className="state-card">Ładowanie statystyk…</div>}
          {statisticsState.error?.status === 404 && <div className="state-card">Dla tego meczu nie zapisano jeszcze statystyk.</div>}
          {statisticsState.error && statisticsState.error.status !== 404 && <div className="state-card state-card--error">Nie udało się pobrać statystyk.</div>}
          {statisticsState.data && <StatisticsGrid statistics={statisticsState.data} match={match} />}
        </div>
        <div className="panel">
          <div className="panel__header"><div><p className="eyebrow">Historia kursów</p><h2>Ostatnie snapshoty</h2></div><a className="text-link" href={routeLink(`/kursy?match=${match.id}`)}>Porównaj kursy →</a></div>
          <OddsPreview state={oddsState} />
        </div>
      </section>
    </>
  );
}

function OddsComparisonPage() {
  const matchesState = useApi("/matches/?page_size=100");
  const matches = matchesState.data?.results ?? [];
  const [selectedMatchId, setSelectedMatchId] = useState("");

  useEffect(() => {
    const requestedMatch = new URLSearchParams(window.location.hash.split("?")[1] ?? "").get("match");
    if (!selectedMatchId && matches.length) {
      setSelectedMatchId(matches.some((match) => String(match.id) === requestedMatch) ? requestedMatch : String(matches[0].id));
    }
  }, [matches, selectedMatchId]);

  const oddsState = useApi(selectedMatchId ? `/matches/${selectedMatchId}/odds/?page_size=100` : null);
  const selectedMatch = matches.find((match) => String(match.id) === selectedMatchId);
  const odds = oddsState.data?.results ?? [];
  const markets = [...new Set(odds.map((snapshot) => snapshot.market))];

  return (
    <>
      <PageHeading eyebrow="Snapshoty kursów" title="Porównanie kursów" description="Zapisane wartości testowe pogrupowane według bukmachera i rynku." />
      <section className="panel">
        <label className="match-select">Wybierz mecz
          <select value={selectedMatchId} onChange={(event) => setSelectedMatchId(event.target.value)}>
            <option value="">Wybierz mecz</option>
            {matches.map((match) => <option key={match.id} value={match.id}>{formatDate(match.kickoff_at)} · {match.home_team.name} — {match.away_team.name}</option>)}
          </select>
        </label>
      </section>
      {selectedMatch && <section className="panel"><p className="eyebrow">Wybrany mecz</p><h2><MatchName match={selectedMatch} /></h2></section>}
      <ApiState state={oddsState} emptyMessage="Dla tego meczu nie ma zapisanych snapshotów kursów.">
        <div className="odds-grid">
          {markets.map((market) => <OddsMarketCard key={market} market={market} odds={odds.filter((snapshot) => snapshot.market === market)} />)}
        </div>
      </ApiState>
    </>
  );
}

function ValuePage() {
  return (
    <section className="value-page panel">
      <p className="eyebrow">W przygotowaniu</p>
      <h1>Potencjalne value</h1>
      <p>Ten widok będzie w przyszłości prezentował porównanie kursów z prawdopodobieństwami wyliczanymi przez model.</p>
      <div className="value-page__note"><strong>Brak aktywnego modelu predykcyjnego.</strong><br />Nie pokazujemy sugestii ani „value betów”, dopóki nie powstanie zweryfikowany model i metodologia oceny.</div>
    </section>
  );
}

function PageHeading({ eyebrow, title, description }) {
  return <header className="page-heading"><p className="eyebrow">{eyebrow}</p><h1>{title}</h1><p>{description}</p></header>;
}

function Metric({ label, value, note }) {
  return <article className="metric"><p>{label}</p><strong>{value}</strong><span>{note}</span></article>;
}

function FixtureCard({ match }) {
  return <a className="fixture-card" href={routeLink(`/mecze/${match.id}`)}><span>{formatDate(match.kickoff_at)}</span><strong><MatchName match={match} /></strong><StatusBadge status={match.status} /></a>;
}

function StatisticsGrid({ statistics, match }) {
  const rows = [
    ["xG", statistics.home_xg, statistics.away_xg],
    ["Strzały", statistics.home_shots, statistics.away_shots],
    ["Posiadanie", statistics.home_possession === null ? null : `${statistics.home_possession}%`, statistics.away_possession === null ? null : `${statistics.away_possession}%`],
  ];
  return <div className="statistics"><div className="statistics__teams"><span>{match.home_team.name}</span><span>{match.away_team.name}</span></div>{rows.map(([label, home, away]) => <div className="statistics__row" key={label}><strong>{home ?? "—"}</strong><span>{label}</span><strong>{away ?? "—"}</strong></div>)}</div>;
}

function OddsPreview({ state }) {
  if (state.loading) return <div className="state-card">Ładowanie kursów…</div>;
  if (state.error) return <div className="state-card state-card--error">Nie udało się pobrać kursów.</div>;
  const latest = (state.data?.results ?? []).slice(0, 6);
  if (!latest.length) return <div className="state-card">Brak kursów dla tego meczu.</div>;
  return <div className="odds-preview">{latest.map((snapshot) => <div key={snapshot.id}><span>{snapshot.bookmaker.name} · {snapshot.selection}</span><strong>{formatOdds(snapshot.odds)}</strong></div>)}</div>;
}

function OddsMarketCard({ market, odds }) {
  const latestByBookmakerAndSelection = new Map();
  odds.forEach((snapshot) => {
    const key = `${snapshot.bookmaker.id}-${snapshot.selection}`;
    if (!latestByBookmakerAndSelection.has(key)) latestByBookmakerAndSelection.set(key, snapshot);
  });
  const latest = [...latestByBookmakerAndSelection.values()];
  return <section className="panel odds-market"><div className="panel__header"><div><p className="eyebrow">Rynek</p><h2>{MARKET_LABELS[market] ?? market}</h2></div></div><div className="table-wrap"><table><thead><tr><th>Bukmacher</th><th>Selekcja</th><th>Kurs</th><th>Snapshot</th></tr></thead><tbody>{latest.map((snapshot) => <tr key={snapshot.id}><td>{snapshot.bookmaker.name}</td><td>{snapshot.selection}</td><td className="odds-value">{formatOdds(snapshot.odds)}</td><td>{formatDate(snapshot.captured_at)}</td></tr>)}</tbody></table></div></section>;
}

function Pagination({ page, totalPages, onChange }) {
  return <div className="pagination"><button className="button button--ghost" disabled={page === 1} onClick={() => onChange(page - 1)}>← Poprzednia</button><span>Strona {page} z {totalPages}</span><button className="button button--ghost" disabled={page === totalPages} onClick={() => onChange(page + 1)}>Następna →</button></div>;
}

export default App;
