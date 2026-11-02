// Text-to-SQL Sales Analyzer: page logic (no framework).

const REPO_URL = "https://github.com/anaskasasbeh/text-to-sql-sales-analyzer";
const PORTFOLIO_URL = "https://anaskasasbeh.onrender.com";
const DATA_URL = "https://www.kaggle.com/datasets/kyanyoga/sample-sales-data";

// Real rows from data/sales_data_sample.csv, shown in "What's in the data".
const SAMPLE_COLUMNS = [
  "ORDERNUMBER",
  "ORDERDATE",
  "CUSTOMERNAME",
  "COUNTRY",
  "PRODUCTLINE",
  "QUANTITYORDERED",
  "SALES",
  "STATUS",
];
const SAMPLE_ROWS = [
  [10107, "2003-02-24", "Land of Toys Inc.", "USA", "Motorcycles", 30, 2871.0, "Shipped"],
  [10126, "2003-05-28", "Corrida Auto Replicas, Ltd", "Spain", "Classic Cars", 38, 7329.06, "Shipped"],
  [10361, "2004-12-17", "Souveniers And Things Co.", "Australia", "Ships", 24, 1089.36, "Shipped"],
];

const STRINGS = {
  en: {
    title: "Text-to-SQL Sales Analyzer",
    lede: "Ask a question about a company's sales in plain English or Arabic. AI turns it into SQL, and the app shows you the answer.",
    questionLabel: "Your question",
    placeholder: "e.g. Which country had the highest sales in 2004?",
    ask: "Ask",
    asking: "Asking…",
    working: "Writing the SQL query…",
    examplesLabel: "Try one:",
    examples: [
      "Total sales by product line",
      "Top 5 customers by sales",
      "Which country had the most orders in 2004?",
      "Monthly sales in 2004",
      "How many orders were cancelled?",
      "Sales in North America vs EMEA",
    ],
    sqlLabel: "SQL written by the AI",
    copy: "Copy SQL",
    copied: "Copied",
    answerLabel: "Answer",
    answeredIn: (s) => `Answered in ${s} s.`,
    fixedOnce: "The first query failed, so the AI fixed it once.",
    rowCount: (n) => (n === 1 ? "1 row." : `${n} rows.`),
    truncated: (n) => `Showing the first ${n} rows.`,
    noRows: "The query ran but found no matching rows.",
    howTitle: "How it works",
    step1Title: "You ask",
    step1Body: "Type a question in English or Arabic, even in Jordanian dialect.",
    step2Title: "AI writes the SQL",
    step2Body: "gpt-oss-120b (on Groq) reads a description of the table, not the data itself, and writes one SQL query.",
    step3Title: "The app runs it safely",
    step3Body: "The query is checked first and can only read data. You see both the SQL and the answer.",
    dataTitle: "What's in the data",
    dataIntro: "One table of orders from a company that sells scale models (cars, motorcycles, planes, ships and trains) to shops around the world.",
    facts: [
      ["2,823", "order lines"],
      ["307", "orders"],
      ["92", "customers"],
      ["19", "countries"],
      ["7", "product lines"],
      ["2003–2005", "Jan 2003 to May 2005"],
    ],
    dataNote: "Each row is one product inside an order. 8 of the 25 columns are shown; the others hold the customer's address and contact, unit price, deal size and sales territory.",
    notInDataTitle: "Not in the data:",
    notInData: "costs or profit, salespeople, stock levels, or anything before January 2003 or after May 2005.",
    footer: `<a href="${REPO_URL}">Code on GitHub</a>. Built by <a href="${PORTFOLIO_URL}">Anas Kasasbeh</a>. Data: <a href="${DATA_URL}">Sample Sales Data</a> (Kaggle, CC0).`,
    switchTo: "العربية",
    unanswerable: "This can't be answered from the sales data.",
    seeData: "See what's in the data",
    errors: {
      invalid_question: "Type a question of up to 300 characters.",
      unsafe_sql: "The AI wrote a query that does more than read data, so it was blocked. Only read-only queries run here.",
      sql_error: "The AI's SQL didn't run, even after one fix. Try asking the question in a different way.",
      rate_limited: (s) => `You've asked a lot of questions in the last minute. Try again in ${s} seconds.`,
      llm_busy: "The free AI quota is busy right now. Try again in about a minute.",
      llm_daily_limit: "Today's free AI quota is used up. Try again tomorrow.",
      llm_unavailable: "The AI service isn't reachable right now. Try again in a minute.",
      not_configured: "The demo isn't connected to the AI right now.",
      network: "The server didn't respond. Check your connection and try again.",
    },
  },
  ar: {
    title: "محلّل المبيعات: من سؤال إلى SQL",
    lede: "اسأل عن مبيعات شركة بالعربية أو الإنجليزية. يحوّل الذكاء الاصطناعي سؤالك إلى SQL، ويعرض لك التطبيق الجواب.",
    questionLabel: "سؤالك",
    placeholder: "مثلاً: أي دولة حققت أعلى مبيعات في 2004؟",
    ask: "اسأل",
    asking: "جارٍ السؤال…",
    working: "جارٍ كتابة استعلام SQL…",
    examplesLabel: "جرّب:",
    examples: [
      "إجمالي المبيعات لكل خط منتجات",
      "مين أكثر 5 زباين اشتروا؟",
      "أي دولة عندها أكثر طلبيات في 2004؟",
      "المبيعات الشهرية في 2004",
      "كم طلبية انلغت؟",
      "قديش مبيعات أمريكا الشمالية؟",
    ],
    sqlLabel: "استعلام SQL الذي كتبه الذكاء الاصطناعي",
    copy: "نسخ SQL",
    copied: "تم النسخ",
    answerLabel: "الجواب",
    answeredIn: (s) => `تمت الإجابة خلال ${s} ثانية.`,
    fixedOnce: "فشل الاستعلام الأول، فصحّحه الذكاء الاصطناعي مرة واحدة.",
    rowCount: (n) => `عدد الصفوف: ${n}.`,
    truncated: (n) => `تظهر أول ${n} صف فقط.`,
    noRows: "تم تنفيذ الاستعلام، لكن لا توجد صفوف مطابقة.",
    howTitle: "كيف يعمل",
    step1Title: "تسأل",
    step1Body: "اكتب سؤالك بالعربية أو الإنجليزية، حتى باللهجة الأردنية.",
    step2Title: "الذكاء الاصطناعي يكتب SQL",
    step2Body: "يقرأ نموذج gpt-oss-120b (على Groq) وصف الجدول فقط، لا البيانات نفسها، ثم يكتب استعلام SQL واحداً.",
    step3Title: "التطبيق ينفّذه بأمان",
    step3Body: "يُفحص الاستعلام أولاً، ولا يستطيع إلا قراءة البيانات. وترى الـ SQL والجواب معاً.",
    dataTitle: "ماذا يوجد في البيانات",
    dataIntro: "جدول واحد لطلبيات شركة تبيع مجسّمات (سيارات ودراجات نارية وطائرات وسفن وقطارات) لمتاجر حول العالم.",
    facts: [
      ["2,823", "سطر طلبية"],
      ["307", "طلبية"],
      ["92", "زبوناً"],
      ["19", "دولة"],
      ["7", "خطوط منتجات"],
      ["2003–2005", "من يناير 2003 إلى مايو 2005"],
    ],
    dataNote: "كل صف هو منتج واحد داخل طلبية. يظهر هنا 8 أعمدة من أصل 25، والباقي فيه عنوان الزبون وجهة الاتصال وسعر القطعة وحجم الصفقة ومنطقة المبيعات.",
    notInDataTitle: "غير موجود في البيانات:",
    notInData: "التكاليف أو الأرباح، ومندوبو المبيعات، والمخزون، وأي فترة قبل يناير 2003 أو بعد مايو 2005.",
    footer: `<a href="${REPO_URL}">الكود على GitHub</a>. من بناء <a href="${PORTFOLIO_URL}">أنس الكساسبة</a>. البيانات: <a href="${DATA_URL}">Sample Sales Data</a> (Kaggle، رخصة CC0).`,
    switchTo: "English",
    unanswerable: "لا يمكن الإجابة عن هذا من بيانات المبيعات.",
    seeData: "اطّلع على محتوى البيانات",
    errors: {
      invalid_question: "اكتب سؤالاً لا يزيد عن 300 حرف.",
      unsafe_sql: "كتب الذكاء الاصطناعي استعلاماً يفعل أكثر من قراءة البيانات، لذلك تم حظره. هنا تعمل استعلامات القراءة فقط.",
      sql_error: "لم يعمل استعلام الذكاء الاصطناعي حتى بعد تصحيحه مرة. جرّب صياغة السؤال بطريقة أخرى.",
      rate_limited: (s) => `سألت أسئلة كثيرة خلال الدقيقة الأخيرة. حاول مجدداً بعد ${s} ثانية.`,
      llm_busy: "الحصة المجانية للذكاء الاصطناعي مشغولة الآن. حاول مجدداً بعد دقيقة تقريباً.",
      llm_daily_limit: "انتهت الحصة المجانية للذكاء الاصطناعي لهذا اليوم. حاول مجدداً غداً.",
      llm_unavailable: "خدمة الذكاء الاصطناعي غير متاحة الآن. حاول مجدداً بعد دقيقة.",
      not_configured: "العرض غير متصل بالذكاء الاصطناعي حالياً.",
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
  facts: document.getElementById("facts"),
  sample: document.getElementById("sample"),
};

let lang = initialLanguage();
let lastView = null; // { kind: "answer" | "error" | "working", ... }

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

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function applyLanguage() {
  const html = document.documentElement;
  html.lang = lang;
  html.dir = lang === "ar" ? "rtl" : "ltr";
  document.title = t("title");
  document.querySelectorAll("[data-i18n]").forEach((node) => {
    node.textContent = t(node.dataset.i18n);
  });
  document.querySelectorAll("[data-i18n-html]").forEach((node) => {
    node.innerHTML = t(node.dataset.i18nHtml);
  });
  els.input.placeholder = t("placeholder");
  els.langSwitch.textContent = t("switchTo");
  els.langSwitch.lang = lang === "ar" ? "en" : "ar";
  renderExamples();
  renderFacts();
  if (lastView) render(lastView);
}

function renderExamples() {
  els.examples.replaceChildren(
    ...t("examples").map((text) => {
      const button = el("button", "", text);
      button.type = "button";
      button.addEventListener("click", () => {
        els.input.value = text;
        ask(text);
      });
      return button;
    }),
  );
}

function renderFacts() {
  els.facts.replaceChildren(
    ...t("facts").map(([value, label]) => {
      const item = el("div");
      const number = el("bdi", "", value); // keeps "2003–2005" in order in Arabic
      number.dir = "ltr";
      const dd = el("dd");
      dd.append(number);
      item.append(el("dt", "", label), dd);
      return item;
    }),
  );
}

function renderSample() {
  const head = el("tr");
  SAMPLE_COLUMNS.forEach((c, i) => head.append(el("th", isNumber(SAMPLE_ROWS[0][i]) ? "num" : "", c)));
  const thead = el("thead");
  thead.append(head);
  const body = el("tbody");
  for (const row of SAMPLE_ROWS) {
    const tr = el("tr");
    row.forEach((value, i) => {
      tr.append(el("td", isNumber(value) ? "num" : "", formatValue(value, SAMPLE_COLUMNS[i])));
    });
    body.append(tr);
  }
  els.sample.replaceChildren(thead, body);
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
      // Isolate quoted names so the quotes stay in place next to Arabic text.
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
  const plain = /year|_id|number|code|month/i.test(column);
  if (Number.isInteger(value) && !/sales|revenue|total|amount|value/i.test(column)) {
    return plain ? String(value) : value.toLocaleString("en-US");
  }
  return value.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

// "total_sales" -> "Total sales". Other names are shown as they are.
function prettyColumn(name) {
  if (!/^[a-z][a-z0-9_]*$/.test(name)) return name;
  const words = name.replaceAll("_", " ");
  return words.charAt(0).toUpperCase() + words.slice(1);
}

function renderAnswerBody(data) {
  const { columns, rows } = data;
  const box = el("div", "answer");
  box.append(el("span", "small-label", t("answerLabel")));

  if (rows.length === 0) {
    box.append(el("p", "meta", t("noRows")));
    return box;
  }

  if (rows.length === 1 && columns.length === 1) {
    box.append(el("p", "figure", formatValue(rows[0][0], columns[0])));
    box.append(el("p", "figure-label", prettyColumn(columns[0])));
    return box;
  }

  const chartable =
    columns.length === 2 &&
    rows.length >= 2 &&
    rows.length <= 25 &&
    rows.every((r) => !isNumber(r[0]) && isNumber(r[1]) && r[1] >= 0);
  if (chartable) {
    const max = Math.max(...rows.map((r) => r[1])) || 1;
    const list = el("ul", "bars");
    list.setAttribute("aria-label", `${prettyColumn(columns[0])} / ${prettyColumn(columns[1])}`);
    for (const [label, value] of rows) {
      const item = el("li");
      const name = el("span", "bar-label", formatValue(label, columns[0]));
      name.dir = "auto";
      const track = el("span", "bar-track");
      const fill = el("span", "bar-fill");
      fill.style.width = `${(value / max) * 100}%`;
      track.append(fill);
      item.append(name, track, el("span", "bar-value", formatValue(value, columns[1])));
      list.append(item);
    }
    box.append(list);
    return box;
  }

  const numeric = columns.map((_, i) => rows.every((r) => r[i] === null || isNumber(r[i])));
  const head = el("tr");
  columns.forEach((c, i) => {
    const th = el("th", numeric[i] ? "num" : "", prettyColumn(c));
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
  const table = el("table");
  table.append(thead, body);
  const wrap = el("div", "table-wrap");
  wrap.append(table);
  box.append(wrap);
  return box;
}

function questionLine(text) {
  const question = el("p", "gloss-question", text);
  question.dir = "auto";
  return question;
}

function renderWorking(question) {
  const gloss = el("div", "gloss");
  gloss.append(questionLine(question), el("p", "working", t("working")), el("div", "progress"));
  els.result.replaceChildren(gloss);
}

function renderAnswer(data) {
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

  const gloss = el("div", "gloss");
  gloss.append(questionLine(data.question), head, pre);

  const notes = [t("answeredIn")((data.elapsed_ms / 1000).toFixed(1))];
  if (data.attempts > 1) notes.push(t("fixedOnce"));
  if (data.rows.length > 1) notes.push(t("rowCount")(data.row_count));
  if (data.truncated) notes.push(t("truncated")(data.row_count));

  els.result.replaceChildren(gloss, renderAnswerBody(data), el("p", "meta", notes.join(" ")));
}

function renderUnanswerable(view) {
  const box = el("div", "message neutral");
  box.append(el("p", "", t("unanswerable")));
  if (view.reason) {
    const reason = el("p", "reason", view.reason);
    reason.dir = "auto";
    box.append(reason);
  }
  const hint = el("p", "hint");
  const link = el("a", "", t("seeData"));
  link.href = "#data";
  hint.append(link);
  box.append(hint);
  els.result.replaceChildren(questionLine(view.question), box);
}

function renderError(view) {
  if (view.code === "unanswerable") {
    renderUnanswerable(view);
    return;
  }
  const messages = t("errors");
  const message = messages[view.code] || messages.llm_unavailable;
  const text = typeof message === "function" ? message(view.retryAfter || 30) : message;
  const box = el("div", "message");
  box.append(el("p", "", text));
  els.result.replaceChildren(box);
}

function render(view) {
  if (view.kind === "answer") renderAnswer(view.data);
  else if (view.kind === "working") renderWorking(view.question);
  else renderError(view);
}

function bringResultIntoView() {
  const top = els.result.getBoundingClientRect().top;
  if (top > window.innerHeight * 0.6 || top < 0) {
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    els.result.scrollIntoView({ behavior: reduce ? "auto" : "smooth", block: "start" });
  }
}

async function ask(question) {
  const text = question.trim();
  if (!text) {
    els.input.focus();
    return;
  }
  els.button.disabled = true;
  els.button.textContent = t("asking");
  lastView = { kind: "working", question: text };
  render(lastView);
  bringResultIntoView();
  try {
    const response = await fetch("/api/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: text }),
    });
    const data = await response.json().catch(() => ({}));
    lastView = response.ok
      ? { kind: "answer", data }
      : {
          kind: "error",
          code: data.error?.code,
          reason: data.reason,
          retryAfter: data.retry_after,
          question: text,
        };
  } catch (_) {
    lastView = { kind: "error", code: "network", question: text };
  } finally {
    els.button.disabled = false;
    els.button.textContent = t("ask");
  }
  render(lastView);
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

renderSample();
applyLanguage();
