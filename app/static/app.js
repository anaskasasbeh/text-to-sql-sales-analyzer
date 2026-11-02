// Text-to-SQL Sales Analyzer: page logic (no framework).

const REPO_URL = "https://github.com/anaskasasbeh/text-to-sql-sales-analyzer";
const PORTFOLIO_URL = "https://anaskasasbeh.onrender.com";

const STRINGS = {
  en: {
    title: "Text-to-SQL Sales Analyzer",
    lede: "Ask a question about 2,823 sales records in English or Arabic. An AI model writes the SQL query, and the app runs it on the data.",
    questionLabel: "Your question",
    placeholder: "e.g. Which country had the highest sales in 2004?",
    ask: "Ask",
    asking: "Writing SQL…",
    examplesLabel: "Try one:",
    examples: [
      "Total sales by product line",
      "Top 5 customers by sales",
      "Which country had the most orders in 2004?",
      "Monthly sales in 2004",
      "How many orders were cancelled?",
      "Sales in North America vs EMEA",
    ],
    sqlLabel: "SQL written by the model",
    copy: "Copy SQL",
    copied: "Copied",
    answerLabel: "Answer",
    answeredIn: (s) => `Answered in ${s} s.`,
    fixedOnce: "The first query failed, so the model fixed it once.",
    rowCount: (n) => (n === 1 ? "1 row." : `${n} rows.`),
    truncated: (n) => `Showing the first ${n} rows.`,
    noRows: "The query ran but found no matching rows.",
    aboutTitle: "About the data",
    aboutData: "Sample Sales Data (Kaggle, CC0): 2,823 order lines from 307 orders between January 2003 and May 2005. 92 customers in 19 countries buy scale models in 7 product lines, such as classic cars, motorcycles, planes and ships. Each row is one product inside an order.",
    aboutSafety: "The model sees only a description of the table, never the data itself. Every query runs read-only, one statement at a time, with a 3-second time limit and at most 200 rows.",
    footer: `Model: gpt-oss-120b on Groq. <a href="${REPO_URL}">Code on GitHub</a>. Built by <a href="${PORTFOLIO_URL}">Anas Kasasbeh</a>.`,
    switchTo: "العربية",
    errors: {
      invalid_question: "Type a question of up to 300 characters.",
      unanswerable: "This question can't be answered from the sales data. Ask about sales, orders, customers, products, countries or dates.",
      unsafe_sql: "The model wrote a query that does more than read data, so it was blocked. Only read-only queries run here.",
      sql_error: "The model's SQL didn't run, even after one fix. Try asking the question in a different way.",
      rate_limited: (s) => `You've asked a lot of questions in the last minute. Try again in ${s} seconds.`,
      llm_busy: "The free model quota is busy right now. Try again in about a minute.",
      llm_daily_limit: "Today's free model quota is used up. Try again tomorrow.",
      llm_unavailable: "The model service isn't reachable right now. Try again in a minute.",
      not_configured: "The demo isn't connected to the model right now.",
      network: "The server didn't respond. Check your connection and try again.",
    },
  },
  ar: {
    title: "محلّل المبيعات: من سؤال إلى SQL",
    lede: "اسأل عن 2,823 سجلّ مبيعات بالعربية أو الإنجليزية. يكتب نموذج ذكاء اصطناعي استعلام SQL، ثم يشغّله التطبيق على البيانات.",
    questionLabel: "سؤالك",
    placeholder: "مثلاً: أي دولة حققت أعلى مبيعات في 2004؟",
    ask: "اسأل",
    asking: "جارٍ كتابة SQL…",
    examplesLabel: "جرّب:",
    examples: [
      "إجمالي المبيعات لكل خط منتجات",
      "مين أكثر 5 زباين اشتروا؟",
      "أي دولة عندها أكثر طلبيات في 2004؟",
      "المبيعات الشهرية في 2004",
      "كم طلبية انلغت؟",
      "قديش مبيعات أمريكا الشمالية؟",
    ],
    sqlLabel: "استعلام SQL الذي كتبه النموذج",
    copy: "نسخ SQL",
    copied: "تم النسخ",
    answerLabel: "الجواب",
    answeredIn: (s) => `تمت الإجابة خلال ${s} ثانية.`,
    fixedOnce: "فشل الاستعلام الأول، فصحّحه النموذج مرة واحدة.",
    rowCount: (n) => `عدد الصفوف: ${n}.`,
    truncated: (n) => `تظهر أول ${n} صف فقط.`,
    noRows: "تم تنفيذ الاستعلام، لكن لا توجد صفوف مطابقة.",
    aboutTitle: "عن البيانات",
    aboutData: "بيانات مبيعات تجريبية (Kaggle، رخصة CC0): ‏2,823 سطر طلبية من 307 طلبيات بين يناير 2003 ومايو 2005. ‏92 زبوناً في 19 دولة يشترون مجسّمات في 7 خطوط منتجات، مثل السيارات الكلاسيكية والدراجات النارية والطائرات والسفن. كل صف هو منتج واحد داخل طلبية.",
    aboutSafety: "يرى النموذج وصف الجدول فقط، ولا يرى البيانات نفسها. كل استعلام يعمل للقراءة فقط، أمراً واحداً في كل مرة، بحد أقصى 3 ثوانٍ و200 صف.",
    footer: `النموذج: gpt-oss-120b على Groq. <a href="${REPO_URL}">الكود على GitHub</a>. من بناء <a href="${PORTFOLIO_URL}">أنس الكساسبة</a>.`,
    switchTo: "English",
    errors: {
      invalid_question: "اكتب سؤالاً لا يزيد عن 300 حرف.",
      unanswerable: "لا يمكن الإجابة عن هذا السؤال من بيانات المبيعات. اسأل عن المبيعات أو الطلبيات أو الزبائن أو المنتجات أو الدول أو التواريخ.",
      unsafe_sql: "كتب النموذج استعلاماً يفعل أكثر من قراءة البيانات، لذلك تم حظره. هنا تعمل استعلامات القراءة فقط.",
      sql_error: "لم يعمل استعلام النموذج حتى بعد تصحيحه مرة. جرّب صياغة السؤال بطريقة أخرى.",
      rate_limited: (s) => `سألت أسئلة كثيرة خلال الدقيقة الأخيرة. حاول مجدداً بعد ${s} ثانية.`,
      llm_busy: "الحصة المجانية للنموذج مشغولة الآن. حاول مجدداً بعد دقيقة تقريباً.",
      llm_daily_limit: "انتهت الحصة المجانية للنموذج لهذا اليوم. حاول مجدداً غداً.",
      llm_unavailable: "خدمة النموذج غير متاحة الآن. حاول مجدداً بعد دقيقة.",
      not_configured: "العرض غير متصل بالنموذج حالياً.",
      network: "لم يستجب الخادم. تحقّق من اتصالك وحاول مجدداً.",
    },
  },
};

