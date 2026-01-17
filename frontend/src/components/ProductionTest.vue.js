import { ref, computed, nextTick } from "vue";
const { defineProps, defineSlots, defineEmits, defineExpose, defineModel, defineOptions, withDefaults, } = await import('vue');
const messages = ref([]);
const currentMessage = ref("");
const isLoading = ref(false);
const messagesContainer = ref();
const tests = ref([
    { name: "Backend Health Check", status: "pending" },
    { name: "API Configuration", status: "pending" },
    { name: "Message Functionality", status: "pending" },
    { name: "Database Connection", status: "pending" },
]);
const testSuggestions = [
    "Hello Noah!",
    "Recommend a book",
    "Help me find something to read",
    "Test message",
];
const testStatus = computed(() => {
    const passCount = tests.value.filter((t) => t.status === "pass").length;
    const failCount = tests.value.filter((t) => t.status === "fail").length;
    const pendingCount = tests.value.filter((t) => t.status === "pending").length;
    if (pendingCount > 0)
        return "Running...";
    if (failCount > 0)
        return `${failCount} Failed, ${passCount} Passed`;
    return `All ${passCount} Tests Passed`;
});
const allTestsPassed = computed(() => tests.value.every((t) => t.status === "pass"));
const hasErrors = computed(() => tests.value.some((t) => t.status === "fail"));
const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api";
async function sendMessage() {
    if (!currentMessage.value.trim() || isLoading.value)
        return;
    const userMessage = {
        id: Date.now().toString(),
        sender: "user",
        content: currentMessage.value,
        timestamp: new Date(),
    };
    messages.value.push(userMessage);
    const messageContent = currentMessage.value;
    currentMessage.value = "";
    isLoading.value = true;
    try {
        const response = await fetch(`${apiBaseUrl}/v1/conversations/test-message`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                content: messageContent,
                user_id: "production-test-user",
            }),
        });
        if (response.ok) {
            const data = await response.json();
            const botMessage = {
                id: (Date.now() + 1).toString(),
                sender: "noah",
                content: data.bot_response,
                timestamp: new Date(),
            };
            messages.value.push(botMessage);
        }
        else {
            throw new Error(`HTTP ${response.status}`);
        }
    }
    catch (error) {
        const errorMessage = {
            id: (Date.now() + 1).toString(),
            sender: "noah",
            content: `Error: ${error instanceof Error ? error.message : "Unknown error"}`,
            timestamp: new Date(),
        };
        messages.value.push(errorMessage);
    }
    finally {
        isLoading.value = false;
        await nextTick();
        scrollToBottom();
    }
}
function sendTestMessage(message) {
    currentMessage.value = message;
    sendMessage();
}
async function runAllTests() {
    isLoading.value = true;
    // Reset all tests
    tests.value.forEach((test) => (test.status = "pending"));
    // Test 1: Backend Health Check
    try {
        const response = await fetch(`${apiBaseUrl.replace("/api", "")}/health`);
        tests.value[0].status = response.ok ? "pass" : "fail";
        tests.value[0].details = response.ok
            ? "Backend is healthy"
            : `HTTP ${response.status}`;
    }
    catch (error) {
        tests.value[0].status = "fail";
        tests.value[0].details =
            error instanceof Error ? error.message : "Unknown error";
    }
    // Test 2: API Configuration
    try {
        const response = await fetch(`${apiBaseUrl.replace("/api", "")}/api/config`);
        tests.value[1].status = response.ok ? "pass" : "fail";
        tests.value[1].details = response.ok
            ? "API config accessible"
            : `HTTP ${response.status}`;
    }
    catch (error) {
        tests.value[1].status = "fail";
        tests.value[1].details =
            error instanceof Error ? error.message : "Unknown error";
    }
    // Test 3: Message Functionality
    try {
        const response = await fetch(`${apiBaseUrl}/v1/conversations/test-message`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ content: "test", user_id: "test-user" }),
        });
        tests.value[2].status = response.ok ? "pass" : "fail";
        tests.value[2].details = response.ok
            ? "Message functionality working"
            : `HTTP ${response.status}`;
    }
    catch (error) {
        tests.value[2].status = "fail";
        tests.value[2].details =
            error instanceof Error ? error.message : "Unknown error";
    }
    // Test 4: Database Connection (via conversation health)
    try {
        const response = await fetch(`${apiBaseUrl}/v1/conversations/health`);
        tests.value[3].status = response.ok ? "pass" : "fail";
        tests.value[3].details = response.ok
            ? "Database connection working"
            : `HTTP ${response.status}`;
    }
    catch (error) {
        tests.value[3].status = "fail";
        tests.value[3].details =
            error instanceof Error ? error.message : "Unknown error";
    }
    isLoading.value = false;
}
function clearMessages() {
    messages.value = [];
}
function formatTime(date) {
    return date.toLocaleTimeString();
}
function scrollToBottom() {
    if (messagesContainer.value) {
        messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
    }
}
// Run tests on component mount
runAllTests();
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
    __VLS_styleScopedClasses['test-header'];
    __VLS_styleScopedClasses['test-status'];
    __VLS_styleScopedClasses['test-status'];
    __VLS_styleScopedClasses['message'];
    __VLS_styleScopedClasses['message'];
    __VLS_styleScopedClasses['send-button'];
    __VLS_styleScopedClasses['test-suggestions'];
    __VLS_styleScopedClasses['suggestion-button'];
    __VLS_styleScopedClasses['suggestion-button'];
    __VLS_styleScopedClasses['test-button'];
    // CSS variable injection 
    // CSS variable injection end 
    let __VLS_resolvedLocalAndGlobalComponents;
    __VLS_elementAsFunction(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({ ...{ class: ("production-test") }, });
    __VLS_elementAsFunction(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({ ...{ class: ("test-header") }, });
    __VLS_elementAsFunction(__VLS_intrinsicElements.h2, __VLS_intrinsicElements.h2)({});
    __VLS_elementAsFunction(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({});
    __VLS_elementAsFunction(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({ ...{ class: ("test-status") }, ...{ class: (({ success: __VLS_ctx.allTestsPassed, error: __VLS_ctx.hasErrors })) }, });
    __VLS_elementAsFunction(__VLS_intrinsicElements.h3, __VLS_intrinsicElements.h3)({});
    (__VLS_ctx.testStatus);
    __VLS_elementAsFunction(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({ ...{ class: ("test-results") }, });
    for (const [test] of __VLS_getVForSourceType((__VLS_ctx.tests))) {
        __VLS_elementAsFunction(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({ key: ((test.name)), ...{ class: ("test-result") }, });
        __VLS_elementAsFunction(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({ ...{ class: ("test-name") }, });
        (test.name);
        __VLS_elementAsFunction(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({ ...{ class: ("test-status-icon") }, ...{ class: ((test.status)) }, });
        (test.status === "pass"
            ? "✅"
            : test.status === "fail"
                ? "❌"
                : "⏳");
    }
    __VLS_elementAsFunction(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({ ...{ class: ("chat-test") }, });
    __VLS_elementAsFunction(__VLS_intrinsicElements.h3, __VLS_intrinsicElements.h3)({});
    __VLS_elementAsFunction(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({ ...{ class: ("messages") }, ref: ("messagesContainer"), });
    // @ts-ignore navigation for `const messagesContainer = ref()`
    __VLS_ctx.messagesContainer;
    for (const [message] of __VLS_getVForSourceType((__VLS_ctx.messages))) {
        __VLS_elementAsFunction(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({ key: ((message.id)), ...{ class: ("message") }, ...{ class: ((message.sender)) }, });
        __VLS_elementAsFunction(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({ ...{ class: ("message-content") }, });
        __VLS_elementAsFunction(__VLS_intrinsicElements.strong, __VLS_intrinsicElements.strong)({});
        (message.sender === "user" ? "You" : "Noah");
        (message.content);
        __VLS_elementAsFunction(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({ ...{ class: ("message-time") }, });
        (__VLS_ctx.formatTime(message.timestamp));
    }
    __VLS_elementAsFunction(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({ ...{ class: ("input-area") }, });
    __VLS_elementAsFunction(__VLS_intrinsicElements.input)({ ...{ onKeyup: (__VLS_ctx.sendMessage) }, placeholder: ("Type a test message..."), disabled: ((__VLS_ctx.isLoading)), ...{ class: ("message-input") }, });
    (__VLS_ctx.currentMessage);
    __VLS_elementAsFunction(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({ ...{ onClick: (__VLS_ctx.sendMessage) }, disabled: ((__VLS_ctx.isLoading || !__VLS_ctx.currentMessage.trim())), ...{ class: ("send-button") }, });
    (__VLS_ctx.isLoading ? "⏳" : "📤");
    __VLS_elementAsFunction(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({ ...{ class: ("test-suggestions") }, });
    __VLS_elementAsFunction(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({});
    for (const [suggestion] of __VLS_getVForSourceType((__VLS_ctx.testSuggestions))) {
        __VLS_elementAsFunction(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({ ...{ onClick: (...[$event]) => {
                    __VLS_ctx.sendTestMessage(suggestion);
                } }, key: ((suggestion)), disabled: ((__VLS_ctx.isLoading)), ...{ class: ("suggestion-button") }, });
        (suggestion);
    }
    __VLS_elementAsFunction(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({ ...{ class: ("test-actions") }, });
    __VLS_elementAsFunction(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({ ...{ onClick: (__VLS_ctx.runAllTests) }, disabled: ((__VLS_ctx.isLoading)), ...{ class: ("test-button") }, });
    (__VLS_ctx.isLoading ? "Running Tests..." : "Run All Tests");
    __VLS_elementAsFunction(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({ ...{ onClick: (__VLS_ctx.clearMessages) }, ...{ class: ("clear-button") }, });
    __VLS_styleScopedClasses['production-test'];
    __VLS_styleScopedClasses['test-header'];
    __VLS_styleScopedClasses['test-status'];
    __VLS_styleScopedClasses['test-results'];
    __VLS_styleScopedClasses['test-result'];
    __VLS_styleScopedClasses['test-name'];
    __VLS_styleScopedClasses['test-status-icon'];
    __VLS_styleScopedClasses['chat-test'];
    __VLS_styleScopedClasses['messages'];
    __VLS_styleScopedClasses['message'];
    __VLS_styleScopedClasses['message-content'];
    __VLS_styleScopedClasses['message-time'];
    __VLS_styleScopedClasses['input-area'];
    __VLS_styleScopedClasses['message-input'];
    __VLS_styleScopedClasses['send-button'];
    __VLS_styleScopedClasses['test-suggestions'];
    __VLS_styleScopedClasses['suggestion-button'];
    __VLS_styleScopedClasses['test-actions'];
    __VLS_styleScopedClasses['test-button'];
    __VLS_styleScopedClasses['clear-button'];
    var __VLS_slots;
    var __VLS_inheritedAttrs;
    const __VLS_refs = {
        "messagesContainer": __VLS_nativeElements['div'],
    };
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
            messages: messages,
            currentMessage: currentMessage,
            isLoading: isLoading,
            messagesContainer: messagesContainer,
            tests: tests,
            testSuggestions: testSuggestions,
            testStatus: testStatus,
            allTestsPassed: allTestsPassed,
            hasErrors: hasErrors,
            sendMessage: sendMessage,
            sendTestMessage: sendTestMessage,
            runAllTests: runAllTests,
            clearMessages: clearMessages,
            formatTime: formatTime,
        };
    },
});
export default (await import('vue')).defineComponent({
    setup() {
        return {};
    },
});
;
