const $ = (id) => document.getElementById(id);
const API = "/api/v1";

let currentUser = null;
let authMode = "login";

// ---------- утилиты ----------

const escapeHtml = (text) => String(text)
  .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
  .replace(/"/g, "&quot;");

function showToast(message, type = "success") {
  const toast = $("toast");
  toast.textContent = message;
  toast.className = `toast toast-${type}`;
  setTimeout(() => toast.classList.add("hidden"), 2500);
}

function authHeaders() {
  const token = localStorage.getItem("token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

// ---------- авторизация ----------

async function loadMe() {
  const token = localStorage.getItem("token");
  if (!token) { currentUser = null; renderAuthPanel(); return; }
  const res = await fetch(`${API}/auth/me`, { headers: authHeaders() });
  if (res.ok) {
    currentUser = await res.json();
  } else {
    localStorage.removeItem("token");
    currentUser = null;
  }
  renderAuthPanel();
}

function renderAuthPanel() {
  const panel = $("auth-panel");
  if (currentUser) {
    panel.innerHTML = `
      <span class="user-badge">${escapeHtml(currentUser.username)}${currentUser.is_admin ? " · админ" : ""}</span>
      <button id="logout-btn" class="btn btn-secondary" type="button">Выйти</button>`;
    $("logout-btn").addEventListener("click", () => {
      localStorage.removeItem("token");
      currentUser = null;
      renderAuthPanel();
      loadLinks();
      showToast("Вы вышли из аккаунта");
    });
    $("clear-btn").classList.toggle("hidden", !currentUser.is_admin);
    $("users-btn").classList.toggle("hidden", !currentUser.is_admin);
    $("author-header").classList.toggle("hidden", !currentUser.is_admin);
  } else {
    panel.innerHTML = `<button id="login-btn" class="btn btn-primary" type="button">🔐 Войти</button>`;
    $("login-btn").addEventListener("click", () => openAuth("login"));
    $("clear-btn").classList.add("hidden");
    $("users-btn").classList.add("hidden");
    $("author-header").classList.add("hidden");
  }
  renderAccessGate();
}

function renderAccessGate() {
  const authed = !!currentUser;
  $("app-section").classList.toggle("hidden", !authed);
  $("login-wall").classList.toggle("hidden", authed);
}

function openAuth(mode) {
  authMode = mode;
  $("auth-title").textContent = mode === "login" ? "Вход" : "Регистрация";
  $("auth-submit").textContent = mode === "login" ? "Войти" : "Создать аккаунт";
  $("auth-toggle").textContent = mode === "login" ? "Нет аккаунта? Зарегистрируйся" : "Уже есть аккаунт? Войти";
  $("auth-error").classList.add("hidden");
  $("auth-modal").classList.remove("hidden");
}

$("auth-toggle").addEventListener("click", () => openAuth(authMode === "login" ? "register" : "login"));
$("auth-close").addEventListener("click", () => $("auth-modal").classList.add("hidden"));
$("auth-modal").addEventListener("click", (e) => {
  if (e.target === $("auth-modal")) $("auth-modal").classList.add("hidden");
});

$("auth-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const body = {
    username: $("auth-username").value,
    password: $("auth-password").value,
  };
  const path = authMode === "login" ? "/auth/login" : "/auth/register";
  const res = await fetch(`${API}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (authMode === "register" && res.status === 201) {
    showToast("Аккаунт создан — теперь войди");
    openAuth("login");
    return;
  }
  if (authMode === "login" && res.ok) {
    const data = await res.json();
    localStorage.setItem("token", data.access_token);
    $("auth-modal").classList.add("hidden");
    await loadMe();
    await loadLinks();
    showToast(`Привет, ${currentUser.username}!`);
    return;
  }
  const detail = await res.json().catch(() => ({}));
  $("auth-error").textContent = detail.detail || "Не удалось выполнить операцию";
  $("auth-error").classList.remove("hidden");
});

// ---------- ссылки ----------

async function loadLinks() {
  if (!currentUser) {
    $("links-body").innerHTML = "";
    return;
  }
  const res = await fetch(`${API}/links`, { headers: authHeaders() });
  if (!res.ok) {
    $("links-body").innerHTML = "";
    return;
  }
  const links = await res.json();
  const body = $("links-body");
  body.innerHTML = "";
  $("empty").classList.toggle("hidden", links.length > 0);

  for (const link of links) {
    const canDelete = currentUser && (currentUser.is_admin || currentUser.id === link.owner_id);
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td><a href="/${link.short_code}" target="_blank">${link.short_code}</a></td>
      <td class="original" title="${escapeHtml(link.original_url)}">${escapeHtml(link.original_url)}</td>
      <td class="clicks">${link.click_count}</td>
      <td>${new Date(link.created_at).toLocaleString("ru-RU")}</td>
      ${currentUser.is_admin ? `<td>${escapeHtml(link.owner_username || "—")}</td>` : ""}
      <td class="row-actions">
        <button class="icon-btn stats-btn" data-id="${link.id}" title="Аналитика">📊</button>
        ${canDelete ? `<button class="icon-btn delete-btn" data-id="${link.id}" title="Удалить">🗑</button>` : ""}
      </td>
    `;
    body.appendChild(tr);
  }
}

async function createLink(event) {
  event.preventDefault();
  const url = $("url-input").value;
  $("error").classList.add("hidden");
  $("result").classList.add("hidden");

  const res = await fetch(`${API}/links`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify({ original_url: url }),
  });

  if (res.status === 201) {
    const data = await res.json();
    const link = $("short-link");
    link.textContent = data.short_url;
    link.href = data.short_url;
    $("result").classList.remove("hidden");
    $("url-input").value = "";
    await loadLinks();
    showToast("Ссылка создана");
  } else if (res.status === 401) {
    showToast("Сессия истекла — войди заново", "error");
    localStorage.removeItem("token");
    currentUser = null;
    renderAuthPanel();
  } else {
    $("error").textContent = "Не удалось создать ссылку. Проверь формат URL.";
    $("error").classList.remove("hidden");
  }
}

async function deleteLink(linkId) {
  if (!confirm("Удалить ссылку вместе со всеми кликами?")) return;
  const res = await fetch(`${API}/links/${linkId}`, {
    method: "DELETE",
    headers: authHeaders(),
  });
  if (res.status === 204) {
    showToast("Ссылка удалена");
    await loadLinks();
  } else if (res.status === 403) {
    showToast("Удалять может только владелец или админ", "error");
  } else {
    showToast("Не удалось удалить ссылку", "error");
  }
}

async function clearAll() {
  if (!confirm("Очистить БД: удалить ВСЕ ссылки и клики? Действие необратимо.")) return;
  const res = await fetch(`${API}/links`, { method: "DELETE", headers: authHeaders() });
  if (res.ok) {
    const data = await res.json().catch(() => ({}));
    showToast(`База данных очищена (удалено ссылок: ${data.deleted ?? "—"})`);
    await loadLinks();
  } else {
    showToast("Недостаточно прав", "error");
  }
}

// ---------- аналитика кликов ----------

async function showClicks(linkId) {
  const res = await fetch(`${API}/links/${linkId}/clicks`, { headers: authHeaders() });
  if (!res.ok) {
    showToast("Аналитика недоступна", "error");
    return;
  }
  const clicks = await res.json();
  const body = $("clicks-body");
  body.innerHTML = "";
  $("clicks-empty").classList.toggle("hidden", clicks.length > 0);
  $("modal-title").textContent = `Аналитика кликов (${clicks.length})`;

  for (const click of clicks) {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${new Date(click.clicked_at).toLocaleString("ru-RU")}</td>
      <td>${escapeHtml(click.ip_address || "—")}</td>
      <td>${escapeHtml(click.user_agent || "—")}</td>
      <td>${escapeHtml(click.referer || "—")}</td>
    `;
    body.appendChild(tr);
  }
  $("modal").classList.remove("hidden");
}

// ---------- обработчики ----------

$("create-form").addEventListener("submit", createLink);
$("refresh-btn").addEventListener("click", loadLinks);
$("clear-btn").addEventListener("click", clearAll);
$("wall-login-btn").addEventListener("click", () => openAuth("login"));
$("wall-register-btn").addEventListener("click", () => openAuth("register"));
$("modal-close").addEventListener("click", () => $("modal").classList.add("hidden"));
$("modal").addEventListener("click", (e) => {
  if (e.target === $("modal")) $("modal").classList.add("hidden");
});
$("links-body").addEventListener("click", (e) => {
  const stats = e.target.closest(".stats-btn");
  if (stats) showClicks(stats.dataset.id);
  const del = e.target.closest(".delete-btn");
  if (del) deleteLink(del.dataset.id);
});
$("copy-btn").addEventListener("click", () => {
  navigator.clipboard.writeText($("short-link").textContent);
  $("copy-btn").textContent = "✅ Скопировано";
  setTimeout(() => ($("copy-btn").textContent = "📋 Копировать"), 1500);
});

loadMe().then(loadLinks);

// ---------- админ: управление пользователями ----------

async function loadUsers() {
  const res = await fetch(`${API}/admin/users`, { headers: authHeaders() });
  if (!res.ok) {
    showToast("Список пользователей недоступен", "error");
    return;
  }
  const users = await res.json();
  const body = $("users-body");
  body.innerHTML = "";
  for (const user of users) {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${user.id}</td>
      <td>${escapeHtml(user.username)}</td>
      <td><span class="role-badge ${user.is_admin ? "role-admin" : "role-user"}">${user.is_admin ? "админ" : "пользователь"}</span></td>
      <td>${new Date(user.created_at).toLocaleString("ru-RU")}</td>
      <td class="row-actions">
        <button class="icon-btn reset-btn" data-id="${user.id}" data-name="${escapeHtml(user.username)}" title="Сбросить пароль">🔑</button>
        <button class="icon-btn role-btn" data-id="${user.id}" data-name="${escapeHtml(user.username)}" data-admin="${user.is_admin}" title="Сменить роль">🎭</button>
        <button class="icon-btn user-delete-btn" data-id="${user.id}" data-name="${escapeHtml(user.username)}" title="Удалить">🗑</button>
      </td>
    `;
    body.appendChild(tr);
  }
}

async function resetUserPassword(userId, username) {
  const newPassword = prompt(`Новый пароль для ${username} (минимум 6 символов):`);
  if (!newPassword) return;
  if (newPassword.length < 6) {
    showToast("Пароль слишком короткий", "error");
    return;
  }
  const res = await fetch(`${API}/admin/users/${userId}/reset-password`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify({ new_password: newPassword }),
  });
  if (res.status === 204) showToast(`Пароль ${username} сброшен`);
  else showToast("Не удалось сбросить пароль", "error");
}

