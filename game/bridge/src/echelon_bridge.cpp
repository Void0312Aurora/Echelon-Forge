#include "echelon_bridge_protocol.h"

#include <winsock2.h>
#include <ws2tcpip.h>

#include <algorithm>
#include <array>
#include <charconv>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <mutex>
#include <optional>
#include <sstream>
#include <string>
#include <string_view>

namespace {

using CallbackProc = int (*)(char const* name, char const* function, char const* data);

constexpr std::string_view kVersion = "echelon_bridge 0.1.0";
constexpr int kOk = 0;
constexpr int kInvalidArgs = 1;
constexpr int kBackendUnavailable = 2;
constexpr int kProtocolError = 3;

std::string sanitize_field(std::string_view value) {
    std::string out;
    out.reserve(value.size());
    for (char c : value) {
        if (c == '\r' || c == '\n' || c == '\t') {
            out.push_back(' ');
        } else {
            out.push_back(c);
        }
    }
    return out;
}

void write_output(char* output, unsigned int output_size, std::string_view text) {
    if (output == nullptr || output_size == 0) {
        return;
    }
    const std::size_t max_len = static_cast<std::size_t>(output_size - 1);
    const std::size_t len = std::min(max_len, text.size());
    std::memcpy(output, text.data(), len);
    output[len] = '\0';
}

bool parse_port(std::string_view text, std::uint16_t& out_port) {
    unsigned int parsed = 0;
    const auto* first = text.data();
    const auto* last = text.data() + text.size();
    const auto result = std::from_chars(first, last, parsed);
    if (result.ec != std::errc{} || result.ptr != last || parsed > 65535U) {
        return false;
    }
    out_port = static_cast<std::uint16_t>(parsed);
    return true;
}

class WinsockRuntime {
public:
    WinsockRuntime() {
        WSADATA data{};
        ready_ = (WSAStartup(MAKEWORD(2, 2), &data) == 0);
    }

    ~WinsockRuntime() {
        if (ready_) {
            WSACleanup();
        }
    }

    bool ready() const {
        return ready_;
    }

private:
    bool ready_ = false;
};

class TcpClient {
public:
    ~TcpClient() {
        close();
    }

    bool connected() const {
        return socket_ != INVALID_SOCKET;
    }

    void close() {
        if (socket_ != INVALID_SOCKET) {
            closesocket(socket_);
            socket_ = INVALID_SOCKET;
        }
    }

    bool connect_to(const epx::BackendConfig& config, std::string& error) {
        if (connected()) {
            return true;
        }

        sockaddr_in addr{};
        addr.sin_family = AF_INET;
        addr.sin_port = htons(config.port);
        if (inet_pton(AF_INET, config.host.c_str(), &addr.sin_addr) != 1) {
            error = "invalid_backend_host";
            return false;
        }

        socket_ = ::socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
        if (socket_ == INVALID_SOCKET) {
            error = "socket_create_failed";
            return false;
        }

        DWORD timeout_ms = 50;
        setsockopt(socket_, SOL_SOCKET, SO_RCVTIMEO,
            reinterpret_cast<const char*>(&timeout_ms), sizeof(timeout_ms));
        setsockopt(socket_, SOL_SOCKET, SO_SNDTIMEO,
            reinterpret_cast<const char*>(&timeout_ms), sizeof(timeout_ms));

        if (::connect(socket_, reinterpret_cast<sockaddr*>(&addr), sizeof(addr)) ==
            SOCKET_ERROR) {
            error = "backend_connect_failed";
            close();
            return false;
        }

        return true;
    }

