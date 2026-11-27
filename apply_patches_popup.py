#!/usr/bin/env python3
"""
Popup redesign for the Violentmonkey fork. Run after the other patches, from the repo root:

    python3 apply_patches_addmatch.py && python3 apply_patches_material.py \
      && python3 apply_patches_popup.py [repo_root]

Adds: script search with history, modern "find scripts" card, aligned group header,
tree-style command menu with icons, bigger 3-dot menus with script title and icons.
"""
import sys
from pathlib import Path

# Each patch: (file, old, new). `old` must appear EXACTLY once in `file`.
PATCHES = [
    (
        'src/popup/index.js',
        r"""import App from './views/app';""",
        r"""import App from './views/app';
import './modern.css';""",
    ),
    # ---------- strings ----------
    (
        '_locales/en/messages.yml',
        r"""menuFindScripts:
  description: Menu item to find scripts for a site.
  message: Find scripts for this site
""",
        r"""menuFindScripts:
  description: Menu item to find scripts for a site.
  message: Find scripts for this site
menuSearchClearAll:
  description: Button in popup search history that removes every entry.
  message: Clear all
menuSearchNoResults:
  description: Shown in popup when no script matches the search text.
  message: No scripts match
menuSearchPlaceholder:
  description: Placeholder of the script search box in popup.
  message: Search scripts by name
menuSearchRecent:
  description: Heading of the search history list in popup.
  message: Recent searches
menuSearchScripts:
  description: Tooltip of the search button in popup.
  message: Search scripts
menuSearchShowLess:
  description: Button that collapses the search history list.
  message: Show less
menuSearchShowMore:
  description: Button that expands the search history list.
  message: Show more
""",
    ),
    # ---------- template: top bar search button ----------
    (
        'src/popup/views/app.vue',
        r"""      <VmVersion class="flex-1 ext-name"/>
""",
        r"""      <VmVersion class="flex-1 ext-name"/>
      <span
        class="menu-area menu-search-btn"
        :class="{ active: searchOpen }"
        :data-message="i18n('menuSearchScripts')"
        :tabIndex
        @click.stop="toggleSearch">
        <svg class="icon icon-search" viewBox="0 0 24 24"><circle cx="10" cy="10" r="6.4"/><path d="M15 15l6 6"/></svg>
      </span>
""",
    ),
    # ---------- template: search panel + find card ----------
    (
        'src/popup/views/app.vue',
        r"""    <div class="menu" v-if="store.injectable" v-show="store.domain">
      <div class="menu-item menu-area menu-find">
        <template v-for="(url, text, i) in findUrls" :key="url">
          <a target="_blank" :class="{ ellipsis: !i, 'mr-1': !i, 'ml-1': i }"
             :href="url" :data-message="url.split('://')[1]" :tabIndex>
            <icon name="search" v-if="!i"/>{{text}}
          </a>
          <template v-if="!i">/</template>
        </template>
      </div>
    </div>
""",
        r"""    <div class="vm-search" v-if="searchOpen" @click.stop>
      <div class="vm-search-box">
        <IconSearch class="vm-search-lead"/>
        <input
          ref="$searchInput"
          v-model="searchQuery"
          type="text"
          class="vm-search-input"
          :placeholder="i18n('menuSearchPlaceholder')"
          spellcheck="false"
          autocomplete="off"
          autocapitalize="off"
          enterkeyhint="search"
          @keydown.enter.prevent="commitSearch"
          @blur="commitSearch"/>
        <a class="vm-search-x" tabindex="0" @mousedown.prevent
           @click.stop="searchQuery ? clearSearch() : closeSearch()"><IconX/></a>
      </div>
      <div class="vm-search-history" v-if="showHistory">
        <div class="vm-history-head">
          <span v-text="i18n('menuSearchRecent')"/>
          <a class="vm-history-clear" tabindex="0" @mousedown.prevent
             @click.stop="clearHistory" v-text="i18n('menuSearchClearAll')"/>
        </div>
        <div v-for="h in visibleHistory" :key="h" class="vm-history-item" tabindex="0"
             @mousedown.prevent @click.stop="useHistory(h)">
          <IconHistory class="vm-history-ico"/>
          <span class="vm-history-text ellipsis" v-text="h"/>
          <a class="vm-history-del" tabindex="0" @mousedown.prevent
             @click.stop="removeHistory(h)"><IconX/></a>
        </div>
        <a v-if="searchHistory.length > HISTORY_COLLAPSED" class="vm-history-more" tabindex="0"
           @mousedown.prevent @click.stop="historyExpanded = !historyExpanded">
          <span v-text="historyExpanded
            ? i18n('menuSearchShowLess')
            : `${i18n('menuSearchShowMore')} (${searchHistory.length - HISTORY_COLLAPSED})`"/>
          <IconChevronDown class="vm-history-chevron" :class="{ up: historyExpanded }"/>
        </a>
      </div>
    </div>
    <div class="menu menu-find-box" v-if="store.injectable" v-show="store.domain">
      <div class="menu-find" :title="i18n('menuFindScripts')">
        <a v-for="(url, text) in findUrls" :key="url" target="_blank" class="find-chip"
           :href="url" :data-message="url.split('://')[1]" :tabIndex>
          <IconSearch class="find-ico"/><span v-text="text"/>
        </a>
      </div>
    </div>
""",
    ),
    # ---------- template: empty search result ----------
    (
        'src/popup/views/app.vue',
        r"""    <div class="failure-reason" v-if="note || store.injectionFailure" :class="{note}">""",
        r"""    <div class="vm-search-empty" v-if="searchQuery.trim() && !injectionScopes.length"
         v-text="i18n('menuSearchNoResults')"/>
    <div class="failure-reason" v-if="note || store.injectionFailure" :class="{note}">""",
    ),
    # ---------- template: command icons ----------
    (
        'src/popup/views/app.vue',
        r"""              <icon v-else name="command" />""",
        r"""              <component :is="cmdIcon(text)" v-else class="cmd-ico"/>""",
    ),
    # ---------- template: 3-dot menus ----------
    (
        'src/popup/views/app.vue',
        r"""    <div v-show="topExtras" ref="$topExtras" class="extras-menu">
      <div v-text="i18n('labelSettings')" @click="onManage(1)" tabindex="0"/>
      <div v-text="i18n('popupSettings')" @click="showSettings = true" tabindex="0"/>
      <div v-text="i18n('updateListedCmd', `${Object.keys(store.updatableScripts).length}`)"
           @click="onUpdateListed" tabindex="0"
           v-if="store.updatableScripts"/>
      <div v-text="i18n('skipScripts')" @click="onSkipTab" tabindex="0"
           v-if="/^(https?|file):/.test(store.tab?.url) /* not reusing `injectable`
           because iframes may run scripts even in non-injectable pages */"/>
    </div>
    <div v-if="extras" ref="$extras" class="extras-menu">
      <code v-if="extras.c">
        <a :href="VM_DOCS_INJECT_INTO" :data-message="INJECT_LEARN" v-bind="EXTERNAL_LINK_PROPS">content</a>
      </code>
      <a v-for="[url, text] in activeLinks"
         :key="url" :href="url" :data-message="url" tabindex="0" v-text="text"
         v-bind="EXTERNAL_LINK_PROPS"/>
      <div v-text="i18n('menuExclude')" tabindex="0" @click="onExclude"/>
      <div v-text="extras.config.removed ? i18n('buttonRestore') : i18n('buttonRemove')"
           tabindex="0"
           @click="onRemoveScript"/>
      <div v-if="'upd' in extras"
           v-text="i18n('buttonUpdate')"
           tabindex="0"
           @click="onUpdateScript"/>
    </div>
""",
        r"""    <div v-show="topExtras" ref="$topExtras" class="extras-menu">
      <div class="extras-item" tabindex="0" @click="onManage(1)">
        <IconSettings class="x-ico"/><span v-text="i18n('labelSettings')"/>
      </div>
      <div class="extras-item" tabindex="0" @click="showSettings = true">
        <IconTune class="x-ico"/><span v-text="i18n('popupSettings')"/>
      </div>
      <div class="extras-item" tabindex="0" @click="onUpdateListed" v-if="store.updatableScripts">
        <IconRefresh class="x-ico"/>
        <span v-text="i18n('updateListedCmd', `${Object.keys(store.updatableScripts).length}`)"/>
      </div>
      <div class="extras-item" tabindex="0" @click="onSkipTab"
           v-if="/^(https?|file):/.test(store.tab?.url) /* not reusing `injectable`
           because iframes may run scripts even in non-injectable pages */">
        <IconBan class="x-ico"/><span v-text="i18n('skipScripts')"/>
      </div>
    </div>
    <div v-if="extras" ref="$extras" class="extras-menu">
      <div class="extras-title" :title="extras.name"><span class="ellipsis" v-text="extrasTitle"/></div>
      <a v-if="extras.c" class="extras-item" :href="VM_DOCS_INJECT_INTO" :data-message="INJECT_LEARN"
         tabindex="0" v-bind="EXTERNAL_LINK_PROPS">
        <IconCode class="x-ico"/><code>content</code>
      </a>
      <a v-for="[url, text, ico] in activeLinks" class="extras-item"
         :key="url" :href="url" :data-message="url" tabindex="0"
         v-bind="EXTERNAL_LINK_PROPS">
        <component :is="ico" class="x-ico"/><span v-text="text"/>
      </a>
      <div class="extras-item" tabindex="0" @click="onExclude">
        <IconBan class="x-ico"/><span v-text="i18n('menuExclude')"/>
      </div>
      <div class="extras-item" :class="{ 'extras-danger': !extras.config.removed }"
           tabindex="0" @click="onRemoveScript">
        <component :is="extras.config.removed ? IconRestore : IconTrash" class="x-ico"/>
        <span v-text="extras.config.removed ? i18n('buttonRestore') : i18n('buttonRemove')"/>
      </div>
      <div class="extras-item" v-if="'upd' in extras" tabindex="0" @click="onUpdateScript">
        <IconRefresh class="x-ico"/><span v-text="i18n('buttonUpdate')"/>
      </div>
    </div>
""",
    ),
    # ---------- script: imports ----------
    (
        'src/popup/views/app.vue',
        r"""import VmVersion from '@/common/ui/vm-version.vue';
""",
        r"""import VmVersion from '@/common/ui/vm-version.vue';
import IconBan from '~icons/tabler/ban';
import IconBug from '~icons/tabler/bug';
import IconChevronDown from '~icons/tabler/chevron-down';
import IconCode from '~icons/tabler/code';
import IconCopy from '~icons/tabler/copy';
import IconCrosshair from '~icons/tabler/crosshair';
import IconDownload from '~icons/tabler/download';
import IconExternal from '~icons/tabler/external-link';
import IconEye from '~icons/tabler/eye';
import IconHeart from '~icons/tabler/heart';
import IconHistory from '~icons/tabler/history';
import IconHome from '~icons/tabler/home';
import IconKeyboard from '~icons/tabler/keyboard';
import IconMessage from '~icons/tabler/message-circle';
import IconPencil from '~icons/tabler/pencil';
import IconPlay from '~icons/tabler/player-play';
import IconRefresh from '~icons/tabler/refresh';
import IconRestore from '~icons/tabler/arrow-back-up';
import IconSearch from '~icons/tabler/search';
import IconSettings from '~icons/tabler/settings';
import IconTrash from '~icons/tabler/trash';
import IconTune from '~icons/tabler/adjustments-horizontal';
import IconWorld from '~icons/tabler/world';
import IconX from '~icons/tabler/x';
""",
    ),
    # ---------- script: constants ----------
    (
        'src/popup/views/app.vue',
        r"""const kNoCmdNames = 'noCmdNames';
""",
        r"""const kNoCmdNames = 'noCmdNames';
const HISTORY_KEY = 'vmPopupSearchHistory';
const HISTORY_COLLAPSED = 4;
const HISTORY_MAX = 30;
/** First match wins. Command names are free text written by script authors. */
const CMD_ICONS = [
  [/hot\s?-?key|shortcut|keybind|keyboard/i, IconKeyboard],
  [/setting|prefer|option|config|menu|panel/i, IconSettings],
  [/donat|sponsor|support|coffee|tip\b|thank|patreon/i, IconHeart],
  [/debug|log\b|logs\b|console|trace/i, IconBug],
  [/feedback|report|issue|contact|comment|chat|message/i, IconMessage],
  [/updat|upgrad|reload|refresh|restart|retry|sync/i, IconRefresh],
  [/pick|select|inspect|element|choose|target|locate/i, IconCrosshair],
  [/copy|clipboard/i, IconCopy],
  [/save|export|download|backup|get\b/i, IconDownload],
  [/show|hide|toggle|view|visible|preview|display/i, IconEye],
  [/clear|reset|delete|remove|clean|purge|wipe/i, IconTrash],
  [/edit|rename|change|modify/i, IconPencil],
  [/open|visit|home|link|website|site|go to/i, IconExternal],
  [/translat|language|locale/i, IconWorld],
  [/search|find/i, IconSearch],
];
""",
    ),
    # ---------- script: reactive state ----------
    (
        'src/popup/views/app.vue',
        r"""const tabIndex = computed(() => extras.value ? -1 : 0);
""",
        r"""const tabIndex = computed(() => extras.value ? -1 : 0);
const $searchInput = ref();
const searchOpen = ref(false);
const searchQuery = ref('');
const searchHistory = ref(loadHistory());
const historyExpanded = ref(false);
const showHistory = computed(() => searchOpen.value && !searchQuery.value.trim()
  && searchHistory.value.length > 0);
const visibleHistory = computed(() => historyExpanded.value
  ? searchHistory.value
  : searchHistory.value.slice(0, HISTORY_COLLAPSED));
/** First 3 words of the script name, so the menu header stays one short line */
const extrasTitle = computed(() => {
  const words = `${extras.value?.name || ''}`.trim().split(/\s+/).filter(Boolean);
  return words.slice(0, 3).join(' ') + (words.length > 3 ? '\u2026' : '');
});
""",
    ),
    # ---------- script: find chips are short labels now ----------
    (
        'src/popup/views/app.vue',
        r"""    [`${i18n('menuFindScripts')} (GF)`]: `https://greasyfork.org/scripts/by-site/${query}`,""",
        r"""    GreasyFork: `https://greasyfork.org/scripts/by-site/${query}`,""",
    ),
    (
        'src/popup/views/app.vue',
        r"""    OUJS: `https://openuserjs.org/?q=${query}`,""",
        r"""    OpenUserJS: `https://openuserjs.org/?q=${query}`,""",
    ),
    # ---------- script: link icons ----------
    (
        'src/popup/views/app.vue',
        r"""    support && [support, i18n('menuFeedback')],
    home && [home, i18n('buttonHome')],""",
        r"""    support && [support, i18n('menuFeedback'), IconMessage],
    home && [home, i18n('buttonHome'), IconHome],""",
    ),
    # ---------- script: filter scripts by the search text ----------
    (
        'src/popup/views/app.vue',
        r"""    for (const script of list) {
      if (groupRunAt) {""",
        r"""    if (searchTokens.length) {
      list = list.filter(item => {
        const lower = `${item.name || ''}`.toLowerCase();
        return searchTokens.every(token => lower.includes(token));
      });
      if (!list.length) continue;
      numTotal = list.length;
      numEnabled = list.filter(({ config: { enabled } }) => enabled).length;
    }
    for (const script of list) {
      if (groupRunAt) {""",
    ),
    (
        'src/popup/views/app.vue',
        r"""  const [topList, frameList] = store[SCRIPTS];
""",
        r"""  const [topList, frameList] = store[SCRIPTS];
  const searchTokens = searchQuery.value.toLowerCase().split(/\s+/).filter(Boolean);
""",
    ),
    # ---------- script: search + icon helpers ----------
    (
        'src/popup/views/app.vue',
        r"""function toggleMenu(name) {""",
        r"""function cmdIcon(text) {
  const str = `${text || ''}`;
  for (const [re, icon] of CMD_ICONS) if (re.test(str)) return icon;
  return IconPlay;
}
function loadHistory() {
  try {
    const list = JSON.parse(localStorage.getItem(HISTORY_KEY));
    return Array.isArray(list)
      ? list.filter(x => x && typeof x === 'string').slice(0, HISTORY_MAX)
      : [];
  } catch {
    return [];
  }
}
function saveHistory() {
  try {
    localStorage.setItem(HISTORY_KEY, JSON.stringify(searchHistory.value));
  } catch {/**/}
}
/** Remembers the current text (newest first, no duplicates) */
function commitSearch() {
  const text = searchQuery.value.trim();
  if (text.length < 2) return;
  const lower = text.toLowerCase();
  searchHistory.value = [text, ...searchHistory.value.filter(x => x.toLowerCase() !== lower)]
    .slice(0, HISTORY_MAX);
  saveHistory();
}
async function openSearch() {
  searchOpen.value = true;
  historyExpanded.value = false;
  await nextTick();
  $searchInput.value?.focus();
}
function closeSearch() {
  commitSearch();
  searchOpen.value = false;
  searchQuery.value = '';
}
function toggleSearch() {
  if (searchOpen.value) closeSearch();
  else openSearch();
}
function clearSearch() {
  searchQuery.value = '';
  $searchInput.value?.focus();
}
function useHistory(text) {
  searchQuery.value = text;
  commitSearch();
  $searchInput.value?.focus();
}
function removeHistory(text) {
  searchHistory.value = searchHistory.value.filter(x => x !== text);
  if (searchHistory.value.length <= HISTORY_COLLAPSED) historyExpanded.value = false;
  saveHistory();
}
function clearHistory() {
  searchHistory.value = [];
  historyExpanded.value = false;
  saveHistory();
}
function toggleMenu(name) {""",
    ),
    # ---------- script: Esc closes the search panel first ----------
    (
        'src/popup/views/app.vue',
        r"""    const item = extras.value || topExtras.value;
    if (item) {""",
        r"""    const item = extras.value || topExtras.value;
    if (!item && searchOpen.value) {
      closeSearch();
    } else if (item) {""",
    ),
]

