#!/usr/bin/env python3
"""
Editor redesign for the Violentmonkey fork. Run after the other patches, from the repo root:

    python3 apply_patches_addmatch.py && python3 apply_patches_material.py \
      && python3 apply_patches_popup.py && python3 apply_patches_editor.py [repo_root]

Adds: two-row header (actions + tab chips, so Close is always visible), search toggle that opens
the find/replace panel under the header (match count, clear buttons), and Gboard fixes
(copy without line numbers, multi-line paste, delete selection, select all).
"""
import sys
from pathlib import Path

# Each patch: (file, old, new). `old` must appear EXACTLY once in `file`.
PATCHES = [
    (
        'src/options/views/edit/index.vue',
        r"""    <div class="edit-header flex mr-1c">
      <nav>
        <div
          v-for="(label, navKey) in navItems" :key="navKey"
          class="edit-nav-item" :class="{ active: nav === navKey, 'with-icon': navKey === EXTERNALS }"
          @click="nav = navKey"
        >{{
          label
        }}<template v-if="navKey === EXTERNALS">
            <a @click.stop="onUpdateDeps"><icon name="refresh"/></a>
            <span v-text="depsProgress" v-if="depsProgress"/>
          </template>
        </div>
      </nav>
      <div class="edit-name text-center ellipsis flex-1">
        <span class="subtle" v-if="script.config.removed" v-text="i18n('headerRecycleBin') + ' / '"/>
        {{scriptName}}
      </div>
      <p v-if="frozen && nav === 'code'" v-text="i18n('readonly')"
         class="text-upper text-right text-red"/>
      <div v-else-if="browserWindows" class="edit-hint text-right ellipsis">
        <a :href="externalEditorInfoUrl"
           v-bind="EXTERNAL_LINK_PROPS"
           v-text="i18n('editHowToHint')"/>
      </div>
      <div class="mr-1">
        <a class="btn-ghost" @click="clipboardCopy" tabindex="0"><IconCopy/></a>
        <a class="btn-ghost" @click="clipboardPaste" tabindex="0" v-if="!frozen"><IconPaste/></a>
      </div>
      <div class="mr-1">
        <button v-text="i18n('buttonSave')" @click="save"
                v-show="canSave || !frozen" :disabled="!canSave"
                :class="{'has-error': $fe = fatal || errors}" :title="$fe"/>
        <button v-text="i18n('buttonSaveClose')" @click="saveClose"
                v-show="canSave || !frozen" :disabled="!canSave"/>
        <button v-text="i18n('buttonClose')" @click="close(true)" title="Esc"/>
      </div>
    </div>""",
        r"""    <div class="edit-header">
      <div class="edit-bar">
        <div class="edit-name ellipsis">
          <span class="subtle" v-if="script.config.removed" v-text="i18n('headerRecycleBin') + ' / '"/>
          {{scriptName}}
        </div>
        <p v-if="frozen && nav === 'code'" v-text="i18n('readonly')" class="edit-ro"/>
        <div v-else-if="browserWindows" class="edit-hint ellipsis">
          <a :href="externalEditorInfoUrl"
             v-bind="EXTERNAL_LINK_PROPS"
             v-text="i18n('editHowToHint')"/>
        </div>
        <div class="edit-tools">
          <a class="btn-ghost edit-tool" @click="clipboardCopy" tabindex="0"><IconCopy/></a>
          <a class="btn-ghost edit-tool" @click="clipboardPaste" tabindex="0" v-if="!frozen"><IconPaste/></a>
          <a class="btn-ghost edit-tool" :class="{ active: $code?.searchShown }" tabindex="0"
             v-if="nav === 'code'" :title="i18n('labelSearch')"
             @click="$code?.toggleSearch()"><IconSearch/></a>
        </div>
        <div class="edit-actions">
          <button v-text="i18n('buttonSave')" @click="save"
                  v-show="canSave || !frozen" :disabled="!canSave"
                  :class="{'has-error': $fe = fatal || errors}" :title="$fe"/>
          <button v-text="i18n('buttonSaveClose')" @click="saveClose"
                  v-show="canSave || !frozen" :disabled="!canSave"/>
          <button v-text="i18n('buttonClose')" @click="close(true)" title="Esc"/>
        </div>
      </div>
      <nav>
        <div
          v-for="(label, navKey) in navItems" :key="navKey"
          class="edit-nav-item" :class="{ active: nav === navKey, 'with-icon': navKey === EXTERNALS }"
          @click="nav = navKey"
        >{{
          label
        }}<template v-if="navKey === EXTERNALS">
            <a @click.stop="onUpdateDeps"><icon name="refresh"/></a>
            <span v-text="depsProgress" v-if="depsProgress"/>
          </template>
        </div>
      </nav>
    </div>""",
    ),
    (
        'src/options/views/edit/index.vue',
        r"""import IconPaste from '~icons/mdi/content-paste';
""",
        r"""import IconPaste from '~icons/mdi/content-paste';
import IconSearch from '~icons/tabler/search';
import './modern.css';
""",
    ),
    (
        'src/common/ui/code.vue',
        r"""    <div class="frame-block editor-search flex" v-show="search.show"
         @keydown.esc.exact.stop="clearSearch">
      <form @submit.prevent="goToLine()">
        <span v-text="i18n('labelLineNumber')"></span>
        <input type="text" class="w-1" v-model="jumpPos" style="max-width: 9ch">
      </form>
      <form class="flex-1 fit" @submit.prevent="findNext()">
        <span v-text="i18n('labelSearch')"></span>
        <tooltip :content="tooltips.find" class="flex-1 fit">
          <!-- id is required for the built-in autocomplete using entered values -->
          <input
            :class="{ 'is-error': !search.num }"
            :title="search.error"
            type="search"
            id="editor-search"
            ref="$search"
            v-model="search.query"
          />
        </tooltip>
        <span class="mx-1" v-text="search.num"/>
        <tooltip :content="tooltips.findPrev" align="end">
          <button type="button" @click="findNext(1)" :disabled="!search.num">&lt;</button>
        </tooltip>
        <tooltip :content="tooltips.findNext" align="end">
          <button type="submit" :disabled="!search.num">&gt;</button>
        </tooltip>
      </form>
      <form class="flex-1" @submit.prevent="replace()" v-if="!readOnly" style="max-width: 100%">
        <span v-text="i18n('labelReplace')"></span>
        <!-- id is required for the built-in autocomplete using entered values -->
        <input class="flex-1" type="search" id="editor-replace" v-model="search.replace">
        <tooltip :content="tooltips.replace" align="end">
          <button type="submit" v-text="i18n('buttonReplace')"></button>
        </tooltip>
        <tooltip :content="tooltips.replaceAll" align="end">
          <button type="button" v-text="i18n('buttonReplaceAll')" @click="replace(1)"></button>
        </tooltip>
      </form>
      <div>
        <tooltip :content="i18n('searchUseRegex')" align="end">
          <toggle-button v-model="search.options.useRegex">.*</toggle-button>
        </tooltip>
        <tooltip :content="i18n('searchCaseSensitive')" align="end">
          <toggle-button v-model="search.options.caseSensitive">Aa</toggle-button>
        </tooltip>
        <tooltip content="Esc" align="end" class="ml-1">
          <button @click="clearSearch">&times;</button>
        </tooltip>
      </div>
    </div>""",
        r"""    <div class="frame-block editor-search" v-show="search.show"
         @keydown.esc.exact.stop="clearSearch">
      <div class="es-row">
        <div class="es-field" :class="{ 'is-error': search.query && !search.num }">
          <IconSearch class="es-ico"/>
          <input
            type="search"
            id="editor-search"
            ref="$search"
            v-model="search.query"
            :placeholder="phFind"
            :title="search.error"
            spellcheck="false"
            autocomplete="on"
            autocapitalize="off"
            enterkeyhint="search"
            @keydown.enter.prevent="findNext()"
          />
          <a v-if="search.query" class="es-x" tabindex="0" @mousedown.prevent
             @click="clearFind"><IconX/></a>
        </div>
        <span class="es-count" :class="{ none: search.query && !search.num }" v-text="search.num"/>
        <button type="button" class="es-btn" :title="tooltips.findPrev"
                @click="findNext(1)" :disabled="!search.num"><IconUp/></button>
        <button type="button" class="es-btn" :title="tooltips.findNext"
                @click="findNext()" :disabled="!search.num"><IconDown/></button>
        <button type="button" class="es-btn es-close" title="Esc" @click="resetSearch"><IconX/></button>
      </div>
      <div class="es-row" v-if="!readOnly">
        <div class="es-field">
          <IconReplace class="es-ico"/>
          <input
            type="search"
            id="editor-replace"
            v-model="search.replace"
            :placeholder="phReplace"
            spellcheck="false"
            autocomplete="on"
            autocapitalize="off"
            enterkeyhint="done"
            @keydown.enter.prevent="replace()"
          />
          <a v-if="search.replace" class="es-x" tabindex="0" @mousedown.prevent
             @click="clearReplace"><IconX/></a>
        </div>
        <button type="button" class="es-text-btn" :title="tooltips.replace"
                v-text="i18n('buttonReplace')" @click="replace()"/>
        <button type="button" class="es-text-btn" :title="tooltips.replaceAll"
                v-text="i18n('buttonReplaceAll')" @click="replace(1)"/>
      </div>
      <div class="es-row es-opts">
        <toggle-button v-model="search.options.useRegex" :title="i18n('searchUseRegex')">.*</toggle-button>
        <toggle-button v-model="search.options.caseSensitive" :title="i18n('searchCaseSensitive')">Aa</toggle-button>
        <form class="es-goto" @submit.prevent="goToLine()">
          <span v-text="i18n('labelLineNumber')"></span>
          <input type="text" class="es-line" v-model="jumpPos" inputmode="numeric">
        </form>
      </div>
    </div>""",
    ),
    (
        'src/common/ui/code.vue',
        r"""import { killTrailingSpaces } from './code-trailing-spaces';
""",
        r"""import { killTrailingSpaces } from './code-trailing-spaces';
import IconDown from '~icons/tabler/chevron-down';
import IconReplace from '~icons/tabler/replace';
import IconSearch from '~icons/tabler/search';
import IconUp from '~icons/tabler/chevron-up';
import IconX from '~icons/tabler/x';
""",
    ),
    (
        'src/common/ui/code.vue',
        r"""import Tooltip from 'vueleton/lib/tooltip';
""",
        r"""""",
    ),
    (
        'src/common/ui/code.vue',
        r"""const reroutedKeys = {};
""",
        r"""const reroutedKeys = {};
const stripColon = str => str.replace(/\s*[:\uFF1A]\s*$/, '');
const phFind = stripColon(i18n('labelSearch'));
const phReplace = stripColon(i18n('labelReplace'));
let selectAllTimer;
""",
    ),
    (
        'src/common/ui/code.vue',
        r"""  getRealContent,
  expandKeyMap,
});""",
        r"""  getRealContent,
  expandKeyMap,
  get searchShown() {
    return search.show;
  },
  toggleSearch,
});""",
    ),
    (
        'src/common/ui/code.vue',
        r"""  // CM already prepared the correct text in DOM selection, which is particularly
  // important when using its lineWiseCopyCut option (on by default)
  const sel = `${getSelection()}` || cm?.getSelection();
""",
        r"""  // CM already put the correct text into clipboardData, which is particularly important when
  // using its lineWiseCopyCut option (on by default). The DOM selection string is not reliable:
  // on touch devices it includes the line numbers of the gutter.
  const sel = e.clipboardData.getData('text') || cm?.getSelection() || `${getSelection()}`;
""",
    ),
    (
        'src/common/ui/code.vue',
        r"""function getRealContent(text) {
""",
        r"""function clearFind() {
  search.query = '';
  $search.value?.focus();
}
function clearReplace() {
  search.replace = '';
}
/** Clears both boxes and closes the panel */
function resetSearch() {
  search.query = '';
  search.replace = '';
  search.num = 0;
  clearSearch();
}
function toggleSearch() {
  if (search.show) clearSearch();
  else find();
}
/** Makes CodeMirror read the browser's current selection right now instead of on its next poll */
function syncDomSelection() {
  try {
    cm.display.input.pollSelection?.();
  } catch {/**/}
}
/**
 * Mobile keyboards (Gboard) bypass CodeMirror's key handling and edit the contenteditable DOM
 * directly: multi-line paste and delete-selection break its DOM bookkeeping
 * ("Node.removeChild: The node to be removed is not a child of this node").
 * So we cancel those edits and apply them through the CodeMirror API instead.
 */
function onBeforeInput(e) {
  const type = e.inputType;
  if (!cm || !type || e.isComposing || cm.isReadOnly()) return;
  const isDelete = type.startsWith('delete');
  const isPaste = /^insertFrom(Paste|Drop|Yank)/.test(type);
  const isMultiLine = /^insert(Replacement)?Text$/.test(type) && /[\r\n]/.test(e.data || '');
  if (!isDelete && !isPaste && !isMultiLine) return; // regular typing is handled by CodeMirror
  syncDomSelection();
  if (isDelete) {
    if (!cm.somethingSelected()) return;
    e.preventDefault();
    if (type === 'deleteByCut') {
      navigator.clipboard?.writeText(getRealContent(cm.getSelection())).catch(() => {});
    }
    cm.replaceSelection('', null, '+delete');
    return;
  }
  const text = isMultiLine ? e.data : e.dataTransfer?.getData('text/plain') || e.data;
  e.preventDefault();
  if (text) {
    cm.replaceSelection(text, 'end', 'paste');
  } else {
    navigator.clipboard?.readText().then(str => {
      if (str) cm.replaceSelection(str, 'end', 'paste');
    }, () => {});
  }
}
/**
 * "Select all" from the keyboard's text menu selects only the DOM CodeMirror has rendered
 * (the viewport), so Cut/Copy/Clear afterwards would affect just a part of the script.
 */
function onSelectionChange() {
  if (!cm || !cm.hasFocus()) return;
  clearTimeout(selectAllTimer);
  selectAllTimer = setTimeout(fixSelectAll, 120);
}
function fixSelectAll() {
  const { display } = cm;
  if (!display.input.div) return; // the textarea input style selects everything natively
  if (display.viewFrom <= cm.firstLine() && display.viewTo > cm.lastLine()) return; // all rendered
  syncDomSelection();
  if (!cm.somethingSelected()) return;
  const range = cm.listSelections()[0];
  const from = range.from();
  const to = range.to();
  if (from.line === display.viewFrom && from.ch === 0
  && to.line === display.viewTo - 1 && to.ch === cm.getLine(to.line).length) {
    cm.execCommand('selectAll');
  }
}
function getRealContent(text) {
""",
    ),
    (
        'src/common/ui/code.vue',
        r"""  cmWrapper::addEventListener('copy', onCopy);
""",
        r"""  cmWrapper::addEventListener('copy', onCopy);
  cmWrapper.addEventListener('beforeinput', onBeforeInput, true);
  document.addEventListener('selectionchange', onSelectionChange);
""",
    ),
    (
        'src/common/ui/code.vue',
        r"""onBeforeUnmount(() => {
  onActive(false);
});""",
        r"""onBeforeUnmount(() => {
  onActive(false);
  clearTimeout(selectAllTimer);
  document.removeEventListener('selectionchange', onSelectionChange);
});""",
    ),
]