const SQL_TOKEN =
  /('(?:[^']|'')*')|("(?:[^"]|"")*")|(\b\d+(?:\.\d+)?\b)|(\b(?:SELECT|FROM|WHERE|GROUP|BY|ORDER|HAVING|LIMIT|OFFSET|AS|AND|OR|NOT|IN|IS|NULL|LIKE|BETWEEN|JOIN|LEFT|INNER|ON|WITH|CASE|WHEN|THEN|ELSE|END|DISTINCT|DESC|ASC|UNION|ALL|OVER|PARTITION|SUM|COUNT|AVG|MIN|MAX|ROUND|STRFTIME|CAST|COALESCE)\b)/gi;

const els = {
  form: document.getElementById("ask-form"),
  input: document.getElementById("question"),
  button: document.getElementById("ask-button"),
  examples: document.getElementById("examples"),
  result: document.getElementById("result"),
  langSwitch: document.getElementById("lang-switch"),
};

let lang = initialLanguage();
let lastView = null; // { kind: "answer", data } or { kind: "error", code, retryAfter }

function initialLanguage() {
  try {
    const saved = localStorage.getItem("lang");
    if (saved === "en" || saved === "ar") return saved;
  } catch (_) {
    // Storage can be blocked; fall back to the browser language.
  }
  const languages = navigator.languages || [navigator.language || "en"];
  return languages.some((l) => String(l).toLowerCase().startsWith("ar")) ? "ar" : "en";
}