    bool request_line(
        const epx::BackendConfig& config,
        std::string_view request,
        std::string& response,
        std::string& error
    ) {
        if (!connect_to(config, error)) {
            return false;
        }

        const std::string line = std::string(request) + "\n";
        const int sent = ::send(socket_, line.data(), static_cast<int>(line.size()), 0);
        if (sent != static_cast<int>(line.size())) {
            error = "backend_send_failed";
            close();
            return false;
        }

        std::array<char, 4096> buffer{};
        const int received =
            ::recv(socket_, buffer.data(), static_cast<int>(buffer.size() - 1), 0);
        if (received <= 0) {
            error = "backend_recv_failed";
            close();
            return false;
        }

        buffer[static_cast<std::size_t>(received)] = '\0';
        response.assign(buffer.data(), static_cast<std::size_t>(received));
        while (!response.empty() &&
               (response.back() == '\n' || response.back() == '\r')) {
            response.pop_back();
        }
        return true;
    }

private:
    SOCKET socket_ = INVALID_SOCKET;
};

struct BridgeRuntime {
    std::mutex mutex;
    WinsockRuntime winsock;
    TcpClient client;
    epx::BackendConfig backend;
    epx::ProxyStateCache cache;
    CallbackProc callback = nullptr;
};

BridgeRuntime& runtime() {
    static BridgeRuntime state;
    return state;
}

void emit_callback(std::string_view function, std::string_view data) {
    auto& state = runtime();
    if (state.callback == nullptr) {
        return;
    }
    const std::string fn = std::string(function);
    const std::string payload = std::string(data);
    state.callback("echelon_proxy", fn.c_str(), payload.c_str());
}

std::string join_context(const char** argv, unsigned int argc) {
    std::ostringstream out;
    for (unsigned int i = 0; i < argc; ++i) {
        if (i != 0U) {
            out << '|';
        }
        out << sanitize_field(argv[i] == nullptr ? "" : argv[i]);
    }
    return out.str();
}

int handle_command(
    std::string_view function,
    const char** argv,
    unsigned int argc,
    std::string& output
) {
    auto& state = runtime();
    std::scoped_lock lock(state.mutex);

    if (function == "version") {
        output = std::string(kVersion);
        return kOk;
    }

    if (function == "ping") {
        output = "pong";
        return kOk;
    }

    if (function == "configure_backend") {
        if (argc < 3U) {
            output = "configure_backend requires [host, port, sessionId]";
            return kInvalidArgs;
        }
        std::uint16_t port = 0;
        if (!parse_port(argv[1] == nullptr ? "" : argv[1], port)) {
            output = "invalid_port";
            return kInvalidArgs;
        }
        state.backend.host = sanitize_field(argv[0] == nullptr ? "" : argv[0]);
        state.backend.port = port;
        state.backend.session_id = sanitize_field(argv[2] == nullptr ? "" : argv[2]);
        state.client.close();
        output = "ok";
        return kOk;
    }

    if (function == "begin_session") {
        if (argc < 3U) {
            output = "begin_session requires [sessionId, worldName, proxyClass]";
            return kInvalidArgs;
        }
        state.backend.session_id = sanitize_field(argv[0] == nullptr ? "" : argv[0]);
        const std::string world = sanitize_field(argv[1] == nullptr ? "" : argv[1]);
        const std::string proxy_class = sanitize_field(argv[2] == nullptr ? "" : argv[2]);
        const std::string request = "begin_session\t" + state.backend.session_id +
            "\t" + world + "\t" + proxy_class;
        std::string response;
        std::string error;
        if (!state.winsock.ready()) {
            output = "winsock_not_ready";
            return kBackendUnavailable;
        }
        if (!state.client.request_line(state.backend, request, response, error)) {
            state.cache.last_error = error;
            output = error;
            return kBackendUnavailable;
        }
        state.cache.session_active = true;
        state.cache.last_backend_line = response;
        output = response;
        emit_callback("session", response);
        return kOk;
    }

    if (function == "submit_host_frame") {
        if (argc < 1U) {
            output = "submit_host_frame requires [sqfPayload]";
            return kInvalidArgs;
        }
        const std::string payload = sanitize_field(argv[0] == nullptr ? "" : argv[0]);
        state.cache.last_host_frame_sqf = payload;
        state.cache.frame_counter += 1U;

        if (!state.cache.session_active) {
            output = "session_not_active";
            return kInvalidArgs;
        }
        if (!state.winsock.ready()) {
            output = "winsock_not_ready";
            return kBackendUnavailable;
        }

        const std::string request = "host_frame\t" + state.backend.session_id + "\t" +
            sanitize_field(state.cache.last_context) + "\t" + payload;
        std::string response;
        std::string error;
        if (!state.client.request_line(state.backend, request, response, error)) {
            state.cache.last_error = error;
            output = error;
            return kBackendUnavailable;
        }

        state.cache.last_backend_line = response;
        if (response.rfind("proxy_state\t", 0) == 0) {
            state.cache.sqf_payload = response.substr(std::strlen("proxy_state\t"));
        }
        output = response;
        return kOk;
    }

    if (function == "fetch_proxy_state") {
        output = state.cache.sqf_payload;
        return kOk;
    }

    if (function == "inject_proxy_state") {
        if (argc < 1U) {
            output = "inject_proxy_state requires [sqfPayload]";
            return kInvalidArgs;
        }
        state.cache.sqf_payload = sanitize_field(argv[0] == nullptr ? "" : argv[0]);
        output = "ok";
        return kOk;
    }

    if (function == "shutdown") {
        const std::string session =
            argc >= 1U ? sanitize_field(argv[0] == nullptr ? "" : argv[0])
                       : state.backend.session_id;
        const std::string request = "shutdown\t" + session;
        std::string response;
        std::string error;
        if (state.winsock.ready()) {
            if (!state.client.request_line(state.backend, request, response, error)) {
                state.cache.last_error = error;
                output = error;
                state.client.close();
                state.cache.session_active = false;
                return kBackendUnavailable;
            }
            state.cache.last_backend_line = response;
            output = response;
        } else {
            output = "winsock_not_ready";
        }
        state.client.close();
        state.cache.session_active = false;
        emit_callback("session", "shutdown");
        return kOk;
    }

    output = "unknown_function";
    return kInvalidArgs;
}

}  // namespace

extern "C" {

__declspec(dllexport) void __stdcall RVExtensionVersion(
    char* output,
    unsigned int outputSize
) {
    write_output(output, outputSize, kVersion);
}

__declspec(dllexport) void __stdcall RVExtension(
    char* output,
    unsigned int outputSize,
    const char* function
) {
    std::string out;
    (void)handle_command(function == nullptr ? "" : function, nullptr, 0U, out);
    write_output(output, outputSize, out);
}

__declspec(dllexport) int __stdcall RVExtensionArgs(
    char* output,
    unsigned int outputSize,
    const char* function,
    const char** argv,
    unsigned int argc
) {
    std::string out;
    const int code =
        handle_command(function == nullptr ? "" : function, argv, argc, out);
    write_output(output, outputSize, out);
    return code;
}

__declspec(dllexport) void __stdcall RVExtensionRegisterCallback(
    int (*callbackProc)(char const* name, char const* function, char const* data)
) {
    auto& state = runtime();
    std::scoped_lock lock(state.mutex);
    state.callback = callbackProc;
}

__declspec(dllexport) void __stdcall RVExtensionContext(
    const char** argv,
    unsigned int argc
) {
    auto& state = runtime();
    std::scoped_lock lock(state.mutex);
    state.cache.last_context = join_context(argv, argc);
}

}  // extern "C"
