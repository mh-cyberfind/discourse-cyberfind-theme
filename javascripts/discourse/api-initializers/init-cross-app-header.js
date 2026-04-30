// init-cross-app-header.js
// Injects the always-dark CyberFind cross-app header above Discourse's native header.
// Reads currentUser from Discourse's app state to render live avatar + display name.
import { apiInitializer } from "discourse/lib/api";

const CYBERFIND_HOME = "https://cyberfind.io";
const INTELHUB_URL = "https://intel.cyberfind.io";

const LOGO_SVG = `<svg class="ca-logo" viewBox="0 0 20 20" width="20" height="20" aria-hidden="true" xmlns="http://www.w3.org/2000/svg">
  <rect width="20" height="20" rx="4" fill="#59BA35"/>
</svg>`;

function buildUserZone(currentUser) {
  if (!currentUser) {
    return `<a href="/login" class="ca-signin">Sign in</a>`;
  }
  const avatarUrl = currentUser
    .get("avatar_template")
    .replace("{size}", "28");
  const displayName =
    currentUser.get("name") || currentUser.get("username");
  return `
    <div class="ca-user-zone">
      <img
        class="ca-avatar"
        src="${avatarUrl}"
        alt="${displayName}"
        width="28"
        height="28"
      />
      <span class="ca-display-name">${displayName}</span>
    </div>`;
}

function buildBar(currentUser) {
  return `
    <div class="cyberfind-cross-app-header">
      <div class="ca-inner">
        <a href="${CYBERFIND_HOME}" class="ca-brand" aria-label="CyberFind home">
          ${LOGO_SVG}
          <span class="ca-wordmark">CyberFind</span>
        </a>
        <nav class="ca-products" aria-label="CyberFind products">
          <a href="${INTELHUB_URL}" class="ca-product-pill">IntelHub</a>
          <span class="ca-product-pill ca-product-active" aria-current="page">Community</span>
        </nav>
        ${buildUserZone(currentUser)}
      </div>
    </div>`;
}

function injectHeader(api) {
  const existing = document.querySelector(".cyberfind-cross-app-header");
  if (existing) existing.remove();

  const currentUser = api.getCurrentUser();
  const wrapper = document.createElement("div");
  wrapper.innerHTML = buildBar(currentUser);
  const bar = wrapper.firstElementChild;

  const discourseHeader = document.querySelector(".d-header");
  if (discourseHeader) {
    discourseHeader.parentNode.insertBefore(bar, discourseHeader);
  } else {
    document.body.prepend(bar);
  }
}

export default apiInitializer("1.8.0", (api) => {
  api.onPageChange(() => injectHeader(api));
});