function t(key) {
  return STRINGS[lang][key];
}

function applyLanguage() {
  const html = document.documentElement;
  html.lang = lang;
  html.dir = lang === "ar" ? "rtl" : "ltr";
  document.title = t("title");
  document.querySelectorAll("[data-i18n]").forEach((el) => {
    el.textContent = t(el.dataset.i18n);
  });
  document.querySelectorAll("[data-i18n-html]").forEach((el) => {
    el.innerHTML = t(el.dataset.i18nHtml);
  });
  els.input.placeholder = t("placeholder");
  els.langSwitch.textContent = t("switchTo");
  els.langSwitch.lang = lang === "ar" ? "en" : "ar";
  renderExamples();
  if (lastView) render(lastView);
}

function renderExamples() {
  els.examples.replaceChildren(
    ...t("examples").map((text) => {
      const button = document.createElement("button");
      button.type = "button";
      button.textContent = text;
      button.addEventListener("click", () => {
        els.input.value = text;
        ask(text);
      });
      return button;
    }),
  );
}

function escapeHtml(text) {
  return String(text)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function highlightSql(sql) {
  let html = "";
  let last = 0;
  for (const match of sql.matchAll(SQL_TOKEN)) {
    html += escapeHtml(sql.slice(last, match.index));
    const [token, single, quoted, number, keyword] = match;
    if (quoted) {
      // Isolate quoted names (often Arabic aliases) so the quotes stay in place.
      html += `<span class="ident">"<bdi>${escapeHtml(token.slice(1, -1))}</bdi>"</span>`;
    } else {
      const cls = keyword ? "kw" : single || number ? "lit" : "";
      html += cls ? `<span class="${cls}">${escapeHtml(token)}</span>` : escapeHtml(token);
    }
    last = match.index + token.length;
  }
  return html + escapeHtml(sql.slice(last));
}

function isNumber(value) {
  return typeof value === "number" && Number.isFinite(value);
}

function formatValue(value, column) {
  if (value === null || value === undefined) return "—";
  if (!isNumber(value)) return String(value);
  const plain = /year|_id|number|code|سنة|عام/i.test(column);
  if (Number.isInteger(value)) {
    return plain ? String(value) : value.toLocaleString("en-US");
  }
  return value.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function renderAnswerBody(data) {
  const { columns, rows } = data;
  const box = el("div", "answer");
  box.append(el("span", "small-label", t("answerLabel")));

  if (rows.length === 0) {
    box.append(el("p", "meta", t("noRows")));
    return box;
  }

  // One value: show it as a figure.
  if (rows.length === 1 && columns.length === 1) {
    box.append(el("p", "figure", formatValue(rows[0][0], columns[0])));
    const label = el("p", "figure-label", columns[0]);
    label.dir = "auto";
    box.append(label);
    return box;
  }

  // Label + positive number: show bars.
  const chartable =
    columns.length === 2 &&
    rows.length >= 2 &&
    rows.length <= 25 &&
    rows.every((r) => !isNumber(r[0]) && isNumber(r[1]) && r[1] >= 0);
  if (chartable) {
    const max = Math.max(...rows.map((r) => r[1])) || 1;
    const list = el("ul", "bars");
    list.setAttribute("aria-label", `${columns[0]} / ${columns[1]}`);
    for (const [label, value] of rows) {
      const item = el("li");
      const name = el("span", "bar-label", formatValue(label, columns[0]));
      name.dir = "auto";
      const track = el("span", "bar-track");
      const fill = el("span", "bar-fill");
      fill.style.display = "block";
      fill.style.width = `${(value / max) * 100}%`;
      track.append(fill);
      item.append(name, track, el("span", "bar-value", formatValue(value, columns[1])));
      list.append(item);
    }
    box.append(list);
    return box;
  }

  const wrap = el("div", "table-wrap");
  const table = el("table");
  const head = el("tr");
  const numeric = columns.map((_, i) =>
    rows.every((r) => r[i] === null || isNumber(r[i])),
  );
  columns.forEach((c, i) => {
    const th = el("th", numeric[i] ? "num" : "", c);
    th.dir = "auto";
    head.append(th);
  });
  const thead = el("thead");
  thead.append(head);
  const body = el("tbody");
  for (const row of rows) {
    const tr = el("tr");
    row.forEach((value, i) => {
      const td = el("td", isNumber(value) ? "num" : "", formatValue(value, columns[i]));
      td.dir = "auto";
      tr.append(td);
    });
    body.append(tr);
  }
  table.append(thead, body);
  wrap.append(table);
  box.append(wrap);
  return box;
}

function renderAnswer(data) {
  const gloss = el("div", "gloss");
  const question = el("p", "gloss-question", data.question);
  question.dir = "auto";

  const head = el("div", "gloss-sql-head");
  head.append(el("span", "small-label", t("sqlLabel")));
  const copy = el("button", "copy", t("copy"));
  copy.type = "button";
  copy.addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(data.sql);
      copy.textContent = t("copied");
      setTimeout(() => (copy.textContent = t("copy")), 1500);
    } catch (_) {
      // Clipboard can be unavailable; the SQL stays selectable.
    }
  });
  head.append(copy);

  const pre = el("pre", "sql");
  pre.dir = "ltr";
  const code = el("code");
  code.innerHTML = highlightSql(data.sql);
  pre.append(code);
  gloss.append(question, head, pre);

  const notes = [t("answeredIn")((data.elapsed_ms / 1000).toFixed(1))];
  if (data.attempts > 1) notes.push(t("fixedOnce"));
  if (data.rows.length > 1) notes.push(t("rowCount")(data.row_count));
  if (data.truncated) notes.push(t("truncated")(data.row_count));

  els.result.replaceChildren(gloss, renderAnswerBody(data), el("p", "meta", notes.join(" ")));
}