NEW_FILES = {
    'src/popup/modern.css': r"""/* Popup redesign. Flat, neutral, outline glyphs, rounded soft-shadow cards.
 * Selectors are prefixed with repeated :root so they beat popup/style.css and material.css
 * (including its html.touch rules) regardless of import order. */

html:root:root:root:root:root {
  --pm-muted: var(--fill-8);
  --pm-danger: #d93025;
  --pm-card-shadow: 0 1px 2px rgba(0, 0, 0, .14), 0 2px 6px rgba(0, 0, 0, .10);
  --pm-surface: #eceef2;
  --pm-border: #b7bdc7;
  --pm-menu-shadow: var(--md-shadow-menu, 0 2px 6px rgba(0, 0, 0, .18), 0 6px 16px rgba(0, 0, 0, .14));
  --pm-line: var(--vm-line, #e5e7eb);
  --pm-hover: var(--md-state-hover, rgba(0, 0, 0, .06));
  --pm-press: var(--md-state-press, rgba(0, 0, 0, .12));
}
@supports (color: color-mix(in srgb, red, blue)) {
  html:root:root:root:root:root {
    --pm-surface: color-mix(in srgb, var(--fg) 8%, var(--bg));
    --pm-border: color-mix(in srgb, var(--fg) 28%, var(--bg));
  }
}
@media (prefers-color-scheme: dark) {
  html:root:root:root:root:root {
    --pm-danger: #f28b82;
  }
}

/* ---------- upstream 2.50 layout: buttons are a flex sibling of the name, not overlaid.
 * material.css still reserves 130px on the right for the old overlay, which would crush the name. ---------- */
html:root:root:root:root:root .page-popup .script > .menu-item {
  padding-right: 6px;
}
html:root:root:root:root:root .page-popup .submenu-buttons {
  position: static;
}
html:root:root:root:root:root .page-popup .menu-buttons .ext-name {
  min-width: 0;
  overflow: hidden;
  font-size: 13px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* ---------- top bar: search toggle ---------- */
html:root:root:root:root:root .page-popup .menu-buttons .menu-search-btn {
  border-radius: 10px;
}
html:root:root:root:root:root .page-popup .menu-buttons .icon-search {
  fill: none;
  stroke: currentColor;
  stroke-width: 3.4;
  stroke-linecap: butt;
}

/* ---------- search panel ---------- */
html:root:root:root:root:root .page-popup .vm-search {
  padding: 2px 10px 10px;
  background: var(--bg);
}
html:root:root:root:root:root .page-popup .vm-search-box {
  display: flex;
  align-items: center;
  height: 44px;
  padding: 0 6px 0 14px;
  border: 1px solid var(--pm-border);
  border-radius: 14px;
  background: var(--bg);
  box-shadow: var(--pm-card-shadow);
}
html:root:root:root:root:root .page-popup .vm-search-box:focus-within {
  border-color: var(--fill-7);
}
html:root:root:root:root:root .page-popup .vm-search-lead {
  flex: none;
  width: 18px;
  height: 18px;
  color: var(--pm-muted);
}
html:root:root:root:root:root .page-popup .vm-search-input {
  flex: 1;
  min-width: 0;
  height: 100%;
  padding: 0 10px;
  border: 0;
  border-radius: 0;
  outline: 0;
  background: transparent;
  color: var(--fg);
  font-size: 15px;
}
html:root:root:root:root:root .page-popup .vm-search-x,
html:root:root:root:root:root .page-popup .vm-history-del {
  display: flex;
  flex: none;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  border-radius: 50%;
  color: var(--pm-muted);
  cursor: pointer;
}
html:root:root:root:root:root .page-popup .vm-search-x svg,
html:root:root:root:root:root .page-popup .vm-history-del svg {
  width: 18px;
  height: 18px;
}
html:root:root:root:root:root .page-popup .vm-search-x:hover,
html:root:root:root:root:root .page-popup .vm-search-x:focus,
html:root:root:root:root:root .page-popup .vm-history-del:hover,
html:root:root:root:root:root .page-popup .vm-history-del:focus {
  background: var(--pm-press);
  color: var(--fg);
}

html:root:root:root:root:root .page-popup .vm-search-history {
  margin-top: 8px;
}
html:root:root:root:root:root .page-popup .vm-history-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-height: 30px;
  padding: 0 4px 0 8px;
  color: var(--pm-muted);
  font-size: 12px;
  font-weight: 600;
}
html:root:root:root:root:root .page-popup .vm-history-clear {
  padding: 6px 8px;
  border-radius: 8px;
  color: var(--fill-10);
  cursor: pointer;
}
html:root:root:root:root:root .page-popup .vm-history-clear:hover,
html:root:root:root:root:root .page-popup .vm-history-clear:focus {
  background: var(--pm-hover);
  color: var(--fg);
}
html:root:root:root:root:root .page-popup .vm-history-item {
  display: flex;
  align-items: center;
  gap: 10px;
  height: 38px;
  padding: 0 4px 0 8px;
  border-radius: 12px;
  cursor: pointer;
}
html:root:root:root:root:root .page-popup .vm-history-item:hover,
html:root:root:root:root:root .page-popup .vm-history-item:focus {
  background: var(--pm-hover);
}
html:root:root:root:root:root .page-popup .vm-history-ico {
  flex: none;
  width: 18px;
  height: 18px;
  color: var(--pm-muted);
}
html:root:root:root:root:root .page-popup .vm-history-text {
  flex: 1;
  min-width: 0;
  font-size: 14px;
}
html:root:root:root:root:root .page-popup .vm-history-more {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  height: 38px;
  border-radius: 12px;
  color: var(--fill-10);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
}
html:root:root:root:root:root .page-popup .vm-history-more:hover,
html:root:root:root:root:root .page-popup .vm-history-more:focus {
  background: var(--pm-hover);
}
html:root:root:root:root:root .page-popup .vm-history-chevron {
  width: 16px;
  height: 16px;
  transition: transform .15s;
}
html:root:root:root:root:root .page-popup .vm-history-chevron.up {
  transform: rotate(180deg);
}
html:root:root:root:root:root .page-popup .vm-search-empty {
  padding: 28px 16px;
  color: var(--pm-muted);
  text-align: center;
}

/* ---------- find scripts card ---------- */
html:root:root:root:root:root .page-popup .menu-find-box {
  padding: 8px 10px 6px;
  border-top: 0;
  background: var(--bg);
}
html:root:root:root:root:root .page-popup .menu-find {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 8px 12px;
  border: 1px solid var(--pm-border);
  border-radius: 14px;
  background: var(--bg);
  box-shadow: var(--pm-card-shadow);
  cursor: default;
}
html:root:root:root:root:root .page-popup .menu-find .find-chip {
  display: inline-flex;
  flex: 1 1 0;
  align-items: center;
  align-self: center;
  justify-content: center;
  gap: 8px;
  box-sizing: border-box;
  max-width: 190px;
  height: 38px;
  padding: 0 14px;
  border: 1px solid var(--pm-border);
  border-radius: 999px;
  color: var(--fg);
  font-size: 13px;
  font-weight: 700;
  text-decoration: none;
  white-space: nowrap;
  cursor: pointer;
}
html:root:root:root:root:root .page-popup .menu-find .find-chip:hover,
html:root:root:root:root:root .page-popup .menu-find .find-chip:focus {
  background: var(--pm-hover);
  color: var(--fg);
}
html:root:root:root:root:root .page-popup .menu-find .find-ico {
  flex: none;
  width: 16px;
  height: 16px;
  margin: 0;
  color: var(--pm-muted);
}

/* ---------- group header ("Matched scripts") ---------- */
html:root:root:root:root:root .page-popup .menu-scripts {
  border-top: 0;
}
html:root:root:root:root:root .page-popup .menu-scripts > .menu-group {
  box-sizing: border-box;
  align-items: center;
  height: 42px;
  min-height: 42px;
  padding: 0 14px 0 14px;
  margin: 0;
  line-height: 1;
  border-bottom: 1px solid var(--pm-border);
}
html:root:root:root:root:root .page-popup .menu-scripts > .menu-group .icon-collapse {
  flex: 0 0 16px;
  width: 16px;
  height: 16px;
  margin: 0 10px 0 0;
  color: var(--pm-muted);
}
html:root:root:root:root:root .page-popup .menu-scripts > .menu-group > .flex-auto {
  align-items: center;
  align-self: center;
  padding: 0;
  font-size: 14px;
  line-height: 1.2;
}
html:root:root:root:root:root .page-popup .menu-scripts > .menu-group [data-totals]::after {
  content: attr(data-totals);
  margin-left: auto;
  padding: 4px 10px;
  border-radius: 999px;
  background: var(--fg);
  color: var(--bg);
  font-size: 12px;
  font-weight: 700;
  line-height: 1;
}
html:root:root:root:root:root .page-popup .menu-scripts.expand > .submenu {
  padding: 8px 0 10px;
  border-top: 1px solid var(--pm-border);
  background: var(--pm-surface);
}
html:root:root:root:root:root .page-popup .menu-scripts .submenu > .script {
  margin: 5px 10px;
  border: 1px solid var(--pm-border);
  box-shadow: var(--pm-card-shadow);
}

/* ---------- script commands: tree ---------- */
html:root:root:root:root:root .page-popup .submenu-commands {
  --tree-x: 23px;
  --tree-pad: 42px;
  --row-h: 36px;
  position: relative;
  box-sizing: border-box;
  padding: 0 12px 10px var(--tree-pad);
  font-size: 13px;
  color: var(--fill-12);
}
html:root:root:root:root:root .page-popup .submenu-commands > .menu-item {
  position: relative;
  display: flex;
  flex-wrap: nowrap;
  align-items: center;
  gap: 10px;
  box-sizing: border-box;
  min-height: var(--row-h);
  height: var(--row-h);
  margin: 0;
  padding: 0 12px;
  border-radius: 10px;
  line-height: 1.2;
  white-space: nowrap;
  overflow: visible;
}
html:root:root:root:root:root .page-popup .submenu-commands > .menu-item > .icon,
html:root:root:root:root:root .page-popup .submenu-commands > .menu-item > .cmd-ico {
  flex: none;
  width: 18px;
  height: 18px;
  margin: 0;
  color: var(--fill-9);
  vertical-align: middle;
}
html:root:root:root:root:root .page-popup .submenu-commands > .menu-item > span {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
}
html:root:root:root:root:root .page-popup .submenu-commands > .menu-item:hover,
html:root:root:root:root:root .page-popup .submenu-commands > .menu-item:focus,
html:root:root:root:root:root .page-popup .submenu-commands > .menu-item:active {
  background: var(--pm-hover);
  color: inherit;
}
html:root:root:root:root:root .page-popup .submenu-commands > .menu-item:active {
  background: var(--pm-press);
}
/* elbow connector into every row + rail continuing down to the next one */
html:root:root:root:root:root .page-popup .submenu-commands > .menu-item::before {
  content: '';
  position: absolute;
  left: calc(var(--tree-x) - var(--tree-pad));
  top: 0;
  width: calc(var(--tree-pad) - var(--tree-x) - 2px);
  height: 50%;
  border-left: 1.5px solid var(--fill-4);
  border-bottom: 1.5px solid var(--fill-4);
  border-bottom-left-radius: 9px;
  pointer-events: none;
}
html:root:root:root:root:root .page-popup .submenu-commands > .menu-item:not(:last-child)::after {
  content: '';
  position: absolute;
  left: calc(var(--tree-x) - var(--tree-pad));
  top: 50%;
  bottom: 0;
  border-left: 1.5px solid var(--fill-4);
  pointer-events: none;
}
/* the first elbow reaches up to the script icon */
html:root:root:root:root:root .page-popup .submenu-commands > details + .menu-item::before,
html:root:root:root:root:root .page-popup .submenu-commands > .menu-item:first-child::before {
  top: -12px;
  height: calc(50% + 12px);
}

/* names on/off toggle: small round chevron at the right edge */
html:root:root:root:root:root .page-popup .submenu-commands > details {
  position: absolute;
  top: 3px;
  right: 8px;
  bottom: auto;
  left: auto;
  z-index: 2;
  display: block;
  width: 30px;
  height: 30px;
}
html:root:root:root:root:root .page-popup .submenu-commands > details > summary {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  padding: 0;
  border-radius: 50%;
  list-style: none;
  color: var(--pm-muted);
  cursor: pointer;
}
html:root:root:root:root:root .page-popup .submenu-commands > details > summary::-webkit-details-marker {
  display: none;
}
html:root:root:root:root:root .page-popup .submenu-commands > details > summary::marker {
  content: '';
}
html:root:root:root:root:root .page-popup .submenu-commands > details > summary::before {
  content: '';
  width: 7px;
  height: 7px;
  border-right: 2px solid currentColor;
  border-bottom: 2px solid currentColor;
  transform: translateY(-2px) rotate(225deg); /* open: points up = collapse names */
}
html:root:root:root:root:root .page-popup .submenu-commands > details:not([open]) > summary::before {
  transform: translateY(-2px) rotate(45deg); /* closed: points down = show names */
}
html:root:root:root:root:root .page-popup .submenu-commands > details > summary:hover {
  background: var(--pm-press);
  color: var(--fg);
}
html:root:root:root:root:root .page-popup .submenu-commands > details[open]:not([style*="none"]) + .menu-item {
  padding-right: 40px;
}

/* names off: icon-only chips in a row, no tree */
html:root:root:root:root:root .page-popup .submenu-commands > details:not([open]) ~ .menu-item {
  display: inline-flex;
  justify-content: center;
  width: 38px;
  height: 38px;
  min-height: 38px;
  margin: 0 4px 4px 0;
  padding: 0;
  border: 1px solid var(--pm-border);
  border-radius: 12px;
}
html:root:root:root:root:root .page-popup .submenu-commands > details:not([open]) ~ .menu-item::before,
html:root:root:root:root:root .page-popup .submenu-commands > details:not([open]) ~ .menu-item::after {
  display: none;
}

/* ---------- 3-dot menus ---------- */
html:root:root:root:root:root .extras-menu {
  box-sizing: border-box;
  min-width: 220px;
  max-width: min(80vw, 320px);
  padding: 6px;
  border: 1px solid var(--pm-border);
  border-radius: 16px;
  background: var(--bg);
  box-shadow: var(--pm-menu-shadow);
  overflow: hidden;
}
html:root:root:root:root:root .extras-menu > .extras-title {
  display: block;
  padding: 8px 12px 10px;
  margin: 0 0 4px;
  border-bottom: 1px solid var(--pm-border);
  color: var(--pm-muted);
  font-size: 12px;
  font-weight: 700;
  cursor: default;
}
html:root:root:root:root:root .extras-menu > .extras-title:focus {
  background: transparent;
  color: var(--pm-muted);
}
html:root:root:root:root:root .extras-menu > .extras-title > span {
  display: block;
}
html:root:root:root:root:root .extras-menu > .extras-item {
  display: flex;
  align-items: center;
  gap: 14px;
  box-sizing: border-box;
  min-height: 44px;
  padding: 0 12px;
  border-radius: 10px;
  color: var(--fg);
  font-size: 14px;
  line-height: 1.2;
  text-decoration: none;
  cursor: pointer;
}
html:root:root:root:root:root .extras-menu > .extras-item:hover,
html:root:root:root:root:root .extras-menu > .extras-item:focus {
  background: var(--pm-hover);
  color: var(--fg);
}
html:root:root:root:root:root .extras-menu > .extras-item:active {
  background: var(--pm-press);
}
html:root:root:root:root:root .extras-menu > .extras-item > .x-ico {
  flex: none;
  width: 20px;
  height: 20px;
  color: var(--fill-9);
}
html:root:root:root:root:root .extras-menu > .extras-item > code {
  padding: 0;
  background: transparent;
  font-size: 14px;
}
html:root:root:root:root:root .extras-menu > .extras-item.extras-danger,
html:root:root:root:root:root .extras-menu > .extras-item.extras-danger > .x-ico {
  color: var(--pm-danger);
}
""",
}


def apply_patches(root: Path):
    for i, (rel, old, new) in enumerate(PATCHES, 1):
        path = root / rel
        text = path.read_text(encoding='utf-8')
        count = text.count(old)
        if count != 1:
            sys.exit(f'[popup patch {i}] FAILED: anchor found {count}x (expected 1) in {rel}\n--- anchor ---\n{old}')
        path.write_text(text.replace(old, new), encoding='utf-8')
        print(f'[popup patch {i}] OK: {rel}')
    for rel, content in NEW_FILES.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding='utf-8')
        print(f'[new file] OK: {rel}')


if __name__ == '__main__':
    apply_patches(Path(sys.argv[1] if len(sys.argv) > 1 else '.'))