NEW_FILES = {
    'src/options/views/edit/modern.css': r"""/* Editor page redesign: two-row header (actions, then tab chips), find/replace panel under it.
 * Selectors use repeated :root so they win over edit/index.vue and code.vue styles. */

html:root:root:root:root:root {
  --em-line: var(--vm-line, #e5e7eb);
  --em-hover: var(--md-state-hover, rgba(0, 0, 0, .06));
  --em-press: var(--md-state-press, rgba(0, 0, 0, .12));
  --em-danger: #d93025;
}
@media (prefers-color-scheme: dark) {
  html:root:root:root:root:root {
    --em-danger: #f28b82;
  }
}

/* line numbers and fold markers must never end up in copied text (touch selections include them) */
.CodeMirror-gutter-wrapper,
.CodeMirror-gutters,
.CodeMirror-linenumber {
  -webkit-user-select: none;
  -moz-user-select: none;
  user-select: none;
}

/* ---------- header ---------- */
html:root:root:root:root:root .edit .edit-header {
  display: block;
  padding: 6px 10px 0;
  border-bottom: 1px solid var(--em-line);
  background: var(--bg);
}
html:root:root:root:root:root .edit .edit-bar {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: 4px 8px;
  min-height: 44px;
}
html:root:root:root:root:root .edit .edit-bar > .edit-name {
  flex: 1;
  min-width: 0;
  margin: 0;
  font-size: 15px;
  font-weight: 700;
  text-align: left;
}
html:root:root:root:root:root .edit .edit-bar > .edit-ro {
  flex: none;
  margin: 0;
  padding: 5px 10px;
  border: 1px solid var(--em-danger);
  border-radius: 999px;
  color: var(--em-danger);
  font-size: 11px;
  font-weight: 700;
  line-height: 1;
  text-transform: uppercase;
}
html:root:root:root:root:root .edit .edit-bar > .edit-hint {
  flex: none;
  max-width: 40%;
  margin: 0;
  font-size: 12px;
}
html:root:root:root:root:root .edit .edit-tools {
  display: flex;
  flex: none;
  align-items: center;
  gap: 2px;
  margin: 0;
}
html:root:root:root:root:root .edit .edit-tools .edit-tool {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  padding: 0;
  border: 0;
  border-radius: 12px;
  color: var(--fill-12);
  cursor: pointer;
}
html:root:root:root:root:root .edit .edit-tools .edit-tool svg {
  width: 20px;
  height: 20px;
}
html:root:root:root:root:root .edit .edit-tools .edit-tool:hover,
html:root:root:root:root:root .edit .edit-tools .edit-tool:focus {
  background: var(--em-hover);
}
html:root:root:root:root:root .edit .edit-tools .edit-tool.active,
html:root:root:root:root:root .edit .edit-tools .edit-tool:active {
  background: var(--em-press);
}
html:root:root:root:root:root .edit .edit-actions {
  display: flex;
  flex: none;
  margin: 0;
}
html:root:root:root:root:root .edit .edit-actions > button {
  height: 36px;
  margin: 0;
  padding: 0 10px;
  border: 1px solid var(--em-line);
  border-radius: 0;
  background: var(--bg);
  color: var(--fg);
  font-size: 13px;
  font-weight: 600;
  line-height: 1;
  white-space: nowrap;
}
html:root:root:root:root:root .edit .edit-actions > button:first-of-type {
  border-radius: 12px 0 0 12px;
}
html:root:root:root:root:root .edit .edit-actions > button:last-of-type {
  border-radius: 0 12px 12px 0;
}
html:root:root:root:root:root .edit .edit-actions > button + button {
  border-left: 0;
}
html:root:root:root:root:root .edit .edit-actions > button:hover:not(:disabled),
html:root:root:root:root:root .edit .edit-actions > button:focus:not(:disabled) {
  background: var(--em-hover);
}
html:root:root:root:root:root .edit .edit-actions > button:active:not(:disabled) {
  background: var(--em-press);
}
html:root:root:root:root:root .edit .edit-actions > button:disabled {
  opacity: .45;
}
html:root:root:root:root:root .edit .edit-actions > button.has-error {
  color: var(--em-danger);
}

/* ---------- tab chips ---------- */
html:root:root:root:root:root .edit .edit-header > nav {
  display: flex;
  flex-wrap: nowrap;
  gap: 6px;
  padding: 4px 0 10px;
  overflow-x: auto;
  scrollbar-width: none;
}
html:root:root:root:root:root .edit .edit-header > nav::-webkit-scrollbar {
  display: none;
}
html:root:root:root:root:root .edit .edit-nav-item {
  display: inline-flex;
  flex: none;
  align-items: center;
  gap: 4px;
  height: 34px;
  padding: 0 14px;
  border: 1px solid var(--em-line);
  border-radius: 999px;
  background: var(--bg);
  box-shadow: none;
  font-size: 13px;
  font-weight: 600;
  line-height: 1;
  white-space: nowrap;
}
html:root:root:root:root:root .edit .edit-nav-item:not(.active):hover {
  background: var(--em-hover);
  box-shadow: none;
}
html:root:root:root:root:root .edit .edit-nav-item.active {
  border-color: var(--fill-7);
  background: var(--fill-1);
  box-shadow: none;
}
html:root:root:root:root:root .edit .edit-nav-item.with-icon {
  padding-right: 4px;
}
html:root:root:root:root:root .edit .edit-nav-item.with-icon > a {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 26px;
  height: 26px;
  margin: 0;
  padding: 0;
  border-radius: 50%;
}
html:root:root:root:root:root .edit .edit-nav-item.with-icon > a:hover {
  background: var(--em-press);
}
html:root:root:root:root:root .edit .edit-nav-item.with-icon > a svg {
  width: 14px;
  height: 14px;
  transform: none;
}
html:root:root:root:root:root .edit .edit-nav-item.with-icon > span {
  padding-right: 10px;
}
/* the "?" hotkey help tab is useless without a keyboard */
html.touch:root:root:root:root .edit .edit-header > nav > .edit-nav-item:last-child {
  display: none;
}

/* ---------- find / replace panel, right under the header ---------- */
html:root:root:root:root:root .edit .editor-search {
  order: -1;
  display: flex;
  flex-direction: column;
  flex-wrap: nowrap;
  gap: 8px;
  padding: 8px 10px 10px;
  border-bottom: 1px solid var(--em-line);
  background: var(--bg);
  white-space: normal;
}
html:root:root:root:root:root .edit .editor-search .es-row {
  display: flex;
  align-items: center;
  gap: 6px;
}
html:root:root:root:root:root .edit .editor-search .es-field {
  display: flex;
  flex: 1;
  align-items: center;
  min-width: 0;
  height: 40px;
  padding: 0 4px 0 10px;
  border: 1px solid var(--em-line);
  border-radius: 12px;
  background: var(--bg);
}
html:root:root:root:root:root .edit .editor-search .es-field:focus-within {
  border-color: var(--fill-7);
}
html:root:root:root:root:root .edit .editor-search .es-field.is-error {
  border-color: #e85600;
}
html:root:root:root:root:root .edit .editor-search .es-ico {
  flex: none;
  width: 18px;
  height: 18px;
  color: var(--fill-8);
}
html:root:root:root:root:root .edit .editor-search .es-field input {
  flex: 1;
  width: 100%;
  min-width: 0;
  height: 100%;
  padding: 0 8px;
  border: 0;
  border-radius: 0;
  outline: 0;
  background: transparent;
  color: var(--fg);
  field-sizing: fixed;
  font-size: 14px;
}
html:root:root:root:root:root .edit .editor-search .es-field input::-webkit-search-cancel-button {
  display: none;
}
html:root:root:root:root:root .edit .editor-search .es-x {
  display: flex;
  flex: none;
  align-items: center;
  justify-content: center;
  width: 30px;
  height: 30px;
  border-radius: 50%;
  color: var(--fill-8);
  cursor: pointer;
}
html:root:root:root:root:root .edit .editor-search .es-x svg {
  width: 16px;
  height: 16px;
}
html:root:root:root:root:root .edit .editor-search .es-x:hover,
html:root:root:root:root:root .edit .editor-search .es-x:focus {
  background: var(--em-press);
  color: var(--fg);
}
html:root:root:root:root:root .edit .editor-search .es-count {
  flex: none;
  min-width: 34px;
  margin: 0;
  padding: 6px 9px;
  border: 1px solid var(--em-line);
  border-radius: 999px;
  color: var(--fill-10);
  font-size: 12px;
  font-weight: 700;
  line-height: 1;
  text-align: center;
}
html:root:root:root:root:root .edit .editor-search .es-count.none {
  border-color: #e85600;
  color: #e85600;
}
html:root:root:root:root:root .edit .editor-search .es-btn,
html:root:root:root:root:root .edit .editor-search .es-text-btn,
html:root:root:root:root:root .edit .editor-search .toggle-button {
  flex: none;
  justify-content: center;
  height: 36px;
  margin: 0;
  border: 1px solid var(--em-line);
  border-radius: 10px;
  background: var(--bg);
  color: var(--fg);
  font-size: 13px;
  font-weight: 600;
}
html:root:root:root:root:root .edit .editor-search .es-btn {
  width: 36px;
  padding: 0;
}
html:root:root:root:root:root .edit .editor-search .es-btn svg {
  width: 18px;
  height: 18px;
}
html:root:root:root:root:root .edit .editor-search .es-text-btn {
  padding: 0 12px;
}
html:root:root:root:root:root .edit .editor-search .toggle-button {
  min-width: 42px;
  padding: 0 10px;
}
html:root:root:root:root:root .edit .editor-search .toggle-button.active {
  border-color: var(--fill-9);
  background: var(--fill-9);
  color: var(--bg);
}
html:root:root:root:root:root .edit .editor-search .es-btn:hover:not(:disabled),
html:root:root:root:root:root .edit .editor-search .es-text-btn:hover:not(:disabled) {
  background: var(--em-hover);
}
html:root:root:root:root:root .edit .editor-search .es-btn:disabled {
  opacity: .4;
}
html:root:root:root:root:root .edit .editor-search .es-goto {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-left: auto;
  color: var(--fill-10);
  font-size: 12px;
}
html:root:root:root:root:root .edit .editor-search .es-line {
  width: 8ch;
  min-width: 0;
  height: 36px;
  padding: 0 8px;
  border: 1px solid var(--em-line);
  border-radius: 10px;
  background: var(--bg);
  color: var(--fg);
  field-sizing: fixed;
  font-size: 13px;
  text-align: center;
}
""",
}


def apply_patches(root: Path):
    for i, (rel, old, new) in enumerate(PATCHES, 1):
        path = root / rel
        text = path.read_text(encoding='utf-8')
        count = text.count(old)
        if count != 1:
            sys.exit(f'[editor patch {i}] FAILED: anchor found {count}x (expected 1) in {rel}\n--- anchor ---\n{old}')
        path.write_text(text.replace(old, new), encoding='utf-8')
        print(f'[editor patch {i}] OK: {rel}')
    for rel, content in NEW_FILES.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding='utf-8')
        print(f'[new file] OK: {rel}')


if __name__ == '__main__':
    apply_patches(Path(sys.argv[1] if len(sys.argv) > 1 else '.'))