async function toggleUserRole(userId, username, isAdmin) {
  const action = isAdmin ? "Разжаловать в пользователя" : "Повысить до админа";
  if (!confirm(`${action}: ${username}?`)) return;
  const res = await fetch(`${API}/admin/users/${userId}/role`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify({ is_admin: !isAdmin }),
  });
  if (res.ok) {
    showToast(`Роль ${username} изменена`);
    await loadUsers();
  } else if (res.status === 409) {
    showToast("Нельзя снять с себя права админа", "error");
  } else {
    showToast("Не удалось изменить роль", "error");
  }
}

async function deleteUser(userId, username) {
  if (!confirm(`Удалить пользователя ${username}? Его ссылки станут без владельца.`)) return;
  const res = await fetch(`${API}/admin/users/${userId}`, {
    method: "DELETE",
    headers: authHeaders(),
  });
  if (res.status === 204) {
    showToast(`Пользователь ${username} удалён`);
    await loadUsers();
    await loadLinks();
  } else if (res.status === 409) {
    showToast("Нельзя удалить собственный аккаунт", "error");
  } else {
    showToast("Не удалось удалить пользователя", "error");
  }
}

$("users-btn").addEventListener("click", async () => {
  await loadUsers();
  $("users-modal").classList.remove("hidden");
});
$("users-close").addEventListener("click", () => $("users-modal").classList.add("hidden"));
$("users-modal").addEventListener("click", (e) => {
  if (e.target === $("users-modal")) $("users-modal").classList.add("hidden");
});
$("users-body").addEventListener("click", (e) => {
  const reset = e.target.closest(".reset-btn");
  if (reset) resetUserPassword(reset.dataset.id, reset.dataset.name);
  const role = e.target.closest(".role-btn");
  if (role) toggleUserRole(role.dataset.id, role.dataset.name, role.dataset.admin === "true");
  const del = e.target.closest(".user-delete-btn");
  if (del) deleteUser(del.dataset.id, del.dataset.name);
});