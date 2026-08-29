import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import "./App.css";

const API = "/api";
const PAGE_SIZE = 50;

function App() {
  // ==========================================================
  // DASHBOARD DATA
  // ==========================================================

  const [summary, setSummary] = useState(null);
  const [payments, setPayments] = useState([]);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // ==========================================================
  // FILTERS
  // ==========================================================

  const [search, setSearch] = useState("");
  const [actionFilter, setActionFilter] = useState("ALL");
  const [failureFilter, setFailureFilter] = useState("ALL");
  const [minAmount, setMinAmount] = useState("");
  const [maxAmount, setMaxAmount] = useState("");

  const [currentPage, setCurrentPage] = useState(1);

  // ==========================================================
  // SELECTED PAYMENT / EVALUATION
  // ==========================================================

  const [selectedPayment, setSelectedPayment] = useState(null);
  const [evaluation, setEvaluation] = useState(null);

  const [evaluationLoading, setEvaluationLoading] = useState(false);
  const [evaluationError, setEvaluationError] = useState("");

  // ==========================================================
  // EXECUTION
  // ==========================================================

  const [executionLoading, setExecutionLoading] = useState(false);
  const [executionResult, setExecutionResult] = useState(null);
  const [executionError, setExecutionError] = useState("");

  // ==========================================================
  // EVENTS
  // ==========================================================

  const [events, setEvents] = useState([]);
  const [eventsLoading, setEventsLoading] = useState(false);

  // ==========================================================
  // REQUEST CONTROL
  // ==========================================================
  //
  // This prevents an old evaluation response from overwriting
  // the currently selected payment.
  //
  // Example:
  //
  // Click PAY_000001
  // Click PAY_000003 immediately after
  //
  // If PAY_000001 responds AFTER PAY_000003, its response is
  // ignored.
  //
  // ==========================================================

  const evaluationRequestId = useRef(0);
  const eventsRequestId = useRef(0);

  // ==========================================================
  // INITIAL DASHBOARD LOAD
  // ==========================================================

  useEffect(() => {
    let cancelled = false;

    async function loadDashboard() {
      try {
        setLoading(true);
        setError("");

        const [summaryResponse, paymentsResponse] =
          await Promise.all([
            fetch(`${API}/dashboard/summary`),
            fetch(`${API}/payments`),
          ]);

        if (!summaryResponse.ok) {
          throw new Error(
            `Summary request failed: ${summaryResponse.status}`
          );
        }

        if (!paymentsResponse.ok) {
          throw new Error(
            `Payments request failed: ${paymentsResponse.status}`
          );
        }

        const [summaryData, paymentsData] =
          await Promise.all([
            summaryResponse.json(),
            paymentsResponse.json(),
          ]);

        if (cancelled) {
          return;
        }

        setSummary(summaryData);
        setPayments(
          Array.isArray(paymentsData.payments)
            ? paymentsData.payments
            : []
        );
      } catch (err) {
        if (cancelled) {
          return;
        }

        console.error("Dashboard load error:", err);

        setError(
          "Unable to connect to RecoveryOS API."
        );
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    loadDashboard();

    return () => {
      cancelled = true;
    };
  }, []);

  // ==========================================================
  // FAILURE REASONS
  // ==========================================================

  const failureReasons = useMemo(() => {
    return [
      ...new Set(
        payments
          .map(
            (payment) =>
              payment.failure_reason
          )
          .filter(Boolean)
      ),
    ].sort();
  }, [payments]);

  // ==========================================================
  // FILTERED PAYMENTS
  // ==========================================================

  const filteredPayments = useMemo(() => {
    const query = search
      .trim()
      .toLowerCase();

    const min =
      minAmount === ""
        ? null
        : Number(minAmount);

    const max =
      maxAmount === ""
        ? null
        : Number(maxAmount);

    return payments.filter((payment) => {
      const paymentCode = String(
        payment.payment_code || ""
      ).toLowerCase();

      const customerCode = String(
        payment.customer_code || ""
      ).toLowerCase();

      const matchesSearch =
        !query ||
        paymentCode.includes(query) ||
        customerCode.includes(query);

      const matchesAction =
        actionFilter === "ALL" ||
        payment.action === actionFilter;

      const matchesFailure =
        failureFilter === "ALL" ||
        payment.failure_reason ===
          failureFilter;

      const amount = Number(
        payment.amount
      );

      const matchesMin =
        min === null ||
        (!Number.isNaN(min) &&
          amount >= min);

      const matchesMax =
        max === null ||
        (!Number.isNaN(max) &&
          amount <= max);

      return (
        matchesSearch &&
        matchesAction &&
        matchesFailure &&
        matchesMin &&
        matchesMax
      );
    });
  }, [
    payments,
    search,
    actionFilter,
    failureFilter,
    minAmount,
    maxAmount,
  ]);

  // ==========================================================
  // RESET PAGE WHEN FILTERS CHANGE
  // ==========================================================

  useEffect(() => {
    setCurrentPage(1);
  }, [
    search,
    actionFilter,
    failureFilter,
    minAmount,
    maxAmount,
  ]);

  // ==========================================================
  // PAGINATION
  // ==========================================================

  const totalPages = Math.max(
    1,
    Math.ceil(
      filteredPayments.length /
        PAGE_SIZE
    )
  );

  const safePage = Math.min(
    currentPage,
    totalPages
  );

  const startIndex =
    (safePage - 1) * PAGE_SIZE;

  const endIndex = Math.min(
    startIndex + PAGE_SIZE,
    filteredPayments.length
  );

  const visiblePayments =
    filteredPayments.slice(
      startIndex,
      endIndex
    );

  // ==========================================================
  // FILTER HELPERS
  // ==========================================================

  const hasFilters =
    search !== "" ||
    actionFilter !== "ALL" ||
    failureFilter !== "ALL" ||
    minAmount !== "" ||
    maxAmount !== "";

  function clearFilters() {
    setSearch("");
    setActionFilter("ALL");
    setFailureFilter("ALL");
    setMinAmount("");
    setMaxAmount("");
    setCurrentPage(1);
  }

  // ==========================================================
  // LOAD EVENTS
  // ==========================================================

  const loadEvents = useCallback(
    async (paymentCode) => {
      if (!paymentCode) {
        return;
      }

      const requestId =
        ++eventsRequestId.current;

      setEventsLoading(true);

      try {
        const response = await fetch(
          `${API}/payments/${encodeURIComponent(
            paymentCode
          )}/events`
        );

        if (!response.ok) {
          throw new Error(
            `Unable to load events: ${response.status}`
          );
        }

        const data =
          await response.json();

        // Ignore stale event response.
        if (
          requestId !==
          eventsRequestId.current
        ) {
          return;
        }

        setEvents(
          Array.isArray(data.events)
            ? data.events
            : []
        );
      } catch (err) {
        if (
          requestId !==
          eventsRequestId.current
        ) {
          return;
        }

        console.error(
          "Event history error:",
          err
        );

        setEvents([]);
      } finally {
        if (
          requestId ===
          eventsRequestId.current
        ) {
          setEventsLoading(false);
        }
      }
    },
    []
  );

  // ==========================================================
  // EVALUATE PAYMENT
  // ==========================================================
  //
  // IMPORTANT:
  //
  // selectedPayment is captured locally.
  //
  // The response is only applied if it belongs to the
  // currently selected payment.
  //
  // ==========================================================

  const evaluatePayment = useCallback(
    async (payment) => {
      if (!payment?.payment_code) {
        return;
      }

      const requestId =
        ++evaluationRequestId.current;

      const paymentCode =
        payment.payment_code;

      // Immediately switch selected payment.
      setSelectedPayment(payment);

      // Clear all previous payment-specific state.
      setEvaluation(null);
      setEvaluationError("");

      setExecutionResult(null);
      setExecutionError("");
      setExecutionLoading(false);

      setEvents([]);
      setEventsLoading(false);

      setEvaluationLoading(true);

      try {
        const response = await fetch(
          `${API}/payments/${encodeURIComponent(
            paymentCode
          )}/evaluate`
        );

        if (!response.ok) {
          throw new Error(
            `Evaluation request failed: ${response.status}`
          );
        }

        const data =
          await response.json();

        // ----------------------------------------------------
        // STALE RESPONSE PROTECTION
        // ----------------------------------------------------

        if (
          requestId !==
          evaluationRequestId.current
        ) {
          return;
        }

        // Extra safety:
        // The API response MUST belong to the payment
        // currently selected.
        if (
          data.payment_code !==
          paymentCode
        ) {
          console.error(
            "Ignoring mismatched evaluation response:",
            {
              expected: paymentCode,
              received:
                data.payment_code,
            }
          );

          setEvaluationError(
            "Received evaluation for a different payment."
          );

          return;
        }

        setEvaluation(data);

        // Load events for THIS payment only.
        await loadEvents(paymentCode);
      } catch (err) {
        if (
          requestId !==
          evaluationRequestId.current
        ) {
          return;
        }

        console.error(
          "Payment evaluation error:",
          err
        );

        setEvaluationError(
          "Unable to evaluate this payment."
        );
      } finally {
        if (
          requestId ===
          evaluationRequestId.current
        ) {
          setEvaluationLoading(false);
        }
      }
    },
    [loadEvents]
  );

  // ==========================================================
  // EXECUTE RECOVERY
  // ==========================================================

  async function executeRecovery() {
    if (
      !selectedPayment ||
      !evaluation
    ) {
      return;
    }

    if (
      evaluation.action ===
      "NO_ACTION"
    ) {
      return;
    }

    if (executionLoading) {
      return;
    }

    const paymentCode =
      selectedPayment.payment_code;

    setExecutionLoading(true);
    setExecutionResult(null);
    setExecutionError("");

    try {
      const response = await fetch(
        `${API}/payments/${encodeURIComponent(
          paymentCode
        )}/execute`,
        {
          method: "POST",
        }
      );

      const data =
        await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail ||
            "Execution failed"
        );
      }

      // Make sure execution response is for
      // the currently selected payment.
      if (
        data.payment_code !==
        paymentCode
      ) {
        throw new Error(
          "Execution response belongs to a different payment."
        );
      }

      setExecutionResult(data);

      // Refresh only this payment's event history.
      await loadEvents(paymentCode);
    } catch (err) {
      console.error(
        "Recovery execution error:",
        err
      );

      setExecutionError(
        err.message ||
          "Unable to execute recovery action."
      );
    } finally {
      setExecutionLoading(false);
    }
  }

  // ==========================================================
  // CLOSE EVALUATION
  // ==========================================================

  function closeEvaluation() {
    // Invalidate any outstanding evaluation request.
    evaluationRequestId.current += 1;

    // Invalidate any outstanding events request.
    eventsRequestId.current += 1;

    setSelectedPayment(null);
    setEvaluation(null);

    setEvaluationLoading(false);
    setEvaluationError("");

    setExecutionLoading(false);
    setExecutionResult(null);
    setExecutionError("");

    setEvents([]);
    setEventsLoading(false);
  }

  // ==========================================================
  // PAGINATION
  // ==========================================================

  function goToPage(page) {
    const target = Math.max(
      1,
      Math.min(page, totalPages)
    );

    setCurrentPage(target);

    window.scrollTo({
      top:
        document.querySelector(
          ".payments-card"
        )?.offsetTop || 0,
      behavior: "smooth",
    });
  }

  // ==========================================================
  // LOADING STATE
  // ==========================================================

  if (loading) {
    return (
      <div className="app">
        <div className="loading">
          <div className="loading-title">
            Loading RecoveryOS...
          </div>

          <div className="loading-subtitle">
            Preparing payment recovery
            intelligence
          </div>
        </div>
      </div>
    );
  }

  // ==========================================================
  // ERROR STATE
  // ==========================================================

  if (error) {
    return (
      <div className="app">
        <div className="error">
          <strong>
            RecoveryOS couldn't load
          </strong>

          <span>{error}</span>
        </div>
      </div>
    );
  }

  // ==========================================================
  // MAIN UI
  // ==========================================================

  return (
    <div className="app">

      {/* ================================================== */}
      {/* HEADER */}
      {/* ================================================== */}

      <header className="header">

        <div>
          <h1>RecoveryOS</h1>

          <p>
            Intelligent payment recovery
          </p>
        </div>

        <div className="status">
          <span className="status-dot" />

          API Connected
        </div>

      </header>

      <main>

        {/* ================================================== */}
        {/* METRICS */}
        {/* ================================================== */}

        <section className="metrics">

          <Metric
            label="Failed Payments"
            value={Number(
              summary?.failed_payments || 0
            ).toLocaleString()}
          />

          <Metric
            label="Failed Payment Value"
            value={`₹${Number(
              summary?.failed_payment_value || 0
            ).toLocaleString(
              "en-IN",
              {
                minimumFractionDigits: 2,
              }
            )}`}
          />

          <Metric
            label="Avg Recovery Probability"
            value={`${(
              Number(
                summary?.average_recovery_probability ||
                  0
              ) * 100
            ).toFixed(1)}%`}
          />

          <Metric
            label="Expected Recovery Value"
            value={`₹${Number(
              summary?.expected_recovery_value || 0
            ).toLocaleString(
              "en-IN",
              {
                minimumFractionDigits: 2,
              }
            )}`}
          />

        </section>

        {/* ================================================== */}
        {/* ACTIONS + MODEL */}
        {/* ================================================== */}

        <section className="content-grid">

          <div className="card actions-card">

            <div className="card-header">
              <h2>Recovery Actions</h2>
            </div>

            <ActionRow
              label="Payment Link"
              value={
                summary?.actions
                  ?.SEND_PAYMENT_LINK || 0
              }
            />

            <ActionRow
              label="Reminder"
              value={
                summary?.actions
                  ?.SEND_REMINDER || 0
              }
            />

            <ActionRow
              label="Offer Retry"
              value={
                summary?.actions
                  ?.OFFER_RETRY || 0
              }
            />

            <ActionRow
              label="No Action"
              value={
                summary?.actions
                  ?.NO_ACTION || 0
              }
            />

          </div>

          <div className="card model-card">

            <div className="card-header">
              <h2>ML Model</h2>
            </div>

            <div className="model-name">
              {summary?.model || "—"}
            </div>

            <div className="model-detail">
              Version{" "}
              {summary?.model_version || "—"}
            </div>

            <div className="model-detail">
              Average probability{" "}
              <strong>
                {(
                  Number(
                    summary?.average_recovery_probability ||
                      0
                  ) * 100
                ).toFixed(1)}
                %
              </strong>
            </div>

            <div className="model-note">
              Estimates are based on the current
              prototype training dataset.
            </div>

          </div>

        </section>

        {/* ================================================== */}
        {/* PAYMENTS */}
        {/* ================================================== */}

        <section className="card payments-card">

          <div className="card-header payments-header">

            <div>

              <h2>Failed Payments</h2>

              <p>
                {filteredPayments.length.toLocaleString()}{" "}
                of{" "}
                {payments.length.toLocaleString()}{" "}
                failed transactions
              </p>

            </div>

          </div>

          {/* ================================================= */}
          {/* FILTERS */}
          {/* ================================================= */}

          <div className="filters">

            <div className="filter-group search-group">

              <label>
                Search
              </label>

              <input
                type="text"
                placeholder="Payment or customer code..."
                value={search}
                onChange={(event) =>
                  setSearch(
                    event.target.value
                  )
                }
              />

            </div>

            <div className="filter-group">

              <label>
                Action
              </label>

              <select
                value={actionFilter}
                onChange={(event) =>
                  setActionFilter(
                    event.target.value
                  )
                }
              >

                <option value="ALL">
                  All Actions
                </option>

                <option value="SEND_PAYMENT_LINK">
                  Payment Link
                </option>

                <option value="SEND_REMINDER">
                  Reminder
                </option>

                <option value="OFFER_RETRY">
                  Retry
                </option>

                <option value="NO_ACTION">
                  No Action
                </option>

              </select>

            </div>

            <div className="filter-group">

              <label>
                Failure Reason
              </label>

              <select
                value={failureFilter}
                onChange={(event) =>
                  setFailureFilter(
                    event.target.value
                  )
                }
              >

                <option value="ALL">
                  All Failures
                </option>

                {failureReasons.map(
                  (reason) => (
                    <option
                      key={reason}
                      value={reason}
                    >
                      {formatFailureReason(
                        reason
                      )}
                    </option>
                  )
                )}

              </select>

            </div>

            <div className="filter-group amount-group">

              <label>
                Min Amount
              </label>

              <input
                type="number"
                min="0"
                placeholder="₹0"
                value={minAmount}
                onChange={(event) =>
                  setMinAmount(
                    event.target.value
                  )
                }
              />

            </div>

            <div className="filter-group amount-group">

              <label>
                Max Amount
              </label>

              <input
                type="number"
                min="0"
                placeholder="₹∞"
                value={maxAmount}
                onChange={(event) =>
                  setMaxAmount(
                    event.target.value
                  )
                }
              />

            </div>

            <button
              className="clear-button"
              onClick={clearFilters}
              disabled={!hasFilters}
            >
              Clear
            </button>

          </div>

          {/* ================================================= */}
          {/* RESULTS BAR */}
          {/* ================================================= */}

          <div className="results-bar">

            <span>

              Showing{" "}

              <strong>
                {filteredPayments.length ===
                0
                  ? 0
                  : startIndex + 1}
                –
                {endIndex}
              </strong>{" "}

              of{" "}

              <strong>
                {filteredPayments.length.toLocaleString()}
              </strong>

            </span>

            {hasFilters && (
              <span className="filtered-label">
                Filters active
              </span>
            )}

          </div>

          {/* ================================================= */}
          {/* TABLE */}
          {/* ================================================= */}

          <div className="table-wrapper">

            <table>

              <thead>

                <tr>
                  <th>Payment</th>
                  <th>Customer</th>
                  <th>Amount</th>
                  <th>Failure</th>
                  <th>Probability</th>
                  <th>Action</th>
                </tr>

              </thead>

              <tbody>

                {visiblePayments.map(
                  (payment) => {

                    const isSelected =
                      selectedPayment
                        ?.payment_code ===
                      payment.payment_code;

                    return (
                      <tr
                        key={
                          payment.payment_code
                        }
                        className={
                          isSelected
                            ? "selected-payment-row"
                            : ""
                        }
                      >

                        <td>

                          <button
                            className="payment-link"
                            onClick={() =>
                              evaluatePayment(
                                payment
                              )
                            }
                          >
                            {
                              payment.payment_code
                            }
                          </button>

                        </td>

                        <td>
                          {
                            payment.customer_code
                          }
                        </td>

                        <td>
                          ₹
                          {Number(
                            payment.amount
                          ).toLocaleString(
                            "en-IN",
                            {
                              minimumFractionDigits: 2,
                            }
                          )}
                        </td>

                        <td>

                          <span className="failure">
                            {formatFailureReason(
                              payment.failure_reason
                            )}
                          </span>

                        </td>

                        <td>

                          {(
                            Number(
                              payment.hybrid_probability
                            ) * 100
                          ).toFixed(1)}
                          %

                        </td>

                        <td>

                          <ActionBadge
                            action={
                              payment.action
                            }
                          />

                        </td>

                      </tr>
                    );
                  }
                )}

                {filteredPayments.length ===
                  0 && (

                  <tr>

                    <td
                      colSpan="6"
                      className="empty-state"
                    >
                      No payments match your
                      filters.
                    </td>

                  </tr>

                )}

              </tbody>

            </table>

          </div>

          {/* ================================================= */}
          {/* PAGINATION */}
          {/* ================================================= */}

          {filteredPayments.length > 0 && (

            <div className="pagination">

              <button
                className="page-button"
                onClick={() =>
                  goToPage(
                    safePage - 1
                  )
                }
                disabled={
                  safePage === 1
                }
              >
                ← Previous
              </button>

              <div className="page-numbers">

                {getPageNumbers(
                  safePage,
                  totalPages
                ).map(
                  (page, index) => {

                    if (
                      page === "..."
                    ) {

                      return (
                        <span
                          className="page-ellipsis"
                          key={`ellipsis-${index}`}
                        >
                          ...
                        </span>
                      );

                    }

                    return (
                      <button
                        key={page}
                        className={`page-number ${
                          page === safePage
                            ? "active"
                            : ""
                        }`}
                        onClick={() =>
                          goToPage(page)
                        }
                      >
                        {page}
                      </button>
                    );

                  }
                )}

              </div>

              <button
                className="page-button"
                onClick={() =>
                  goToPage(
                    safePage + 1
                  )
                }
                disabled={
                  safePage ===
                  totalPages
                }
              >
                Next →
              </button>

            </div>

          )}

        </section>

        {/* ================================================== */}
        {/* EVALUATION PANEL */}
        {/* ================================================== */}

        {selectedPayment && (

          <section className="evaluation-panel">

            <div className="evaluation-header">

              <div>

                <h2>
                  Payment Evaluation
                </h2>

                <p>
                  {
                    selectedPayment.payment_code
                  }{" "}
                  ·{" "}
                  {
                    selectedPayment.customer_code
                  }
                </p>

              </div>

              <button
                className="close-button"
                onClick={
                  closeEvaluation
                }
              >
                ×
              </button>

            </div>

            {/* ================================================= */}
            {/* EVALUATION LOADING */}
            {/* ================================================= */}

            {evaluationLoading && (

              <div className="evaluation-loading">
                Evaluating{" "}
                {
                  selectedPayment.payment_code
                }
                ...
              </div>

            )}

            {evaluationError && (

              <div className="evaluation-error">
                {evaluationError}
              </div>

            )}

            {/* ================================================= */}
            {/* EVALUATION */}
            {/* ================================================= */}

            {evaluation && (

              <>

                {/* --------------------------------------------- */}
                {/* SUMMARY */}
                {/* --------------------------------------------- */}

                <div className="evaluation-summary">

                  <div>

                    <span>
                      Amount
                    </span>

                    <strong>
                      ₹
                      {Number(
                        evaluation.amount
                      ).toLocaleString(
                        "en-IN",
                        {
                          minimumFractionDigits: 2,
                        }
                      )}
                    </strong>

                  </div>

                  <div>

                    <span>
                      Hybrid Probability
                    </span>

                    <strong>
                      {(
                        Number(
                          evaluation.hybrid_probability
                        ) * 100
                      ).toFixed(1)}
                      %
                    </strong>

                  </div>

                  <div>

                    <span>
                      Recommended Action
                    </span>

                    <ActionBadge
                      action={
                        evaluation.action
                      }
                    />

                  </div>

                </div>

                {/* --------------------------------------------- */}
                {/* PROBABILITY / VALUE GRID */}
                {/* --------------------------------------------- */}

                <div className="evaluation-grid">

                  <div className="evaluation-card">

                    <span>
                      Rules Probability
                    </span>

                    <strong>
                      {(
                        Number(
                          evaluation.rules_probability
                        ) * 100
                      ).toFixed(1)}
                      %
                    </strong>

                  </div>

                  <div className="evaluation-card">

                    <span>
                      ML Probability
                    </span>

                    <strong>
                      {(
                        Number(
                          evaluation.ml_probability
                        ) * 100
                      ).toFixed(1)}
                      %
                    </strong>

                  </div>

                  <div className="evaluation-card">

                    <span>
                      Expected Value
                    </span>

                    <strong>
                      ₹
                      {Number(
                        evaluation.expected_value
                      ).toLocaleString(
                        "en-IN",
                        {
                          minimumFractionDigits: 2,
                        }
                      )}
                    </strong>

                  </div>

                  <div className="evaluation-card">

                    <span>
                      Intervention Cost
                    </span>

                    <strong>
                      ₹
                      {Number(
                        evaluation.intervention_cost
                      ).toLocaleString(
                        "en-IN",
                        {
                          minimumFractionDigits: 2,
                        }
                      )}
                    </strong>

                  </div>

                </div>

                {/* --------------------------------------------- */}
                {/* DETAILS */}
                {/* --------------------------------------------- */}

                <div className="evaluation-details">

                  <div>

                    <span>
                      Failure Reason
                    </span>

                    <strong>
                      {formatFailureReason(
                        evaluation.failure_reason
                      )}
                    </strong>

                  </div>

                  <div>

                    <span>
                      Status
                    </span>

                    <strong>
                      {
                        evaluation.status
                      }
                    </strong>

                  </div>

                  <div>

                    <span>
                      Model
                    </span>

                    <strong>
                      {
                        evaluation.model
                      }
                    </strong>

                  </div>

                  <div>

                    <span>
                      Model Version
                    </span>

                    <strong>
                      {
                        evaluation.model_version
                      }
                    </strong>

                  </div>

                </div>

                {/* --------------------------------------------- */}
                {/* REASON */}
                {/* --------------------------------------------- */}

                <div className="evaluation-reason">

                  <span>
                    Decision Reason
                  </span>

                  <p>
                    {
                      evaluation.reason
                    }
                  </p>

                </div>

                {/* ================================================= */}
                {/* EXECUTION */}
                {/* ================================================= */}

                <div className="execution-section">

                  <div className="execution-header">

                    <div>

                      <span>
                        Recovery Execution
                      </span>

                      <p>
                        Execute the recommended
                        recovery action for this
                        payment.
                      </p>

                    </div>

                    {evaluation.action !==
                      "NO_ACTION" && (

                      <button
                        className="execute-button"
                        onClick={
                          executeRecovery
                        }
                        disabled={
                          executionLoading ||
                          executionResult?.executed ===
                            true
                        }
                      >

                        {executionLoading
                          ? "Executing..."
                          : executionResult?.executed
                          ? "Action Executed"
                          : "Execute Recovery Action"}

                      </button>

                    )}

                  </div>

                  {evaluation.action ===
                    "NO_ACTION" && (

                    <div className="no-action-message">
                      No intervention is recommended
                      for this payment.
                    </div>

                  )}

                  {executionError && (

                    <div className="execution-error">
                      {
                        executionError
                      }
                    </div>

                  )}

                  {executionResult && (

                    <div className="execution-success">

                      <div>

                        <span>
                          Execution Status
                        </span>

                        <strong>
                          {
                            executionResult.outcome ||
                            "ACTION_EXECUTED"
                          }
                        </strong>

                      </div>

                      <div>

                        <span>
                          Event ID
                        </span>

                        <strong>
                          #
                          {
                            executionResult.event_id
                          }
                        </strong>

                      </div>

                      <div>

                        <span>
                          Action
                        </span>

                        <strong>
                          <ActionBadge
                            action={
                              executionResult.action
                            }
                          />
                        </strong>

                      </div>

                      <div>

                        <span>
                          Predicted Probability
                        </span>

                        <strong>
                          {(
                            Number(
                              executionResult.predicted_probability
                            ) * 100
                          ).toFixed(1)}
                          %
                        </strong>

                      </div>

                    </div>

                  )}

                </div>

                {/* ================================================= */}
                {/* EVENT HISTORY */}
                {/* ================================================= */}

                <div className="events-section">

                  <div className="events-header">

                    <div>

                      <span>
                        Recovery Event History
                      </span>

                      <p>
                        Actions recorded for this
                        payment.
                      </p>

                    </div>

                    <strong>
                      {events.length}{" "}
                      {events.length === 1
                        ? "event"
                        : "events"}
                    </strong>

                  </div>

                  {eventsLoading && (

                    <div className="events-loading">
                      Loading event history...
                    </div>

                  )}

                  {!eventsLoading &&
                    events.length === 0 && (

                    <div className="events-empty">
                      No recovery events recorded
                      yet.
                    </div>

                  )}

                  {!eventsLoading &&
                    events.length > 0 && (

                    <div className="events-list">

                      {events.map(
                        (event) => (

                        <div
                          className="event-row"
                          key={
                            event.event_id
                          }
                        >

                          <div>

                            <strong>
                              <ActionBadge
                                action={
                                  event.action
                                }
                              />
                            </strong>

                            <span>
                              Event #
                              {
                                event.event_id
                              }
                            </span>

                          </div>

                          <div>

                            <span>
                              Probability
                            </span>

                            <strong>
                              {(
                                Number(
                                  event.predicted_probability
                                ) * 100
                              ).toFixed(1)}
                              %
                            </strong>

                          </div>

                          <div>

                            <span>
                              Expected Value
                            </span>

                            <strong>
                              ₹
                              {Number(
                                event.expected_value ||
                                  0
                              ).toLocaleString(
                                "en-IN",
                                {
                                  minimumFractionDigits: 2,
                                }
                              )}
                            </strong>

                          </div>

                          <div>

                            <span>
                              Outcome
                            </span>

                            <strong>
                              {
                                event.outcome ||
                                "—"
                              }
                            </strong>

                          </div>

                        </div>

                      )
                    )}

                    </div>

                  )}

                </div>

              </>

            )}

          </section>

        )}

      </main>

    </div>
  );
}