function renderError(code, retryAfter) {
  const messages = t("errors");
  const message = messages[code] || messages.llm_unavailable;
  const text = typeof message === "function" ? message(retryAfter || 30) : message;
  const box = el("div", code === "unanswerable" ? "message neutral" : "message");
  box.append(el("p", "", text));
  els.result.replaceChildren(box);
}

function render(view) {
  if (view.kind === "answer") renderAnswer(view.data);
  else renderError(view.code, view.retryAfter);
}

async function ask(question) {
  const text = question.trim();
  if (!text) {
    els.input.focus();
    return;
  }
  els.button.disabled = true;
  els.button.textContent = t("asking");
  try {
    const response = await fetch("/api/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: text }),
    });
    const data = await response.json().catch(() => ({}));
    lastView = response.ok
      ? { kind: "answer", data }
      : { kind: "error", code: data.error?.code, retryAfter: data.retry_after };
  } catch (_) {
    lastView = { kind: "error", code: "network" };
  } finally {
    els.button.disabled = false;
    els.button.textContent = t("ask");
  }
  render(lastView);
  const top = els.result.getBoundingClientRect().top;
  if (top > window.innerHeight * 0.6) {
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    els.result.scrollIntoView({ behavior: reduce ? "auto" : "smooth", block: "start" });
  }
}

els.form.addEventListener("submit", (event) => {
  event.preventDefault();
  ask(els.input.value);
});

els.langSwitch.addEventListener("click", () => {
  lang = lang === "ar" ? "en" : "ar";
  try {
    localStorage.setItem("lang", lang);
  } catch (_) {
    // Ignore: the choice just won't be remembered.
  }
  applyLanguage();
});

applyLanguage();
