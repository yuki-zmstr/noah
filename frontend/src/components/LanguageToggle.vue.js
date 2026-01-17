import { ref, onMounted, onUnmounted } from "vue";
import { useLanguageStore } from "@/stores/language";
const { defineProps, defineSlots, defineEmits, defineExpose, defineModel, defineOptions, withDefaults, } = await import('vue');
const languageStore = useLanguageStore();
const isDropdownOpen = ref(false);
const toggleDropdown = () => {
    isDropdownOpen.value = !isDropdownOpen.value;
};
const selectLanguage = (language) => {
    languageStore.setLanguage(language);
    isDropdownOpen.value = false;
};
// Close dropdown when clicking outside
const handleClickOutside = (event) => {
    const target = event.target;
    if (!target.closest(".relative")) {
        isDropdownOpen.value = false;
    }
};
onMounted(() => {
    document.addEventListener("click", handleClickOutside);
});
onUnmounted(() => {
    document.removeEventListener("click", handleClickOutside);
});
const __VLS_fnComponent = (await import('vue')).defineComponent({});
;
let __VLS_functionalComponentProps;
function __VLS_template() {
    const __VLS_ctx = {};
    const __VLS_localComponents = {
        ...{},
        ...{},
        ...__VLS_ctx,
    };
    let __VLS_components;
    const __VLS_localDirectives = {
        ...{},
        ...__VLS_ctx,
    };
    let __VLS_directives;
    let __VLS_styleScopedClasses;
    let __VLS_resolvedLocalAndGlobalComponents;
    __VLS_elementAsFunction(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({ ...{ class: ("relative") }, });
    __VLS_elementAsFunction(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({ ...{ onClick: (__VLS_ctx.toggleDropdown) }, ...{ class: ("flex items-center space-x-2 px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-colors") }, title: (('Select language')), });
    __VLS_elementAsFunction(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({ ...{ class: ("text-lg") }, });
    (__VLS_ctx.languageStore.isEnglish ? "🇺🇸" : "🇯🇵");
    __VLS_elementAsFunction(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
    (__VLS_ctx.languageStore.languageLabel);
    __VLS_elementAsFunction(__VLS_intrinsicElements.svg, __VLS_intrinsicElements.svg)({ ...{ class: ("w-4 h-4 ml-1 transition-transform") }, ...{ class: (({ 'rotate-180': __VLS_ctx.isDropdownOpen })) }, fill: ("none"), stroke: ("currentColor"), viewBox: ("0 0 24 24"), });
    __VLS_elementAsFunction(__VLS_intrinsicElements.path)({ "stroke-linecap": ("round"), "stroke-linejoin": ("round"), "stroke-width": ("2"), d: ("M19 9l-7 7-7-7"), });
    if (__VLS_ctx.isDropdownOpen) {
        __VLS_elementAsFunction(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({ ...{ class: ("absolute right-0 mt-2 w-48 bg-white border border-gray-300 rounded-lg shadow-lg z-50") }, });
        __VLS_elementAsFunction(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({ ...{ class: ("py-1") }, });
        __VLS_elementAsFunction(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({ ...{ onClick: (...[$event]) => {
                    if (!((__VLS_ctx.isDropdownOpen)))
                        return;
                    __VLS_ctx.selectLanguage('english');
                } }, ...{ class: ("flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 transition-colors") }, ...{ class: (({ 'bg-primary-50 text-primary-700': __VLS_ctx.languageStore.isEnglish })) }, });
        __VLS_elementAsFunction(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({ ...{ class: ("text-lg mr-3") }, });
        __VLS_elementAsFunction(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
        if (__VLS_ctx.languageStore.isEnglish) {
            __VLS_elementAsFunction(__VLS_intrinsicElements.svg, __VLS_intrinsicElements.svg)({ ...{ class: ("w-4 h-4 ml-auto text-primary-600") }, fill: ("currentColor"), viewBox: ("0 0 20 20"), });
            __VLS_elementAsFunction(__VLS_intrinsicElements.path)({ "fill-rule": ("evenodd"), d: ("M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"), "clip-rule": ("evenodd"), });
        }
        __VLS_elementAsFunction(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({ ...{ onClick: (...[$event]) => {
                    if (!((__VLS_ctx.isDropdownOpen)))
                        return;
                    __VLS_ctx.selectLanguage('japanese');
                } }, ...{ class: ("flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 transition-colors") }, ...{ class: (({
                    'bg-primary-50 text-primary-700': __VLS_ctx.languageStore.isJapanese,
                })) }, });
        __VLS_elementAsFunction(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({ ...{ class: ("text-lg mr-3") }, });
        __VLS_elementAsFunction(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
        if (__VLS_ctx.languageStore.isJapanese) {
            __VLS_elementAsFunction(__VLS_intrinsicElements.svg, __VLS_intrinsicElements.svg)({ ...{ class: ("w-4 h-4 ml-auto text-primary-600") }, fill: ("currentColor"), viewBox: ("0 0 20 20"), });
            __VLS_elementAsFunction(__VLS_intrinsicElements.path)({ "fill-rule": ("evenodd"), d: ("M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"), "clip-rule": ("evenodd"), });
        }
    }
    __VLS_styleScopedClasses['relative'];
    __VLS_styleScopedClasses['flex'];
    __VLS_styleScopedClasses['items-center'];
    __VLS_styleScopedClasses['space-x-2'];
    __VLS_styleScopedClasses['px-3'];
    __VLS_styleScopedClasses['py-2'];
    __VLS_styleScopedClasses['text-sm'];
    __VLS_styleScopedClasses['font-medium'];
    __VLS_styleScopedClasses['text-gray-700'];
    __VLS_styleScopedClasses['bg-white'];
    __VLS_styleScopedClasses['border'];
    __VLS_styleScopedClasses['border-gray-300'];
    __VLS_styleScopedClasses['rounded-lg'];
    __VLS_styleScopedClasses['hover:bg-gray-50'];
    __VLS_styleScopedClasses['focus:outline-none'];
    __VLS_styleScopedClasses['focus:ring-2'];
    __VLS_styleScopedClasses['focus:ring-primary-500'];
    __VLS_styleScopedClasses['focus:border-transparent'];
    __VLS_styleScopedClasses['transition-colors'];
    __VLS_styleScopedClasses['text-lg'];
    __VLS_styleScopedClasses['w-4'];
    __VLS_styleScopedClasses['h-4'];
    __VLS_styleScopedClasses['ml-1'];
    __VLS_styleScopedClasses['transition-transform'];
    __VLS_styleScopedClasses['absolute'];
    __VLS_styleScopedClasses['right-0'];
    __VLS_styleScopedClasses['mt-2'];
    __VLS_styleScopedClasses['w-48'];
    __VLS_styleScopedClasses['bg-white'];
    __VLS_styleScopedClasses['border'];
    __VLS_styleScopedClasses['border-gray-300'];
    __VLS_styleScopedClasses['rounded-lg'];
    __VLS_styleScopedClasses['shadow-lg'];
    __VLS_styleScopedClasses['z-50'];
    __VLS_styleScopedClasses['py-1'];
    __VLS_styleScopedClasses['flex'];
    __VLS_styleScopedClasses['items-center'];
    __VLS_styleScopedClasses['w-full'];
    __VLS_styleScopedClasses['px-4'];
    __VLS_styleScopedClasses['py-2'];
    __VLS_styleScopedClasses['text-sm'];
    __VLS_styleScopedClasses['text-gray-700'];
    __VLS_styleScopedClasses['hover:bg-gray-50'];
    __VLS_styleScopedClasses['transition-colors'];
    __VLS_styleScopedClasses['text-lg'];
    __VLS_styleScopedClasses['mr-3'];
    __VLS_styleScopedClasses['w-4'];
    __VLS_styleScopedClasses['h-4'];
    __VLS_styleScopedClasses['ml-auto'];
    __VLS_styleScopedClasses['text-primary-600'];
    __VLS_styleScopedClasses['flex'];
    __VLS_styleScopedClasses['items-center'];
    __VLS_styleScopedClasses['w-full'];
    __VLS_styleScopedClasses['px-4'];
    __VLS_styleScopedClasses['py-2'];
    __VLS_styleScopedClasses['text-sm'];
    __VLS_styleScopedClasses['text-gray-700'];
    __VLS_styleScopedClasses['hover:bg-gray-50'];
    __VLS_styleScopedClasses['transition-colors'];
    __VLS_styleScopedClasses['text-lg'];
    __VLS_styleScopedClasses['mr-3'];
    __VLS_styleScopedClasses['w-4'];
    __VLS_styleScopedClasses['h-4'];
    __VLS_styleScopedClasses['ml-auto'];
    __VLS_styleScopedClasses['text-primary-600'];
    var __VLS_slots;
    var __VLS_inheritedAttrs;
    const __VLS_refs = {};
    var $refs;
    return {
        slots: __VLS_slots,
        refs: $refs,
        attrs: {},
    };
}
;
const __VLS_self = (await import('vue')).defineComponent({
    setup() {
        return {
            languageStore: languageStore,
            isDropdownOpen: isDropdownOpen,
            toggleDropdown: toggleDropdown,
            selectLanguage: selectLanguage,
        };
    },
});
export default (await import('vue')).defineComponent({
    setup() {
        return {};
    },
});
;