// ============================================================
// PAGINATION NUMBERS
// ============================================================

function getPageNumbers(
  currentPage,
  totalPages
) {
  if (totalPages <= 7) {
    return Array.from(
      {
        length: totalPages,
      },
      (_, index) => index + 1
    );
  }

  if (currentPage <= 4) {
    return [
      1,
      2,
      3,
      4,
      5,
      "...",
      totalPages,
    ];
  }

  if (
    currentPage >=
    totalPages - 3
  ) {
    return [
      1,
      "...",
      totalPages - 4,
      totalPages - 3,
      totalPages - 2,
      totalPages - 1,
      totalPages,
    ];
  }

  return [
    1,
    "...",
    currentPage - 1,
    currentPage,
    currentPage + 1,
    "...",
    totalPages,
  ];
}


// ============================================================
// FAILURE REASON FORMATTER
// ============================================================

function formatFailureReason(reason) {
  if (!reason) {
    return "";
  }

  return String(reason)
    .replaceAll("_", " ")
    .toLowerCase()
    .replace(
      /\b\w/g,
      (letter) =>
        letter.toUpperCase()
    );
}


// ============================================================
// METRIC
// ============================================================

function Metric({
  label,
  value,
}) {
  return (
    <div className="metric">

      <span>
        {label}
      </span>

      <strong>
        {value}
      </strong>

    </div>
  );
}


// ============================================================
// ACTION ROW
// ============================================================

function ActionRow({
  label,
  value,
}) {
  return (
    <div className="action-row">

      <span>
        {label}
      </span>

      <strong>
        {value}
      </strong>

    </div>
  );
}


// ============================================================
// ACTION BADGE
// ============================================================

function ActionBadge({
  action,
}) {
  const labels = {
    SEND_PAYMENT_LINK:
      "Payment Link",

    SEND_REMINDER:
      "Reminder",

    OFFER_RETRY:
      "Retry",

    NO_ACTION:
      "No Action",
  };

  const safeAction =
    action || "NO_ACTION";

  return (
    <span
      className={`badge badge-${safeAction
        .toLowerCase()
        .replaceAll("_", "-")}`}
    >
      {labels[safeAction] ||
        safeAction}
    </span>
  );
}


export default App;