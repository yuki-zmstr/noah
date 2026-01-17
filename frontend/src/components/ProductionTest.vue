<template>
  <div class="production-test">
    <div class="test-header">
      <h2>🧪 Noah Production Test</h2>
      <p>Testing basic message functionality in production environment</p>
    </div>

    <div
      class="test-status"
      :class="{ success: allTestsPassed, error: hasErrors }"
    >
      <h3>Test Status: {{ testStatus }}</h3>
      <div class="test-results">
        <div v-for="test in tests" :key="test.name" class="test-result">
          <span class="test-name">{{ test.name }}</span>
          <span class="test-status-icon" :class="test.status">
            {{
              test.status === "pass"
                ? "✅"
                : test.status === "fail"
                  ? "❌"
                  : "⏳"
            }}
          </span>
        </div>
      </div>
    </div>

    <div class="chat-test">
      <h3>💬 Chat Test</h3>
      <div class="messages" ref="messagesContainer">
        <div
          v-for="message in messages"
          :key="message.id"
          class="message"
          :class="message.sender"
        >
          <div class="message-content">
            <strong>{{ message.sender === "user" ? "You" : "Noah" }}:</strong>
            {{ message.content }}
          </div>
          <div class="message-time">{{ formatTime(message.timestamp) }}</div>
        </div>
      </div>

      <div class="input-area">
        <input
          v-model="currentMessage"
          @keyup.enter="sendMessage"
          placeholder="Type a test message..."
          :disabled="isLoading"
          class="message-input"
        />
        <button
          @click="sendMessage"
          :disabled="isLoading || !currentMessage.trim()"
          class="send-button"
        >
          {{ isLoading ? "⏳" : "📤" }}
        </button>
      </div>

      <div class="test-suggestions">
        <p>Try these test messages:</p>
        <button
          v-for="suggestion in testSuggestions"
          :key="suggestion"
          @click="sendTestMessage(suggestion)"
          :disabled="isLoading"
          class="suggestion-button"
        >
          {{ suggestion }}
        </button>
      </div>
    </div>

    <div class="test-actions">
      <button @click="runAllTests" :disabled="isLoading" class="test-button">
        {{ isLoading ? "Running Tests..." : "Run All Tests" }}
      </button>
      <button @click="clearMessages" class="clear-button">
        Clear Messages
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick } from "vue";

interface Message {
  id: string;
  sender: "user" | "noah";
  content: string;
  timestamp: Date;
}

interface TestResult {
  name: string;
  status: "pending" | "pass" | "fail";
  details?: string;
}

const messages = ref<Message[]>([]);
const currentMessage = ref("");
const isLoading = ref(false);
const messagesContainer = ref<HTMLElement>();

const tests = ref<TestResult[]>([
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

  if (pendingCount > 0) return "Running...";
  if (failCount > 0) return `${failCount} Failed, ${passCount} Passed`;
  return `All ${passCount} Tests Passed`;
});

const allTestsPassed = computed(() =>
  tests.value.every((t) => t.status === "pass"),
);

const hasErrors = computed(() => tests.value.some((t) => t.status === "fail"));

const apiBaseUrl =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api";

async function sendMessage() {
  if (!currentMessage.value.trim() || isLoading.value) return;

  const userMessage: Message = {
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
    const response = await fetch(
      `${apiBaseUrl}/v1/conversations/test-message`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          content: messageContent,
          user_id: "production-test-user",
        }),
      },
    );

    if (response.ok) {
      const data = await response.json();
      const botMessage: Message = {
        id: (Date.now() + 1).toString(),
        sender: "noah",
        content: data.bot_response,
        timestamp: new Date(),
      };
      messages.value.push(botMessage);
    } else {
      throw new Error(`HTTP ${response.status}`);
    }
  } catch (error) {
    const errorMessage: Message = {
      id: (Date.now() + 1).toString(),
      sender: "noah",
      content: `Error: ${error instanceof Error ? error.message : "Unknown error"}`,
      timestamp: new Date(),
    };
    messages.value.push(errorMessage);
  } finally {
    isLoading.value = false;
    await nextTick();
    scrollToBottom();
  }
}

function sendTestMessage(message: string) {
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
  } catch (error) {
    tests.value[0].status = "fail";
    tests.value[0].details =
      error instanceof Error ? error.message : "Unknown error";
  }

  // Test 2: API Configuration
  try {
    const response = await fetch(
      `${apiBaseUrl.replace("/api", "")}/api/config`,
    );
    tests.value[1].status = response.ok ? "pass" : "fail";
    tests.value[1].details = response.ok
      ? "API config accessible"
      : `HTTP ${response.status}`;
  } catch (error) {
    tests.value[1].status = "fail";
    tests.value[1].details =
      error instanceof Error ? error.message : "Unknown error";
  }

  // Test 3: Message Functionality
  try {
    const response = await fetch(
      `${apiBaseUrl}/v1/conversations/test-message`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content: "test", user_id: "test-user" }),
      },
    );
    tests.value[2].status = response.ok ? "pass" : "fail";
    tests.value[2].details = response.ok
      ? "Message functionality working"
      : `HTTP ${response.status}`;
  } catch (error) {
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
  } catch (error) {
    tests.value[3].status = "fail";
    tests.value[3].details =
      error instanceof Error ? error.message : "Unknown error";
  }

  isLoading.value = false;
}

function clearMessages() {
  messages.value = [];
}

function formatTime(date: Date): string {
  return date.toLocaleTimeString();
}

function scrollToBottom() {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
  }
}

// Run tests on component mount
runAllTests();
</script>

<style scoped>
.production-test {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
  font-family:
    -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
}

.test-header {
  text-align: center;
  margin-bottom: 30px;
}

.test-header h2 {
  color: #333;
  margin-bottom: 10px;
}

.test-status {
  background: #f5f5f5;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 30px;
  border-left: 4px solid #ccc;
}

.test-status.success {
  background: #f0f9f0;
  border-left-color: #28a745;
}

.test-status.error {
  background: #fdf2f2;
  border-left-color: #dc3545;
}

.test-results {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 10px;
  margin-top: 15px;
}

.test-result {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: white;
  border-radius: 4px;
  border: 1px solid #ddd;
}

.test-name {
  font-weight: 500;
}

.test-status-icon {
  font-size: 16px;
}

.chat-test {
  background: white;
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 20px;
}

.messages {
  height: 300px;
  overflow-y: auto;
  border: 1px solid #eee;
  border-radius: 4px;
  padding: 15px;
  margin-bottom: 15px;
  background: #fafafa;
}

.message {
  margin-bottom: 15px;
  padding: 10px;
  border-radius: 8px;
  max-width: 80%;
}

.message.user {
  background: #007bff;
  color: white;
  margin-left: auto;
  text-align: right;
}

.message.noah {
  background: #e9ecef;
  color: #333;
}

.message-content {
  margin-bottom: 5px;
}

.message-time {
  font-size: 0.8em;
  opacity: 0.7;
}

.input-area {
  display: flex;
  gap: 10px;
  margin-bottom: 15px;
}

.message-input {
  flex: 1;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.send-button {
  padding: 10px 15px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.send-button:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.test-suggestions {
  margin-bottom: 15px;
}

.test-suggestions p {
  margin-bottom: 10px;
  font-weight: 500;
}

.suggestion-button {
  margin: 5px;
  padding: 8px 12px;
  background: #f8f9fa;
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
}

.suggestion-button:hover:not(:disabled) {
  background: #e9ecef;
}

.suggestion-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.test-actions {
  display: flex;
  gap: 10px;
  justify-content: center;
}

.test-button {
  padding: 12px 24px;
  background: #28a745;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 500;
}

.test-button:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.clear-button {
  padding: 12px 24px;
  background: #6c757d;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 500;
}
</style>
